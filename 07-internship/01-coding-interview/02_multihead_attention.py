


import torch
def multihead_attention(
    hidden_states: torch.FloatTensor, # (B, S, D)
    qkv_weight: torch.FloatTensor, # (D, 3D)
    o_weight: torch.FloatTensor, # (D, D)
    num_heads: int,
    softmax_scale: float, 
):
    # Step0: get the shape
    B, S, D = hidden_states.shape
    
    # check the hidden head dimension
    assert D % num_heads == 0, "hidden dimension must be divisible by num_heads"
    head_dim = D // num_heads  # dimension per head
    
    # step1: apply qkv weight on hidden
    qkv = hidden_states @ qkv_weight  # shape: (B, S, 3D)
    
    # split across dim
    q, k, v = qkv.split(D, dim=-1)  # each shape: (B, S, D)
    
    # reshape to mutihead attention
    q = q.view(B, S, num_heads, head_dim).transpose(1, 2)  # shape: (B, num_heads, S, head_dim)
    k = k.view(B, S, num_heads, head_dim).transpose(1, 2)  # shape: (B, num_heads, S, head_dim)
    v = v.view(B, S, num_heads, head_dim).transpose(1, 2)  # shape: (B, num_heads, S, head_dim)
    
    # calcualte attention score
    attention_score = (q @ k.transpose(-2, -1)) 
    
    # apply softmax scale and apply softmax
    # softmax score here is usually sqrt d dim 
    attention_score = torch.softmax(attention_score * softmax_scale, dim=-1)  # shape: (B, num_heads, S, S)
    
    attention_out = attention_score @ v # shape : (B, num_heads, S, head_dim)
    
    # reshape back to (B, S, D)
    attention_out = attention_out.transpose(1, 2).contiguous().view(B, S, D)  # shape: (B, S, D)
    
    # apply o weight, o weight should be (D, D_out). Here we assume D_out = D
    output = attention_out @ o_weight  # shape: (B, S, D)
    
    return output
    
    
    
    
    
    
    
    

