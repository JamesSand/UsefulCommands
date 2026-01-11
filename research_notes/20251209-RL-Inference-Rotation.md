# RL Inference benifit from rotation


> Work with Haniqng, we want to investigate how can we use the ratation in RL to merge the ability of different RL trained models



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









