

## Conda

要在好几个 server 上装 miniconda，记一下指令
https://www.anaconda.com/docs/getting-started/miniconda/install#linux-2 
```bash
mkdir -p ~/miniconda3
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda3/miniconda.sh
bash ~/miniconda3/miniconda.sh -b -u -p ~/miniconda3
rm ~/miniconda3/miniconda.sh

source ~/miniconda3/bin/activate

conda init --all
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

