

### KL Divergence

http://joschu.net/blog/kl-approx.html


$$
\mathrm{KL}[q, p] = \mathbb E_{x \sim q} [\log \frac{q(x)}{p(x)}] = \sum_x q(x) \log \frac{q(x)}{p(x)}
$$

第二个等号是因为在实际采样中，需要用 Monte-Carlo approximation 来算 KL 





