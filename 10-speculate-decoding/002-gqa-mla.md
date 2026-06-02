# GQA 与 MLA 详解

> 注：文件名里的 "gpa" 应为 **GQA**（Grouped Query Attention，分组查询注意力）。
> 这里一起讲它和 **MLA**（Multi-head Latent Attention，多头潜在注意力）。
> 两者都是为了解决同一个问题：**自回归推理时 KV cache 太大**。

---

## 0. 先搞清楚问题：KV cache 为什么是瓶颈

标准多头注意力 **MHA（Multi-Head Attention）** 里，每个 head 都有自己独立的 Q、K、V 投影。

设：
- `d_model` = 隐藏维度
- `h` = head 数量
- `head_dim = d_model / h` = 每个 head 的维度

推理时为了避免重复计算，每生成一个 token，都要把它的 **K 和 V 存进 KV cache**，后面所有 token 都要读它。

**每个 token、每一层** 的 KV cache 大小：

```
MHA:  2 * h * head_dim  =  2 * d_model   (个元素，2 是 K 和 V)
```

问题在于：
- 它随 **序列长度线性增长**，长上下文时显存爆炸；
- decoding 阶段是 **memory-bound**（算得快、读得慢），读 KV cache 的带宽直接决定延迟。

> 举例：Llama-2-70B，`d_model=8192`, `h=64`, `head_dim=128`, 共 80 层。
> 每 token KV cache = `2 * 64 * 128 = 16384` 个元素/层 = `16384 * 80 ≈ 1.3M` 元素/token。
> FP16 下约 **2.6 MB/token**。32K 上下文 ⇒ 约 **84 GB**，单卡放不下。

### 0.1 为什么 prefill 是 compute-bound、decoding 是 memory-bound？

核心概念只有一个：**算术强度（arithmetic intensity）= 每从显存读 1 字节数据，能做多少次浮点运算（FLOPs / byte）**。

硬件有个临界值——**roofline 模型的“脊点”** = `算力 ÷ 显存带宽`。
- 算术强度 **高于**脊点 ⇒ 算力先打满 ⇒ **compute-bound**
- 算术强度 **低于**脊点 ⇒ 带宽先打满，算力单元闲着等数据 ⇒ **memory-bound**

> H100 脊点 ≈ `990 TFLOP/s ÷ 3.35 TB/s ≈ 295 FLOP/byte`。
> 也就是说：每读 1 字节，得做近 300 次运算才能喂饱算力，否则就是在等内存。

**直觉：关键在于「一份权重被多少个 token 复用」。**

- **Prefill（处理 prompt）**：一次性吃进整个 prompt 的 `S` 个 token。
  权重矩阵从显存只读 **一次**，却被 `S` 个 token 一起用 → 这是 **矩阵 × 矩阵（GEMM）**。
  每读一份权重做了 `~S` 次计算，`S` 是几百上千 → 算术强度远超脊点 → **算力是瓶颈**。

- **Decoding（逐字生成）**：一次只产出 **1 个** 新 token。
  但仍要把 **整个模型权重** 从显存完整搬一遍，只为这 1 个 token 服务 → 这是 **矩阵 × 向量（GEMV）**。
  每读一份权重只做了几次计算 → 算术强度极低 → GPU 大把时间在 **等权重 + KV cache 从 HBM 搬过来**，算力单元空转 → **带宽是瓶颈**。

**做一道算术题就一目了然**（Llama-2-70B，FP16，权重 ≈140 GB，H100：990 TFLOP/s、3.35 TB/s）：

| 阶段 | 读权重耗时（带宽下限） | 算力耗时 | 谁更慢 ⇒ 瓶颈 |
|---|---|---|---|
| **Decode**（1 token） | `140GB / 3.35TB/s ≈ 42 ms` | `2×70e9 FLOP / 990e12 ≈ 0.14 ms` | 内存慢 **~300×** ⇒ memory-bound |
| **Prefill**（S=2000 tokens） | 权重仍只读一次 ≈ `42 ms` | `2×70e9×2000 / 990e12 ≈ 283 ms` | 算力慢 **~7×** ⇒ compute-bound |

> 同样搬一遍 140GB 权重：decode 只摊给 1 个 token（极度浪费带宽），prefill 摊给 2000 个 token（物尽其用）。

**厨师与储藏室的类比**：算力 = 厨师，显存 = 储藏室。
- Prefill = 办宴席：去储藏室取一次面粉（读一次权重），就做出 1000 个面包 → 厨师忙不过来（compute-bound）。
- Decode = 一次只做一道菜，但每道菜都要把**整个储藏室**搬来又搬回去，只用一丁点 → 全程在来回搬运，厨师几乎在发呆（memory-bound）。

**两个直接推论**（也是工程上最重要的两点）：
1. **批处理（batching）能救 decode**：把 `B` 个请求拼在一起一步解码，`M` 维从 1 变成 `B`，算术强度随之抬高 → 这正是 vLLM 等推理服务做 continuous batching 的根本原因。
2. **KV cache 越小，decode 越快**：decode 既要读权重也要读 KV cache，都是纯内存流量。GQA / MLA 把 KV cache 压小，直接减少这部分搬运 → 这就是下面两节的主题。

