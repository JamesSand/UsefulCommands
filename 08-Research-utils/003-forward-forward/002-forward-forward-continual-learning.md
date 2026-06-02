# Forward-Forward 研究进展调研（侧重 continual learning + 三大会）

> **种子论文**：G. Hinton, *The Forward-Forward Algorithm: Some Preliminary Investigations*, arXiv:2212.13345（2022-12）→ 见 [`001-forward-forward.md`](./001-forward-forward.md)
> **调研方法**：拉取 Semantic Scholar 引用图谱（380+ 篇引用，覆盖 2022-12 → 2026 初，分 4 页各 100 条）+ WebSearch 定向检索 + 对重点论文逐个到 arXiv / OpenReview / PMLR 核实会议与年份。
> **引用数**：来自 Semantic Scholar，仅作相对影响力参考（会低估很新的论文）。
> **调研日期**：2026-05-31。
> **一句话提醒**：这领域已经很大也很噪（大量低质的边缘设备/医学应用论文），下文只保留有分量的工作，没核实成功的在第五节单独列出。

---

## TL;DR（先看这段）

1. **FF 没死，但重心偏移了**。种子论文 380+ 引用，2025–2026 仍有稳定跟进；但**纯 FF** 的论文主要落在中端会议和硬件期刊（ECAI、AAAI、Scientific Reports、Nature Communications 的硬件向、IEEE 神经形态/边缘会议），**三大会（NeurIPS/ICML/ICLR）更多接收的是"广义 forward-only / 无反传"这个更大的框**，而不是 Hinton 原版 FF。
2. **FF 还是不扩展（doesn't scale）**。所有 FF 专属结果都卡在 MNIST / CIFAR-10/100 量级，没人做到 ImageNet 级别；大数据上仍明显落后反向传播。进步来自"层间协作 / 对称-对比目标 / 空间 goodness 编码"等小改良，**没有单点突破**。
3. **关于你最关心的 continual learning**：「**FF 解决了持续学习**」这个说法目前**站不住**；更准确的结论是「**forward-only learning 对缓解灾难性遗忘有帮助**」。
   - 真·Hinton 式 FF 用于 CL 的代表作只有一篇拿得出手：**SFFA（CoLLAs 2025）**。
   - 而真正打进三大会的 CL 强结果（**ZeroFlow @ ICML 2025**、FoRo @ ACM MM 2025、FLEX）其实是**零阶优化 / 进化策略 / 冻结骨干**这一类 forward-only 方法，**不是** FF。
4. FF 真正的"主场"是**模拟/光学/脉冲/神经形态硬件**和边缘设备——反传在这些硬件上难实现，FF 只需两次前向，正好补位。Hinton 当初的「生物可信度 + 凡人计算」动机仍是这条线最持久的吸引力。

---

## 一、整体格局：FF 现在到哪一步了

- **动量**：引用量持续上升（"flat-to-rising in volume"），但**野心在收窄**（"narrowing in ambition"）——FF 正在固化成一个 **「硬件高效 + 生物启发的小众方法」**，而不是"大规模取代反向传播"。
- **技术共识**：FF 能训出来、能诱导出**稀疏且类别专一**的表示、在反传难落地的硬件上有吸引力；但**不扩展**，CIFAR-10/100 就到顶，更大的数据上拼不过反传。
- **改良方向**（哪些"招"真有用）：层间协作（Layer Collaboration）、对称/对比式 goodness、空间 goodness 编码、通道级竞争、把"长度+方向"的技巧用到 CNN/ViT/GNN/SNN 上。

---

## 二、三大会（NeurIPS / ICML / ICLR）上的相关工作 ⭐

> 这是你点名要的重点。注意一个反直觉的事实：**纯 FF 在三大会其实很少**，三大会更偏爱"广义 forward-only / BP-free"。下表把两类都列出来，并标注是「真·FF」还是「广义 forward-only」。

