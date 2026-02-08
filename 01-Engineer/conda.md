

### conda install 和 pip install 的区别

这个 blog 总结的很全面

https://blog.csdn.net/whc18858/article/details/127135973 

[支持语言]：

- pip 是 python 官方推荐的包下载工具，但是只能安装python包

- conda 是一个跨平台（支持linux, mac, win）的通用包和环境管理器，它除了支持python外，还能安装各种其他语言的包，例如 C/C++, R语言等

[Repo源]：

- pip 从PyPI（Python Package Index）上拉取数据。上面的数据更新更及时，涵盖的内容也更加全面
- conda 从 Anaconda.org 上拉取数据。虽然Anaconda上有一些主流Python包，但在数量级上明显少于PyPI，缺少一些小众的包

[包的内容]：

- pip 里的软件包为wheel版或源代码发行版。wheel属于已编译发新版的一种，下载好后可以直接使用；而源代码发行版必须要经过编译生成可执行程序后才能使用，编译的过程是在用户的机子上进行的
- conda 里的软件包都是二进制文件，下载后即可使用，不需要经过编译

[环境隔离]：

- pip 没有内置支持环境隔离，只能借助其他工具例如virtualenv or venv实现环境隔离
conda 有能力直接创建隔离的环境

[依赖关系]：

- pip安装包时，尽管也对当前包的依赖做检查，但是并不保证当前环境的所有包的所有依赖关系都同时满足。当某个环境所安装的包越来越多，产生冲突的可能性就越来越大。
- conda会检查当前环境下所有包之间的依赖关系，保证当前环境里的所有包的所有依赖都会被满足

[库的储存位置]：

- 在conda虚拟环境下使用 pip install 安装的库： 如果使用系统的的python，则库会被保存在 ~/.local/lib/python3.x/site-packages 文件夹中；如果使用的是conda内置的python，则会被保存到 anaconda3/envs/current_env/lib/site-packages中
- conda install 安装的库都会放在anaconda3/pkgs目录下。这样的好处就是，当在某个环境下已经下载好了某个库，再在另一个环境中还需要这个库时，就可以直接从pkgs目录下将该库复制至新环境而`不用重复下载`






### 没有 sudo

```bash
# 没有 sudo 怎么用 conda 安装 npm
conda install -c conda-forge nodejs=20 -y
npm install -g @openai/codex
# 没有 sudo 怎么安装 git lfs
conda install -c conda-forge git-lfs -y
```

### 退出 conda

当我在用 uv 的时候，会需要 deactivate conda

```
conda deactivate
```





### 安装 Conda

首先第一步要了解自己的机器是什么架构的

```bash
uname -m
```



https://www.anaconda.com/docs/getting-started/miniconda/install#linux-2 

```bash
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
# 如果是 arch64 的
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-aarch64.sh
```



conda clean cache
``` bash
conda clean -a
```

conda create env

```bash
conda create -n <env_name> python=3.10
```

conda delete environment
``` bash
conda env remove -n <env_name>
```





