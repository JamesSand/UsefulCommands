

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
