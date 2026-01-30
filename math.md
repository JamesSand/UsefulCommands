

### Reiman



### SVD related

SVD 分解的公式
$$
W = U \Sigma V^\top
$$


#### Principal Angle

这个文章介绍的非常好，有很多数学推导，但是这里我们只记录最终的结论。

https://xyfjason.top/blog-main/2024/03/02/%E5%AD%90%E7%A9%BA%E9%97%B4%E7%9A%84%E8%B7%9D%E7%A6%BB/







#### Stable Rank

$$
\mathrm{erank}(A) =  \frac{\sum_i \sigma_i^2}{\sigma_1^2}
$$

- stable rank 的取值范围是 $[1, n]$ 
- stable rank = 1 的时候，说明整个 singular value 都分布在最大的上边，很尖
- stable rank = n 的时候，说明整个 singular value 均匀分布在所有的上边，很平



下边是一些跟 singular value 和别的东西的联系

跟着苏神的 blog 学

https://zhuanlan.zhihu.com/p/1899586138747937721

首先复习一下矩阵范数

- Spectral Norm $\| A\|_2 = \sigma_1$ 最大的奇异值
- Nuclear Norm $\| A \|_* = \sum_i \sigma_i$ 所有奇异值的和

由于所有奇异值都是非负的，可以将其归一化成一个概率分布
$$
p_i = \frac{\sigma_i^\gamma}{\sum_j \sigma_j^\gamma}
$$
这里 $\gamma$ 可以取 1 或者 2

有了概率分布，就可以计算信息熵
$$
H = - \sum_i p_i \log p_i
$$
于是，我们的 effective rank，或者说 stable rank 的定义就是
$$
\mathrm{erank}(A) = \exp(H)
$$
苏神关于 stable rank 还有很多推导，这里就不都写出来了。



### KL Divergence

http://joschu.net/blog/kl-approx.html


$$
\mathrm{KL}[q, p] = \mathbb E_{x \sim q} [\log \frac{q(x)}{p(x)}] = \sum_x q(x) \log \frac{q(x)}{p(x)}
$$

第二个等号是因为在实际采样中，需要用 Monte-Carlo approximation 来算 KL 





### 奇怪的知识

#### Bayes risk

给定真实数据分布和损失函数的时候，任何可实现策略能够达到的最小期望损失。

能够达到理论最小期望损失的函数 / 决策称之为 Bayes rule (Bayes 决策)



#### Population Risk

给定输入 X、输出 Y 的真实分布 P 和损失函数 L，任何预测函数 h 的 population risk 定义为在真实分布下的期望损失：
 R(h) = E_{(X,Y)∼P}[ L(h(X), Y) ]
 它衡量的是模型在“整个数据分布”上平均会犯多大错误，而不是只在训练数据上。



和 empirical risk（经验风险）的区别
 经验风险 Ŕ_n(h) 是在训练样本 {(x_i,y_i)}*{i=1}^n 上的平均损失：
 Ŕ_n(h) = (1/n) ∑*{i=1}^n L(h(x_i), y_i)
