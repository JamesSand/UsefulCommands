

### windows 开启卓越性能模式

https://zhuanlan.zhihu.com/p/590232882 

打开终端，输入

```
# 看当前用的是哪个方案
powercfg /getactivescheme

# 查看所有的性能方案
powercfg /list

# 注册卓越性能模式到 powercfg 里边去
powercfg -duplicatescheme e9a42b02-d5df-448d-aa00-03f14749eb61

```

运行完注册卓越性能的指令你会得到这个

```
PS D:\UsefulCommands> powercfg -duplicatescheme e9a42b02-d5df-448d-aa00-03f14749eb61
电源方案 GUID: b188249b-1f48-4b4f-84f4-d43c145879de  (卓越性能)
```

把这里的电源方案好复制到下边就行了

```
# 激活卓越性能方案
powercfg /setactive <power config ID>
```






### login 链接服务器

login command

```
# windows 这样不能 login
ssh zhsha@stampede3.tacc.utexas.edu

# window 这样 login 可以的
ssh -m hmac-sha2-512 zhsha@stampede3.tacc.utexas.edu
```

config 要这样写
```
Host stampede3
    Hostname stampede3.tacc.utexas.edu
    User zhsha
    MACs hmac-sha2-512
```



### vscode accessibility setting 怎么关掉

是的，我也是。我都不记得我当初是怎么开启它的了，但你可以试试：Ctrl + Shift + p 打开命令面板，搜索 Preferences: Open Accessibility Settings，就像 [u/Ok-Stick-6322](https://www.reddit.com/user/Ok-Stick-6322/) 说的那样，但对我来说，展开 Features > Accessibility > Accessibility: Hide Accessible View - 把它勾上就搞定了。



### ray 报错 ModuleNotFoundError: No module named 'click'

这个是因为你错误的把环境变量设置了

```
HOME=xxx 被覆盖了成了什么别的值
```

所以这个时候只需要用一个别的变量名就行了





### Stampede3 坏掉的节点

c561-007 

c561-001

c563-001

c562-005 有一个 GPU 挂掉了，这个最后一个 GPU 总是掉




### idev srun 拿计算节点

这是两条指令，之后可能会经常用的到

sbatch -p gh -N 1 -n 1 -t 24:00:00 -A ASC25082 \
 -J tacc-vscode --parsable --wrap="sleep infinity"


申请一个 debug 计算节点

```bash
idev -p icx -N 1 -n 1 -t 12:00:00 

idev -p h100 -N 1 -n 1 -t 48:00:00 -- -w c561-006

# 这个能够指定要哪些节点
idev -p h100 -N 2 -n 2 -t 48:00:00 -- -w c561-[004,008]

idev -p h100 -N 2 -n 2 -t 48:00:00 -- -w c562-[005-007]

idev -p h100 -N 2 -n 2 -t 48:00:00 -- -w c562-006

# 这个是排队排到之后给你自动发 email 的
idev -p h100 -N 2 -n 2 -t 48:00:00 -E

idev -p h100 -N 1 -n 1 -t 48:00:00 -- --exclude=c561-007,c561-001,c563-001,c562-005

idev -p h100 -N 2 -n 2 -t 48:00:00 -- --exclude=c561-007,c561-001,c563-001,c562-005

idev -p h100 -N 3 -n 3 -t 48:00:00 -- --exclude=c561-007,c561-001,c563-001,c562-005

# 这个是看现在我的 job 的 priority 的
sprio -u zhsha

# 这个是看 h100 这个 cluster 上的 job 的 priority 的
sprio -p h100


idev_email_address shazhizhou0@gmail.com


idev -p h100 -N 2 -n 2 --exclude=c561-001,c561-007 -t 48:00:00

# 这是 vista 上的指令
idev -p gh -N 1 -n 1 -t 48:00:00 -A ASC26009

idev -p gh-dev -N 1 -n 1 -t 2:00:00 -A ASC26009

sinfo -S+P -o "%18P %8a %20F"

sinfo -p h100

squeue -u $USER


# tmux open mouse on
Ctrl + b
:

set -g mouse on

# 底下这个能用
srun -J debug -N 1 -p gh-dev -n 28 -t 2:00:00 -A ASC25082  --pty /bin/bash
```

### Vista Stampede3 Docs

这是 TACC Vista 的文档

https://docs.google.com/document/d/1URcWe8mLQF8HMNre7vZwgk6TiRNxFxVBwK_HCcRXQdM/edit?usp=sharing 

这是 stampede3 的文档 

https://docs.tacc.utexas.edu/hpc/stampede3/ 



### 安装 torch

没想到安装 torch 也这么麻烦

```
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
```



### conda 安装 tree

```
conda install -c conda-forge tree -y

# 通过这个指令验证
which tree

# 如果要打印一个 folder 下的两层目录结构，用这个
tree -L 2 <folder>

# 只想看目录，不想看文件
tree -L 2 -d <folder>
```







### server load module

```
# 查看所有的 module
module avail

# 查看当前 load 了哪些 module
module list

module avail cuda
module avail conda
```





### slurm 查看空闲节点

```bash
sinfo -S+P -o "%18P %8a %20F"
```

输出

```bash
PARTITION          AVAIL    NODES(A/I/O/T)
gg                 up       185/59/7/251
gh                 up       404/89/59/552
gh-dev*            up       2/22/0/24
```

（A=Alloc、I=Idle、O=Other、T=Total）



### Vscode Tunnel

安装 https://code.visualstudio.com/docs/remote/tunnels 

```
curl -Lk 'https://code.visualstudio.com/sha/download?build=stable&os=cli-alpine-x64' --output vscode_cli.tar.gz

tar -xf vscode_cli.tar.gz
```

这个似乎必须要在计算节点才能开，在 login 节点不行

其实我已经安装好了，可执行文件在 workspace 下边，每次只需要到 `~/workspace` 下边跑一下

```bash
code tunnel 
```

就行了



tourble shooting 

遇到了这个报错

```
[2025-10-27 15:10:28] warn error access singleton, retrying: the process holding the singleton lock file (pid=3659417) exited
[2025-10-27 15:10:30] warn error access singleton, retrying: the process holding the singleton lock file (pid=3659417) exited
```

这个是上一次 code tunnel 的锁还没有拿掉

只需要 run 这个指令

```
rm -rf ~/.vscode/cli/tunnel-stable.lock
```

reference link

https://github.com/microsoft/vscode-remote-release/issues/9806#issuecomment-2135635511 



如果要重新登陆的话

```
code tunnel user logout
```



### bashrc setup

通过这个可以重置为经典的 bash 命令行前缀

```bash
# setup bash like terminal
export PS1='\u@\h:\w\$ '

# add code tunnel code to system path
export PATH="$PATH:$HOME/workspace"

# setup useful command
alias ll='ls -la'

alias si='sinfo -S+P -o "%18P %8a %20F"'
alias sq="squeue -u $USER"

alias code="/home1/10922/zhsha/workspace/code"
alias grp="cd /scratch/10922/zhsha/workspace/rotation-project"

alias ll="ls -la"

alias tl="tmux ls"

tn() {
  if [ -n "$1" ]; then
    tmux new -s "$1"
  else
    tmux new
  fi
}


```

然后放到 `~/.bashrc` 里边就行了



### setup 软连接

```bash
# run under ~/ folder
ln -s /scratch/10922/zhsha/.cache .cache
ln -s /scratch/10922/zhsha/miniconda3 miniconda3
```















