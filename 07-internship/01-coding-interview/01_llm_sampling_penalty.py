'''
Docstring for 01_llm_sampling_penalty

Presence / Frequency penalty（OpenAI / LLM sampling 常见惩罚项）

- presence penalty:
  只要某个 token 出现过至少 1 次，就对它施加固定惩罚（鼓励新 token）。

- frequency penalty:
  某个 token 出现次数越多，惩罚越大（鼓励多样性）。

常见形式（对每个 token i 的 logit）：
    logits[i] <- logits[i]
                - presence_coef  * 1[count_i > 0]
                - frequency_coef * count_i
'''


import torch

def presence_frequency_penalty(
    logits: torch.FloatTensor, # shape: (B, V) denote the logits for current step,
    context_indices: torch.LongTensor, # shape: (B, S) denote the context token indices, expteced integer dtype
    presence_coef: torch.FloatTensor, # shape: (B,) or (B, 1) denote the presence penalty coefficient,
    frequency_coef: torch.FloatTensor, # shape: (B,) or (B, 1) denote the frequency penalty coefficient,
):
    # Step 0: get the shape
    B, V = logits.shape
    
    # Step1: cout present time for each vocab
    counts = torch.zeros_like(logits)  # shape: (B, V)
    # 指定 dimension = 1 这里干的事情是
    # tensor[i][index[i][j]] += src[i][j]
    # 这里相当于是 counts, index, src 三个的 shape 要是一样的才行
    # index 提供 position, src 提供 value。最后结果加到 dst 上去
    counts.scatter_add_(
        dim=1, 
        index=context_indices, 
        src=torch.ones_like(context_indices, dtype=counts.dtype)
    )
    
    # reshape coefficient for broadcasting
    presence_coef = presence_coef.view(B, 1)  # shape: (B, 1)
    frequency_coef = frequency_coef.view(B, 1)  # shape: (B, 1)
    
    # add presence penalty
    logits = logits - presence_coef * (counts > 0).float()
    
    # add conut penalty
    logits = logits - frequency_coef * counts
    
    return logits


def test_minimal():
    # ----- setup -----
    # B=1, V=5
    logits = torch.tensor([[10., 11., 12., 13., 14.]], dtype=torch.float32)
    # context contains tokens: 1,1,3  -> counts: [0,2,0,1,0]
    context = torch.tensor([[1, 1, 3]], dtype=torch.long)

    freq = torch.tensor([0.5], dtype=torch.float32)   # frequency coeff
    pres = torch.tensor([1.0], dtype=torch.float32)   # presence coeff

    # ----- run -----
    out = presence_frequency_penalty(logits, context, pres, freq)

    # ----- expected (hand-computed) -----
    # token 0: count=0, pres=0 -> 10 - 0 - 0 = 10
    # token 1: count=2, pres=1 -> 11 - 0.5*2 - 1 = 11 - 1 - 1 = 9
    # token 2: count=0, pres=0 -> 12
    # token 3: count=1, pres=1 -> 13 - 0.5*1 - 1 = 11.5
    # token 4: count=0, pres=0 -> 14
    expected = torch.tensor([[10., 9., 12., 11.5, 14.]], dtype=torch.float32)

    torch.testing.assert_close(out, expected, rtol=0, atol=0)
    print("✅ minimal test passed")
    print("out:", out)


if __name__ == "__main__":
    test_minimal()
    
    
    
# 关于 torch gather 和 torch scatter 的一些区别
# torch gather 的意思是，given index，从一个大 tensor 里边根据这些 index 把 value 取出来
# torch scatter 是，given index，把一些 value 放到一个大 tensor 对应的位置里边去



