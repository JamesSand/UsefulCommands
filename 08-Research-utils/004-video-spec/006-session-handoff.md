# 会话 Handoff —— 给接手的 Claude Code

> **这份文档的用途**：把上一段会话的项目状态、已确立结论、已纠正的坑、工作方法、开放线索，整理成可直接接手续做的形式。**不是逐字转录**，是状态快照 + 续做指南。
> **写于**：2026-06-01。所在目录：`/Users/zhizhousha/workspace/UsefulCommands/08-Research-utils/004-video-spec/`

---

## 0. 怎么用这份文档

1. 先读本节 + 第 1、2、3、4 节（项目、文件、已确立结论、已纠正的坑）。
2. 续做前**务必看第 4 节"已纠正的前提"**——我（上一个 Claude）早期有几处口误已被核实纠正，别重新踩。
3. 工作方法（第 5 节）和用户偏好（第 6 节）**必须延续**。
4. 要继续做什么 → 第 8 节"开放线索"。

---

## 1. 用户 & 项目（一句话）

用户在 **Together.ai**，研究**视频生成的 speculative decoding**，目标是把 Together 自己的 **Aurora**（在线自改进 speculator）/ **ATLAS**（静态+自适应双 speculator）推广到**视频**，并在其上做**跨域持续学习 + 长 context + 量化/稀疏**等系统优化。种子论文是 **SDVG**（`004-video-spec/2604.17397v1.pdf`，arXiv:2604.17397，training-free 视频投机解码：1.3B Wan2.1 Self-Forcing drafter 出块 → ImageReward 路由 → 14B Krea Realtime target 重生成被拒块；1.59×@98.1%）。

---

## 2. 文件清单（都在本目录）

| 文件 | 内容 | 状态 |
|---|---|---|
| `2604.17397v1.pdf` | 种子论文 SDVG | — |
| `001-video-spec-decoding-progress.md` | 视频投机解码进展；公开 pipeline（无专用 pipeline，得自拼 Self-Forcing+Krea/LightX2V+ImageReward）；训练算力（drafter 蒸馏便宜 ~128 H100-时、data-free）| 完成 |
| `002-video-spec-online-learning-aurora.md` | 在线自改进 speculator + Aurora/ATLAS 迁到视频；含 **§1.5 双 speculator+控制器** 详解 | 完成 |
| `003-video-spec-continual-multidomain.md` | 跨域持续学习/防遗忘；**§六** 回答了 ΔW（小/低秩→LoRA bank）和视频 domain 怎么分（按接受难度聚类，非语义类）| 完成 |
| `004-quantized-kv-cache-speculator.md` | 量化 Aurora payload + 在量化特征上训 speculator（前提纠正：Aurora 不传 KV）| 完成 |
| `005-long-context-speculator-training.md` | 长 context 训 speculator；两个顾虑都不是根本障碍；**§六** sliding-window/selective-attention 能否训 + 盲窗 caveat + NSA/MoBA 空白 | 完成 |
| `006-session-handoff.md` | 本文档 | — |

**复用的方法（skill）**：`/Users/zhizhousha/workspace/UsefulCommands/.claude/skills/citation-deep-research/SKILL.md` —— 引用图谱 deep research 方法（Semantic Scholar API + WebSearch + 逐篇核实 + 后台 agent 并行）。**续做时优先用它。**

**记忆**：`~/.claude/projects/-Users-zhizhousha-workspace/memory/video-spec-decoding-research.md`（项目线）和 `naming-convention-numbered-md.md`（命名规矩）。

---

## 3. 已确立的关键结论（别重新查，直接用）

