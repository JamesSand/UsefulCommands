# 方向二：让 video speculator 在推理中越变越好（在线/持续学习 + 与 Aurora 结合）

> **背景**：种子论文 SDVG（arXiv:2604.17397）是 **training-free** 的视频自回归 speculative decoding——1.3B drafter 出块、ImageReward 路由器逐块接受/拒绝、14B target 重生成被拒块。目标：让 **drafter 在服务过程中在线自我改进**，并尽量与 Together 的 **Aurora** 融合。
> **调研方法**：Semantic Scholar 引用/参考图谱 + WebSearch + 逐篇到 arXiv/官博/GitHub 核实（详见第五节可信度分级）。
> **调研日期**：2026-06-01。
> **三条硬约束**（决定一个方法能不能搬过来）：
> (a) **连续时空块**，不是离散 token；(b) **没有 token 级 logit 分布**可供蒸馏/精确拒绝采样；(c) 接受/拒绝信号来自 **reward 模型路由（ImageReward）**，不是精确匹配验证。

---

## TL;DR

1. **你的直觉完全成立，而且已经有现成蓝图**：**Aurora 本身就是"在线自我改进的 speculator"**——它让 draft model 在**线上服务时**持续从 target/真实流量学习、异步热替换权重。这正是你想对 video speculator 做的事，只不过 Aurora 目前只做 **LLM（token 级）**。
2. **Aurora 不是孤例，它有产品化前身 ATLAS**（Together，NeurIPS 2025）：**静态 speculator 当"速度地板" + 轻量自适应 speculator 在线学习 + 控制器**，对 vLLM baseline 最高 **4×**。**ATLAS 的"双 speculator + 控制器"架构是可以直接照搬的骨架**（详解见下方第一节「§1.5 双 speculator + 控制器到底是什么」）。
3. **能直接 apply 的方法是有的，但都需要一处"手术"**：把 Aurora/OSD 那套**针对离散 token 的 logit-KD 损失**，换成 **连续块损失 + 用 ImageReward 接受/拒绝当奖励**。好消息是——**SDVG 拒绝一个块时本来就会让 14B target 重生成那个块，这个重生成块就是天然的、已经付过费的"teacher 目标"**，不用额外算力。
4. **推荐落地路线**：**以 Aurora/ATLAS 为骨架** + 三处 SDVG 专属替换（连续块损失 / ImageReward 当奖励 / 长视频内"边生成边自适应"）。另有两个**不需要训练**的"接受率增强器"可以叠加：**DAS**（reward 加权重采样）和 **Pathwise 测试时校正**（长视频稳定化）。

---

## 一、Aurora 是什么，它是否在做"在线 speculator 学习"？

**是，几乎就是你要的东西。这是本方向最对口的参考。**

