
看一下 aurora 的 codebase

/home/zhsha/workspace/aurora-project/aurora-internal

根据下边的示意图拆解一下 aurora 的结构，告诉我 training
inference
还有 mooncake 对应的代码都在哪里，是耦合的还是解耦的？

```
┌─────────────────────┐   HTTP callback (hidden states + tokens)   ┌──────────────────────┐
│  Training (GPU 0,1) │  ◄─────────────────────────────────────── │ sglang (GPU 2,3,4,5) │
│  aurora.train_entry │                                            │ EAGLE3 spec decoding │
│  FSDP draft model   │  ────► Mooncake KV-store ────► weight sync│ Qwen3-8B + draft     │
│  callback server    │        (新 draft 权重)                     │                      │
│  :18080             │                                            │ :30000               │
└─────────────────────┘                                            └──────────────────────┘
        ▲                                                                    ▲
        │                                                                    │ /v1/chat/completions
        │                                                                    │
        │                                                            ┌──────────────────┐
        │                                                            │ send_requests.sh │
        │                                                            │ (dataset prompts)│
        │                                                            └──────────────────┘
        │ Ray head on :6380
        │ TOTAL 6 GPUs
```

GPU 切分（非重叠）：
- GPU 0-1：训练（FSDP/DP，2 卡）
- GPU 2-5：sglang server（TP=4）

---

## Aurora 代码结构拆解

代码根目录：`/home/zhsha/workspace/aurora-project/aurora-internal/aurora/`

```
aurora/
├── train_entry.py        # 主入口
├── training/             # 训练（FSDP / 优化器 / Eagle3 loss）
├── inference/            # 推理引擎封装（HF / sglang Ray actor）
├── transfer/mooncake/    # Mooncake KV-store 客户端 + master 进程
├── controller/           # 控制平面：训练 controller / 推理 manager / HTTP callback server
├── ray/                  # Ray actor 基类、placement group、train group
├── models/               # 模型定义（draft / target）
├── config/               # 配置 dataclass（含 mooncake_config.py）
├── data/                 # 数据加载
└── utils/                # types.py: InferenceInput / InferenceOutput 等跨进程数据契约
```

### 1) Training 训练侧

| 文件 | 作用 |
| --- | --- |
| `aurora/train_entry.py` | 主入口 `train_async_no_generation`：起 placement group、起 Mooncake master、建训练 actor 和推理 engine、把控制权交给 controller |
| `aurora/training/trainer_actor.py` | Ray actor，封装 FSDP trainer，从 Ray queue 取 batch，调 train_step |
| `aurora/training/eagle3_trainer.py` | Eagle3 训练逻辑：draft 前/反向、loss |
| `aurora/training/fsdp.py` | FSDP v2 切分、full-state-dict 加载 |
| `aurora/training/trainer.py` | Trainer 核心：fwd/bwd/累加梯度 |
| `aurora/training/optimizer.py` | BF16 优化器 + grad scaling |
| `aurora/training/checkpoint.py` | `save_draft_model_for_serving(sync_dir)`：把 draft 权重落盘，供推理侧热加载 |
| `aurora/controller/training_controller.py` | `AsyncTrainingController`（Ray actor）：管 prompt buffer / sample pool，把推理回来的 sample 派发给训练 actor |
| `aurora/controller/loop.py` | 主训练循环：派发 batch、按步保存、**每 N 步同步 draft 权重到推理** |
| `aurora/controller/training_external_server.py` | **HTTP callback server**（FastAPI，监听 `0.0.0.0:18080`，端点 `POST /push_sample`）：接收外部 sglang 发回的 mooncake key + tensor 元数据，构造 `InferenceOutput` 推给 controller |

> 也就是说图里训练框那个 `:18080` 不在 training/ 里，而是在 `controller/training_external_server.py`。

### 2) Inference / sglang 侧

| 文件 | 作用 |
| --- | --- |
| `aurora/inference/engine/hf_engine.py` | `HFEngine`：HF runner 封 Ray actor，本地推理路径 |
| `aurora/inference/engine/sgl_engine.py` | `SglEngine`：把 `sgl.Engine`（**打过 patch** 的）封 Ray actor，跑 spec_training 模式，产出 token + 辅助 hidden states 写进 Mooncake |
| `aurora/inference/factory.py` | 工厂方法，按配置造 HF/Sgl engine |
| `aurora/controller/inference_manager.py` | `AsyncInferenceManager`（Ray actor）：watermark 缓冲调度器，轮询补 prompt，把 mooncake key 回灌给 controller |
| `patches/sglang/v0.5.8.post1/sglang.patch` | **sglang 源码补丁**：加 `spec_training` 模式、可配 aux hidden state、Mooncake 写入、HTTP callback 发射 |
| `patches/sglang/de-minimax-681f31056/sglang.patch` | 另一个 sglang commit 的补丁版本 |
| `examples/qwen3-8b-external-with-draft/config.yaml` | 图里这套部署的真实 config：训练 2 卡 / `inference_num_gpus: 0` / 外部 sglang，`online_serving.port: 18080` |