**Aurora / ATLAS（方向二，`002`）**
- Aurora（[arXiv:2602.06932](https://arxiv.org/abs/2602.06932)，Together）= serve-to-train 飞轮：SGLang 推理服务器流式传 `{EAGLE-3 多层 hidden states, logits, tokens, 拒绝轨迹}` → 异步训练服务器梯度更新 + 热替换 speculator 权重。RL 形式化 + "Discard Sampling" 拒绝 KL。
- ATLAS（NeurIPS'25）= **静态 speculator(速度地板) + 自适应 speculator + 置信度控制器**；最高 4× over vLLM。**双 speculator+控制器把"稳定-可塑性"焊进架构**：静态永不遗忘保最坏，自适应学新域，控制器仲裁 + 调 lookahead。
- 迁到视频：token-logit 蒸馏换成**对 target 重生成块的潜变量蒸馏**（重生成块是已付费的 teacher）；路由奖励换成 **ImageReward 块接受率**。

**持续学习/多域（方向三，`003`）**
- 防遗忘比通用 CL 便宜（静态地板保底、接受/拒绝是免费稠密奖励、draft 小养得起 bank）。
- 推荐架构：静态地板 + per-域 LoRA 银行(O-LoRA 正交) + 域路由(MetaSD 式 bandit) + 跨域 reservoir replay + per-域检索 datastore(冷启动) + plasticity 保护(continual backprop)。
- **MetaSD 没 release**；唯一 release speculator 的是 **Aurora**（HF: `togethercomputer/Aurora-Spec-*`，0.5B EAGLE3），但是按(基座,单域)的单个 drafter，**不是可互换多域 bank**。
- **ΔW（域 drafter 间权重差）= 小/低秩**（无直接测量，从 LoRA r=1–4 / intrinsic-dim ~200 参 / task vector / EDA 27.5% 推断）→ **per-域用 rank-4–16 LoRA bank 就够**。
- **视频 domain 该按"接受难度聚类"分，不按语义类**：主轴=运动幅度、场景稳定性、风格规律性、生成任务(I2V/编辑更好预测)。建议 运动×任务(≈6桶)×可选风格。

**量化 KV（`004`）**
- 量化 KV *跑* 投机解码已成熟（QuantSpec 2502.10424 自投机4-bit KV >90%接受；QSpec 2410.11305；SPEQ；ML-SpecQD），**但全 training-free**。
- **在量化特征上 *训* speculator = 空白 = 机会**。

**长 context 训（`005`）**
- 有人做过且有效：OWL 的 EAGLE-3-L（32K 续训，64K 接受 1.28→3.23）；TorchSpec 生产里训 100K–200K（Kimi K2.5）。
- 顾虑1(OOM)=工程问题（显存大头是 target hidden states ~7GB/128K，disaggregation 把 4K 上限抬到 200K）；顾虑2(capacity)=大体伪命题（真问题是 train-short/serve-long 位置 OOD + attention drift；TTS 不改大模型就救回、OWL 用更小 LSTM 反超）。
- **sliding window/selective attention 能训**（LongSpec 512滑窗、TriForce 检索稀疏都行），但**盲窗在远程依赖 token 上崩**（TriForce needle: 盲窗 0.0519 vs 检索 0.9878）→ 用**内容/检索/验证引导稀疏**而非盲窗。
- **用可训练块稀疏(NSA/MoBA)训 draft 头 = 空白 = novelty**。

---

## 4. 已纠正的前提 / 易踩的坑（重要！）

1. **Aurora 不传 KV cache**。它传 EAGLE-3 hidden states + logits + tokens。logits 已被它压 128×；**BF16 hidden states 才是没压的大头**。（用户最初说"瓶颈是 KV transfer"，已纠正。）
2. **"online-from-scratch 超过 pretrained" 是分场景的**：混合流量下能超（3.08 vs 2.63）；**有序域漂移下只是追平**（~10k 请求后 2.46 vs 2.57）。别一概而论。
3. **"EAGLE-3 ≤2K 训→~20K 时掉到 ~1×" 这个具体数字是上一个 Claude 的综合**，TTS 摘要没逐字给；方向/量级由 OWL 实测 EAGLE-3=1.28@64K 独立佐证。引用时按"方向成立、具体数待核"处理。
4. **MovieGenVideoBench 官方是 5 类**（Human activity / Animals / Nature&scenery / Physics / Unusual），**没有 fantasy/text/cinematic**；SDVG 里"cinematic/landscapes"是非正式说法。
5. **隔离条目**：`arXiv:2602.07223` 标题元数据冲突（列表"SpecAttn" vs 正文"Vegas"），**不作承重引用**（其思路被 SpecAttn 2510.27641 独立佐证）。
6. **ATLAS 没有独立 arXiv**（仅 Together 博客 + NeurIPS'25 talk 页）；EAGLE 3.1、TorchSpec 是厂商博客、非同行评审——引用时标注。
7. 大量 2026 的 arXiv ID（2602/2603/2604/2605.xxxxx）是真的（已逐个打开），但也有 Semantic Scholar 返回的**幻影未来 ID**——**任何 2026 ID 续用前必须自己打开核实**。

---

## 5. 工作方法（必须延续）

1. **不抓 Google Scholar**（封爬虫）。用 **Semantic Scholar Graph API**（`https://api.semanticscholar.org/graph/v1/paper/arXiv:<ID>/citations?fields=...&limit=100&offset=0`，429 就重试/减字段）+ WebSearch + WebFetch。
2. **逐篇核实**，分三档标注：✅ 打开确认 / ⚠️ 据二手·待复核 / ❌ 未能核实·隔离（不进正文）。**宁可少而实，不可多而虚。绝不编造 ID/标题/数字/repo。**
3. **大范围检索丢给后台 `general-purpose` agent**（`run_in_background:true`），自己复核关键论断再落 md。
4. **诚实优先**：结论哪怕和用户提问框架相反也先说底线（已多次如此，用户认可）；每份 md 必有"信源可信度"节。

---

## 6. 用户偏好

- **文件命名**：`00x-english-kebab.md`（零填充数字前缀 + 英文 kebab）；**内容用中文**，文件名英文。续做新 md 用下一个序号（下一个是 `007-`）。
- **语言**：中文讲解；技术名词/论文 ID 用英文。
- **风格**：要硬数据和链接、要诚实的可信度标注、喜欢"先给结论再展开"、喜欢 ASCII 图解；会主动追问细节（release 没有、ΔW 多大、input length 多少）。
- 用户习惯让我**把答案写回对应 md**，而不只是口头答。

---

## 7. 对话脉络（问了什么，按顺序）

1. 读 SDVG → 写论文总结（注：早期还做过一个 Hinton Forward-Forward 的总结，在 `~/workspace/forward-forward/`，与本项目无关）。
2. 方向一：视频投机解码进展（公开 pipeline？训练算力？）→ `001`。
3. 方向二：让 speculator 在线变好 + 结合 Aurora → `002`。
4. 追问"双 speculator+控制器是什么" → `002 §1.5`。
5. 方向三：跨域持续学习不遗忘 → `003`。
6. 追问"LLM speculator CL 值不值 + 他们 release 了吗 + ΔW 多大" + "视频有哪些 domain" → `003 §六`。
7. 想法：量化 KV 训 speculator（沿 Aurora 瓶颈）→ `004`。
8. 追问 TTS 有没有 codebase（无）+ TTS drafter input length（训≤2K、推理被迫到 32K=失配根因）。
9. 想法：很长 context 下训 speculator，两个顾虑成立吗 → `005`。
10. 追问：sliding window / selective attention 能训吗 → `005 §六`。
11. （本次）写 handoff → `006`。

---

## 8. 开放线索 / 从哪继续

### 已识别的"可发表空白"（用户最感兴趣的贡献点）
1. **没人用 backward-transfer 指标测过 draft model 在域增量序列上的灾难性遗忘**（`003`）。→ 建议先搭 **draft-model 域增量 benchmark**。
2. **没有 per-content-category 的视频投机接受率分解**（`003`/`005`，SDVG 只报聚合）。
3. **没人直接测过域 drafter 间的 ΔW（L2/task-vector 范数）**（`003 §六`）——便宜可跑。
4. **在量化 hidden states/KV 上做 QAT 训 speculator**（`004`）——无人占。
5. **没有 per-position 接受长度 vs context 曲线、没有长 ctx 下 drafter 尺寸消融**（`005`）。
6. **用可训练块稀疏(NSA/MoBA)训 draft 头 / 在 NSA/MoBA target 上训 draft 头**（`005 §六`）——无人占。
7. **盲窗 sliding-window 在远程依赖 token 上的接受率窟窿，没人在"已训 drafter"上显式测过**（`005 §六`）。

### 现成的推荐实验（已写在各 md）
- `004 §五`：先给 Aurora 插桩确认 transfer-bound；特征精度消融 {BF16/INT8/INT4/INT2} 测接受率+加速；train/serve 匹配 vs 不匹配。
- `005 §五`：2×2（训练 ctx 长度 × 位置处理）+ drafter 尺寸扫描 + MagicDec 式大 draft 臂；测 per-position 接受曲线。

### 用户可能的下一步
用户上一条提到想把"长 context 这条线的可发表贡献点单独汇总"。若用户继续，可做：(a) 汇总贡献点成提案；(b) 把某个空白具化成实验方案/代码骨架；(c) 沿任一新种子（ZeroFlow/SFFA/QuantSpec/OWL）再 deep research。

---

## 9. 关键论文速查（均已核实，✅；2026 ID 续用前再开一次）

- **SDVG**（种子）2604.17397 · **Aurora** 2602.06932 · **ATLAS**（NeurIPS'25 博客）
- **EAGLE-3**；**OSD** 2310.07177 · **DistillSpec** 2310.08461 · **MetaSD** 2604.05417（未 release）· **OmniDraft** 2507.02659 · **EvoSpec** 2605.27390 · **Training Domain Draft Models** 2503.07807（域漂移接受率 Bio−38%/Zh−28%/Code−7%/Math−4%）· **TTS** 2605.09329（无代码）
- **CL 工具箱**：O-LoRA 2310.14152 · EWC(PNAS'17) · SI(ICML'17) · L2P(CVPR'22) · Loss-of-Plasticity(Nature 2024)
- **ΔW 旁证**：LoRA 2106.09685 · Intrinsic-Dim 2012.13255 · Task-Vectors 2212.04089 · EDA 2603.09527（27.5%）
- **量化 KV 投机**：QuantSpec 2502.10424 · QSpec 2410.11305 · SPEQ 2510.18525 · ML-SpecQD 2503.13565 · 兼容性 2505.22179
- **长 ctx 投机**：TriForce 2404.11912 · MagicDec 2408.11049 · LongSpec 2502.17421(512滑窗) · OWL 2510.07535 · SpecExtend 2505.20776 · TorchSpec(PyTorch 博客) · EAGLE 3.1(vLLM 博客) · P-EAGLE 2602.01469
- **可训练稀疏**：NSA 2502.11089 · MoBA 2502.13189（均不提投机解码）
- **视频基准**：VBench 2311.17982 · VBench-2.0 2503.21755 · MovieGenVideoBench(Meta HF)
- **隔离**：2602.07223（标题元数据冲突，勿承重引用）

---

*接手提示：先把本目录 `001`–`005` 扫一遍（每篇都有 TL;DR + 信源节），再回到第 8 节挑线续做。续做产出仍按 `00x-english-kebab.md`、内容中文、附信源可信度节。*