GQA 和 MLA 就是两条不同的“压缩 KV cache”的路线。

---

## 1. 从 MHA → MQA → GQA

### MQA（Multi-Query Attention，多查询注意力）—— 极端方案

所有 query head **共享同一个 K head 和同一个 V head**。

```
KV cache:  2 * 1 * head_dim    (h 个 query 头，但只有 1 套 KV)
```

图解（以 h=4 为例）：

```
        MQA：h 个 Query 头，但只共用 1 套 K / V
        ─────────────────────────────────────

  Query 侧（h=4，每个头都不同）       KV 侧（只有 1 套）
   Q0   Q1   Q2   Q3                   K0      V0
    │    │    │    │                    │       │
    │    │    │    └──── 查询 ──────────┤       │
    │    │    └──────── 查询 ───────────┤       │
    │    └─────────── 查询 ─────────────┤       │
    └────────────── 查询 ───────────────┘       │
                                                │
   每个 Q 头各算各的 attention，                  │
   但读的都是同一份 K0 / V0  ◄───────────────────┘
```

关键对比——**每个 token** 要往 KV cache 里塞什么：

```
  MHA(h=4)：K [K0][K1][K2][K3]   V [V0][V1][V2][V3]   → 2 × 4 × head_dim
  MQA(h=4)：K [K0]               V [V0]               → 2 × 1 × head_dim
                └─ Q0 Q1 Q2 Q3 全部共用这一个
```

所以那条公式 `2 * 1 * head_dim` 的每个数是：

```
            2          ×          1          ×       head_dim
            ↑                     ↑                     ↑
        K 和 V 两类          只有 1 个 KV 头        每个向量的长度
       （要各存一份）      （不管多少 Query 头）
```

省了 `h` 倍显存，但因为 KV 表达能力太弱，**模型质量明显下降**。

### GQA —— 折中方案（现在的主流）

把 `h` 个 query head 分成 `g` 个组，**同一组内的 query head 共享一套 K/V head**。

```
KV cache:  2 * g * head_dim
```

- `g = h`  ⇒ 退化成 MHA（每个 query 头独享 KV）
- `g = 1`  ⇒ 退化成 MQA（所有 query 头共享一套 KV）
- `1 < g < h` ⇒ GQA，在质量和显存之间取平衡

```
       MHA (g=h)              GQA (g=2)               MQA (g=1)
   Q0 Q1 Q2 Q3            Q0 Q1   Q2 Q3            Q0 Q1 Q2 Q3
   |  |  |  |              \ /     \ /               \  \ /  /
   K0 K1 K2 K3              K0      K1                  K0
   V0 V1 V2 V3              V0      V1                  V0
   (4套KV)                 (2套KV)                   (1套KV)
```

#### 具体例子（小数字，方便数维度）

设 `d_model=8`, query head 数 `h=4`, `head_dim=2`。GQA 取 `g=2`：

- Query 头：Q0, Q1, Q2, Q3（4 个）
- KV 头：只有 2 套 —— K0/V0 和 K1/V1
- 分组：Q0、Q1 都用 K0/V0；Q2、Q3 都用 K1/V1
- KV cache/token = `2 * 2 * 2 = 8` 个元素（MHA 是 `2*4*2=16`，省一半）

#### 真实模型例子

| 模型 | query 头 `h` | KV 头 `g` | 共享比 | 相对 MHA 省 |
|---|---|---|---|---|
| Llama-2-70B | 64 | 8 | 8 个 Q 共享 1 套 KV | **8×** |
| Llama-3-8B | 32 | 8 | 4:1 | 4× |
| Mistral-7B | 32 | 8 | 4:1 | 4× |

> Llama-2-70B 用 GQA 后，KV cache 从 2.6 MB/token 降到约 **0.33 MB/token**，质量几乎不掉。
> 这就是为什么几乎所有现代大模型都默认用 GQA。

---

## 2. MLA（Multi-head Latent Attention）—— DeepSeek 的路线

GQA 的思路是“**减少 KV 头的数量**”。
MLA 换了个思路：**头数不减，但把 KV 压缩成一个低维的“潜在向量”再缓存**。

### 核心想法：低秩压缩

不直接缓存完整的 K、V，而是：

1. 把隐藏状态 `h_t` **下投影（down-project）** 成一个很小的潜在向量 `c_KV`（维度 `d_c`，远小于 `h*head_dim`）；
2. **只缓存这个 `c_KV`**；
3. 用的时候再用 **上投影（up-project）** 把 `c_KV` 还原成每个头的 K 和 V。

```
c_KV  = W_DKV · h_t       # 下投影，d_c 维（要缓存的就是它）
k_C   = W_UK  · c_KV      # 上投影还原 key（内容部分）
v_C   = W_UV  · c_KV      # 上投影还原 value
```

