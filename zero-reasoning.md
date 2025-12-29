#### Multi Agent Evolve

https://arxiv.org/pdf/2510.23595 

Extend 了一下 absolute zero reasoning。因为 AZR 是只能在 code 上做。





#### Absolute Zero Reasoning

https://arxiv.org/pdf/2505.03335

文章的核心公式

![image-20251119155748799](imgs/image-20251119155748799.png)

propose 的 reward 是给 solver 出难度适中的题，需要一个 $\lambda$ term 来平衡 propose reward 和 solver reward

<img src="imgs/image-20251119155920525.png" alt="image-20251119155920525" style="zoom:30%;" />

首先定义三个东西，input I, program P 和 output O

|   Name    | Given | Predict |
| :-------: | :---: | :-----: |
| Deduction | I, P  |    O    |
| Abduction | P, O  |    I    |
| Induction | I, O  |    P    |