**关键点**：图里 `sglang (GPU 2,3,4,5)` 这一框是**独立进程**，不是 aurora Python 里 import 进来的。aurora 不去启动它，是外部用打了 patch 的 sglang CLI 自己拉起来，再通过 HTTP 回调把样本送回 `:18080`。`aurora/inference/engine/sgl_engine.py` 那条路是「本地 sglang Ray actor」分支，跟图里画的 external sglang 是两条并行路径（本 config 里 `inference_num_gpus: 0` 关闭了本地分支）。

### 3) Mooncake KV-store 侧

| 文件 | 作用 |
| --- | --- |
| `aurora/transfer/mooncake/utils.py` | `MooncakeMaster` Ray actor：起 mooncake master 子进程（gRPC 50051 + metadata HTTP 50052），父进程死了发 SIGTERM 清理 |
| `aurora/transfer/mooncake/store.py` | `MooncakeHiddenStateStore`：包 `mooncake.store.MooncakeDistributedStore`，管 RDMA buffer + async put |
| `aurora/transfer/mooncake/eagle_store.py` | `EagleMooncakeStore`：Eagle3 专用，按后缀 `_hs/_tgt/_ids/_lhs` 分键存 hidden_states / target tokens / input_ids / last_hidden_states |
| `aurora/transfer/mooncake/buffers.py` | `HostBufferPool / GPUSendBuffer / GPUReceiveBuffer / AsyncPutManager`：RDMA-registered buffer 池 + 异步批量 put |
| `aurora/config/mooncake_config.py` | `MooncakeConfig` dataclass：master 地址、metadata server、TCP/RDMA、segment/buffer 大小 |

**注意**：图里 "Mooncake KV-store ──► weight sync 新 draft 权重" 这一条线在代码里其实是**两条机制**：
- **样本传输（hidden states / tokens）**走 Mooncake：sglang 侧写 key，训练侧凭 key 拿数据
- **draft 权重同步**走**本地磁盘**：`loop.py` 调 `train_group.save_draft_model_for_serving(sync_dir)` 落盘，然后调 `engine.update_weights_from_disk.remote(sync_dir)` 让推理侧 reload。**不走 Mooncake**（图里这块标注有点 misleading）。

### 4) Ray 编排

| 文件 | 作用 |
| --- | --- |
| `aurora/ray/ray_actor.py` | `RayActor` 基类：GPU/CUDA device 选取、端口发现、分布式 init address |
| `aurora/ray/placement_group.py` | `create_placement_groups` / `allocate_train_group`：硬切训练组 vs 推理组的 GPU 资源 |
| `aurora/ray/train_group.py` | `TrainGroup`：多个训练 actor 的 DP 包装，广播 init、收集结果、统一存/取 model |
| `aurora/controller/setup.py` | `setup_async_training_with_engines`：把 controller + inference manager + engines 拧到一起 |

Ray head（图里的 `:6380`）由外部启动或 `train_entry` 启动时连接，driver 通过 `NodeAffinitySchedulingStrategy` 绑到 head 节点。

### 5) 跨进程数据契约

`aurora/utils/types.py`：
- `InferenceInput`（data_id, input_ids, loss_mask, ...）
- `InferenceOutput`（data_id, **mooncake_key**, tensor_shapes, tensor_dtypes, packed_loss_mask）

**跨进程只传 key + 元信息，不传 tensor**——tensor 在 Mooncake 里。

---

## 耦合度评估：**解耦（loosely coupled）**

理由：

1. **核心模块互不 import**：`aurora.training/*` 不 import `aurora.inference/*`，反之亦然。两侧都只依赖 `aurora.controller`、`aurora.ray`、`aurora.transfer`、`aurora.utils` 这些中立胶水。

2. **进程边界清楚**：
   - 训练 actor 是 Ray actor，跑在 GPU 0-1
   - 本地推理 engine 是另一组 Ray actor，跑 GPU 2-5
   - **外部 sglang 是单独的 OS 进程**（patch 过的 CLI 启动），跟 aurora 之间只有：HTTP（`POST /push_sample` 到 `:18080`）+ Mooncake（按 key 取 tensor）+ 磁盘（reload draft 权重）三条通道
   - Mooncake master 也是独立子进程，靠 gRPC + HTTP 暴露

3. **通信全部异步/管道化**：
   - 训练 → 推理：Ray queue（prompt）
   - 推理 → 训练：mooncake key（不传 tensor）走 HTTP 或 Ray actor method
   - 权重：训练写盘 → 推理 `update_weights_from_disk`
   - 数据：只通过 Mooncake key 间接共享

4. **可替换/可关掉**：config 里 `inference_num_gpus: 0` 就能彻底关掉本地推理 engine，只留外部 sglang。说明推理后端是**可插拔**的（HF / 本地 sglang Ray actor / 外部 sglang server 三选一）。

5. **单机紧凑、API 解耦**：当前部署所有进程都在一台机器上（共享 Ray 调度、Mooncake 走 TCP），但接口契约（`InferenceInput/Output` + mooncake key + HTTP endpoint）允许后续把外部 sglang 拆到别的机器上而不改训练侧代码。

**一句话**：训练 / 推理 / Mooncake 在**代码组织**上同包但分子目录、互不直接 import；在**运行时**是多个独立进程，靠 Ray / HTTP / Mooncake / 磁盘四种胶水通信。属于「同仓库、跨进程、解耦运行」的结构。


