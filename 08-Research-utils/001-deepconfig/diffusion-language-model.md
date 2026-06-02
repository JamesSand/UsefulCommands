
Simple diffusion language model tutorial 2406
https://www.youtube.com/watch?v=WjAUX23vgfg 


blog for diffusion language model
https://spacehunterinf.github.io/blog/2025/diffusion-language-models/ 






两个 idea

### 1 improve training efficiency of DLM

这个文章里边提到了 diffusion model 的 order 的问题
https://arxiv.org/abs/2511.19152

Setion 3


现在 DLM 的 training，其实 training signal 只会在那些从 mask 变成 unmask 的 token 上用到。

但是 AR model 就没有这个问题，因为 AR model 因为 casual attention mask 的存在所以，所有的 token 都能够被用来提供 training signal

如果说我们能够找到所有 token 生成之间的 dependency，通过这个 dependency 构造 attention mask，就能够让所有 token 都提供 training signal


### 2 transfer a GPT model to a DLM model

这个文章里边提到了可以把一个 GPT model 改造成一个 diffusion language model
https://arxiv.org/abs/2512.14067

LLaDA 2.0 也是在做这个事情的


这个问题本质上也是找 AR 里边的 order。

假设现在又 10 个 token。AR 的话就是按照 1，2，3，- ，10 的顺序生成这 10 个 token

但是假如说按照 dependency 来看的话，其实生成顺序可以是 1 -> 6, 10 -> 2, 7 这种顺序。只要我们能够找到 order 的这个顺序，我们就能够实现这样的事情









