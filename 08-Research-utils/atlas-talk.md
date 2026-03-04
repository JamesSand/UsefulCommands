
yuandong 
cocotunt paper

latent reasoning: 如果每次 reasoning 的时候不用 deocde 到 token，而是用上一个 latent 作为下一个 step 的 input。这样每一步不是 sample 一个 token，而是一直保留 probability 到最后一个 decode step

latent reasoning 可以 somehow 在 pretrian 的时候 save token


Neel

在 traffic setting 下边，我们会看一下 agent 能不能学会 environment 的 rules. 如果是从零学会 rule 可能太难了，所以我们会先告诉他几个 rule，然后看他们能不能学剩下的 rules 

现在会认为 natural language 的 rule 是很难学的。另一条路是 formal verification，尽管 formal verification 是 noisy 的，但是 noisy formal verification 是更好的。


kevin

如果只是用 verifiable env，只会被限制在 math, code, planning 这三个东西里边去

现在把 unverifiable env 转换成 verifiable env 是一个 research 和busniess direction

PNL 是什么，和 agent planning 有关系





