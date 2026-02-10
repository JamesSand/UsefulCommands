# agent 领域的几个综述



agent tool call cache？有人做过这个东西吗？




## Adaptation of Agentic AI

https://arxiv.org/pdf/2512.16301

https://github.com/pat-jj/Awesome-Adaptation-of-Agentic-AI 

### 1 Taxtomy 分类学

agent tool adaption 被分为四种情形

首先是 agent 侧的：

#### 1.1 agent use tool 
   1. 优化 agent 调用 tool 的 action

![image-20260206171909852](../../imgs/image-20260206171909852.png)

#### 1.2 agent tool output 

1. 直接优化 agent + tool 结果的 output
2. 对于 SFT 场景下，只优化最终的 output；对于 RL 的场景下，action 和 output 都会被优化到

![image-20260206172017689](../../imgs/image-20260206172017689.png)



还有 tool 侧的 

#### 2.1 agent agnostic tool adaptation

agent agnostic 通过调这个 tool 来更好适应 agent

1. 这个好像没有什么人做，感觉这个分类像是硬编出来的


 ![image-20260206172209338](../../imgs/image-20260206172209338.png)

#### 2.2 agent supervised tool adaptation

1. 通过 agent 的反馈结果优化 tool 本身
1. 这里基本上都是 model as a tool。用这种方式才能说是去 tune 这个 tool

![image-20260206172516771](../../imgs/image-20260206172516771.png)

这里边有几个有趣的 paper

RA-DIT
https://arxiv.org/abs/2310.01352

这个paper 搞了一个 

LSR (LM Supervised Retrival) ：对于每一个检索到的 chunk，都喂给 LLM，看正确答案的概率能够提升多少。这个作为整个 chunk 的 LSR score；接下来只需要让 retriver 去 match 这个 LSR 的分数就行了

他们的 retriver 用的是 DRAGON+ ，这是一个双塔结构 dual encoder，他们的分数是这样算的
$$
s(q, c) = E_q(q) \cdot E_d(c)
$$
所有 chunk 都会被提前 preprocess 成一个向量索引，这样 query 来了之后就直接找最相近的 k 个就行了

关于怎么把 docs 变成 chunk，这里边的学问可就大了，chunk size，overlap size 这些东西都是可能会影响 model performance 的可调参数



Proxy tuning

https://arxiv.org/abs/2401.08565 

这个其实相当于 LLM 里边的 cfg。在一个小模型上对比训练前后的 logits 该变量，直接把这个改变量 adapt 到大 model 上，这样就省下了 train 大 model 的费用了
$$
\Delta = logits(proxy\_tuned) - logits(proxy\_untuned) \\
logits(large) \gets logits(large) + \alpha \cdot \Delta
$$


memento: 这个东西是一个 tool use based llm memory 的框架实现，这个东西可以帮助我们的 tool failure results 的实现

https://arxiv.org/pdf/2508.16153 

















### 2 现在的 challenge

？

















