
aurora codebase

## 组件

aurora 里边包含了以下几个组件
1 ray
2 mooncake
3 trainer
4 sglang engine

## 组织方式

关于 ray 的组织方式还没有太搞明白，但是现在知道的是在 external mode 下 sglang engine 和剩下几个组件是分开的，sglang engine 是不受 ray 管理的独立进程（另外还有一个 online mode 把 sglang 作为 Ray 内部 SglEngine actor 起，那种情况下 sglang 受 ray 管理；我们当前 case 是 external mode）

流程是这样的
在 inference 的时候
1 每一个 prompt 结束之后，sglang 会把 hidden state 用一个 put 请求放到 mooncake 里边去。这个是异步的（put 入队就返回，实际传输在后台跑）
2 等这个 batch 都跑完了，会有一个 flush 操作，等所有的 hidden 都传到 mooncake 里边去。这个时候 sglang 给 trainer 侧发一个 HTTP POST（payload 含 `mooncake_key + tensor_shapes + 长度`，不是抽象信号，trainer 需要这个 key 才知道从 mooncake 哪里拉数据）
3 trainer 收到 POST 之后样本进 sample_pool 排队，等 pool 攒够一个 batch 才 dispatch 给 TrainerActor，TrainerActor 用 mooncake_key 从 mooncake 拉 hidden，开始 train spec

┌────────────────────────────────────────────────────────────────┐
│ External sglang (独立进程，GPU 2,3,4,5)                         │
│                                                                 │
│   user POST /v1/chat/completions                               │
│        ↓                                                        │
│   EAGLE3 spec decoding 推理                                     │
│        ↓                                                        │
│   ┌─────────────────────────────────────────────┐              │
│   │ 推理过程中（不等推理完）:                    │              │
│   │   EagleMooncakeStore.put(...)                │              │
│   │   ↳ async DtoH 在 _copy_stream               │              │
│   │   ↳ 后台线程 RDMA/TCP 传给 Mooncake          │              │
│   │   ↳ callback 入队 _pending_callbacks         │              │
│   └─────────────────────────────────────────────┘              │
│        ↓                                                        │
│   batch 推理完成 (stream_output)                                │
│        ↓                                                        │
│   ┌─────────────────────────────────────────────┐              │
│   │ flush 同步点（毫秒级）:                      │              │
│   │   eagle_mooncake_store.flush()               │              │
│   │   ↳ 等所有 async put 完成（确保 Mooncake     │              │
│   │     已落盘，trainer 才能 get 到）            │              │
│   └─────────────────────────────────────────────┘              │
│        ↓                                                        │
│   POST :18080/push_sample (daemon thread, fire-and-forget)     │
│        ↓                                                        │
│   返回 inference response 给用户（与 POST 并行）                │
└────────┬────────────────────────────────────────────────────────┘
         ▼
┌────────▼───────────────────────────────────────────────────────┐
│ Training process (GPU 0,1)                                      │
│                                                                 │
│   TrainingExternalServer :18080                                │
│        ↓                                                        │
│   controller.push_sglang_sample.remote()  ← Ray async          │
│        ↓                                                        │
│   sample_pool += sample (只存 metadata)                         │
│        ↓                                                        │
│   主循环派发 → train_queues[dp_rank]                            │
│        ↓                                                        │
│   TrainerActor.train_from_queue():                              │
│     EagleMooncakeStore.get(mooncake_key, shapes)               │
│        ↓                                                        │
│     [batch_get_into() via RDMA → 直接到训练 GPU]               │
│        ↓                                                        │
│     forward / backward / optimizer.step                        │
└─────────────────────────────────────────────────────────────────┘

## speculator 具体的细节

speculator 需要的是 model 的 low middle 和 high 这几层的 hidden，我们这个具体的 case 是 3 层 hidden

## TODO
接下来需要做的事情

### 1. 让 radix cache 跟 spec training 数据收集兼容（目标：优化 TTFT）

**方向：方案 ① —— 缓存 KV 时同时缓存 hidden states。**

为什么只能走方案 ①（目标导向）：
- TTFT 主要被 prefill 时间拖累，**减少 prefill 是优化 TTFT 的核心手段**
- radix cache 之所以能省 TTFT，就是因为它**跳过缓存 prefix 的 forward**
- 方案 ②（cache 命中也跑 forward）等于退化成 disable radix cache，对 TTFT 没帮助
- 方案 ③（只用 cache miss 训练）不改变 prefill 路径，对 TTFT 也没帮助
- 所以**只有方案 ① 既能保留 radix cache 的 TTFT 收益、又能正确拿到 EAGLE3 训练所需的 hidden**

实施要点（待调研）：
- 在 sglang radix cache 的 entry 里**追加存 aux hidden states + last_hidden_states**（跟着 KV cache 一起的生命周期）
- cache 命中时，trainer 这边把 hidden 从 cache 里拉出来，跟正常 forward 抓的拼起来交给 mooncake
- 需要改的地方大致在 sglang patch + EagleMooncakeStore 写入路径
- 详细约束见 `aurora-internal/zhizhou-note/004-gotchas-and-constraints.md`

### 2. 搞清楚现在 aurora 性能的 bottleneck 在哪里




