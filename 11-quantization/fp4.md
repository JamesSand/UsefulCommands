# FP4 笔记

FP4 是用 4 bit 来表示 LLM 权重的一种方法。

FP4 是一个**统称**——没有"FP4 spec"这个东西，业界实际部署的 4-bit 浮点都是 NVFP4 或 MXFP4 这两种具体格式。

---

## Question 0: 什么是 FP4

FP4 用 4 bits 来表示一个浮点数：其中 1 bit 表示 sign，2 bits 表示 exponent，1 bit 表示 mantissa。

## Question 1: 同样是 4 bit，为什么 fp4 比 int4 更适合做 quantization？

**核心**：FP4 的码点分布是 log scale，INT4 的码点分布是 linear scale。两者都有 16 个码点（4 bit = $2^4$），但**分布不同**——分布跟 LLM weight 实际分布（heavy-tail，大量小值 + 少量 outlier）的匹配程度决定优劣。

### FP4 和 INT4 能够表示的范围

**INT4 (signed, symmetric)**：linear grid

```
{-8, -7, -6, -5, -4, -3, -2, -1, 0, +1, +2, +3, +4, +5, +6, +7}
```

相邻 grid 间距 **constant = 1**（×scale 后是 constant absolute step）。

**FP4 (E2M1)**：log-spaced grid

正值（8 个）：
```
{0, 0.5, 1, 1.5, 2, 3, 4, 6}
```

负值对称（8 个）：
```
{0, -0.5, -1, -1.5, -2, -3, -4, -6}
```

相邻 grid 间距 **不均匀**：`{0.5, 0.5, 0.5, 0.5, 1, 1, 2}`——**近 0 处密，远离 0 处稀**。Dynamic range = $[-6, +6]$。

### FP4 (E2M1) 的具体推导

E2M1 = **1 sign bit + 2 exponent bits + 1 mantissa bit = 4 bits**。Exponent bias = $2^{E-1} - 1 = 2^{2-1} - 1 = 1$。

IEEE-style decode 公式：
- **Normal** ($e \ne 0$): $\text{value} = (-1)^s \times 2^{e - \text{bias}} \times (1.f)_2$ ← 隐含 leading 1
- **Subnormal** ($e = 0$): $\text{value} = (-1)^s \times 2^{1 - \text{bias}} \times (0.f)_2$ ← 隐含 leading 0
- OCP MX 的 E2M1 **不保留 Inf/NaN**，all-ones exponent (`e=11`) reclaim 给 normal numbers 用（多榨 ±4 和 ±6 四个值）

穷举 $s \in \{0, 1\}, e \in \{00, 01, 10, 11\}, f \in \{0, 1\}$ = 16 个码点。列正值（$s=0$）8 个：

| $e$ (bin) | $e$ (dec) | $f$ | Category | Formula | Value |
|---|---|---|---|---|---|
| `00` | 0 | 0 | subnormal | $(0.0)_2 \times 2^{1-1} = 0 \times 1$ | **0** |
| `00` | 0 | 1 | subnormal | $(0.1)_2 \times 2^{1-1} = 0.5 \times 1$ | **0.5** |
| `01` | 1 | 0 | normal | $(1.0)_2 \times 2^{1-1} = 1 \times 1$ | **1** |
| `01` | 1 | 1 | normal | $(1.1)_2 \times 2^{1-1} = 1.5 \times 1$ | **1.5** |
| `10` | 2 | 0 | normal | $(1.0)_2 \times 2^{2-1} = 1 \times 2$ | **2** |
| `10` | 2 | 1 | normal | $(1.1)_2 \times 2^{2-1} = 1.5 \times 2$ | **3** |
| `11` | 3 | 0 | normal | $(1.0)_2 \times 2^{3-1} = 1 \times 4$ | **4** |
| `11` | 3 | 1 | normal | $(1.1)_2 \times 2^{3-1} = 1.5 \times 4$ | **6** |

负值（$s=1$）对称 8 个。

**快速记忆**：$\{0, 0.5, 1, 1.5\}$ 是 "1× scale"，$\{2, 3\}$ 是 "2× scale"，$\{4, 6\}$ 是 "4× scale"——每段相对 grid 相同但绝对 scale 翻倍。这是浮点本质：grid 密度近 0 处密、远离 0 处稀（指数级展开）。

### 为什么 log scale 比 linear scale 好（对 LLM weight）

LLM weight 经验上 heavy-tail Gaussian-ish：大量 weight 集中在 0 附近（|w| < 0.1），少量 outlier 在 tail。

