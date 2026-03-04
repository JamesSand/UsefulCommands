

fact
1. 很多原生的 base model 比如说 qwen3 其实不会去调用 agent team 里边的这些组件啥的（这个需要实证一下
2. 现在没法做到 main agent 和 subagent 一起做 RL training。（这个需要调查一下）

solution:
1. 我用 tools 来模拟 subagent 的调用，比如说每个 subagent 就是一个 tool，有不同的接口。
2. 每个 subagent 擅长的东西不一样，所以在不同 task 下的 performance 也不一样。这个需要 main agent 去在 test time 去选择应该去调用哪个 agent

这里的 research question 有两个
1. 如果有一个一开始没有 agent 调度能力的 base model，我要怎么训能够让他具备 main agent 那种调度能力？
2. 如果一个 main agent 具备了调度能力，这种 test time 的调度能力有多大的 generalization 能力？换了一组 agent team 之后还能不能继续成功调度？


UT Austin Peter Stone 组下边可能有类似的工作，但是肯定不是 agent team 这个 direction 的。
如果我没记错的话是 jiaxun cui 学姐的工作，https://scholar.google.com/citations?user=SwEYj9YAAAAJ&hl=en

你给我 survey 一下我这个 idea ，主要看
1. 有没有现成的 agent team 的这种 benchmark
2. 有没有人做过类似的事情
3. 原生 base model 不能做 agent 调度这个事情有没有人发现过
4. main agent 和 subagent jointing training 是不是不能实现


https://chatgpt.com/g/g-p-6998a80822c481919f92de51e4e28926-research-ideas/c/6998a80c-3c84-832e-b7d0-456ee5f2a042