**Aurora: Online-Adaptive / Self-Improving Speculative Decoding** — Together AI + Princeton 等（Junxiong Wang, …, Tri Dao, Percy Liang, Ce Zhang, Ben Athiwaratkun, Shuaiwen Leon Song, Chenfeng Xu, Xiaoxia Wu）。
- 论文 [arXiv:2602.06932](https://arxiv.org/abs/2602.06932) · 代码 [github.com/togethercomputer/aurora](https://github.com/togethercomputer/aurora) · 博客 [together.ai/blog/aurora](https://www.together.ai/blog/aurora) ✅已核实

**核心机制（"serve-to-train 飞轮"，训练与推理解耦）**：
- **SGLang 推理服务器**跑 speculative decoding，把每次推理的「接受/拒绝结果 + hidden states」异步流入一个分布式、线程安全的 LRU 数据 buffer。
- **独立的异步训练服务器**从 buffer 取 batch、做梯度更新，把新 speculator 权重**热替换（hot-swap）**回推理服务器，**不中断服务**。
- **异步 RL 形式化**：策略 = draft model；环境 = target + verifier 返回接受/拒绝；奖励 = 最大化**接受长度**（每次验证步通过的 token 数）。接受 token = 正向（模仿）反馈；被拒分支 = **反事实负反馈**。
- **"Discard Sampling"（丢弃采样）**：损失 = (i) **接受损失**（在接受 token 上的交叉熵）+ (ii) **拒绝损失**（top-k 过滤的 KL，权重 λ，把概率质量**推离**被拒分支——教 drafter "别提议什么"）。主要在大 lookahead(~10) 有用，lookahead~5 时收益小。
- **训练信号 = EAGLE-3 式 hidden states + target logits**（拼了 target 三层 early/mid/late 的 hidden states + 输出 logits + token 序列 + 拒绝轨迹）。**→ 注意：Aurora 本质是个依赖 target logits/hidden states 的 EAGLE-3 式 drafter。**
- **Tree attention**：把整棵投机树（接受+拒绝分支）在一次 batched 前/反向里训完。
- **陈旧度（staleness）处理**：同步节奏可调，"适度懒"（如每 48 个请求同步一次）是 Pareto 甜点；同步太勤反而伤吞吐/缓存有效性。

**数字**：混合流量下接受长度从 1.0 → **3.08**（静态预训练只有 2.63）；有序域漂移流量下约 **1 万条请求**恢复到 ~2.46；比训练良好的静态 speculator 再快 **1.25×**；前沿大模型（MiniMax M2.1 229B、Qwen3-Coder-Next 80B）day-0 约 **1.45–1.51×**。在 5 个领域 44k prompt 上测试。

**重要背景——ATLAS 是 Aurora 的产品化前身**：
**ATLAS（AdapTive-LeArning Speculator System）**，Together，**NeurIPS 2025**（[官博](https://www.together.ai/blog/adaptive-learning-speculator-system-atlas)）。已部署的**双 speculator 系统**：一个**静态 speculator 当"速度地板"** + 一个**轻量自适应 speculator 从实时流量学习**，外加一个**控制器**——随着自适应模型变强，越来越多地依赖它并**拉长 lookahead**。对 FP8/vLLM baseline 最高 **400%（4×）**加速（DeepSeek, ~500 tok/s, BS=1, 4×B200）。

> **谱系**：ATLAS（产品，运行时学习，NeurIPS'25）→ Aurora（开源 RL 研究框架，arXiv 2602.06932）。对你的项目，**ATLAS 的"静态+自适应双 drafter + 控制器"是可直接复用的架构模式**。

### §1.5 「双 speculator + 控制器」到底是什么（ATLAS 的核心架构）

**先讲它要解决的痛点**：一个"纯在线自适应"的 speculator 有个**下行风险**——投机解码只有在 drafter 提议的**接受率够高**时才加速；接受率一旦低，你白算了 draft、还得 target 验证，**反而更慢**。而自适应 speculator 偏偏在「冷启动」「刚遇到新 domain」「学跑偏/漂移」这几种时刻，接受率最不确定甚至很差。所以"只押一个会变的 speculator"= 把吞吐压在一个不稳定的东西上。

ATLAS 的解法是**同时养两个 speculator，再加一个控制器来仲裁**：

1. **静态 speculator（速度地板 / speed floor）**：一个**冻结的、广泛预训练**的 draft 模型，**永不更新 → 永不变差**。它在通用流量上保证一个**保底接受率**——就是安全网，**最坏情况下你至少有通用 speculator 的速度，永远不会更慢**。

2. **自适应 speculator（自适应头）**：一个**轻量**的 draft 模型，用 Aurora 式 serve-to-train 飞轮**从实时流量持续学习**。在熟悉/稳定的 domain 上它能**远超**静态那个（接受长度更长 → 加速更大）；但它"有脾气"——冷启动/漂移时质量不保。

3. **控制器（controller）**：一个**运行时策略**，逐请求/逐步决定两件事——
   - **信谁**：用静态、还是用自适应（或怎么混合）。判据是**实测接受率 / 置信度**（confidence-aware）。
   - **看多远（lookahead / 投机深度 K）**：投机解码里 drafter 一次提议 K 个 token（视频里是 K 个**块**）。**接受率高时，K 越大 → 一次 target 验证能过越多 token → 加速越大**；接受率低时，大 K 纯属浪费（提议大半被拒）。所以——**自适应模型越被验证证明靠谱，控制器就越信它、并把 K 拉长**；一旦置信度掉 / 检测到漂移，就**缩短 K 或切回静态路径**，边保延迟边让自适应模型重学。

```
                      ┌──────────────────────────────┐
   请求 ──────────────▶          控制器 controller       │ ◀── 实测接受率/置信度
                      │   选 静态/自适应 + 调 lookahead K   │
                      └────────┬───────────────┬───────┘
                               │               │
              ┌────────────────▼──┐      ┌──────▼─────────────────┐
              │  静态 speculator   │      │  自适应 speculator       │
              │ (冻结·速度地板)    │      │ (在线学·Aurora 飞轮)     │
              │ 永不变差·保底接受率 │      │ 熟域远超·冷启动/漂移时弱  │
              └────────────────┬──┘      └──────┬─────────────────┘
                               │                │
                               ▼                ▼
                       target 验证 (接受/拒绝) ───┐
                               ▲                  │ 接受/拒绝信号
                               └──────────────────┘ →（① 喂自适应头训练 ② 喂控制器决策）
```

**为什么这个设计是关键（核心洞察）**：它把**「稳定-可塑性」权衡直接焊进了架构**——静态 = 稳定（不会被遗忘），自适应 = 可塑（学新域），控制器仲裁。结果是：**你拿到了在线自适应的上行收益，却没有它的下行风险**——最坏也不会比通用静态 speculator 更慢。换句话说，它把"灾难性遗忘 / 学跑偏"从「吞吐崩盘的风险」降级成「顶多少赚一点」的风险。**这就是它能直接照搬当骨架的原因**（也是方向三防遗忘配方的第一块基石）。

**数字**：对 FP8/vLLM baseline 最高 **4×**（DeepSeek, ~500 tok/s, BS=1, 4×B200）。

**搬到视频（SDVG）怎么映射**：
- 静态地板 = SDVG 现有的 **1.3B Self-Forcing drafter**（不动它）；
- 自适应头 = 一个在线学习的**轻量 drafter（或 drafter 上的 LoRA）**；
- 控制器的"接受率"信号 = **ImageReward 的块接受率**；
- "lookahead K" = **一次投机几个视频块**。

控制器按 ImageReward 通过率决定信哪个 drafter、投机几块；漂移时回退到静态 1.3B 兜底——既能越用越快，又保证最坏不慢于现在的 SDVG。

---

## 二、可迁移的方法（分组）

### B1. LLM 在线 / 持续 speculative decoding（最近的类比）

| 方法 | 出处 | 机制要点 |
|---|---|---|
| **Aurora** ✅ | Together 等，[2602.06932](https://arxiv.org/abs/2602.06932)（2026）| 见上：异步 RL 飞轮 + EAGLE-3 hidden states + 接受损失 + Discard-Sampling 拒绝 KL + 热替换 |
| **ATLAS** ✅ | Together，NeurIPS 2025 | 双（静态+自适应）speculator + 控制器随热身拉长 lookahead；4× over vLLM |
| **TTS — Test-Time Speculation** ✅ | Kumar, Sanghavi, Das（UT Austin），[2605.09329](https://arxiv.org/abs/2605.09329)（2026）| **在单次长生成过程中**在线蒸馏适配 drafter（否则接受长度几千 token 内衰减到 1）；**复用验证前向当 teacher，"零额外开销"**。接受长度 +72% 峰值 / +41% 均值。**⚠️ 截至 2026-06 无公开代码**（arXiv 页/搜索均无 GitHub/项目页；纯方法论文，可在现成 EAGLE-3 codebase 上自加在线蒸馏 loop 复现）|
| **OmniDraft** ✅ | Qualcomm，[2507.02659](https://arxiv.org/abs/2507.02659)，NeurIPS 2025 | 一个**跨词表**在线自适应 drafter，靠**在线 n-gram cache + 混合蒸馏**逐用户适配，一个小 drafter 服务多 target；端侧 1.5–2× |
| **EvoSpec** ✅ | S. Zhang 等，[2605.27390](https://arxiv.org/abs/2605.27390)（2026）| 实时 drafter 进化：长尾 token 检索 + 轻量**课程学习在线对齐**，对付域/话题漂移；1.13× over FR-Spec、省 27% 内存 |
| **Draft-OPD** ⚠️机制 | Lei 等，[2605.29343](https://arxiv.org/abs/2605.29343)（2026）| **on-policy 蒸馏**：target 辅助 rollout + **从被拒（验证暴露）位置回放**。机制是在线式，但当作*训练阶段*配方（非实时服务）。>5× / +23% over EAGLE-3 |
| **DVI — Draft, Verify, and Improve** ✅ | Bhansali, Heck，[2510.05421](https://arxiv.org/abs/2510.05421)（2025）| **自投机**（drafter 是 target 上的头）；验证接受/拒绝驱动**持续在线学习**，**KL→RL 课程**（先在线 KL 蒸馏，后 reward-masked CE + 策略梯度）。Spec-Bench 2.16×，数据量小几个数量级 |
| **ReSpec** ✅ | Q. Chen 等，[2510.26475](https://arxiv.org/abs/2510.26475)（2025）| 在 RL 训练中 target 策略**持续变化**时用 KD 让 drafter 跟上——"移动靶"问题，类比你 router/target 漂移；最高 4.5× |
| **OSD — Online Speculative Decoding** ✅ | Liu 等，[2310.07177](https://arxiv.org/abs/2310.07177)（2023，奠基）| 周期性在 **target 对被拒 token 的纠正**上微调 drafter；buffer 满/陈旧时 flush；KD。接受率 +0.1–0.65，延迟 1.42–2.17× |
| **DistillSpec** ✅ | Google，[2310.08461](https://arxiv.org/abs/2310.08461)（2023）| 离线 KD baseline；要点是 on-policy 数据 + 合适的散度——帮你判断到底需不需要 logits |
| *(次要)* AdaSPEC([2510.19779](https://arxiv.org/abs/2510.19779))、SelecTKD([2510.24021](https://arxiv.org/abs/2510.24021))、SpecBlock([2605.07243](https://arxiv.org/abs/2605.07243), 部署期 **bandit** 用免费验证反馈更新 drafter) | ⚠️ 标题已核实 | 选择性/加权 KD；bandit 在线选择 |

### B2. Diffusion / 视频 的测试时 & 在线蒸馏（迁移的是"模态"）

- **Pathwise Test-Time Correction for Autoregressive Long Video Generation** ✅ — 南大/腾讯混元/CUHK/USTC，[2602.05871](https://arxiv.org/abs/2602.05871)（2026）。**training-free** 轨迹干预，治自回归长视频的误差累积：参考锚定到第 0 帧、选择性 高→低噪声 校正、pathwise 重加噪。稳定生成从 ~5s 拉到 30s。**无在线学习、无 reward model**——是最贴模态的 AR-视频论文，但属"引导"不是"学习"。
- **DAS — Diffusion Alignment as Sampling**（测试时对齐，不过拟合 reward）✅ — SNU/KRAFTON，[2501.05803](https://arxiv.org/abs/2501.05803)（2025）。**测试时、不更新权重**：用 SMC + **reward 加权重采样** + tempering，从 KL 正则的 reward-tilted 分布采样，避免 reward 过优化。**→ 直接对应"推理时用 ImageReward 引导"**。
- **Diffusion-LLM speculative decoding 簇**（⚠️ 标题已核实，2026 新作、引用极少，方兴未艾）：d3LLM([2601.07568](https://arxiv.org/abs/2601.07568))、FailFast([2512.20573](https://arxiv.org/abs/2512.20573))、Jacobi Forcing([2512.14681](https://arxiv.org/abs/2512.14681))、Bastion([2605.29727](https://arxiv.org/abs/2605.29727), 树结构 block-diffusion 起草)、Optimus([2605.24832](https://arxiv.org/abs/2605.24832))、PSD([2605.15609](https://arxiv.org/abs/2605.15609))、FlashMesh([2511.15618](https://arxiv.org/abs/2511.15618), 3D mesh)。说明 spec-decode 正被移植到 block/diffusion 生成——对**块结构**相关，对**在线学习**不相关。
- **Diffusion VLA spec-decode**（⚠️ 邻域、很新）：Fast-dDrive([2605.23163](https://arxiv.org/abs/2605.23163))、Realtime-VLA FLASH([2605.13778](https://arxiv.org/abs/2605.13778))。

### B3. 在线 reward model 改进 / 把接受-拒绝当学习信号（路由器角度）

- **From Reward Modeling to Online RLHF** ✅ — Dong 等，[2405.07863](https://arxiv.org/abs/2405.07863)（2024）。经典在线 reward 配方：收偏好→更新 reward model→改进策略，迭代。
- **Provably Efficient Online RLHF with One-Pass Reward Modeling** ✅ — [2502.07193](https://arxiv.org/abs/2502.07193)（2025）。**常数时间、无回放**的 reward model 在线更新——若你也想让 **ImageReward 路由器**便宜地在线变好，这个对口。
- **Online Preference Alignment via Count-based Exploration** ✅ — [2501.12735](https://arxiv.org/abs/2501.12735)（2025）。在线偏好学习的探索 bonus，防止 drafter 塌缩到"刷 reward"的块。
- *(⚠️ 未能打开)* **"Verifier Matters in Video Diffusion Models"** — BMVC 2025。一个**学习式 verifier/reward model 用于选择/引导视频扩散输出**；标题/会议经检索确认，PDF 二进制未解析，谨慎对待。

---

## 三、能不能搬到 SDVG？逐方法迁移评估

| 方法 | 可迁移性 | 相对 SDVG 的障碍 | 怎么映射 |
|---|---|---|---|
| **Aurora** | **高（需手术）** | 损失是离散 token 的 logit/hidden-state KD；SDVG 是连续块、无 logits、reward 路由 | 保留**飞轮 + 异步热替换 + Discard-Sampling 式奖励**。把 per-token CE/KL 换成**连续块目标**：接受块上模仿 target 潜变量（MSE/flow-matching/扩散损失），用 ImageReward 接受/拒绝当奖励——"Discard Sampling" 变成"把 drafter 的块分布推离被 reward 拒的块"。lookahead → 投机的视频块数。**推荐作为核心。** |
| **ATLAS** | **高** | 同上 连续/无 logit | 采用**双 drafter + 控制器**：SDVG 现有 1.3B drafter = 静态地板；加一个轻量自适应头在线学；控制器随接受率（ImageReward 通过率）上升而拉长 块-lookahead。 |
| **TTS（测试时投机）** | **概念上高** | 为离散 token KD 设计；"免费 teacher = 验证前向"假设有 target logits | "**在单次长生成里自适应**"对**长自回归视频**是金点子（视频越长接受率越衰减）。免费 teacher 技巧可映射：**被拒时 target 重生成的那个块就是 teacher 目标**（SDVG 的拒绝路径已经付过这笔算力）。 |
| **OSD** | **中高** | buffer 存 token logit 对；KD 在 logits 上 | "**缓冲被拒样本→周期性微调**"的环可干净迁移：存 (drafter 块, target 块, ImageReward 分) 三元组；"距离度量"换成潜变量/感知损失。比 Aurora 简单，**适合做第一个原型**。 |
| **DVI（自投机）** | **中** | 自投机要共享 backbone；SDVG drafter(1.3B)≠target(14B) | **KL→RL 课程**（先模仿热启，后 reward/策略梯度）即使两模型分离也是干净的自适应 drafter 训练课表。 |
| **Draft-OPD** | **中高** | 离线、token 级；需 target 辅助 rollout | **从被拒位置回放**直接对应 SDVG（拒绝本就触发 target 重生成→免费的"已纠正块"rollout）。当作喂给 Aurora buffer 的**数据筛选**配方。 |
| **ReSpec** | **中** | 为 RL 训练的陈旧度设计 | 若 **ImageReward 路由器自身也在线漂移/更新**——同一个"移动靶"问题，指导 drafter+router 协同自适应。 |
| **EvoSpec / OmniDraft** | **低-中** | n-gram cache & 词表是 token 专属，连续块无对应 | 仅概念可借："为当前域(prompt 簇)检索/专化"→按 prompt 风格自适应的视频 drafter；缓存机制本身搬不过来。 |
| **DAS（测试时对齐）** | **高（路由器侧）** | 是采样时搜索，不是 drafter 学习 | 直接可用作 **reward 引导的块采样器**：对候选起草块做 SMC、按 ImageReward 重采样、tempering 防过优化。**与在线 drafter 学习互补**——可在任何学习之前先把接受率抬上去。 |
| **Pathwise 测试时校正** | **中（模态）** | training-free 引导、无学习、无 reward | 用它的**AR 长视频稳定化**（参考锚定、高→低噪声校正）让起草块更连贯→ router 接受更多。正交的接受率增强器，不是学习方法。 |
| **Online RLHF / One-Pass RM / Count-based** | **中（路由器角度）** | 改的是 reward model/策略，不是 drafter | 若想让 **ImageReward 路由器在线变好**：One-Pass RM 给常数时间廉价更新；count-based 探索防 drafter 塌缩到 reward-hack 的块。 |

---

## 四、给你的落地建议（推荐架构）

**一句话**：**以 Aurora/ATLAS 为骨架**（异步 serve-to-train 飞轮 + 双 静态/自适应 drafter + 热替换 + Discard-Sampling 式奖励目标），做**三处 SDVG 专属替换**：

1. **损失**：把 token CE/KL 换成**连续块损失**——**被拒时 target 重生成的块就是 teacher 目标（已经算好了，零额外开销）**，用 MSE / flow-matching / 扩散损失在潜空间上让 drafter 块逼近它。
2. **学习信号**：用 **ImageReward 接受/拒绝当奖励**（而非 LLM 的精确匹配验证）——天然就是 RL，接受=正、拒绝=负（Discard-Sampling 把分布推离被拒块）。
3. **长视频自适应**：借 **TTS 的"单次生成内自适应"** 对付长片接受率衰减；借 **Draft-OPD 的"从被拒块回放"** 做数据筛选喂 buffer。

**两个不用训练就能先上的接受率增强器**（可叠加、低风险，建议先做）：
- **DAS**：推理时对候选块按 ImageReward 做 SMC 重采样 + tempering → 不动权重就抬接受率。
- **Pathwise 测试时校正**：稳住长视频起草块的连贯性 → router 少拒。

**建议的推进顺序**：① 先上 DAS / Pathwise（无训练，验证"reward 路由还有多少没榨干"）→ ② 做 **OSD 式最简在线原型**（缓冲被拒块、周期性微调 drafter，最小改动）→ ③ 升级到 **Aurora/ATLAS 飞轮**（异步训练服务器 + 热替换 + 双 drafter 控制器）。

**最大的开放风险**（写给你提前知道）：
- **Aurora 依赖 target 的 hidden states + logits（EAGLE-3 式）**；视频 target 是扩散 transformer，"logits"不存在，得改成"潜变量/特征蒸馏"，这块没有现成论文验证过，是**真正要自己趟的部分**。
- **奖励黑客**：用 ImageReward 当唯一奖励，drafter 可能学会生成"ImageReward 高但人看着差"的块（ImageReward 是单帧、缺时序）。需要 count-based 探索或更强的视频 reward（见 B3 的 "Verifier Matters"、以及 SDVG 自己也承认 ImageReward 缺时序）。
- **drafter 漂移 vs 稳定**：在线学习可能让 drafter 过拟合近期 prompt 分布而忘了其它——这正是方向 1 之外、**持续学习的"灾难性遗忘"**会进来的地方（回放 buffer / ATLAS 的静态地板能兜底）。

---

## 五、信源可信度 & 注意事项

- **✅ 已打开核实（机制+数字确认）**：Aurora(2602.06932 + 博客 + GitHub)、ATLAS(Together 博客 + NeurIPS'25)、TTS(2605.09329)、OmniDraft(2507.02659)、EvoSpec(2605.27390)、Draft-OPD(2605.29343, 机制)、DVI(2510.05421)、ReSpec(2510.26475)、OSD(2310.07177)、DistillSpec(2310.08461)、DAS(2501.05803)、Pathwise(2602.05871)、Online RLHF(2405.07863)、One-Pass RM(2502.07193)、Count-based(2501.12735)。
- **⚠️ 标题/会议经检索确认、但未逐页打开（多为 2026 预印、引用≈0，谨慎引用）**：AdaSPEC、SelecTKD、SpecBlock；diffusion-LLM 簇（d3LLM、FailFast、Jacobi Forcing、Bastion、Optimus、PSD、FlashMesh）；VLA（Fast-dDrive、Realtime-VLA FLASH）；"Verifier Matters in Video Diffusion Models"(BMVC 2025, PDF 未能解析)。
- **❌ 无杜撰条目。** 唯一内容没读到的是 BMVC "Verifier Matters"（二进制 PDF），已标 ⚠️ 而非据其立论。
- **日期警告**：最强的几个类比（Aurora、TTS、EvoSpec、Draft-OPD、整个 diffusion-LLM 簇）都是 **2026 预印、引用极低**——已确认存在且机制如述，但**未经同行评审/独立复现**。最稳的建设基座是 **Aurora、ATLAS、OmniDraft、OSD、DistillSpec 和那几篇 online-RLHF reward 论文**。

---

## 六、与方向一的衔接

方向一（公开 pipeline + 训练算力）的结论会决定这里第 4 节"推荐顺序"的可行性——尤其**训练一个自适应视频 drafter 到底要多少算力**，直接关系到"在线飞轮"在你的预算下是否现实。等方向一报告出来后，我会在两份文件间做一次交叉引用。
