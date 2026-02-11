### conda install codex

```
conda install -y nodejs

npm install -g @openai/codex
```


### windows wsl install codex

> windows 下也可以安装 codex

参考这里
https://developers.openai.com/codex/windows/

具体的指令如下，在 wsl 下边执行
```
# https://learn.microsoft.com/en-us/windows/dev-environment/javascript/nodejs-on-wsl
# Install Node.js in WSL (via nvm)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/master/install.sh | bash

# In a new tab or after exiting and running `wsl` again to install Node.js
nvm install 22

# Install and run Codex in WSL
npm i -g @openai/codex
codex
```

### codex 全局指令

claude code 里边是 `CLAUDE.md` 对于 codex 而言是 `AGENTS.md` 


### codex 全自动

https://developers.openai.com/codex/security

如果需要完全完全自动执行，可以用这个
```
codex --yolo
```

如果弱一点，可以用这个会更安全一些

这个要放在 `~/.codex/config.toml` 里边
```
approval_policy = "never"
sandbox_mode    = "workspace-write"
```