- **INT4 linear grid**：小值区域 bin 太稀（grid 间距粗）+ 大值区域 bin 太密但 weight 稀少 → bin 利用率低
- **FP4 log grid**：小值区域 bin 密集（grid 间距细）+ 大值区域 bin 稀疏对齐 outlier → bin 利用率高

**Information theory 角度**：最优 quantization grid 是 source distribution 的 inverse CDF（让每个 bin 承载等量 mass）。LLM weight 的 inverse CDF 长得像 log-spaced，FP4 的 grid 正好匹配这个 prior。

**等价说法**：INT4 的 **absolute error** 在所有 magnitude 上 constant，但相对误差在小值处爆炸；FP4 的 **relative error** 大致 constant，小值和大值都享受相近的相对精度。LLM matrix multiply 关心 relative 不关心 absolute——所以 FP4 赢。

---

## Question 2: NVFP4 和 MXFP4 的区别

### 数据本体 (4-bit) 一样

两者**数据格式相同**：都是 E2M1 = 1 sign + 2 exp + 1 mantissa = 4 bits。16 个码点 grid 相同。

### Scale 不同

虽然两者都用 **8 bit** 做 block scale，但 8 bit 的 layout 和 grouping 不同。

**MXFP4**: 用 **E8M0** scale, **group 32**（每 32 个 FP4 值共享一个 scale）
- E8M0 = 0 sign + 8 exponent + 0 mantissa = 8 bits
- **没有 sign bit**（scale 总正，省下来给 exponent）+ **没有 mantissa**
- 只能表示 $2^k$（power-of-2 only），相邻 scale 差正好 2 倍
- Dynamic range 极大（256 个不同 exponent 值），但精度粗
- **Dequant 硬件成本**：一个移位（multiply by $2^k$ = shift），最简

**NVFP4**: 用 **E4M3** scale, **group 16**（每 16 个 FP4 值共享一个 scale）
- E4M3 = 1 sign + 4 exponent + 3 mantissa = 8 bits
- 有 mantissa bits → scale 可以是 **non-power-of-two**（fractional precision）
- 相邻 scale 间距约 13%（vs E8M0 的 100%），表达力强很多
- Dynamic range ~5 数量级（比 E8M0 窄但 LLM block 内够用）
- **Dequant 硬件成本**：FP8 multiply

⚠️ **NVFP4 实际是两级 scale**（容易漏掉的细节）：
- **Per-block scale**: E4M3 FP8（block 16）
- **Per-tensor scale**: FP32（全 tensor 一个 global normalizer）

NVIDIA blog 原话：*"NVFP4 encodes blocks using E4M3 FP8 precision. NVFP4 uses the E4M3 FP8 format variant that enables non-power-of-two scaling factors with fractional precision."*

MXFP4 **没有 per-tensor 这一级**——只有 per-block E8M0。这是两者的关键架构差异：NVFP4 的 FP32 global scale 吸收大方向 dynamic range，让 per-block E4M3 只需做"相对 global 的微调"；MXFP4 单层 scale 必须同时承担全部范围，所以需要 E8M0 的宽 dynamic range。

### Metadata overhead 对比

| | MXFP4 | NVFP4 |
|---|---|---|
| Block scale 类型 | E8M0 (8 bits) | E4M3 (8 bits) |
| Block size | 32 | 16 |
| Per-block overhead | 8 bits / 32 vals = **0.25 bit/val** | 8 bits / 16 vals = **0.5 bit/val** |
| Per-tensor overhead | 无 | FP32 / tensor (amortized → 几乎 0) |
| 跨硬件 | OCP 标准（AMD, Intel, MS） | NVIDIA Blackwell only |

这里给我写一个 MXFP4 和 NVFP4 在计算过程中恢复的总结

### 一句话总结

NVFP4 用 "FP8 scale + block 16 + 双层 scale" 实现更精细的控制，但 metadata 是 MXFP4 的 2 倍、且锁死 NVIDIA 硬件。MXFP4 用 "E8M0 scale + block 32 + 单层 scale" 换取低 metadata + 硬件简单（一个移位）+ 跨厂商标准化。

---

## Question 3: MXFP4 vs NVFP4 在 matmul 里怎么算（具体例子）

### 先把 i, j, k, g 说清楚

普通 matmul：`C = A @ B`，A 是 `[M, K]`，B 是 `[K, N]`，C 是 `[M, N]`。

- `i` = A 的行号 / C 的行号（0 ~ M-1）
- `j` = B 的列号 / C 的列号（0 ~ N-1）
- `k` = K 方向上的位置（0 ~ K-1）——这是「被求和掉」的那个维度

