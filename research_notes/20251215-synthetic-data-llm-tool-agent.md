

### Idea3: Noisy tools and confidential verification

这个东西的本质是要做 tool calling and reasoning 的 robustness。具体来说，在正确的 reasoning path 上边，我们能够通过给 tool calling 的结果增加一些扰动。这些扰动本质上分为两类

1. non-critical 扰动：增加这些扰动不会影响掉最终的决策
2. critical 扰动：这些扰动将会导致模型没法做出最终的决策
3. contradict 扰动：这些扰动主要是模型对 calling 不同的 tool 会得到不同的答案？或者是什么别的东西

上边我想的是一种 taxonomy，还有另一种 taxonomy 是按照 tool corruption 的种类来分类的

1. staleness
2. 反事实但是连贯的输出
3. partial response
4. 有效的错误代码

这种分类和上边分类的关联在这里 https://docs.google.com/document/d/1m4BQKEH5zwmxapjNcNUGGkZ_JOn09iLZK4O-oR57TKw/edit?usp=sharing 

要给模型两个额外的选项，第一个是 validation，另一个是 refuse


evaluation 可以画两条曲线

1. Robustness curve: 成功率和 robustness budget。给更多干扰的时候，成功率会降低
2. risk-coverage: 模型弃权比例和错误率的关系（这个感觉可以调整弃权的 negative reward 的值的大小


具体的可以操作方法可以是

1. Hard-negative mining: 找到那些困难的负样本。（这里的意思是我需要找到一些 agent trajectory 上边的 hard negative 负样本
   1. 这里涉及到一些背景知识。具体来说，我们需要用一些 triple loss 相关的东西。Anchor, Positive data, Negative data. triple loss 的原理是拉近 positive data 和 anchor 的距离，推远 negative data 和 anchor 的距离。

2. minmax coruption 。人为构造困难的 negative training data。让 negative data 尽可能和 anchor 相似，然后让模型区分 negative data 和 anchor

   1. 这玩意在 nlp 上边还有一个变种，就是给 positive data 加 noise，然后让模型将 noisy positive data 也识别成 positive data。这个对应到 noisy tool 上边是，在 tool call 的结果上加上一些 noisy info 的返回值，但是正确的信息仍然 preserve

   

实际上上边两种方式很难直接操作到 tool calling 的 trajectory 上边去。所以在具体 corrupt tool calling results 的时候，只能是借助这里的思想，到时候构造几种 tool calling corruption 的方案。

所以现在的 plan 是

1. 找到一些正确的 agent tool call trajectory 在上边构造一些 perturbation，构造一些 perturbed trajectory
2. 给 agent 除了 direct answer 之外的 validation 和 reject 两个额外选项
3. 测试一下现有模型的 robustness
4. filter 出一些 syhnthetic trajectory 出来，用这些 trajectory 来做 SFT。或者是用这些 tool call 的 setting 来做 RL training 



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