### 关键难点：RoPE 不兼容，所以“解耦 RoPE”

RoPE（旋转位置编码）是按位置作用在 K 上的。如果先缓存 `c_KV`、用时再上投影，位置信息没法干净地塞进低秩压缩里（上投影矩阵会和 RoPE 的旋转矩阵纠缠，破坏“吸收”技巧）。

DeepSeek 的解法是 **把 K 拆成两部分**：
- **内容部分 `k_C`**：来自压缩潜在 `c_KV`，不带位置；
- **位置部分 `k_R`**：单独算一个小维度、带 RoPE、**所有头共享**。

```
# Query 侧也做了压缩
c_Q = W_DQ · h_t                  # query 也下投影成潜在
q_C = W_UQ · c_Q                  # 内容部分（每头）
q_R = RoPE(W_QR · c_Q)            # 位置部分（每头）

# Key 侧
k_C = W_UK · c_KV                 # 内容部分（每头，来自缓存）
k_R = RoPE(W_KR · h_t)            # 位置部分（所有头共享！）

# 拼起来做注意力
q = [q_C ; q_R]
k = [k_C ; k_R]
attn_score = q · k
```

**真正缓存的只有两样东西**：
- `c_KV`：压缩潜在，维度 `d_c`
- `k_R`：解耦的 RoPE key，维度 `d_rope`（所有头共享，不是每头一份）

```
MLA KV cache/token/层 = d_c + d_rope
```

### “矩阵吸收”技巧（为什么推理时不用真的展开 K/V）

注意力分数里的内容项：

```
q_C^T · k_C = (W_UQ c_Q)^T (W_UK c_KV) = c_Q^T (W_UQ^T W_UK) c_KV
```

`W_UQ^T W_UK` 可以 **预先乘成一个矩阵**，于是从来不需要把 `c_KV` 展开成完整的 K——直接用缓存的低维 `c_KV` 算就行。
同理 `W_UV` 可以被 **吸收进输出投影**，V 也不用展开。
所以推理时显存里只躺着小小的 `c_KV`。

### 具体例子

#### 小数字版

`d_model=8`, `h=4`, `head_dim=2` ⇒ 完整 K、V 各 `4*2=8` 维。
MLA 取 `d_c=3`, `d_rope=2`：
- 缓存 = `c_KV`(3) + `k_R`(2) = **5 个元素/token**
- 对比 MHA 的 `2*4*2 = 16` ⇒ 省约 3.2×（且头数一个没减！）

#### 真实模型例子（DeepSeek-V2）

| 参数 | 值 |
|---|---|
| `d_model` | 5120 |
| head 数 `h` | 128 |
| `head_dim` | 128 |
| 压缩维度 `d_c` | 512 |
| 解耦 RoPE 维度 `d_rope` | 64 |

- **MLA 缓存/token/层** = `d_c + d_rope` = `512 + 64` = **576 个元素**
- 对应 **MHA**（128 头）= `2 * 128 * 128` = **32768 个元素**
- 压缩比 ≈ **57×**！而且 **128 个头一个都没少**，表达能力远强于 MQA/GQA。

> DeepSeek 论文里换算：MLA 的 KV cache 大约等价于 “GQA 只用 2.25 个组”的开销，
> 但效果比那个量级的 GQA 好得多——这就是 MLA 的卖点：
> **用低秩压缩拿到“接近 MQA 的显存 + 接近 MHA 的质量”。**

---

## 3. GQA vs MLA 对比总结

| 维度 | MHA | MQA | GQA | MLA |
|---|---|---|---|---|
| 压缩思路 | 不压缩 | 共享到 1 套 KV | 共享到 `g` 套 KV | 低秩压缩成潜在向量 |
| KV cache/token/层 | `2·h·d_head` | `2·d_head` | `2·g·d_head` | `d_c + d_rope` |
| 头的表达能力 | 最强 | 最弱 | 中等 | 强（头数不减） |
| 质量损失 | 基线 | 明显 | 很小 | 几乎无 / 更好 |
| 代表模型 | GPT-3、原始 Transformer | PaLM、Falcon | Llama-2/3、Mistral | DeepSeek-V2/V3 |
| 实现复杂度 | 低 | 低 | 低 | 高（解耦 RoPE + 矩阵吸收） |

**一句话记忆**
- **GQA**：让多个 query 头“拼车”共用一套 KV，靠 **减少 KV 头数** 省显存。
- **MLA**：把 KV “压缩打包”成一个低维潜在向量再缓存，靠 **低秩压缩** 省显存，头数一个不减。

---

## 4. 和投机解码（speculative decoding）的关系

这个目录叫 `speculate-decoding`，顺带说一句两者的联系：

- 投机解码用一个小的 draft model 一次猜多个 token，再用大模型并行验证，**核心瓶颈也是大模型读 KV cache 的带宽**。
- KV cache 越小（GQA/MLA），验证阶段读得越快，**投机解码的加速比越高**。
- 所以现代高效推理通常是 **GQA/MLA（省 KV）+ 投机解码（省步数）** 一起上。
