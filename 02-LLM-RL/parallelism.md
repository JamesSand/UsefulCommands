

### sequence parallel

今天在看 verl 的时候把 sequence parallel 重新学了一下，感觉蛮有意思的

sp 起作用的阶段在 training 和 prefilling，在那些每次 forward 有多个 q query 的时候，把不同的 q query 分配到不同的 GPU 上边去。但是在 decoding 阶段，每次只有一个 q query，所以这个时候 sp 就没有什么效果了。

tp 是沿着 tensor dimension 的维度进行切分，所以在 prefilling 和 decoding 阶段都有作用

Attention 实现里边 QK 的复杂度是 $O(L^2 d)$ sp 主要是针对 L 这个维度进行这样的优化 $O(L (L / sp) \cdot d)$

但是 attention 里边也有这种操作 $X \in \R^{L\times d}, W \in \R^{d \times d}$ 所以 $XW$ 是 $O(L d^2)$ 的，那如果是 tp 的话，复杂度会变为 $O(L \cdot d (d / tp))$

