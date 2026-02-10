


### Idea3: Noisy tools and confidential verification

问题的核心 idea 是我们要做一个能够探索现在 reasoning agent reason 的边界的方法。具体来说，我们想做的事情是控制在 tool use 的场景下，控制 agent 通过调用 tool 得到的外部世界信息，来探索 agent 在 tool use 不准确的情况下，究竟能够忍受多大的鲁棒性。以下是具体的试试方案



#### 3.1 Problem definition 拆分 robustness 问题

重新做了一种 taxonomy 

1. 第一种 distraction 是 Procedural 程序性的，也就是当 tool 失效的时候 agent 能够 fall back 做什么（这 agent 能 fall back 到什么啊hhh

2. 第二种是 epistemic 的。如果是出现 tool 仍然响应，但是响应结果可能有以下几种问题

1. staleness
2. 反事实但是连贯的输出
3. partial response
4. 有效的错误代码

要给模型两个额外的选项，第一个是 validation，另一个是 refuse




上述的两个 procedure 和 epistemic 是两个不一样的 robustness 的体现。需要两个不一样的 evaluation metric

#### Metric 

robustness budget 这个东西需要在最终的 ranking 和 output level 上边来定义。加 Gaussian noise 会让 reviewer 看不懂这个 current noise 到底有多大

具体来说，我们应该用三个具体的统计指标

1 recall @k 召回率 @前K个

2 MRR (Mean Reciprocal Rank, 平均倒数排名) 第一个正确答案出现得有多早？敏捷度指标。它只关心第一个相关结果出现在哪里。如果第一个正确结果排在第 1 位，得 1 分；排在第 2 位，得 1/2 分；排在第 10 位，得 1/10 分。

3 nDCG (Normalized Discounted Cumulative Gain, 归一化折损累计增益) 当前情况下的 retrival score 除以 idea 情况下的 retrival score

4 还有一个可能的结果是 Kendall-tau 这个是 

$$\tau = \frac{\text{同序对数量} - \text{逆序对数量}}{\text{所有可能的配对总数}}$$


#### 3.3 Methodology

具体的可以操作方法可以是

1. Hard-negative mining: 找到那些困难的负样本。（这里的意思是我需要找到一些 agent trajectory 上边的 hard negative 负样本
   1. 这里涉及到一些背景知识。具体来说，我们需要用一些 triple loss 相关的东西。Anchor, Positive data, Negative data. triple loss 的原理是拉近 positive data 和 anchor 的距离，推远 negative data 和 anchor 的距离。

2. minmax coruption 。人为构造困难的 negative training data。让 negative data 尽可能和 anchor 相似，然后让模型区分 negative data 和 anchor

   1. 这玩意在 nlp 上边还有一个变种，就是给 positive data 加 noise，然后让模型将 noisy positive data 也识别成 positive data。这个对应到 noisy tool 上边是，在 tool call 的结果上加上一些 noisy info 的返回值，但是正确的信息仍然 preserve



#### reference

RAGSynth https://arxiv.org/pdf/2505.10989 



#### 3.2 Evaluations

evaluation 可以画两条曲线

1. Robustness curve: 成功率和 robustness budget。给更多干扰的时候，成功率会降低。
Expected trained 出来的 model 的 performance degrade 应该更慢


2. risk-coverage: 模型弃权比例和错误率的关系（这个感觉可以调整弃权的 negative reward 的值的大小




实际上上边两种方式很难直接操作到 tool calling 的 trajectory 上边去。所以在具体 corrupt tool calling results 的时候，只能是借助这里的思想，到时候构造几种 tool calling corruption 的方案。

所以现在的 plan 是

1. 找到一些正确的 agent tool call trajectory 在上边构造一些 perturbation，构造一些 perturbed trajectory
2. 给 agent 除了 direct answer 之外的 validation 和 reject 两个额外选项
3. 测试一下现有模型的 robustness
4. filter 出一些 syhnthetic trajectory 出来，用这些 trajectory 来做 SFT。或者是用这些 tool call 的 setting 来做 RL training 











