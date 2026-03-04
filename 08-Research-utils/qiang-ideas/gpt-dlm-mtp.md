
## Bridge the gap between GPT and DLM. 

### Idea

idea 是这样的，我们现在想让 GPT 能够实现并行推理的效果。举一个例子来说，
假如我们有一个 user query "Please introduce the history of AI", 我们可以构造这样的 prompt
1. Please introduce the history of AI. Please predicet the 1-st token of your output: 
2. Please introduce the history of AI. Please predicet the 2-nd token of your output:
3. Please introduce the history of AI. Please predicet the 3-rd token of your output:
4. Please introduce the history of AI. Please predicet the 4-th token of your output:
5. Please introduce the history of AI. Please predicet the 5-th token of your output:
... 

这样的话，我们把上边的 prompt 做成一个 batch，喂给 gpt，这样的话能够一下子得到前 5 个 token 的预测结果，相当于一次 forward 可以得到 5 个 token。

这个 idea 和 medusa 的 idea 本质上是相似的

https://arxiv.org/abs/2401.10774 但是问题在于 medusa 用的是 last latent 来做的 prediction，

qiang 觉得这里可以 improve 的点在于，用 last latent vector 不 make sense，里边的 information 更好，如果能用整个的 KV Cache 来做的话，效果应该会更好

于是说还是用上边这种 prompt 的方式，现在有三种可能可以尝试以下
1. 对整个 model 做 finetune，来让他适配这种 ood 的 prompt task
2. model 是 freeze 的，对 prompt embedding 做 finetune，做一个 soft prompt 出来
3. 用于 prefill 前缀的 model 是 freeze 住的，后边重新训一个新的 model 来做 k-th token prediction 

想到的 idea：
(1) self distillation 看起来是一个不错的 idea，能不能把 self distillation 和 bidirectional attention 结合起来。(这个东西已经在2602 MTP with self distillation 里边在 ablation 里边做掉了)

### Literature

注意这里我们想做的其实是 multi token prediction (MTP) 这个 task，不是 speculate decoding

https://arxiv.org/pdf/2508.08712? LLM decoding survey. Section 3.3 说的是 MTP

#### 1.1 训 soft embedding tokens

https://arxiv.org/abs/2311.13581 PaSS 这个是我那个 placeholder 的 idea。他们这里是训了一堆 LA_i tokens

https://arxiv.org/pdf/2401.12522v2 BiTA: Bi-Directional Tuning for Lossless Acceleration in Large Language Models
https://github.com/linfeng93/BiTA
加了一些 prompt token，mask 在 generation 的时候 attend 到 prompt token 上去

#### 1.2 训 multi head 来做 MTP

https://arxiv.org/abs/2401.10774 Medusa: multi-medusa head prediction on last latent vector (Multi-token prediction)

https://openreview.net/pdf?id=gKInyC9nlQ On multi-token prediction for efficient LLM inference
这个 exactly 是我们想做的 MTP，但是他们没有 codebase 

https://openreview.net/pdf?id=0VDmWjW456 Leap-MTP, NeurIPS 2025
和 medusa 一样，训练 multi head 来做 prediction

### 1.3 训一个小的 model，来做 parallel draft 

https://arxiv.org/pdf/2410.05589v1 ParallelSpec: Parallel Drafter for Efficient Speculative Decoding
训了一个 draft model 和 special tokens 来支持 MTP

#### 1.4 finetune NTP model，训成一个支持 MTP 的 model

https://arxiv.org/pdf/2602.06019v1 Multi-Token Prediction via Self-Distillation 
把一个 NTP 的 model，通过 self distillation 训成一个 MTP 的 model (这个 paper 和 ParallelSpec 的区别是，不需要 verifier，直接吧 NTP 改进 MTP)

https://arxiv.org/pdf/2509.04185v1 Set Block Decoding is a LM inference accelerator


#### 2.1 Speculate decoding


https://arxiv.org/pdf/2510.11958v1 Direct Multi-Token Decoding. 混合体 MTP and speculate decoding. 相当于是 hierarchical AR (see Figure 3).


https://arxiv.org/abs/2402.02082 GliDe CAPE: loww hassle method use KV Cache for Draft model (speculate decoding) 所有 speculate decoding 的和我们的都不一样






