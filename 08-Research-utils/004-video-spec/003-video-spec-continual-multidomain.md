# 方向三：让 speculator 跨域持续学习（沿 Aurora，不断学不同 domain 的投机知识而不遗忘）

> **背景**：沿 Together 的 **Aurora**（在线自改进 speculator，[arXiv:2602.06932](https://arxiv.org/abs/2602.06932)）和 **ATLAS**（NeurIPS 2025，静态+自适应双 speculator），最终迁到视频 speculator（**SDVG**，[arXiv:2604.17397](https://arxiv.org/abs/2604.17397)）。
> **本方向焦点**：让一个**在线、热替换**的 draft model **跨多个 domain 持续积累"投机知识"而不灾难性遗忘**——即持续学习（continual learning）的机制本身（LLM 域的证据即可，最后说视频迁移）。
> **调研方法**：Semantic Scholar 引用图谱 + WebSearch + 逐篇核实。**日期**：2026-06-01。

---

## TL;DR

1. **遗忘是真实存在且被测量到的**：当线上流量切换 domain（chat→code→法律→某个具体 repo），单个小 drafter 在这条非平稳流上微调会出三种问题——**灾难性遗忘（域干扰）**、**冷启动/恢复延迟**、以及长周期下的 **plasticity 损失（彻底学不动）**。
2. **但在 speculator 上"防遗忘"比通用持续学习更便宜**，因为：(a) **一个冻结的静态 speculator 当"速度地板"**就能保证最坏情况永不低于通用基线；(b) **验证器的接受/拒绝信号是免费的稠密奖励**，天然适合做路由；(c) draft model 很小，所以**一个 per-domain LoRA / datastore 银行**养得起。
3. **最关键的诚实发现（也是机会）**：**目前没有任何一篇已核实的论文，真正用 backward-transfer 指标去测量 draft model 在"域增量序列"上的灾难性遗忘**。现有证据只是"域漂移时接受率下降"+ 通用持续学习文献。**→ 这是一个真实空白，是可发表的贡献点。**
4. **推荐架构**：**静态地板 + per-domain LoRA 银行（O-LoRA 正交）+ 域路由（MetaSD 式 bandit）+ 有界跨域 reservoir replay buffer + per-domain 检索 datastore（冷启动）+ plasticity 保护（continual backprop）**。详见第三节。

---

## 一、在线 speculator 的"遗忘"长什么样，怎么防

### 失败模式（三种，要分清）

1. **灾难性遗忘 / 域干扰**。适配新域会覆盖掉让旧域变快的权重。**"Training Domain Draft Models"（Hong 等，ICLR 2025 SCOPE workshop，[2503.07807](https://arxiv.org/abs/2503.07807)）** 直接记录了前提：*把投机解码适配到特定域 target 时，通用 drafter 的接受率因域漂移显著下降*。专精域 B 的 drafter 在域 A 上的接受率会**比通用 drafter 还低**（负向后向迁移）。**EvoSpec（[2605.27390](https://arxiv.org/abs/2605.27390)）** 从时间角度描述同一问题：静态 drafter 在 code/law/medicine 的"话题切换"时吃力。
2. **冷启动 / 恢复延迟**。即便遗忘被控制住，重新适配一个"回头客"域时也有一段降速窗口。**Aurora 博客实测：域漂移后约 1 万条请求恢复接受长度**（这是 Aurora 的数字；ATLAS 博客里我**没能**核实到同样的"~1万请求"说法——见第四节）。ATLAS 的设计也是针对这点：检测到漂移就缩短 lookahead 或回退到静态路径，边保延迟边让自适应头重学。
3. **Plasticity 损失（长周期陷阱）**。与遗忘不同：**Dohare 等，*Nature* 2024《Loss of plasticity in deep continual learning》** 证明持续训练下标准反向传播会**逐渐失去学习能力**（神经元大量"死亡"，最高 ~90%，网络退化成浅模型）。一个连训数周的在线 speculator 正好踩在这个区间——**而且 replay/正则都治不了它**（那俩治遗忘，不治可塑性）。

### 防住它的设计模式（生产系统已经编码了一部分）

- **静态"速度地板" + 自适应头（ATLAS 的核心招）**。保留一个冻结的、广泛训练的**静态 speculator** 当常驻基线，让一个轻量**自适应 speculator** 在线专精，外加一个**置信度感知控制器**逐步决定信谁、看多远。这等于**把"稳定-可塑性"权衡直接焊进架构**：静态路径**永远不会被遗忘**（它从不更新），所以无论自适应头怎么漂，最坏吞吐都不会低于通用基线。**这是在线 speculator 最重要的模式**——它把"灾难性遗忘"从"正确性/吞吐风险"降级成"顶多少赚一点"的风险。
- **模块化 per-domain adapter，而不是一个不断变异的模型**。不覆盖共享权重，而是挂域专属 LoRA/prompt 模块、按域切换。**O-LoRA（Wang 等，EMNLP Findings 2023，[2310.14152](https://arxiv.org/abs/2310.14152)）** 让每个任务的 LoRA 子空间**互相正交**，新域更新不干扰旧域，**且不需要 replay buffer、不存用户数据**——对在线、隐私敏感的服务循环都友好。直接映射成"按域索引的 LoRA 银行"。
- **Mixture-of-drafters + 路由**。**MetaSD（Kim 等，ICLR 2025 投稿 → ACL 2026 Findings，[2604.05417](https://arxiv.org/abs/2604.05417)）** 保留**多个** drafter，各擅一域，用**对验证器对齐反馈的多臂老虎机**路由（接受/拒绝信号*就是*奖励）。彻底绕开遗忘，代价是显存：不更新共享模型，只挑对的专家。**OmniDraft（NeurIPS 2025，[2507.02659](https://arxiv.org/abs/2507.02659)）** 是 per-*用户* 版（在线 n-gram cache + 混合蒸馏）。
- **从验证信号蒸馏/replay**。**OSD（Liu 等，ICML 2024，[2310.07177](https://arxiv.org/abs/2310.07177)）** 和 **Draft-OPD（[2605.29343](https://arxiv.org/abs/2605.29343)）** 都维护一个**有界 buffer，存错误位置上的 draft-vs-target 分布**并周期性蒸馏——天然便宜的经验回放循环，**只要 buffer 是跨域 reservoir 采样而非纯近期**，就兼做防遗忘。
- **per-domain 检索 datastore（REST）**。**REST（He 等，NAACL 2024）** 靠从 datastore 检索 n-gram 续写来起草——**training-free**。**一个 per-domain datastore 给某域瞬时"记忆"、零遗忘**（知识在数据里不在权重里），加一个域 = 加一个 datastore。
- **Plasticity 保护**。把 continual-backprop 式的"周期性重初始化低效用神经元"（Dohare 2024）加到那个*确实在线训练*的组件里，免得自适应头在长部署里慢慢僵化。

> **小结**：speculator 上的遗忘是真的、能测的（域漂移下接受率掉），但**这里比通用 CL 更好防**——冻结静态地板保最坏、接受/拒绝是免费稠密奖励、draft 模型小所以养得起 per-domain 银行。

---

## 二、分组方法清单（已核实）

### B1. 在线 / 自适应 / 多域投机解码（最近的先验）

| 方法 | 出处 | 机制 | 适配度 |
|---|---|---|---|
| **Aurora** | Together 等，2026，[2602.06932](https://arxiv.org/abs/2602.06932) | 从实时推理数据**持续 RL 训练** speculator；为即时部署+快速适配流量/域漂移设计 | **高**（目标系统）|
| **ATLAS** | Together，NeurIPS 2025 | 冻结*静态* speculator=速度地板；轻量*自适应*在线专精；**置信度控制器**路由+调 lookahead，漂移时回退静态 | **高**（"地板+头"范式）|
| **OSD** | Liu 等，ICML 2024，[2310.07177](https://arxiv.org/abs/2310.07177) | 用空闲算力在观测到的 query 上蒸馏 drafter；buffer 满则蒸；接受率 +0.1–0.65、延迟 1.42–2.17× | **高**（便宜的异步 replay/蒸馏）|
| **OmniDraft** | NeurIPS 2025，[2507.02659](https://arxiv.org/abs/2507.02659) | 一 drafter 服务多 target；**在线 n-gram cache + 混合蒸馏**逐用户端侧适配 | **高**（per-用户/域在线适配）|
| **EvoSpec** | 2026-05，[2605.27390](https://arxiv.org/abs/2605.27390) | 上下文感知长尾 token 检索 + 在线课程对齐，跟踪话题漂移；1.13× over FR-Spec | **高**（显式处理域漂移）|
| **MetaSD** | Kim/Jung/Yun，ICLR'25 投稿→ACL 2026 Findings，[2604.05417](https://arxiv.org/abs/2604.05417) | 多个 per-域 drafter，**对齐反馈上的多臂 bandit**动态路由 | **高**（mixture-of-drafters + router）|
| **Training Domain Draft Models** | Hong 等(SambaNova)，ICLR'25 SCOPE workshop，[2503.07807](https://arxiv.org/abs/2503.07807) | **确立问题**：通用 drafter 接受率随域漂移下降；给出 per-域蒸馏最佳实践 | **中**（论证 per-域银行；无 CL 机制）|
| **Draft-OPD** | 2026-05，[2605.29343](https://arxiv.org/abs/2605.29343) | on-policy 蒸馏修离线-推理失配；从验证暴露位置 replay | **中**（on-policy replay；非多域）|
| **REST** | He 等，NAACL 2024 | training-free：从 datastore 检索精确后缀 n-gram，tree attention 验证；1.6–2.4× | **高**（per-域 datastore = 零遗忘记忆）|
| **Steering Pretrained Drafters** | [2511.09844](https://arxiv.org/abs/2511.09844) | 用验证器 hidden states 注入 steering 向量，会话内修 drafter-verifier 失配 | **低**（单对、非跨域）邻接 |

### B2. 通用持续学习工具箱（按"能否塞进异步在线循环"评判）

**(a) Replay / 回放**

| 方法 | 出处 | 机制 | 适配度 |
|---|---|---|---|
| Experience Replay / reservoir + tiny memory | Chaudhry 等，2019，[1902.10486](https://arxiv.org/abs/1902.10486) | 存少量旧样本与当前交错；reservoir 采样 | **高**（便宜，配 OSD buffer）|
| A-GEM | Chaudhry 等，ICLR 2019 | 投影当前梯度，不增加记忆平均梯度上的损失 | **中**（每步多一次反向）|
| Deep Generative Replay (DGR) | Shin 等，NeurIPS 2017，[1705.08690](https://arxiv.org/abs/1705.08690) | 训生成器合成旧任务数据来回放 | **低**（生成器成本高）|

**(b) 正则化**

| 方法 | 出处 | 机制 | 适配度 |
|---|---|---|---|
| EWC | Kirkpatrick 等，PNAS 2017 | 对旧任务重要(Fisher)权重的改变加二次惩罚 | **中**（Fisher 估计成本、近似需任务边界）|
| Synaptic Intelligence (SI) | Zenke 等，ICML 2017 | 从 梯度×Δ权重 的路径积分**在线**算每权重重要度 | **中-高**（在线、无额外反向）|
| MAS | Aljundi 等，ECCV 2018 | 重要度=输出对权重的敏感度；无监督、在线 | **中-高**（在线、task-free）|
| LwF | Li & Hoiem，2017 | 在新数据上蒸馏旧模型输出（不存旧数据）| **中**（需旧模型副本=你的静态地板！）|

**(c) 参数隔离 / 模块化**

| 方法 | 出处 | 机制 | 适配度 |
|---|---|---|---|
| **O-LoRA** | Wang 等，EMNLP Findings 2023，[2310.14152](https://arxiv.org/abs/2310.14152) | per-任务 LoRA 在**互相正交**子空间；无 replay、不存数据 | **高**（自适应头的 per-域 LoRA 银行）|
| PackNet | Mallya & Lazebnik，CVPR 2018，[1711.05769](https://arxiv.org/abs/1711.05769) | 迭代剪枝把多任务用 per-任务二值 mask 塞进一个网；旧权重冻结 | **中**（mask 簿记、容量固定）|
| Progressive Neural Networks | Rusu 等，2016，[1606.04671](https://arxiv.org/abs/1606.04671) | 每任务加一列冻结网+横向连接；零遗忘但体积增长 | **低**（无界增长）|

**(d/e) Prompt-based CL（免回放）**

| 方法 | 出处 | 机制 | 适配度 |
|---|---|---|---|
| L2P | Wang 等，CVPR 2022，[2112.08654](https://arxiv.org/abs/2112.08654) | 推理时按 key 取的可学 prompt 池；无回放、无需 task ID | **中-高**（参数极小、可按域切换）|
| DualPrompt | Wang 等，ECCV 2022，[2204.04799](https://arxiv.org/abs/2204.04799) | 冻结骨干上拆 任务不变(G)/任务专属(E) prompt | **中**（干净的稳定/可塑性拆分）|

### B3. 终身 / 可塑性理论

| 主题 | 出处 | 与这里的关系 |
|---|---|---|
| **Loss of plasticity + Continual Backprop** | Dohare 等，***Nature* 2024**（s41586-024-07711-7）| 标准反传在长持续训练中**失去学习能力**（死神经元）；周期性重初始化低效用单元可恢复可塑性 |
| 稳定-可塑性 & CL 分类 | (框架) | **域增量**(label 空间同、输入分布变——**就是你的设定**) vs 任务增量(给 task ID) vs 类增量(新类、无 ID)；在线 CL=单遍非平稳流(=服务循环) |

---

## 三、推荐配方：多域、不遗忘的在线 speculator 架构

**架构（LLM 域为主，视频迁移见下）：**

1. **冻结静态地板（稳定性）**。ATLAS 的广训静态 speculator 永久冻结：永不遗忘、保证吞吐不低于通用基线——不可妥协的安全网。**还可复用它当 LwF teacher**（它的输出就是要蒸馏对齐的"旧知识"）。
2. **自适应头上的 per-域 LoRA 银行（模块化可塑性）**。每个发现的域一个小 LoRA，用 **O-LoRA 正交性**训练，使新域更新落在与已有域正交的子空间→干扰有界、不存跨域数据。adapter 存储便宜、可热替换（契合 Aurora/ATLAS 的权重热替换）。
3. **域路由器（单模型设计里缺的那块）**。用 MetaSD 的 **对齐反馈 bandit**：验证器接受/拒绝率是免费的逐步奖励，按实测接受率在 {静态地板, LoRA[域k]} 间路由。漂移检测（接受率掉）触发 (a) 立刻回退静态路径（ATLAS）、(b) 为新兴域 spawn/选一个 LoRA。
4. **有界、跨域 reservoir 采样的 replay buffer（对受训头防遗忘）**。复用 OSD/Draft-OPD 的思路——buffer 存被拒/验证暴露位置的 draft/target 分布——但**跨域 reservoir 采样**而非只存近期，使异步蒸馏步不会把共享自适应头拽向当下最热的域。在 LoRA 挂载间的共享参数上用 **SI/MAS 在线重要度**（便宜、无额外反向、task-free）做软正则。
5. **per-域检索 datastore（REST）当零遗忘冷启动**。对全新/稀有、还没训出 LoRA 的域，从 per-域 n-gram datastore 起草（training-free、瞬时）。数据里的知识=不可能被遗忘；在 LoRA 热身期间桥接冷启动窗口。
6. **可塑性保护（长周期）**。在自适应头里跑 continual-backprop 式周期性重初始化低效用单元，使数周部署不会慢慢僵化（Dohare 2024）。**这是目前所有投机解码论文都没有的一个保护。**

**异步在线循环（什么足够便宜）**：路由(bandit)和检索是逐请求、开销极小；LoRA 蒸馏和 continual-backprop 在**关键路径之外**用空闲算力跑（OSD 的前提）并热替换权重（Aurora/ATLAS）。**热路径上避免 A-GEM/EWC-Fisher**（额外反向/边界假设）；优先 SI/MAS 式在线重要度 + reservoir replay。

**视频迁移（SDVG）**：SDVG 起草连续时空块、用 **ImageReward 质量路由**（阈值 接受/重生成）验证——**没有 token logits**，所以 token 分布蒸馏（OSD/Draft-OPD）和 n-gram 检索（REST）不能直接搬。能搬的是：(i) **静态地板+自适应头** 分解；(ii) 1.3B drafter 上按内容域（动画 vs 写实 vs UI/录屏）索引的 **per-域 LoRA 银行**；(iii) **路由奖励从"token 接受"换成"ImageReward 块接受率"**——一个连续奖励，**其实比离散接受/拒绝更适合 bandit/RL 更新**；(iv) 可塑性保护不变。

**开放风险**：
- (a) **域识别**：服务流里域是隐变量，错路由或把 LoRA 银行切得太碎会同时拖慢速度和吃显存。
- (b) **LoRA 银行无界增长**：需合并/淘汰（LoRA-merge 或 PackNet 式整合），而合并本身又带遗忘风险。
- (c) **低流量域的奖励稀疏/噪声**让 bandit 难学。
- (d) **没有论文测量过 draft model 在域增量序列上的遗忘**（backward-transfer 指标）——真实空白、可发表贡献。
- (e) 异步循环里 **可塑性 vs replay 的相互作用**对 speculator 完全未测。

---

## 四、信源可信度 & 注意事项

- **✅ 已打开核实**：Aurora(2602.06932)、SDVG(2604.17397)、OSD(2310.07177, ICML'24 + GitHub)、OmniDraft(2507.02659, NeurIPS'25)、EvoSpec(2605.27390, 2026-05 非幻影)、MetaSD(OpenReview 5haYLrlyGj + 2604.05417)、Training Domain Draft Models(2503.07807, ICLR'25 SCOPE)、Draft-OPD(2605.29343)、REST(NAACL'24 + GitHub)、Loss of Plasticity(*Nature* 2024 + GitHub)、EWC(PNAS'17)、SI(ICML'17)、DGR(NeurIPS'17)、A-GEM(1902.10486/ICLR'19)、O-LoRA(2310.14152)、PackNet(1711.05769)、Progressive Nets(1606.04671)、L2P(CVPR'22)、DualPrompt(2204.04799)。
- **⚠️ 据二手来源、引用前再确认**：
  - **ATLAS**——据 Together 博客 + NeurIPS 2025 talk 页确认；"静态地板+自适应头+置信度控制器"是**博客原话**。**未找到独立的 ATLAS arXiv PDF**，其确切发表形式/ID 未确认。
  - **"~1 万请求恢复"这个数字属于 Aurora（其博客已核实），不是 ATLAS**；direction-3 调研在 ATLAS 来源里没找到同样说法。
  - MAS(ECCV'18)、LwF——经多个二手源确认，本轮未开原始 PDF。
  - "Steering Pretrained Drafters"(2511.09844)——读了摘要，仅作*邻接*列入。
- **❌ 无杜撰/幻影 ID**：OSD 引用图谱里若干 2026 投机解码标题（Test-Time Speculation 2605.09329、CATS 2605.11186、D-PACE 2605.18810、SpecBlock 2605.07243 等）**未打开、未采用**，剔除以保列表已核实。Aurora 的 S2 引用图谱目前只返回一篇引用(SpecBlock)，所以**尚无针对 Aurora 的"防遗忘"后续工作**。
- **核心诚实空白**：**没有已核实论文用 backward-transfer 指标显式测量 draft/speculator 在域增量序列上的灾难性遗忘**。现有证据=「域漂移下接受率下降」(Training Domain Draft Models, EvoSpec) + 通用 CL 文献——这正是第三节把它定位成"开放贡献"的原因。

---

## 五、与方向一/二的衔接

- **方向一**（`001`）：训练视频 drafter 便宜（~128 H100-GPU-时、data-free）→ per-域 LoRA 银行的"加一个域"边际成本极低，这个配方在算力上可行。
- **方向二**（`002`）：Aurora/ATLAS 飞轮是本方向的**底座**；本方向是在那个底座上加"跨域不遗忘"的 CL 层。两者合起来 = 一个**既能在线变好、又能跨域积累、还不遗忘**的视频 speculator。
- **最值得做的下一步**：方向三第三节 (d) 那个空白——**先搭一个 draft-model 域增量 benchmark（带 backward-transfer 指标）**，因为现在整条线连"遗忘到底多严重"都还没人正经测过。


## 六、两个关键问题：LLM speculator CL 值不值 + 视频 domain 怎么分

### Q1. 做 LLM speculator 的 continuous learning 有意义吗？他们 release 了不同 speculator 吗？ΔW 多大？

**(a) 值不值 —— 结论：值，但要做成"随域漂移在线适配"，而不是"养一大堆静态 per-域 speculator"。**

**支持（CL 有用）：**
- **Aurora（[2602.06932](https://arxiv.org/abs/2602.06932)，Together）** 明说 **"域漂移是投机解码的首要失败模式"**；比训练良好的**静态** speculator 再快 **1.25×**（分布漂移下），前沿模型 day-0 **1.5×**。
- **Training Domain Draft Models（SambaNova，[2503.07807](https://arxiv.org/abs/2503.07807)，ICLR'25 SCOPE workshop）** 实测通用 drafter 碰到域专精 target 时接受率掉得很狠（直接读 PDF Table 1）：

  | 域 | 通用 target 接受率 | 域 target 接受率 | 相对降幅 |
  |---|---|---|---|
  | Biology | 60.7% | 37.5% | **−38.2%** |
  | Chinese | 49.6% | 35.7% | **−28.0%** |
  | Coding | 59.4% | 55.2% | −7.1% |
  | Math | 78.3% | 75.4% | −3.7% |

**反对（一个强通用 drafter 也许就够）：**
- **降幅极不均匀**：Biology/Chinese 掉 28–38%，但 Coding/Math 只掉 4–7%。**离通用分布近的域，一个强 EAGLE-3 通用 drafter 就吃掉大部分收益**，per-域专精只换来边际接受率，却加了路由/显存/运维复杂度。
- 这也是 MetaSD 存在的理由——没有单一 drafter 处处赢；但它的解法（bank + bandit）本身就是成本。

> **底线**：**持续学习值得做，但定位是"按域漂移在线适配"，不是"一大堆静态 per-域模型"**。一个强通用 EAGLE-3 + 一个轻量在线适配环（Aurora 式），**只对"离通用分布远的垂直域"（专业垂类、非英语）才升级到专属 adapter**。
>
> ⚠️ **顺带纠正我之前一句口误**：我说过"从零在线训练能超过预训练 speculator"——要分场景：**混合流量下确实能超**（Aurora 博客 3.08 vs 静态 2.63）；但**有序域漂移流量下只是追平**（PDF：~10k 请求后 2.46 vs 预训练 2.57，是"打平 + 可 day-0 部署"，不是碾压）。

**(b) 他们 release 了不同的 speculator 吗？**（你记得的"用很多 spec decoder 的 paper" = **MetaSD**）

| 系统 | arXiv | 训了 per-域 drafter？ | 公开 release？ |
|---|---|---|---|
| **MetaSD** | 2604.05417 | 是（多个 EAGLE drafter 各自自蒸馏；路由 training-free）| **❌ 没找到任何公开 release**（仅研究用）|
| **Training Domain Draft Models**(SambaNova) | 2503.07807 | 是（Function-Calling/Biology/Chinese；**全量蒸馏，非 LoRA**）| **❌ 没 release 域 drafter checkpoint** |
| **OmniDraft**(Qualcomm) | 2507.02659 | 一个自适应 drafter + 在线 n-gram（非 per-域 bank）| **❌ 没找到代码/权重** |
| **Aurora**(Together) | 2602.06932 | 是（EAGLE3，每个绑定 一个 (target, 域)）| **✅ 唯一有 release 的** |

**所以直接回答你：你记得的那篇（MetaSD）没 release。** 唯一放出 speculator 的是 **Aurora**：
- 代码 [github.com/togethercomputer/aurora](https://github.com/togethercomputer/aurora)
- 权重 `togethercomputer/Aurora-Spec-Qwen3-Coder-Next-FP8`（0.5B，单层 EAGLE3 decoder，在 80k 条 Code 域请求上从零训，3.1× 平均接受长度、1.51× 加速）、`Aurora-Spec-Minimax-M2.1`、`-M2.5`；数据集也放了。
- **关键 caveat**：Aurora 放的是**按 (基座模型, 单一域) 组织的单个 drafter**，**不是同一基座下可互换的"多域 bank"**。**所以"为固定 target 公开一组可互换的域 drafter bank"这件事，目前还没人做过。**

**(c) ΔW（不同域 speculator 之间的权重差）到底多大？** —— 你这个问题问到了点子上。

- **没有任何论文直接测过 drafter 之间的权重空间 ΔW（L2 距离 / task-vector 范数）**。这是个真实空白（值得你自己跑一下）。
- **最接近的 drafter 专属数字**：**EDA（[2603.09527](https://arxiv.org/abs/2603.09527)）**——把 draft 模型从 Qwen2.5-7B 适配到 Qwen2.5-**Math**-7B，只需更新一个小"私有分量"，**可训参数 = 127MB = 全量重训(462MB)的 27.5%**（Table 4，gated 私有专家、非 LoRA）。即"per-域专精是个 < 三分之一模型 的更新，不是全量重训"。
- **旁证（都已核实，全指向"小而低秩"）**：
  - **LoRA（[2106.09685](https://arxiv.org/abs/2106.09685)）**：ΔW 内在秩极低，**r=1 或 r=4 常就够**；GPT-3 175B 只需 ~18M 可训参（~0.01% 权重，1 万倍缩减）。
  - **Intrinsic Dimensionality（Aghajanyan，[2012.13255](https://arxiv.org/abs/2012.13255)）**：RoBERTa 把任务微调投影到 **~200 个可训参数**就能达到全量微调 90% 的效果。
  - **Task Vectors（Ilharco，[2212.04089](https://arxiv.org/abs/2212.04089)）**：θ_微调 − θ_预训练 这个向量小、有方向性、**跨任务可加可组合**。
  - **drafter 本来就小**：EAGLE-3 草稿模块 = **单个 Transformer decoder 层**（Aurora 放的就是 **0.5B**，约 8B target 的 6%）；Medusa 加 K 个小头。**连"整个 per-域 drafter"都小，两个域 drafter 之间的"差"更是小得多。**

> **ΔW 结论**：多条证据汇聚——**per-域专精一个 drafter 是个"小的、低秩的 ΔW"**。**正确且便宜的架构 = 在一个共享基座 drafter 上挂 per-域 LoRA bank（rank ~4–16），每域很可能 <1% 参数、serve 时热切换**，不需要每域存整模型。唯一缺的那个直接 ΔW 测量（两个已训域 drafter 的 L2 / task-vector 范数），是个**便宜、干净、值得你直接在 SambaNova 或 MetaSD 式 drafter 上跑一下的实验**，用来实测确认秩。

### Q2. 视频生成一般有哪些"domain"？speculator 该按哪个轴分？

**权威分类（都已打开核实）：**

- **VBench（[2311.17982](https://arxiv.org/abs/2311.17982)，CVPR'24；GitHub `Vchitect/VBench`）**——两条正交轴：
  - **16 个评测维度**：subject/background consistency、temporal flickering、motion smoothness、**dynamic_degree（运动幅度）**、aesthetic/imaging quality、object class、multiple objects、human action、color、spatial relationship、scene、temporal_style、**appearance_style**、overall consistency。
  - **8 个内容类别**（按 YouTube 分类）：**Animal、Architecture、Food、Human、Lifestyle、Plant、Scenery、Vehicles**。
  - **风格轴**（appearance/temporal_style）：oil painting、黑白、水彩、cyberpunk + 镜头运动风格。
- **VBench-2.0（[2503.21755](https://arxiv.org/abs/2503.21755)）**——从表面质量转向**能力/难度**：**Human Fidelity、Controllability、Creativity、Physics、Commonsense** 5 维。这是个*难度*分类，不是内容分类。
- **MovieGenVideoBench**（Meta；SDVG 用的，1003 prompt @ 832×480）——官方 **5 个概念类别**（直接读 Meta HF README 纠正）：**1) Human activity 2) Animals 3) Nature & scenery 4) Physics（流体/重力/碰撞/爆炸）5) Unusual subjects & activities**，外加**运动等级 high/med/low** 覆盖。（注意：没有"fantasy/text/cinematic"这种官方类别；SDVG 里"cinematic/landscapes"是论文的非正式说法。）
- **生成任务轴**：T2V、I2V、V2V/编辑/inpainting（VBench 有专门的 VBench-I2V 轨）。

**综合 —— 对 speculator 而言，哪个轴才重要？**

draft 模型相关的"domain" **不是语义类别**（动物 vs 车），而是**"下一个视频块好不好预测"——即什么东西在给接受率聚类**。（注意：SDVG 只报了 1003 prompt 的*聚合*加速，**没给 per-类别接受率分解**——这也是个空白。）从维度推理，speculator 相关的轴是：

1. **运动幅度**（VBench `dynamic_degree`；MovieGen high/med/low）——**主导轴**。低运动/近静态/talking-head 块极好预测（高接受）；高运动/动作/爆炸块变化快（低接受）。这就是"高熵 next token"的视频版。
2. **场景/时间稳定性**（subject/background consistency、flickering）——稳定场景+慢镜头 ⇒ 块间差小 ⇒ 高接受；切镜/快速 pan/无人机镜头/物理事件（碰撞、流体）⇒ 低接受。
3. **风格规律性**（appearance_style）——平整规律的风格（动画、卡通、3D 渲染）局部熵低、好预测；写实高频纹理更难。
4. **分辨率/token 密度**——分辨率越高每块 token 越多，接受率区间不同（正交的 scaling 旋钮）。
5. **生成任务**（T2V vs I2V vs 编辑）——I2V/编辑**更**好预测（强条件锚住草稿），自成一个"易"的接受聚类。

语义内容类别（动物/食物/车）只在**它们与上面这些相关时**才有意义（"scenery"≈低运动+稳定；"human activity"/"physics"≈高运动+不稳）。它们是**噪声代理，不是真正的划分**。

> **推荐的 per-域视频 speculator LoRA bank 划分**：**按"接受难度聚类"分，不按语义类**。一个实用的 2–3 轴网格：
> - 主网格：**运动**{低/静态, 中, 高/动作} × **条件任务**{T2V, I2V/编辑}（~6 桶）；
> - 可选二级：**风格**{写实 vs 平整/动画/3D}。
>
> 落地：**用"实测块接受率（或块散度奖励，正是 MetaSD 给 LLM 用的那个信号）"对块做聚类**，每个聚类拟一个低秩 LoRA，配 Aurora 式在线环持续适配。结合 Q1(c)——每个视频域 adapter 都是便宜的 rank-4–16 LoRA——**一个 运动×风格×任务 的 bank 完全养得起，远便宜于每域整一个视频 drafter。**

**本节信源**：✅ 已读 PDF/页面核实：SambaNova Table 1、Aurora 数字 + HF release、EDA 27.5%、LoRA / Intrinsic-Dim / Task-Vector、VBench 16 维+8 类、VBench-2.0 5 维、MovieGenVideoBench 5 类。❌ 两个真实空白（都是你能直接做的贡献点）：(1) 无任何论文直接测 drafter 间 ΔW（L2 / task-vector 范数）；(2) SDVG 无 per-类别接受率分解。


