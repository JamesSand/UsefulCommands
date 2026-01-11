backup from synthetic data markdown







### Idea2: Synthetic data and data selection

https://arxiv.org/pdf/2501.18962

这个是一个关于 synthetic data 的 generation 和 training 的 trade off 的 paper

给定预算之下，怎么balance synthetic data generation 和 training ，才能让 model 的 performance 达到 optimal。

他们实际上优化的是每一轮迭代使用的样本量





### Idea1 synthetic data idea

data selection

https://chatgpt.com/s/t_692aad8683d481918a3452dd60a25476 



https://github.com/TheAgentArk/Toucan 

感觉这个 synthetic data pipeline 有点复杂啊。

#### Method1: Simia Agent Training

https://arxiv.org/pdf/2511.01824 

https://github.com/microsoft/Simia-Agent-Training

这个的 SFT data generation pipeline 跑通了



#### Dataset1: APIGEN-MT

https://arxiv.org/pdf/2504.03601 

他们相当于是生成了一堆数据，然后用这些生成的数据做 behavior cloning。实际上本质是在 distill 更大的 model 的能力啊



#### Benchmark1: tau2 bench

https://arxiv.org/pdf/2506.07982 

https://github.com/sierra-research/tau2-bench

这里边没有任何 training data 的，只是一个 simulation environment

观察到了一些现象，user agent 能力不行，导致最后 task agent 的操作失败。导致最终的任务失败

Section E 里边他们提到了这个事情

| 域      | 任务数 | 复杂度 | 双向控制 | Solo模式 | 典型场景               |
| ------- | ------ | ------ | -------- | -------- | ---------------------- |
| Airline | 50     | 中     | ✓        | ✗        | 政策合规性、预订管理   |
| Retail  | 114    | 中     | ✓        | ✗        | 订单管理、换货退货     |
| Telecom | 2285   | 高     | ✓        | ✓        | 技术故障排除、账户管理 |
| Mock    | 9      | 低     | ✓        | ✗        | 框架测试               |



τ²-bench有四种奖励类型：

| 类型         | 说明                               | 文件位置                   |
| ------------ | ---------------------------------- | -------------------------- |
| COMMUNICATE  | 代理是否传达必要信息               | evaluator_communicate.py   |
| DB           | 数据库状态是否符合预期             | evaluator_env.py           |
| ACTION       | 代理是否调用了必要的工具           | evaluator_action.py        |
| NL_ASSERTION | 自然语言断言（如"代理应拒绝取消"） | evaluator_nl_assertions.py |




### alpha mix

用 prompt 控制 alpha，实现对 model 输出的控制

现在的组合是在 llama factory 上用 amazon review 训练

llama 3 8B lora finetune