### message to qiang

Hi Professor, I dug deeper into this direction. I found that there are already some papers that are quite similar to the three directions we discussed yesterday:

1. Train some special tokens as the MTP input while freezing the model.
2. Keep the model for prefilling the user query fixed, and use an additional model to do MTP.
3. Fine-tune the entire model so that it can adapt to MTP as an out-of-distribution (OOD) task.

I made a slide deck summarizing current progress on these directions. 

https://docs.google.com/presentation/d/1Wdrwuds-WLplQM_m8azZGkXVKCVRCpxUtUXh-_P3-_4/edit?usp=sharing


Would it be possible to find a time that works for you so we can discuss what design choices we can still explore on top of this and how we should move forward? 



Hi Professor, I’ve been thinking more about the GPT-DLM idea you mentioned two days ago. 

I realized there is a 2024 paper called Medusa (https://arxiv.org/abs/2401.10774) that uses a very similar approach: it trains several lightweight “Medusa heads” on top of the model’s last hidden states to predict the next n tokens in parallel. 

This seems closely related to your GPT-DLM idea, in the sense that a single forward pass can produce predictions for multiple future tokens.


### 现在的进展



I have tried the GPT DLM idea for a while. I found that the model cannot easily generate tokens from the middle of a response at the beginning of a sentence. It seems that it can only generate tokens like “suppose” when they appear at the start of a sentence.

I have tried several prompting methods, but none of them can bypass this limitation.
method 1: direct prompt
==================================================
Prompt for step 3:
[prompt] Please introduce Beijing. please predict the 3-th token of your final answer: 
[response] 1. Beijing is the capital of China and one
==================================================
==================================================
Prompt for step 4:
[prompt] Please introduce Beijing. please predict the 4-th token of your final answer: 
[response] 1. Beijing is the capital of China and one
==================================================
==================================================
Prompt for step 5:
[prompt] Please introduce Beijing. please predict the 5-th token of your final answer: 
[response] 1. Beijing is the capital of China and one
==================================================

# method 2: instruct to output one token
==================================================
Prompt for step 3:
[prompt] Please introduce Beijing. please predict the 3-th token of your final answer, reply only with the token without any explanation or punctuation. the token is: 
[response] 1

Beijing is the capital of China,
==================================================
==================================================
Prompt for step 4:
[prompt] Please introduce Beijing. please predict the 4-th token of your final answer, reply only with the token without any explanation or punctuation. the token is: 
[response] 1

Beijing is the capital of China,
==================================================
==================================================
Prompt for step 5:
[prompt] Please introduce Beijing. please predict the 5-th token of your final answer, reply only with the token without any explanation or punctuation. the token is: 
[response] 1

Beijing is the capital of China and
==================================================

# method 3: try use <placeholder> token
==================================================
Prompt for step 3:
[prompt] Please introduce Beijing. please predict the 3-th token of your final answer: <placeholder> <placeholder> 
[response] 1. Beijing is the capital of China and one
==================================================
==================================================
Prompt for step 4:
[prompt] Please introduce Beijing. please predict the 4-th token of your final answer: <placeholder> <placeholder> <placeholder> 
[response] 4-th token: 

Beijing is the capital
==================================================
==================================================
Prompt for step 5:
[prompt] Please introduce Beijing. please predict the 5-th token of your final answer: <placeholder> <placeholder> <placeholder> <placeholder> 
[response]  <placeholder>

Beijing is the capital of China
==================================================

This phenomenon is not only observed on Qwen, but also on GPT. (see attached screenshot)

@qiang So it seems that if we want to use GPT for DLM, we may need to add an extra fine-tuned k-th prediction head to adapt to this pattern.

Yes I think the instruction following capability of GPT is quite limited, especially for these non-common tasks. SFT will be better.
Runlong Liao  [下午 1:37]
these ood tasks
Zhizhou Sha  [下午 1:42]
yeah. It seems we can construct some SFT data to make pre-train model understand how these ood tasks perform. Then maybe we can unlock their potential
qiang  [晚上 8:34]
Yes. But also the actual accuracy requirement that we need for generation can be small

你给我解释一下 qiang 最后一句话是什么意思