| 会议 | 论文 | 类型 | 在干嘛 | 链接 |
|---|---|---|---|---|
| **ICLR 2024** | Forward Learning with Top-Down Feedback — Srinivasan et al. | 真·FF（理论） | **证明 FF 与 PEPITA 共享同一学习原理**，都近似"自适应反馈对齐"。最干净的 FF 顶会理论入口。✅已核实(OpenReview) | [OpenReview](https://openreview.net/forum?id=My7lkRNnL9) · [arXiv](https://arxiv.org/abs/2302.05440) |
| **ICLR 2024** | Forward Learning of Graph Neural Networks (ForwardGNN) — Park et al. | 真·FF（扩展） | 把 forward-only 训练搬到图神经网络。 | [arXiv](https://arxiv.org/abs/2403.11004) |
| **ICLR 2025** | What should a neuron aim for? Designing local objective functions based on information theory — Schneider et al. | 广义（局部目标） | 用信息论（Infomax 式）设计**局部目标函数**，把 FF 放进"信息论局部学习规则"的谱系里。 | [arXiv](https://arxiv.org/abs/2412.02482) |
| **ICLR 2025** | FLOPS: Forward Learning with Optimal Sampling — Ren et al. | 广义（forward-gradient） | 提升 forward-gradient 学习的**样本效率**。 | [arxiv.org/abs/2410.05966](https://arxiv.org/abs/2410.05966) |
| **ICML 2025** | **ZeroFlow: Overcoming Catastrophic Forgetting is Easier than You Think** — Feng et al. | 广义（CL 重点❗） | **仅靠前向传播的零阶优化就能显著缓解持续学习中的遗忘**，并给出原因分析。CL 方向最强的"前向就够了"主张。 | [arxiv.org/abs/2501.01045](https://arxiv.org/abs/2501.01045) |
| **ICML 2025** | Dendritic Localized Learning — Lv et al. | 广义（生物局部规则） | 树突局部学习规则，生物可信的 BP 替代。 | [arxiv.org/abs/2501.09976](https://arxiv.org/abs/2501.09976) |
| **NeurIPS 2024** | Counter-Current Learning — Kao & Cheng | 广义（双网络 BP 替代） | 生物可信的双网络对偶学习，替代反传。 | [arxiv.org/abs/2409.19841](https://arxiv.org/abs/2409.19841) |
| **NeurIPS 2023** | Fine-Tuning Language Models with Just Forward Passes (**MeZO**) — Malladi et al. | 广义（forward-only，标杆） | **零阶、只用前向**微调大语言模型。是整条 forward-only 线里影响力最大的工作（~394 引用）。 | [arxiv.org/abs/2305.17333](https://arxiv.org/abs/2305.17333) |
| **AAAI 2024** | Layer Collaboration in the Forward-Forward Algorithm — Lorberbom et al. | 真·FF | 指出 FF **没充分利用跨层信息**，加入层间协作来改进。（非三大会，但顶会、强相关） | [arxiv.org/abs/2305.12393](https://arxiv.org/abs/2305.12393) |
| **AAAI 2024** | Convolutional Channel-wise Competitive Learning for FF — Papachristodoulou et al. | 真·FF | **通道级竞争**把 goodness 适配到 CNN。 | [arxiv.org/abs/2312.12668](https://arxiv.org/abs/2312.12668) |

> ⚠️ 表中 AAAI / ICLR / ICML / NeurIPS 的归属，除标「✅已核实」的两项外，其余是 Semantic Scholar 给的会议信息（arXiv ID 真实、归属极可能正确），引用前建议花 30 秒在 OpenReview/DBLP 上复核具体 track（详见第五节）。

**读这张表的关键结论**：你要找"FF 这种方法在三大会的进展"，会发现**真正以"Forward-Forward"为标题、又进了 NeurIPS/ICML/ICLR 的论文几乎没有**；最接近的是 ICLR 2024 那篇把 FF 与 PEPITA 统一起来的**理论**论文。三大会真正在收的是更上位的 **forward-only / 局部学习 / 零阶优化** 这一类——其中和 continual learning 直接挂钩、且分量最重的是 **ZeroFlow（ICML 2025）**。

---

## 三、Continual Learning 专题（你最关心的部分）⭐

触及 CL 的工作分三条线：

### 线 1：直接用 FF / 局部 goodness 做 CL
- **SFFA — A Contrastive Symmetric Forward-Forward Algorithm for Continual Learning Tasks**（Terres-Escudero, Del Ser, Garcia-Bringas，**CoLLAs 2025 / PMLR v274**）。**这是真·FF 用于 CL 的旗舰论文**。✅已核实。
  - 核心论点是**结构性**的：逐层 FF 训练会产出**稀疏、类别专一的神经元**，这种专一性天然抗遗忘。
  - 做法：把每层神经元分成 正/负 两组，goodness 定义为"正激活占总激活的**比值**"，得到对称损失、更强的类别分离。
  - 评测：task-incremental 和 class-incremental 都做了，CL 精度有竞争力且激活稀疏——但**只在 MNIST/CIFAR 量级**。
  - 同组的 **Neural Polarization（ECAI 2024）** 改善了 CL 需要的泛化/稳定性。[arXiv](https://arxiv.org/abs/2408.09210)
  - 机制旁证：**Emergent representations in networks trained with FF（TMLR 2023, Tosato et al.）** 独立证实 FF 会诱导"祖母细胞"式的稀疏专一表示——这正是上面 CL 论文所依赖的机制基础。[arXiv](https://arxiv.org/abs/2305.18353)

### 线 2：广义 forward-only / 无梯度 的 CL（不是经典 FF，但同样"不反传"）
- **FoRo — Forward-Only Continual Learning**（Jiao Chen et al.，**ACM Multimedia 2025**，DOI 10.1145/3746027.3755302）。✅已核实 arXiv。冻结预训练骨干，**纯前向**做 CL：进化策略（CMA-ES）做 prompt tuning + 随机投影/递归最小二乘做知识编码，显著降低平均遗忘，且省内存省时间。[arXiv](https://arxiv.org/abs/2509.01533)
- **ZeroFlow（ICML 2025）**：见上表。**"仅前向的零阶优化本身就能大幅减少遗忘"**——这是目前 CL 方向最强的 forward-only 主张。
- **FLEX — Continuous Agent Evolution via Forward Learning from Experience**（Zhicheng Cai et al.，2025 预印，上升很快）。✅已核实。把"前向学习"的精神扩到 **LLM agent**：靠一个"经验库"成长而非梯度更新；报告 AIME25 +23%、ProteinGym +14%，还给出经验迁移的 scaling law。[arXiv](https://arxiv.org/abs/2511.06449)

### 线 3：生物启发的局部学习（作为"抗遗忘"的对照基线，非 FF）
- **Improving Performance in Continual Learning Tasks using Bio-Inspired Architectures**（Madireddy et al.，**CoLLAs 2023**）。✅已核实。用突触可塑性 + 神经调制（**不是 FF**），在 Split-MNIST/CIFAR-100 上**不用回放缓冲**就追平了 replay 方法——是 FF-CL 工作常用的对照基线。[arXiv](https://arxiv.org/abs/2308.04539)

### what works（哪些确实有效）
- 来自"逐层局部目标"的**稀疏 + 类别专一**，确实能减少类间干扰；**小规模上无需回放的 CL 可达成**。
- **forward-only 优化（零阶 / ES / 进化式 prompt tuning）** 是一条**可信、低内存**的抗遗忘路线，也是当前能进顶会（ICML 2025、ACM MM 2025）的角度。

### open problems（未解难题）
1. **规模**：所有 FF 专属的 CL 结果都在 MNIST/CIFAR 量级，没有接近 ImageNet 级 CL。
2. **class-incremental（无 task ID）** 仍明显比 task-incremental 难得多。
3. FF 依赖"标签条件化的 goodness"，导致标准 CL 推理协议（**对每个类别各跑一遍**）随类别数增长**越来越贵、越别扭**。
4. **缺横向对比**：还没有把 FF 和 EWC / replay / LwF 放在标准 CL 套件上正面 PK 的基准，现有论断多是内部对比。
5. 最强的 forward-only CL 战绩（ZeroFlow、FoRo、FLEX）都是**零阶/ES 或冻结骨干**，**不是** Hinton 式 FF —— 所以「FF 解决 CL」尚未被证实，「forward-only learning 对 CL 有帮助」才是更站得住的结论。

---

## 四、按主题分类的完整跟进列表（备查）

### 4.1 FF 变体 / 更好的目标函数 / 收敛
- **The Predictive Forward-Forward Algorithm** — Ororbia & Mali，**CogSci 2023**。FF 表示回路 + 自上而下生成回路耦合；早期最高引之一（~47）。[arXiv](https://arxiv.org/abs/2301.01452)
- **SymBa: Symmetric Backprop-Free Contrastive Learning with FF** — Lee & Song，2023。对称 goodness 损失，修 FF 梯度不对称、加速收敛（~29）。[arXiv](https://arxiv.org/abs/2303.08418)
- **The Cascaded Forward Algorithm (CaFo)** — Zhao et al.，2023。用级联前向替代逐层 goodness（~23）。[arXiv](https://arxiv.org/abs/2303.09728)
- **Self-Contrastive Forward-Forward** — Xing Chen et al.，**Nature Communications 2025**。自对比负样本；同行评审里最强的 FF 结果之一，瞄准神经形态硬件（~15）。[arXiv](https://arxiv.org/abs/2409.11593)
- **Mono-Forward** — Gong et al.，2025。目标-局部性分解，在多个 benchmark 上**追平 BP 精度**且保持 forward-only。[arXiv](https://arxiv.org/abs/2501.09238)
- **Reshaping FF with a Similarity-Based Objective** — Gong et al.，2025。用相似度 goodness 替代平方激活目标。[arXiv](https://arxiv.org/abs/2509.08697)
- **Extending the Forward Forward Algorithm** — Gandhi et al.，2023。复现 + 扩展到 IMDb/文本（~11）。[arXiv](https://arxiv.org/abs/2307.04205)
- **Contrastive Forward-Forward: 训练 ViT** — Aghagolzadeh & Ezoji，**Neural Networks 2025**。用对比目标把 FF 带到 ViT（~5）。[arXiv](https://arxiv.org/abs/2502.00571)

### 4.2 把 FF 做深 / 做得有竞争力
- **The Trifecta: 训练更深 FF 的三个简单技巧** — Dooms et al.，**TMLR 2023**。三招把 FF 在 CIFAR-10 拉到 ~84%（比 vanilla FF +25%）。✅已核实。[arXiv](https://arxiv.org/abs/2311.18130)
- **Scalable Forward-Forward Algorithm** — Krutsylo，2025。[arXiv](https://arxiv.org/abs/2501.03176)
- **Adaptive Spatial Goodness Encoding** — Gong et al.，2025 / ICASSP 2026。空间 goodness 编码，在卷积网上扩展 FF。[arXiv](https://arxiv.org/abs/2509.12394)
- **The Integrated Forward-Forward Algorithm** — 2023。FF + 浅层 BP + 局部损失整合。[arXiv](https://arxiv.org/abs/2305.12960)
- **Neural Polarization（ECAI 2024）** — 见第三节。

### 4.3 卷积 / 架构
- Convolutional Channel-wise Competitive Learning（**AAAI 2024**）— 见第二节。
- **Training CNNs with the FF Algorithm** — Scodellaro et al.，**Scientific Reports 2025**。傅里叶/形态学空间标签图让 FF-CNN 扩到 CIFAR-100（~19）。[arXiv](https://arxiv.org/abs/2312.14924)
- **Graph Neural Networks Go Forward-Forward** — Paliotta et al.，2023（~8）。[arXiv](https://arxiv.org/abs/2302.05282)
- ForwardGNN（**ICLR 2024**）— 见第二节。

### 4.4 理论 / 分析 / 统一
- Forward Learning with Top-Down Feedback（**ICLR 2024**）— 见第二节。✅
- Emergent representations in FF（**TMLR 2023**）— 见第三节。
- **A theory for the sparsity emerged in FF** — Yang，2023。分析 FF 激活为何变稀疏（~7）。[arXiv](https://arxiv.org/abs/2311.05667)
- **A Study of FF for Self-Supervised Learning** — Brenig & Timofte，2023（~6）。[arXiv](https://arxiv.org/abs/2309.11955)
- **Unifying BP and FF through Model Predictive Control** — Ren et al.，2024。用 MPC 框架同时涵盖 BP 与 FF。[arXiv](https://arxiv.org/abs/2409.19561)
- What should a neuron aim for?（**ICLR 2025**）— 见第二节。

### 4.5 模拟 / 光学 / 脉冲 / 神经形态硬件（FF 的天然主场）
- **BP-free SNN with FF** — Ghader et al.，**Scientific Reports 2025**（~7）。[arXiv](https://arxiv.org/abs/2502.20411)
- **Forward-Forward Training of an Optical Neural Network** — Oguz et al.，**Optics Letters 2023**。物理光学系统上跑 FF（~29）。[arXiv](https://arxiv.org/abs/2305.19170)
- **On-Chip Learning in Vertical NAND Flash Memory Using FF** — IEEE T-ED 2024（~10）。[DOI](https://doi.org/10.1109/TED.2024.3392170)
- **FFCL: Forward-Forward Net with Cortical Loops** — ACM GLSVLSI 2024（~17）。[arXiv](https://arxiv.org/abs/2405.12443)
- **µ-FF: On-Device FF Training for Microcontrollers** — SMARTCOMP 2023（~19）。[DOI](https://doi.org/10.1109/SMARTCOMP58114.2023.00024)
- **Traces propagation: 内存高效的 forward-only SNN 学习** — Pes et al.，Neuromorphic Computing & Engineering 2025。[arXiv](https://arxiv.org/abs/2509.13053)

### 4.6 更上位的 forward-only / BP-free（背景，非严格 FF）
- MeZO（**NeurIPS 2023**）、NoProp（2025, [arXiv](https://arxiv.org/abs/2503.24322)）、Counter-Current Learning（**NeurIPS 2024**）、Dendritic Localized Learning（**ICML 2025**）、ZeroFlow（**ICML 2025**）、FLOPS（**ICLR 2025**）——见第二节表格。

---

## 五、信源可信度 & 注意事项（务必看）

- **✅ 已逐个打开核实**：SFFA（PMLR v274 + arXiv）、Forward Learning with Top-Down Feedback（OpenReview 确认 ICLR 2024 poster）、FLEX（2511.06449）、FoRo（2509.01533）、Madireddy 生物启发 CL（2308.04539）、The Trifecta（TMLR）。其余条目的 arXiv/DOI ID 真实，但未逐页打开。
- **⚠️ 会议归属据 Semantic Scholar，建议复核**：*Layer Collaboration*（2305.12393）与 *Channel-wise Competitive*（2312.12668）的 AAAI 2024；*ForwardGNN*（2403.11004）的 ICLR 2024；*ZeroFlow*、*Dendritic Localized Learning* 的 ICML 2025；*Counter-Current Learning* 的 NeurIPS 2024；*FLOPS*、*Schneider et al.* 的 ICLR 2025。ID 真实、极可能正确，引用前花 30 秒 OpenReview/DBLP 查一下具体 track。
- **⚠️ FoRo / ACM MM 2025**：Semantic Scholar 给了 ACM MM 系的 DOI，但 arXiv 页本身未声明录用。"ACM MM 2025"按**很可能但未最终确认**处理。
- **❌ 未能核实 / 疑似脏数据（已从正文剔除，请勿直接引用）**：引用图谱里若干 2026 年的 arXiv ID 用了不太合理的编号（如 "2605.x / 2604.x / 2603.x"），对应 *HCL-FF*、*Covariance-Aware Goodness*、*Hyperspherical Forward-Forward*、*FAAST*、*Adaptive Multi-Scale Goodness Aggregation* 等。可能是 DB 伪条目或极新的预印本，**需到 arXiv 直接确认后再用**。
- **未穷尽覆盖**：大量边缘设备 / 医学影像 / 传感器应用论文（相机陷阱、黑色素瘤 U-Net、皮肤病变、土壤虫害音频、裂缝检测、高光谱等）——真实但影响力低、且不在你的"三大会"优先级里，略过。
- **引用数**：均为 Semantic Scholar 数值，会低估很新的会议论文，**只作相对信号**。

---

## 六、我的判断 + 接下来可以追什么

**判断**：如果你的兴趣是"FF 作为一种 continual learning 方法到哪了"——坦白说，**FF 本身并没有成为 CL 的主流解法**。CL 这条线真正打进顶会的是更广义的 forward-only / 零阶优化（ZeroFlow、FoRo、FLEX）。FF 自己的 CL 代表作只有 SFFA（CoLLAs 2025），且停在小规模。FF 当前最有生命力的反而是**硬件**（光学/SNN/存内计算/MCU）方向。

**如果要继续深挖，建议挑下面任一条主线往下追**（我可以接着做，分别写进 `003-...md`）：
1. **CL 主线**：以 **ZeroFlow（ICML 2025）** 为新种子往下追"forward-only 抗遗忘"，这是和你需求最贴的。
2. **真·FF 主线**：以 **SFFA / Layer Collaboration** 为种子，追 FF 算法本身的改良与扩展。
3. **硬件主线**：以 **Self-Contrastive FF（Nature Comms 2025）/ 光学 FF** 为种子，追 FF 在神经形态硬件上的落地。

告诉我追哪条（或都追），我就接着用同样的方法做。
