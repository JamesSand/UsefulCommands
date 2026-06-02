# 方向一：视频 speculative decoding 现在的进展（公开 pipeline + 训练算力）

> **种子论文**：SDVG — *Speculative Decoding for Autoregressive Video Generation*，[arXiv:2604.17397](https://arxiv.org/abs/2604.17397)，Hu & Zhang，UC Berkeley，2026-04-19。
> training-free：Wan2.1-T2V-1.3B Self-Forcing drafter 用 4 步去噪出块 → ImageReward 按"最差帧"打分 → Krea Realtime 14B target 重生成被拒块。1.59× 加速保 98.1% 质量（τ=−0.7），最高 2.09×@95.7%，在 1003 条 MovieGenVideoBench prompt（832×480）、2× RTX A6000 上评测。
> **调研方法**：Semantic Scholar 引用/参考图谱 + WebSearch + 逐篇到 arXiv/GitHub/HF 核实。**调研日期**：2026-06-01。

---

## TL;DR（最重要的两点先说）

1. **SDVG 目前是把 LLM 式 speculative decoding（draft→verify→regenerate）用到视频生成上的"唯一一篇"**。种子论文才 6 周、**0 引用**；真正活跃的中心是它的 drafter 来源 **Self-Forcing**（~100 篇引用，几乎全是 2026-05 的自回归视频工作）。它周边的"加速"其实是三类**不同**的东西：
(a) step-distillation 少步 drafter、
(b) step 级 大-小模型拼接、
(c) 给扩散 transformer 做 **speculative feature caching**——这些都**不是**真正的 token 式投机解码。
2. **没有专门的、公开的"视频投机解码 pipeline"**。SDVG 没放代码。你现在要复现 SDVG，得**自己拼**：Self-Forcing drafter + Krea/LightX2V target + 一个 ImageReward 路由器。
3. **训练一个视频 drafter 其实很便宜、而且基本 data-free**：Self-Forcing 标准配方 **64× H100 上 <2 小时（~128 H100-GPU-时）**、只用文本 prompt 就收敛。贵的是上游基座（Wan，算力未披露）和某些 pipeline 需要的 **causal-ODE 初始化**（1.3B 规模 ≈11,600 A800-GPU-时）。

---

## 一、按主题分类的方法清单

### A1. 真·视频投机解码（draft–verify–regenerate）
- **SDVG（种子）** — Hu & Zhang, 2026。块级 drafter + ImageReward 路由 + target 重生成；training-free；1.59×@98.1%。[2604.17397](https://arxiv.org/abs/2604.17397)（~0 引用）。**调研范围内唯一一篇真·视频投机解码。**

### A2. Speculative feature caching（把"投机"原理用到 DiT 推理，training-free）
- **SpeCa: Accelerating Diffusion Transformers with Speculative Feature Caching** — Liu 等，2025-09-15。"forecast-then-verify"：预测未来时间步的特征，无参数地接受/拒绝；覆盖视频（HunyuanVideo 6.1× 时 VBench 79.84%）、FLUX 6.34×、DiT 7.3×。training-free。[2509.11628](https://arxiv.org/abs/2509.11628) ✅
  > 注意：这是"沿时间步预测特征"，不是"小模型起草 / 大模型验证"，和 SDVG 是两条路，但同样借了"投机+验证"的思想。

### A3. Step 级 大-小模型拼接（概念上的近亲/前辈）
- **T-Stitch** — Pan, Zhuang 等，2024-02。早期去噪步用小模型、后期用大模型；仅图像（ImageNet/SD）；~40% 早期步换成快 10× 的 DiT-S。[2402.14167](https://arxiv.org/abs/2402.14167) ✅
- **SRDiffusion: Sketching-Rendering Cooperation** — Cheng 等，2025-05。大模型做高噪声"勾勒"、小模型做低噪声"渲染"；Wan 上 >3×、CogVideoX 2×。[2505.19151](https://arxiv.org/abs/2505.19151) ✅
- **HybridStitch: Pixel and Timestep Level Model Stitching** — Sun, Hon, Zhang, Liu，2026（与 SDVG 共同作者 Jintao Zhang）。[2603.07815](https://arxiv.org/abs/2603.07815)（⚠️ 仅 S2 元数据，未逐页打开）

### A4. 自回归/因果视频蒸馏（**这些就是 SDVG 复用的 drafter 和 target**）
- **Self-Forcing: Bridging the Train-Test Gap in Autoregressive Video Diffusion** — Huang, He 等，**NeurIPS 2025 Spotlight**，[2506.08009](https://arxiv.org/abs/2506.08009)。用 DMD + self-rollout 把 Wan2.1-1.3B 蒸成因果自回归模型；**data-free**。**→ 产出 SDVG 的 drafter。** ✅ 这是整条线的活跃中心。
- **CausVid — From Slow Bidirectional to Fast Causal Video Generators** — Yin 等，**CVPR 2025**，[2412.07772](https://arxiv.org/abs/2412.07772)。把 DMD 扩到视频，50 步双向 → 4 步因果；单卡 H100 9.4 fps。**Self-Forcing 的方法学父辈。** ✅
- **Causal Forcing++: Scalable Few-Step Autoregressive Diffusion Distillation** — Zhao, Zhu 等（清华/生数/人大），2026-05，[2605.15141](https://arxiv.org/abs/2605.15141)。用"因果一致性蒸馏"替代昂贵的 causal-ODE 初始化；4× 加速；**披露了详细算力**（见 Q2）。✅（~2 引用）
- **Wan: Open and Advanced Large-Scale Video Generative Models** — Team Wan（61 作者），[2503.20314](https://arxiv.org/abs/2503.20314)。上面一切蒸馏的 1.3B/14B 基座；训练用了"数十亿图像和视频"（算力未披露）。✅

### A5. Step-distillation 少步 drafter（充当便宜 proposer 的少步模型）
- **AnyFlow: Any-Step Video Diffusion with On-Policy Flow Map Distillation** — Gu, Fang, …, Song Han, Mike Shou，2026-05，[2605.13724](https://arxiv.org/abs/2605.13724)。flow-map 蒸馏，任意步数下质量一致；1.3B→14B。✅（算力未披露）
- **LightX2V Wan2.1-T2V-14B-StepDistill-CfgDistill** — LightX2V，HF 模型。Wan2.1-14B 的 4 步 + CFG 蒸馏，Apache-2.0；**Krea Realtime 的时间步蒸馏就建在它上面**。[HF 链接](https://huggingface.co/lightx2v/Wan2.1-T2V-14B-StepDistill-CfgDistill-Lightx2v) ✅

---

## 二、Q1 —— 有没有成熟的公开 pipeline？

| 仓库 / 资产 | 提供什么 | 链接 | 成熟度 |
|---|---|---|---|
| **SDVG（种子）** | 投机解码方法本身 | [arXiv](https://arxiv.org/abs/2604.17397) | **截至 2026-06 未找到公开代码——只有论文** |
| **guandeh17/Self-Forcing** | 官方 drafter 训练+推理代码（DMD/data-free 蒸馏 Wan2.1-1.3B）；HF 有 checkpoint | [GitHub](https://github.com/guandeh17/Self-Forcing) | 研究代码，活跃（3.4k★，NeurIPS'25 Spotlight）；59 open issues、无正式 release——"维护中的研究代码"，非产品化 pipeline |
| **krea-ai/realtime-video** | SDVG 的 target。仅推理：WebSocket 流式服务 + 离线批采样；权重在 HF | [GitHub](https://github.com/krea-ai/realtime-video) | 维护中的推理 pipeline（产品形态：配置、FA4/SageAttention 后端）。仅推理、无蒸馏代码。**CC-BY-NC-SA-4.0（非商用）** |
| **tianweiy/CausVid** | 因果 DMD 蒸馏训练代码（8 节点×8 卡 torchrun）+ 评测；MixKit-6K 玩具数据 | [GitHub](https://github.com/tianweiy/CausVid) | 研究 dump，自标"work in progress"（1.3k★，MIT，无 release，玩具数据警告）|
| **ModelTC/lightx2v** | 推理框架：step 蒸馏（4 步）、量化（int8/fp8/nvfp4）、attention kernel；支持 Wan2.1/2.2、HunyuanVideo-1.5、LTX、Self-Forcing | [GitHub](https://github.com/ModelTC/lightx2v) | **成熟、活跃维护的生产级推理框架**（2.3k★，Apache-2.0，2026-05 仍活跃）|
| **GoatWu/Self-Forcing-Plus** | LightX2V 的蒸馏训练代码（Self-Forcing 的 fork/扩展）| [GitHub](https://github.com/GoatWu/Self-Forcing-Plus) | 研究扩展（⚠️ 据 LightX2V 的 HF 卡推断存在，未直接打开）|

**Q1 结论**：**没有专门的、公开的视频投机解码 pipeline**——SDVG 没放代码。现存的"大-小协作"拼图分两块：(i) *drafter/target 蒸馏*侧（Self-Forcing、CausVid = 维护中研究代码；LightX2V = 生产级推理）；(ii) step 拼接（SRDiffusion、T-Stitch = 研究代码）。**今天要复现 SDVG，得自己用 Self-Forcing drafter + Krea/LightX2V target + ImageReward 路由器拼出来。**

---

## 三、Q2 —— 训练这些 speculator 要多大算力？

| 方法 | 模型规模 | 硬件 | GPU-时 / 时长 | 数据 | 来源 |
|---|---|---|---|---|---|
| **Self-Forcing (DMD)** — drafter | 1.3B（从 Wan2.1-1.3B）| 64× H100 | **<2 h（600 iters）≈128 H100-GPU-时**；或 8×H100 上 <16 h（梯度累积）| **Data-free**（无视频数据），仅文本 prompt | [GitHub README](https://github.com/guandeh17/Self-Forcing) ✅ |
| **CausVid** — 因果蒸馏 | 50步→4步 因果学生 | 8 节点×8 卡 = 64 GPU（型号未注明）| 未报告（玩具跑"~1K iters 饱和"）| MixKit 6K 视频（玩具）；注明真实跑需更大数据 | [GitHub](https://github.com/tianweiy/CausVid) + [主页](https://causvid.github.io) ✅ |
| **Krea Realtime 14B** — target | 14B（从 Wan2.1-14B）| causal ODE 预训练 **128× H100**；Self-Forcing DMD 64× H100（FSDP ZeRO-3）| 预训练 = 128 H100 上 3k 步；DMD 墙钟/GPU-时 **未披露** | Data-free；VidProm prompt 的合成 ODE 轨迹；时间步蒸馏建于 LightX2V 14B step-distill | [Krea 博客](https://www.krea.ai/blog/krea-realtime-14b) ✅ |
| **Causal Forcing++** — drafter 蒸馏 | teacher Wan2.1-1.3B；Stage-3 critic 14B | A800（数量未注明；batch 64）| **causal-ODE 初始化 ≈11,600 A800-GPU-时** vs 他们的 causal-CD 初始化 **≈2,900 A800-GPU-时**；三阶段 20K/5K/1K 步 | 80K 视频采自 OpenVid（阶段 1-2）；VidProM（阶段 3）| [arXiv](https://arxiv.org/abs/2605.15141) ✅ |
| **LightX2V 14B StepDistill** — drafter | 14B | 未报告 | 未报告（"extended iterations"）| "更高质量数据集"（未具体）| [HF](https://huggingface.co/lightx2v/Wan2.1-T2V-14B-StepDistill-CfgDistill-Lightx2v) ✅ |
| **AnyFlow** — flow-map 蒸馏 | 1.3B → 14B | 摘要/元数据未报告 | 未报告 | 未报告 | [arXiv](https://arxiv.org/abs/2605.13724) ✅（算力未披露）|
| **Wan 2.1 基座**（上下文）| 1.3B / 14B | 未披露 | 未披露 | "数十亿图像和视频" | [arXiv](https://arxiv.org/abs/2503.20314) ✅（无算力数字）|

**Q2 结论**：**造一个视频 drafter 的"蒸馏"步出乎意料地便宜、而且基本 data-free**——经典 Self-Forcing 配方 **64× H100 上 <2 h（~128 H100-GPU-时）**、只用文本 prompt 就收敛（或 8×H100 上 <16 h）。贵的地方有两处：(a) 上游基座（Wan "数十亿图像/视频"，算力未披露）；(b) 某些 pipeline 需要的 **causal-ODE 初始化**——Causal Forcing++ 实测 1.3B 规模 **≈11,600 A800-GPU-时**（正因为太贵，他们才提出 ~2,900 A800-时 的 causal-CD 替代）。**升到 14B（Krea）**：预训练涨到 **128 H100 跑 3k 步** + 64-H100 FSDP-ZeRO-3 的 DMD（墙钟未披露）。

> **对你的意义**：如果走"在线持续学习 drafter"（方向二/三），好消息是**基础 drafter 的蒸馏成本低到 ~百 H100-时量级**，在线增量更新只会更小；真正的算力大头在基座和（可选的）causal-ODE 初始化，而那些是一次性的、可以直接用现成开源权重绕过。

---

## 四、信源可信度 & 注意事项

- **✅ 已打开核实**：SDVG(2604.17397)、Self-Forcing(2506.08009 + GitHub)、CausVid(2412.07772 + 主页 + GitHub)、Krea Realtime 14B(krea.ai 博客 + GitHub + HF)、Causal Forcing++(2605.15141)、SRDiffusion(2505.19151)、SpeCa(2509.11628)、T-Stitch(2402.14167)、Wan(2503.20314)、AnyFlow(2605.13724)、LightX2V(GitHub + HF step-distill 卡)。
- **⚠️ 仅 S2 元数据（未逐页打开）**：HybridStitch(2603.07815)、GoatWu/Self-Forcing-Plus（据 LightX2V HF 卡，未直接打开）。
- **❌ 已剔除/警惕**：Self-Forcing 的引用列表里有 ~100 个 2026-05（2605.xxxxx）arXiv ID，符合"疑似未来日期幻影 ID"的警示——**除了我逐个打开确认的 4 个（Causal Forcing++ 2605.15141、AnyFlow 2605.13724 等），其余一律未纳入**。
- **已知缺口**：(1) SDVG 截至 2026-06 无公开代码；(2) Movie Gen(2410.13720) 只作为 prompt benchmark 来源，未调研其算力；(3) 多数 step-distill drafter（LightX2V、AnyFlow）不披露训练算力，只有学术蒸馏论文（Self-Forcing、Causal Forcing++）给了具体 GPU-时。

---

## 五、与其它方向的衔接

- **方向二**（`002-video-spec-online-learning-aurora.md`）：Aurora/ATLAS 式在线自适应 speculator——本方向给出的"drafter 蒸馏成本低、基座可用开源权重绕过"是它落地的前提。
- **方向三**（`003-...`，进行中）：沿 Aurora 做**跨域持续学习**，让 speculator 不断学不同 domain 的投机知识而不遗忘。
