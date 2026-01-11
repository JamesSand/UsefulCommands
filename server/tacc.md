### 链接服务器





### TACC Command

这是两条指令，之后可能会经常用的到


sbatch -p gh -N 1 -n 1 -t 24:00:00 -A ASC25082 \
 -J tacc-vscode --parsable --wrap="sleep infinity"


申请一个 debug 计算节点

```bash
idev -p gh -N 1 -n 1 -t 24:00:00 -A ASC25082

# 底下这个能用
srun -J debug -N 1 -p gh-dev -n 28 -t 2:00:00 -A ASC25082  --pty /bin/bash
```

### TACC Docs

这是 TACC 的 docs

https://docs.google.com/document/d/1URcWe8mLQF8HMNre7vZwgk6TiRNxFxVBwK_HCcRXQdM/edit?usp=sharing 



### 安装 torch

没想到安装 torch 也这么麻烦

```
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
```



### slurm

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

# setup scratch and work folder
export SCRATCH=/scratch/10922/zhsha
export WORK=/work/10922/zhsha/vista

# add code tunnel code to system path
export PATH="$PATH:$HOME/workspace"

# setup useful command
alias ll='ls -la'
# fast change to scratch or work folder
alias cds='cd "$SCRATCH"'
alias cdw='cd "$WORK"'


```

然后放到 `~/.bashrc` 里边就行了



### setup 软连接

```bash
# run under ~/ folder
ln -s /scratch/10922/zhsha/.cache .cache
ln -s /scratch/10922/zhsha/miniconda3 miniconda3
```















