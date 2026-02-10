### LLM Sampling

top k sampling ：只在概率最高的 k 个候选里抽样，其他 token 概率设为 0，然后重新归一化再采样。

top p sampling: 按从大到小排序，取累计概率刚好达到阈值 p 的最小集合，再重新归一化抽样。 


### LLM Chunked Prefill

简单来说 decode 截断是 memory bound，prefill 阶段是 compute bound。所以这两个阶段可以 merge 起来操作

https://zhuanlan.zhihu.com/p/14689463165







