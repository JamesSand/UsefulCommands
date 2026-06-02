# 在很长 context 下训 speculator 来提 accept length —— 有人做过吗？你那两个顾虑成立吗？

> **你的想法**：context 特别长（比如 100k）时，用这么长的 context 训 speculator 会有两个顾虑——(1) batch 开不大（长 context → GPU 放不下）；(2) drafter capacity 不够。**但这真的是问题吗？有没有人在很长 context 下训 speculator 提 accept length？**
> **调研方法**：Semantic Scholar + WebSearch + WebFetch（arXiv/GitHub/vLLM/PyTorch 博客），逐篇打开核实（所有 2026 ID 都单独打开确认非幻影）。**日期**：2026-06-01。

---

## TL;DR

1. **有人做过，而且有效**：**OWL 的 "EAGLE-3-L" 基线**就是你说的实验——把 EAGLE-3 在 **32K** context 上续训，64K 测试时 accept length 从 **1.28 → 3.23**（≈2.5×）。**TorchSpec（PyTorch）已经在生产里把 EAGLE-3 drafter 训在 100K–200K tokens**（给 Kimi K2.5）。所以"长 context 训 drafter 提 accept length"既被验证有效、也已在部署。
2. **顾虑 1（batch 小 / OOM）：真实，但是纯工程问题，不是根本障碍**。长 context 下显存大头是 **target 的 hidden states/激活**（TorchSpec 实测 **一个 128K 样本 ≈ 7GB**），**不是那个小 drafter**。**Disaggregation（推理集群 RDMA 流式传 hidden states 给专用训练集群）把共置时的 4K 上限直接抬到 200K**。再加梯度累积 / 窗口化 draft KV / short→long 位置技巧，batch 不必被迫开很小。
3. **顾虑 2（capacity 不够）：大体是个伪命题**。真正的病根是 **train-short / serve-long 的位置分布失配 + "attention drift"**，不是参数容量。证据：TTS **不改大模型**光靠 test-time 适配就救回接受长度；**OWL 用一个更小的 LSTM（只 condition 在单个 token 的 hidden state 上）反而打败了长 context 训的 EAGLE-3**；MagicDec 甚至论证长 context 下"容量是过剩的、可以白嫖更大的 draft"。
4. **最高杠杆不是"训更长/做更大"，而是"修位置分布失配"**：OWL（256-token LSTM）、LongSpec（Anchor-Offset 位置索引）、TTS（test-time 适配）、EAGLE 3.1（norm 修 attention drift）都比硬训长 context 更便宜、还更好或相当。

---

## 一、长 context 投机解码方法一览（关键看：有没有真去训 drafter）

