
import torch

def top_k_sampling(
    logits: torch.FloatTensor, # shape (B, V)
    k: int
):
    if k <= 0:
        return logits
    
    B, V = logits.shape
    
    # extract topk logits from logits
    # 第二个 return value 是 indices value，这个不通关
    topk_values, _ = torch.topk(logits, k=k, dim=-1)  # shape: (B, k)
    # find the kth value
    kth = topk_values[:, -1].view(B, 1)  # shape: (B, 1)
    
    # set all values below kth to -inf
    # torch where 是这样的
    # 第一个 param 是 condition，第二个是 conditoin 为 true 的时候的，第三个是 condition 为 false 的时候的
    logits = torch.where(
        logits < kth,
        torch.full_like(logits, float('-inf')),
        logits
    )
    
    return logits


# TODO: 下边这个需要我自己整理一遍
def top_p_sampling(
    logits: torch.FloatTensor, # shape (B, V)
    p: float
):
    # step 0 sort all logits
    # step1: cumsum
    
    # step2: find all position that cumsum > p
    
    # step3: set those position to -inf
    
    # 1) sort
    sorted_logits, sorted_idx = torch.sort(logits, dim=-1, descending=True)  # (..., V)

    # 2) probs + 3) cumulative probs
    sorted_probs = torch.softmax(sorted_logits, dim=-1)                      # (..., V)
    cumprobs = torch.cumsum(sorted_probs, dim=-1)                            # (..., V)

    # 4) remove tokens with cumprob > p, but KEEP the first token that crosses p
    remove = cumprobs > p                                                    # (..., V)
    remove[..., 1:] = remove[..., :-1].clone()                               # shift right
    remove[..., 0] = False                                                   # always keep top-1

    # 5) mask in sorted space
    filtered_sorted_logits = sorted_logits.masked_fill(remove, float('-inf'))  # (..., V)

    # 6) unsort back to original vocab order
    filtered_logits = torch.empty_like(filtered_sorted_logits)
    filtered_logits.scatter_(-1, sorted_idx, filtered_sorted_logits)
    return filtered_logits



    
    



