

### 没有 sudo



```bash
# 没有 sudo 怎么用 conda 安装 npm
conda install -c conda-forge nodejs=20 -y
npm install -g @openai/codex
# 没有 sudo 怎么安装 git lfs
conda install -c conda-forge git-lfs -y
```

### 安装 Conda

要在好几个 server 上装 miniconda，记一下指令
https://www.anaconda.com/docs/getting-started/miniconda/install#linux-2 
```bash
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
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