| 方法 | arXiv/来源 | 训 drafter？ | 训练 ctx 长度 | accept-len / 加速 vs context | 状态 |
|---|---|---|---|---|---|
| **TriForce** | [2404.11912](https://arxiv.org/abs/2404.11912)（COLM'24）| **training-free**（target 权重 + 检索式稀疏 KV 自起草，分层）| — | 128K 上 A100 2.31×；4090 offload 4.86× | ✅ |
| **MagicDec** | [2408.11049](https://arxiv.org/abs/2408.11049)（2024）| **training-free**（自投机；full target 当 draft + StreamingLLM **固定窗口 KV**）| — | ~2.0×（Llama2-7B-32K），最高 2.51×；**batch 越大收益越大** | ✅ |
| **QuantSpec** | [2502.10424](https://arxiv.org/abs/2502.10424)（2025）| **training-free**（target 当 draft + 分层 **4-bit 量化 KV**）| — | ~2.5×，>90% 接受；长 ctx 自投机 | ✅ |
| **LongSpec** | [2502.17421](https://arxiv.org/abs/2502.17421)（2025, SAIL）| **训**，但位置泛化靠**短序列**训 + 小 64K 子集 | 多数短 + 小 64K | 平均接受 3.14–4.21；1.8–3.26×。**Anchor-Offset 索引**修 train-short/serve-long | ✅ |
| **OWL** | [2510.07535](https://arxiv.org/abs/2510.07535)（2025-10）| **训** —— LSTM drafter，只在 **256-token** 序列上训 | **256 tokens** | 64K 上 **EAGLE-3 1.28 → OWL 4.00 → HOWL 6.14**（≈3–5×）| ✅ |
| **OWL 的 "EAGLE-3-L" 基线** | （在 2510.07535 内）| **在长 ctx(32K) 上续训** | **32K（被 OOM 卡住）** | 原版 EAGLE-3 1.28 → EAGLE-3-L **3.23** @64K（仍 < OWL 4.00）| ✅ |
| **SpecPV** | [2512.02337](https://arxiv.org/abs/2512.02337)（2025-12）| **training-free** 自投机（部分-KV 验证）| — | 最高 6× vs AR；指出长 ctx 下**验证**成瓶颈 | ✅ |
| **Sequoia** | [2402.12374](https://arxiv.org/abs/2402.12374)（2024）| **training-free**（树优化）| — | 非长 ctx 专用 | ✅ |
| **SWIFT** | [2410.06916](https://arxiv.org/abs/2410.06916)（2024）| **training-free**（target 跳层自起草）| — | 最高 1.6×；非长 ctx 专用 | ✅ |
| **EAGLE 3.1** | vLLM 博客 2026-05-26 | **training-free 架构修复**（FC-norm/post-norm，修 "attention drift"）| — | 长 ctx 上接受长度比 EAGLE-3 **最高 ×2** | ✅（博客）|
| **P-EAGLE** | [2602.01469](https://arxiv.org/abs/2602.01469)（2026-02）| **训**，靠序列切分 + 梯度累积把并行起草训练扩到长 ctx | 长（已支持）| 1.10–1.36× over AR EAGLE-3（重点是并行起草）| ✅ |
| **SpecForge** | [2603.18567](https://arxiv.org/abs/2603.18567)（2026-03）| 训练**框架**（在线/离线 + 混合并行）| EAGLE-3 默认 2048 | 基础设施，非方法 | ✅ |
| **TorchSpec** | PyTorch 博客 2026 | **把 EAGLE-3 训在 100K–200K tokens**（Kimi K2.5）| **100K–200K** | +26–60% 吞吐；未报 per-position 接受长度 | ✅（博客）|

---

## 二、有没有人"离线在长 context 上训 drafter 提 accept length"？—— 有，三个独立已核实数据点

1. **TorchSpec（PyTorch, 2026）**：为 Kimi K2.5 把 EAGLE-3 draft 训在 **100K–200K tokens** 序列上，生产规模（600K 样本、6B tokens、1500 H200-时）。**这是当下部署中的离线长 ctx drafter 训练配方。**
2. **OWL 的 "EAGLE-3-L" 基线（2510.07535）**：**就是你想做的实验**——把 EAGLE-3 在 **32K** context 续训。结果 64K 测试接受长度 **1.28 → 3.23**（≈2.5×）。即**在长 context 上训确实大幅提接受长度**。但他们**因 OOM 没法超过 32K**——你的顾虑 1 的具象化。
3. **LongSpec（2502.17421）**：训长 ctx drafter，但刻意把大部分训练**保持短**，用 **Anchor-Offset 位置索引**让短训 draft 泛化到长 ctx——是 TTS 那个 test-time 修复的**训练时版本**。

> 所以离线长 ctx 训练配方**存在且有效**；真正开放的设计问题是**怎么训**（直接喂长序列 vs 位置索引技巧 vs 架构改）。

---

## 三、顾虑 2（drafter capacity 不够）成立吗？—— 大体不成立，真问题是分布失配 / attention drift

**capacity 不是瓶颈的证据：**
- **TTS（[2605.09329](https://arxiv.org/abs/2605.09329)）**：**不改大模型**，靠 test-time 适配就救回接受长度——若是容量撞墙，固定尺寸的 draft 不可能恢复。
- **OWL（2510.07535）**：用一个**更小、更简单的 LSTM**（只 condition 在**单个 token** 的 hidden state 上）**打败了长 ctx 训的 EAGLE-3**。他们把 EAGLE-3 的失败归因于 **transformer 在训练窗口外的泛化差（位置/attention 行为）**，而非容量。
- **EAGLE 3.1** 独立定位出 **"attention drift"**（drafter 把注意力从 sink token 上偏移、hidden-state 幅度涨）才是长 ctx 失败模式——又是个分布/动力学问题，**不加容量、靠架构改就修好**。
- **EAGLE 式 drafter 吃的是 target 的 hidden states/KV，长 context 已经被 target 编码进去了**——OWL 把这点推到极致（只用最后一个 token 的 state）。**draft 不需要自己"建模"100K。**
- **MagicDec（2408.11049）** 直接论证了顾虑 2 的反面：长 ctx / 高吞吐下瓶颈是 target 的 KV，所以你可以**白嫖一个更大更强的 draft**（甚至 full target + 固定窗口）。**容量是过剩，不是稀缺。**

**顾虑 2 里那点真理核**：OWL 长 ctx 训的 EAGLE-3（3.23）仍**没追上** OWL（4.00），所以*部分*差距是**长程的架构适配**——但**纯参数容量不是那堵墙**。

> **判决：顾虑 2 大体是红鲱鱼；主导问题是 train-short/serve-long 的位置 OOD + attention drift。**

---

## 四、顾虑 1（长 context → batch 小 → OOM）成立吗？—— 真实，但是工程问题，不是根本

- **真实到会咬人**：OWL **在 32K 撞 OOM**、"没法再加"；**共置（co-located）**训练时，一旦 72GB 的 target 占着显存，EAGLE-3 训练在 H200 上**只到 ~4K tokens**（TorchSpec）。
- **但成因正好印证你的直觉**：显存大头是 **target 的 hidden states/激活，不是那个小 drafter**。TorchSpec 量化：**一个 128K 样本 ≈ 7GB 的 target hidden states**（5.25GB 辅助层 + 1.75GB 最后 hidden）；EAGLE 头本身可忽略。
- **标准缓解手段已经部署、且够用**：
  - **Disaggregation（TorchSpec）**：推理集群把 hidden states 经 RDMA 流给训练集群，训练集群显存全给 draft → **4K 上限抬到 200K**。
  - **序列切分 + 序列内梯度累积**（P-EAGLE），驯服并行起草的二次成本。
  - **常数/窗口化 draft KV（512-token 滑窗）+ FlashAttention 兼容的"加噪"训练 + embedding/LM-head 权重共享**（LongSpec）。
  - **短序列训练 + 位置索引泛化**（LongSpec Anchor-Offset、OWL 256-token 训练）——**直接绕开长 ctx 训练显存**。
- **这个 niche 里还没怎么用上的开放杠杆**：显式 **ring attention / 完整 context-parallelism**、以及给 *drafter* 用 **YaRN/NTK/PI**（LongSpec 反而刻意把 RoPE base 固定成和 target 一致，而非插值）。

> **判决：顾虑 1 是"已解决/可解决的工程问题"（disaggregation、梯度累积、窗口化 draft KV、short→long 位置技巧），不是根本障碍。"batch 被迫很小"不成立——把 drafter 的显存和 target 解耦即可。**

---

## 五、结论 + 推荐实验

**结论**：**是的，长 context 训 speculator 能提长 ctx 的接受长度**（OWL EAGLE-3-L 1.28→3.23@64K；TorchSpec 100K–200K 生产训练）。但数据说**最高杠杆是"修 train-short/serve-long 的位置分布失配 / attention drift"，而不是买容量、也不是硬付百万-token 的训练 batch**：OWL（256-token LSTM）、LongSpec（Anchor-Offset）、TTS（test-time）、EAGLE 3.1（norm 修复）都比暴力长 ctx 训练更便宜、还更好或相当。**你那两个顾虑都是真实信号，但都不是根本墙——#1 是工程，#2 多半是被错贴标签的"分布失配"。**

**推荐实验（干净的 2×2）**：
1. 固定 target + EAGLE-3 头尺寸。变 **(a) 训练 context 长度** {2K, 8K, 32K}，用 **TorchSpec 式 disaggregation**（这样 batch 不被迫很小——梯度累积 + 流式 hidden states）；变 **(b) 位置处理** {vanilla RoPE, Anchor-Offset/随机偏移索引, YaRN/NTK 扩展}。
2. 测 **接受长度 vs *测试* context 位置** 的曲线（4K/16K/32K/64K/128K）——这条 per-position 曲线 OWL/LongSpec 都没好好报。
3. 加一个 **drafter 尺寸扫描**（如 1 层 vs 2–4 层头）在**固定长 ctx**下，直接检验顾虑 2——**若接受长度对尺寸平、对位置处理陡，容量就坐实是红鲱鱼**。
4. 加一个 **MagicDec 式"更大 draft + 固定窗口"**臂、高 batch，检验"容量过剩"的说法。

> 文献给的假设：**位置处理 ≫ 训练长度 ≫ drafter 尺寸**（对长 ctx 接受长度的影响）；且 disaggregation 直接消掉 OOM/小 batch 约束。

---

## 六、能不能用 sliding window / selective attention 训长 ctx drafter？（这也是伪命题吗？）

### 判决
**能，而且这本来就是主流做法——但"盲目滑动窗口"不是免费午餐，机制要紧。** 根因和"capacity 是伪命题"同一个：drafter 吃的是 target 的 hidden states、只做局部精修，**它自己的 attention 大体只是个局部层，小窗口通常够**。所以——
- **"训长 ctx drafter 必须 full attention" = 假前提**：LongSpec 的 drafter 就是用 **512-token 滑窗**训出来的，长 ctx 上仍 **最高 3.26×**、且无损（验证对的是 full target）。
- **但"随便开个盲窗就行" = 也不对**：固定 StreamingLLM 式窗口在**依赖远处上下文的 token**上会**崩**。**内容感知 / 检索式 / 验证引导的稀疏**才能保住接受率。

### 关键 caveat（最直接相关的发现）—— 盲窗 vs 选择性稀疏，接受率差一个数量级

- **TriForce Table 1（120K ctx，4K KV 预算）**，needle 检索任务上 draft 接受率：
  **StreamingLLM 盲窗 0.0519 / H2O 0.0739 / 检索式 0.9878** —— **~19× 的差距**，正好砸在"从远处 copy/检索"这类 token 上。而在 PG-19（局部可预测文本）上三者几乎没差（0.91~0.96）。→ **盲窗在"局部可预测"时没事，在"远程依赖"时灾难。**
- **SpecExtend（[2505.20776](https://arxiv.org/abs/2505.20776)）**：用"跨模型检索"（target 末层 attention 给 chunk 打分、填 draft 的小 KV），把小 draft 的 needle 准确率从 **16.6%（StreamingLLM）→ 82.3%**（接近用 full target 的 97.6%）。原文：*静态驱逐策略下，需要细粒度用到过去上下文的任务（如 needle）draft 准确率会退化……因丢失重要上下文、target-draft 分歧增大。*
- **机制根因 = target-draft 分歧**：盲窗让 draft 注意到的上下文（被截断）和 target 验证用的不一样，远程依赖处分布一岔，接受率就掉。**内容选择把 draft 的有效上下文重新对齐到 target。**

> **对你的设计**：若 LongSpec 式用滑窗训 drafter，平均长 ctx 加速会不错，但**在远程依赖 token 上有个没人公开测过的接受率窟窿**。要补上 → 给 draft 用**内容/检索/验证引导的 KV 选择**，而不是固定 StreamingLLM 窗口；或"小局部窗 + top-k 检索/sink 集"二者合一。

### 相关工作一览

| 工作 | arXiv/来源 | 窗口/稀疏机制 | 训 drafter？ | 接受率影响 | 状态 |
|---|---|---|---|---|---|
| **LongSpec** | [2502.17421](https://arxiv.org/abs/2502.17421) | draft 自注意 **512 滑窗** + 常数 KV + anchor 位置 | **是** | 最高 3.26×、无损；**无窗口大小消融、无 per-距离接受分析** | ✅ |
| **TriForce** | [2404.11912](https://arxiv.org/abs/2404.11912) | **检索式稀疏 KV**（分块、query 对 chunk-mean key 打分、取 top，~3% 预算）| 否（training-free）| 检索 needle 0.9878 vs 盲窗 0.0519 | ✅ |
| **MagicDec** | [2408.11049](https://arxiv.org/abs/2408.11049) | draft 用 **StreamingLLM 固定窗 KV**（常数预算）| 否 | 最高 2.51×；针对大 batch KV 带宽 | ✅ |
| **SpecExtend** | [2505.20776](https://arxiv.org/abs/2505.20776) | **跨模型检索**：target 末层 attention 选 chunk → 填 draft 小 KV | 否（即插即用）| needle 16.6%(盲窗)→82.3%(检索) | ✅ |
| **OWL** | [2510.07535](https://arxiv.org/abs/2510.07535) | LSTM draft 只 condition 单 token state（≈窗口=1）| **是** | 长 ctx 接受 ≈EAGLE-3 的 5× | ✅ |
| **NSA**（Native Sparse Attention）| [2502.11089](https://arxiv.org/abs/2502.11089) | **可训练**分层稀疏（压缩+细选+滑窗分支，端到端）| 骨干（非 drafter）| 匹配/超过 full attn；**全文不提投机解码** | ✅ |
| **MoBA**（Mixture of Block Attn）| [2502.13189](https://arxiv.org/abs/2502.13189) | **可训练** MoE 式块选择，full↔sparse 可切 | 骨干（非 drafter）| 长 ctx 增益；**不提投机解码** | ✅ |
| **SD + Blockwise Sparse Attn（MatX）** | [matx.com/research/sd_nsa](https://matx.com/research/sd_nsa)（2025-07）| 用 NSA 训 **target** + 自投机；强制一批 draft token 共享同一上下文块子集，使验证保持稀疏 | target 训 NSA；自投机 | 质量保持、验证算术强度最高 3.5× | ⚠️（产业技术报告、非 arXiv、小模型短 ctx）|
| **SpecAttn** | [2510.27641](https://arxiv.org/abs/2510.27641) | draft 跑 full attn → 其 attn 权重选显著 token → **验证器**对 top-p 集跑稀疏 | 否 | ~75% KV 访问削减；仅测 2048 ctx；端到端增益小 | ✅ |
| ~~Vegas / SpecAttn-codesign~~ | [2602.07223](https://arxiv.org/abs/2602.07223) | 验证引导稀疏（验证副产物当 draft 稀疏 KV）| 否（自投机）| 1.25–2.81× vs vLLM | ❌ **隔离**（2026 ID、标题元数据冲突）|

### 可训练稀疏注意力 训 drafter —— 空白评估（你的潜在 novelty）

- **NSA / MoBA 是货真价实的可训练稀疏 *骨干*，但两篇都完全没提投机解码 / draft model**（逐篇打开确认）。所以"用 NSA/MoBA 式块稀疏注意力去训一个 EAGLE 式 draft 头"**在原始论文里没有被做过**。
- **最接近的只有 MatX 那篇技术报告**：它训的是 **target**（NSA）+ 自投机，**没有在 NSA/MoBA target 上训一个独立 draft 头**，且是小模型/短 ctx 的产业报告。
- **空白判决 ⚠️ 真实且大体敞开**：没有已核实工作 *用可训练块稀疏（NSA/MoBA）训一个专用 draft 头*，也没有 *在 NSA/MoBA target 上训 draft 头*。**这是个站得住的新意点**——前提是把 draft 的稀疏设计成**内容/可学**的，而不是盲窗（见上面 caveat）。

### 训练效率角度（顺带回答"能不能省训练显存"）

- LongSpec 的 512 滑窗给的是**常数大小 draft KV**（明确是*推理*显存收益）；它**没量化**长 ctx *训练*显存的节省（把训练可行性归给"flash noisy training"）。→ 训练省显存**合理但未实测**。
- **P-EAGLE（[2602.01469](https://arxiv.org/abs/2602.01469)）** 直说长 ctx drafter *训练*成本"随 序列长×并行位置 二次增长"，但它用的是 **attention-mask 预计算 + 序列切分**，**不是稀疏注意力**——侧面证实长 ctx drafter 训练确是 OOM/算力痛点，也暗示窗口/稀疏 draft attention *应当* 能省训练显存（O(window) 而非 O(L)），但**没有已核实论文为 drafter 单独测过这个训练侧数字**。
- **NSA 报告稀疏注意力同时加速 forward 和 backward（训练）**（64k 上）——所以训练算力收益**对骨干是确立的**，原则上可迁移到稀疏注意力 drafter。

**本节信源**：✅ 已核实：LongSpec 2502.17421、TriForce 2404.11912（Table 1 两次核对）、MagicDec 2408.11049、OWL 2510.07535、NSA 2502.11089、MoBA 2502.13189、SpecExtend 2505.20776（退化引文已核）、SpecAttn 2510.27641、代码长程依赖 2407.21049。⚠️ MatX 报告（产业、非同行评审）；EAGLE 3.1（仅博客）；P-EAGLE 2602.01469（2026 ID）。❌ 隔离：2602.07223（标题元数据冲突，不作承重引用，但其"验证引导稀疏"思路被 SpecAttn 独立佐证）。

---

## 七、信源可信度

- ✅ **打开并确认**（arXiv 摘要+正文）：TriForce 2404.11912、MagicDec 2408.11049（+Together 博客确认 StreamingLLM 窗口、training-free）、QuantSpec 2502.10424、LongSpec 2502.17421（v2：Anchor-Offset、512 窗口）、OWL 2510.07535（v1：256-token 训练、1.28→4.00→6.14、EAGLE-3-L 32K OOM→3.23）、SpecPV 2512.02337、Sequoia 2402.12374、SWIFT 2410.06916、TTS 2605.09329、Aurora 2602.06932、P-EAGLE 2602.01469、SpecForge 2603.18567。
- ✅ **博客（一手、非 arXiv）**：TorchSpec（PyTorch, 2026 —— Kimi K2.5 100K–200K 训练、~7GB/128K hidden states、disaggregation）；EAGLE 3.1（vLLM, 2026-05-26 —— attention drift、长 ctx 接受 ×2）。
- ⚠️ **二手/需注意**：TTS 摘要确认 EAGLE-3/DFlash/PARD 的接受长度衰减到 ~1，但**没逐字给出"≤2K 训→~20K 时 ~1×"这个具体数**——那个具体说法是我之前的综合，**方向/量级由 OWL 实测 EAGLE-3=1.28@64K 独立佐证**。EAGLE 3.1、TorchSpec 是厂商博客、非同行评审。
- ❌ **真实空白**：LongSpec/TorchSpec **没发 per-position 接受长度 vs context 曲线**；**没有公开的长 ctx 下 drafter-尺寸消融**（OWL 明确说没有）。→ 正是上面推荐实验要填的。

---

## 八、与视频 speculator 的衔接

- **同样的病在视频上必然出现**：视频越长 → block 数越多 → drafter 要 condition 的时序上下文越长；若 drafter 只在短片段上训，长视频接受率同样会衰减（=本文件的 train-short/serve-long）。
- **修法直接迁移**：(i) **位置处理优先**（Anchor-Offset 式索引 / test-time 适配）远比"把视频 drafter 做大"划算；(ii) **disaggregation** 同样适用——视频 target（扩散 transformer）的特征也是显存大头，把 drafter 训练与 target 解耦即可绕开长视频 OOM；(iii) **drafter 吃 target 特征**——长时序信息已被视频 target 编码，drafter 容量需求不高（呼应方向三 Q1c：低秩小 ΔW）。
- **一句话**：在视频上，"长 context 训 speculator"同样**值得做、且两个顾虑同样不构成根本障碍**；优先投资**位置/分布对齐 + disaggregated 训练**，而不是堆容量或硬开大 batch。
