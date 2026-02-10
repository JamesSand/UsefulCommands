

Document retrival 

考虑这样一个场景，我有一个 query，一堆 documents，一个 embedding model $f_\theta$。

retrivial 的流程是
1 算 query 和 decument 的 embedding $v_q = f_\theta(q), v_d = f_\theta(d)$
2 计算相似度 $sim(v_q, v_d)$

一般来说，大家会用 contrastive loss 来训练 embedding model。假如说 (q, d) 是一个 query 和 document pair，(q, d') for all $d' \neq d$ 是 negative samples，那么 contrastive objective 可以写成
$$
\max \mathbb{E}_{(q, d)} [\langle f_\theta(q), f_\theta(d) \rangle - \frac1{|B|} \sum_{d' \neq d} \langle f_\theta(q), f_\theta(d') \rangle]
$$

找 hard negative example。对于这些 example 的选择，有很多种策略。其中一种策略是我们用 traditional retrival method 找到很多 relevant 的 docs，从里边采样 negative sample。这样 sample 出来的一定是和 positive sample 很相似的 negative samples