普通 matmul 写法：`C[i, j] = sum over k of A[i, k] * B[k, j]`

Quantization 把 **K 维切成若干 block**：block 大小 `Bs`（MXFP4 是 32，NVFP4 是 16），切出 `G = K / Bs` 个 block。

- `g` = block 编号（0 ~ G-1），表示「我们现在处理 K 维上的第几段」
- 每个 block 内部仍然有 Bs 个元素，用 `k = 0, ..., Bs-1` 标号

每个 block 共享一个 scale：
- `s_A[i, g]` = A 第 i 行第 g 个 block 的 scale（A 的每一行有 G 个 scale）
- `s_B[g, j]` = B 第 g 个 block 行 × 第 j 列的 scale（B 的每一列有 G 个 scale）

为了让例子简单，下面取 **M = 1, N = 1, K = 32**——A 退化成一个长度 32 的行向量，B 是长度 32 的列向量，C 就是一个标量（内积）。`i` 和 `j` 都固定为 0，只剩 `g` 和 `k` 在动。

---

### 例子的数据

```
A 前 16 个 (g=0 这个 block) = [0.5]*15 + [1.5]
A 后 16 个 (g=1 这个 block) = [0.3]*15 + [4.5]

B = [1.0] * 32   (全是 1.0，让算术干净)
```

真实答案（不量化）：

```
C = sum(A[k] * B[k] for k in 0..31)
  = sum(A)
  = 15·0.5 + 1.5 + 15·0.3 + 4.5
  = 18.0
```

复习一下 FP4 (E2M1) 的 16 个码点——每个 FP4 值只能落在这 16 个上：

```
{0, ±0.5, ±1, ±1.5, ±2, ±3, ±4, ±6}
```

---

### 用 MXFP4 算

MXFP4 的 `Bs = 32`，所以**整个 K=32 就是一个 block**（G=1，g 只取 0）。scale 只能是 2 的幂（E8M0）。

**Step 1：给 A 选 scale（`s_A[0, 0]`）**

A 里最大绝对值 = 4.5。试不同的 2 的幂：

| 候选 `s_A` | 4.5 / s_A | 落到 FP4 grid 上的结果 |
|---|---|---|
| `s_A = 1` (=2⁰) | 4.5 | round 到 4（差 0.5） |
| `s_A = 0.5` (=2⁻¹) | 9 | overflow（FP4 max 6） |
| `s_A = 2` (=2¹) | 2.25 | 0.3/2 = 0.15 ≈ 0，太多小值丢光 |

最佳选 `s_A = 1`。把 A 每个值除以 s_A 再 round 到 FP4 grid：

```
A_quant = [0.5]*15 + [1.5] + [0.5]*15 + [4]
                                  ↑15 个 0.3 全 round 成 0.5    ↑4.5 round 成 4
```

**Step 2：给 B 选 scale（`s_B[0, 0]`）**

B 全是 1.0。`s_B = 1`，B_quant = [1]*32，无损。

**Step 3：block 内做 32 次 FP4 × FP4 内积**

硬件这一步用 FP4 算乘加，累加到一个 FP32 accumulator P：

```
P = Σ_{k=0..31} A_quant[k] × B_quant[k]
  = 15·(0.5·1) + 1·(1.5·1) + 15·(0.5·1) + 1·(4·1)
  = 7.5 + 1.5 + 7.5 + 4
  = 20.5
```

**Step 4：应用 block scale（白嫖）**

因为 `s_A = 2⁰`、`s_B = 2⁰`，相乘还是 `2⁰`，所以 `P × s_A × s_B` 等价于「把 P 的 FP32 exponent **加 0**」——一个 exponent 加法，**完全不需要乘法器**：

```
C_MXFP4 = P × s_A × s_B = 20.5 × 1 × 1 = 20.5
```

**结果**：MXFP4 算出 **20.5**，真实 18.0，**误差 = 2.5**。
误差主要来自那 15 个 0.3：FP4 grid 上离 0.3 最近的非零码点是 0.5（grid 步长粗），s_A=1 时只能 round 成 0.5，每个值错 0.2，累计 3.0 的偏差。

---

### 用 NVFP4 算

NVFP4 的 `Bs = 16`，所以 **K=32 切成 2 个 block**（G=2，g ∈ {0, 1}）。每个 block 自带一个 E4M3 FP8 scale（**可以是非 2 的幂**）。

#### Block g=0：A[0:16] 和 B[0:16]

A[0:16] = `[0.5]*15 + [1.5]`，max = 1.5。

