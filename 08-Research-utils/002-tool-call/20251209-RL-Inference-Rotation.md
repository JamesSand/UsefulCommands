# RL Inference benifit from rotation


> Work with Haniqng, we want to investigate how can we use the ratation in RL to merge the ability of different RL trained models



## 这些 idea 都不 work

主要是在 2e-6 svd muon adam 上试一试

1 trace 要试一下

2 history 信息要试一下 SGD 上做 0.9 -》 0.5 ；adam 的 0.999 的 V 也要调小

2.1 tangent projection。

要不要 scedule grad norm？

adam history 信息缩小

adam vaiance 信息缩小



3 U V 搞出来





1 用 trace 来 constraint ，证明在 adam 5e-6 能 work

2 现在的实验，收敛更快



tricks to try

1 plain sgd + tangent gradient / VS / plain sgd

2 change sgd momemtom to adam style mometum 

3 step norm scale with sqrt(R). 

4 gradient cliping when grad is large. See verl code actor



tacc 2-4 node

qwen3 1.7b 全部都 try 出来



5 U V statics. Geo distance. Grad norm. U V momemtum, U V variance



看一下 U 和 V 的 statics



Yes. I agree the sig value will change numerically. 



But the relative difference is only





adam

二阶全关掉，一阶调小



下边这两个开四组

sgd momentum: 1e-5 / 1e-4 / 1e-3, momentum 0.9 

msign 之前的 U 做一个 normalization，这个可以做到 Delta U 或者 U + Delta U 上边去



1e-5 mom 0.9

1e-4 mom 0.9

1e-3 mom 0.9

1e-4 mom 0.0

1e-4 mom 0.9 , norm before step

1e-4 mom 0.9 , norm before msign



adam svd muon 2e-6 norm before step

adam svd muon 2e-6 norm before msign

adam svd muon 3e-6 norm before step

adam svd muon 3e-6 norm before msgin





U: m * r  |U|_F = sqrt(r)



1 lr 后期可以 decay

2 U V 想一想怎么加 constraint

3 tangent space 上的 gradient





## High level Ideas

We hypothesis that RL on LLM actually learn some matrix rotation operations. We want to see if we can use this insight to find a better model merging method. 

We use 2 experiment to demonstrate the rotation nature. 



### Evaluation Results

重新换 evaluation 的框架

https://github.com/wizard-III/ArcherCodeR

还有 ProRL



发现了一个这个东西，好像看起来不错

https://github.com/huggingface/open-r1?tab=readme-ov-file#evaluating-models







如果是 DeepScalR 和 DeepCoder。这个是在 Transferbility 的 eval 框架跑的 DeepScaleR 和 DeepCoder

|         Model          | AIME24 | AIME25 | Math500 | LivecodeBench |
| :--------------------: | :----: | :----: | :-----: | :-----------: |
| DeepScaleR 1.5B (run1) | 0.4200 | 0.2567 |  0.85   |    0.3288     |
| DeepScaleR 1.5B (run2) | 0.4000 | 0.3100 |  0.84   |    0.3268     |


|         Model         | AIME24 | AIME25 | Math500 | LivecodeBench |
| :-------------------: | :----: | :----: | :-----: | :-----------: |
| DeepCoder 1.5B (run1) | 0.4367 | 0.3033 |  0.844  |    0.3581     |
| DeepCoder 1.5B (run2) | 0.4267 | 0.2867 |  0.86   |    0.3796     |

这不太对啊，这玩意怎么测出来，是 deepcoder 全面碾压 deepscaleR 啊




## Implementation details



### Setup evaluation codebase

https://github.com/ReasoningTransfer/Transferability-of-LLM-Reasoning/tree/main/eval 

这个 evaluation framework 的 pass k value 是写死的



pip 还需要设置临时变量目录

```
export TMPDIR=/ssd2/zhizhou/tmp
```



### Models we want to use

huggingface link

https://huggingface.co/agentica-org/DeepScaleR-1.5B-Preview

https://huggingface.co/agentica-org/DeepCoder-1.5B-Preview





从这个网站上搞下来的

https://agentica-project.com/

他们这个好像不是 paper，只是一堆 model 的 checkpoints

DeepScaleR https://pretty-radio-b75.notion.site/DeepScaleR-Surpassing-O1-Preview-with-a-1-5B-Model-by-Scaling-RL-19681902c1468005bed8ca303013a4e2 

DeepCoder https://pretty-radio-b75.notion.site/DeepCoder-A-Fully-Open-Source-14B-Coder-at-O3-mini-Level-1cf81902c14680b3bee5eb349a512a51 



我发现他们的 codebase 里边有对应的 evaluation code。但是他们的 evaluation code 不在主 branch 上，而且文档写的一坨。不用了









