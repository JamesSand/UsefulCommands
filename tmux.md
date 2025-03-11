

## 安装 tmux

```bash
sudo apt-get update
sudo apt-get install tmux
```

enable mouse in tmux

put the following in `~/.tmux.conf`
``` bash
set -g mouse on
```

## Tmux 使用技巧

``` bash
# 创建一个 tmux session
tmux new -s <session name>

# 如果需要 tmux 中显示中文字符要使用
tmux -u new -s <session name>

# 关掉一个 tmxu session
# Ctrl + D

# detach from a tmux session
# Ctrl + B 然后按 D

# 链接到 session 上
tmux a -t <session name>
```

tmux 真是博大精深

在缓冲区里边搜索
```bash
# 按下 Ctrl + b 然后按下 [ 进入 copy mode
# 从上往下搜索用 /
# 从下往上搜索用 ?

# 按下 n 搜索下一个
# 按下 N 搜索上一个
# 按下 q 退出搜索模式
```
