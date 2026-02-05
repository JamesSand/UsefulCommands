
### openclaw 配置 discord bot

https://cloud.tencent.com/developer/article/2626068



```
# 看 openclaw  token 消耗
openclaw status 

# 配置
openclaw configure
```


### clawhub

```
# install
npm i -g clawhub

clawhub login

clawhub whoami
```

wsl 下边会出现这个报错
```
Opening browser: https://clawhub.ai/cli/auth?redirect_uri=http%3A%2F%2F127.0.0.1%3A35599%2Fcallback&label_b64=Q0xJIHRva2Vu&state=8d233b170637296f3170020e52a4a144
node:events:497
      throw er; // Unhandled 'error' event
      ^

Error: spawn xdg-open ENOENT
    at ChildProcess._handle.onexit (node:internal/child_process:285:19)
    at onErrorNT (node:internal/child_process:483:16)
    at process.processTicksAndRejections (node:internal/process/task_queues:90:21)
Emitted 'error' event on ChildProcess instance at:
    at ChildProcess._handle.onexit (node:internal/child_process:291:12)
    at onErrorNT (node:internal/child_process:483:16)
    at process.processTicksAndRejections (node:internal/process/task_queues:90:21) {
  errno: -2,
  code: 'ENOENT',
  syscall: 'spawn xdg-open',
  path: 'xdg-open',
  spawnargs: [
    'https://clawhub.ai/cli/auth?redirect_uri=http%3A%2F%2F127.0.0.1%3A35599%2Fcallback&label_b64=Q0xJIHRva2Vu&state=8d233b170637296f3170020e52a4a144'
  ]
}

Node.js v22.22.0
```

装一个就行了
```
sudo apt update
sudo apt install -y xdg-utils
```