NVFP4 让 max 正好打到 FP4 上界 6，最大化 grid 利用率：

```
s_A[0, 0] = 1.5 / 6 = 0.25
```

（0.25 = 2⁻²，这里碰巧也是 2 的幂；下面 block g=1 用的 0.75 就不是 2 的幂了。）

量化：
- `0.5 / 0.25 = 2` ✓（FP4 grid 上有 2）
- `1.5 / 0.25 = 6` ✓（FP4 grid 上界）

```
A_quant[0:16] = [2]*15 + [6]
```

B[0:16] = `[1]*16`，`s_B[0, 0] = 1`，B_quant = [1]*16。

block 内 16 次 FP4 × FP4 内积：

```
P_g0 = 15·(2·1) + 1·(6·1) = 30 + 6 = 36
```

应用 block scale（一次真的 FP8 multiply）：

```
contrib_g0 = P_g0 × s_A[0,0] × s_B[0,0] = 36 × 0.25 × 1 = 9.0
```

block g=0 真实值 = 15·0.5 + 1.5 = 9.0，**零误差**。

#### Block g=1：A[16:32] 和 B[16:32]

A[16:32] = `[0.3]*15 + [4.5]`，max = 4.5。

```
s_A[0, 1] = 4.5 / 6 = 0.75
```

**关键**：`0.75` 不是 2 的幂——MXFP4 的 E8M0 做不到，NVFP4 的 E4M3 有 mantissa，可以精确表示。

量化：
- `0.3 / 0.75 = 0.4` → round to 0.5
- `4.5 / 0.75 = 6` ✓（完美落在 grid 上界）

```
A_quant[16:32] = [0.5]*15 + [6]
```

`s_B[1, 0] = 1`，B_quant = [1]*16。

```
P_g1 = 15·(0.5·1) + 1·(6·1) = 7.5 + 6 = 13.5
contrib_g1 = P_g1 × s_A[0,1] × s_B[1,0] = 13.5 × 0.75 × 1 = 10.125
```

block g=1 真实值 = 9.0，NVFP4 算出 10.125。
（dequant 后那 15 个 0.3 变成 `0.5 × 0.75 = 0.375`，每个错 0.075，累计 1.125。）

#### 合并所有 block + per-tensor scale

```
C_blocks = contrib_g0 + contrib_g1 = 9.0 + 10.125 = 19.125
```

最后乘 per-tensor FP32 global scale（这个例子里设 1.0，所以不变）：

```
C_NVFP4 = C_blocks × s_global = 19.125 × 1.0 = 19.125
```

**结果**：NVFP4 算出 **19.125**，真实 18.0，**误差 = 1.125**。

---

### 并排对比

| | 真实 | MXFP4 | NVFP4 |
|---|---|---|---|
| 计算结果 | 18.0 | 20.5 | **19.125** |
| 误差 | 0 | 2.5 | **1.125** |
| K 维 block 数 (G) | – | 1 | 2 |
| A 用了几个 scale | – | 1 个：`s_A = 1` | 2 个：`0.25, 0.75` |
| Scale 必须 2 的幂吗 | – | 是 | 否，E4M3 任意 |
| Scale apply 成本 | – | 免费（exponent add） | 每 block 一次 FP8 multiply |

### 为什么 NVFP4 的误差是 MXFP4 的一半

1. **Block 小一半（16 vs 32）→ 每个 block 单独选 scale**
   - block g=0 max 只有 1.5，配细 scale 0.25
   - block g=1 max 4.5，配粗 scale 0.75
   - 两个量级互不污染。MXFP4 一个 scale 管 32 个值，被 outlier 4.5 拖大，小值被牺牲。

2. **Scale 可以是非 2 的幂**
   - NVFP4 能用 0.75 让 max=4.5 完美打到 FP4 上界 6
   - MXFP4 只有 2 的幂选项：用 1（4.5 浪费 round 成 4）或用 0.5（4.5 overflow），都不理想

### 那 MXFP4 还有什么好的

- **Scale apply 免费**：因为 scale 是 2 的幂，apply 时只是 FP32 accumulator 的 exponent 加加，不动 mantissa，没有 multiplier。NVFP4 每个 block 都要做真的 FP8 multiply。
- **Metadata 少一半**：block 32 → 0.25 bit/val 的 scale overhead，NVFP4 是 0.5 bit/val。
- **跨厂商**：OCP 标准，AMD / Intel / Microsoft 都支持；NVFP4 只跑 NVIDIA Blackwell。

精度差一点，但 throughput / 能耗 / 兼容性能赢回来——所以两个格式各有场景。
