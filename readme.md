# Useful Commands

> By JamesSand


## Tmux
enable mouse in tmux

put the following in `~/.tmux.conf`
``` bash
set -g mouse on
```

## Autodl

``` bash
# Enable vpn
source /etc/network_turbo
# Disable vpn
unset http_proxy && unset https_proxy
```

## Pip

install a package with proxy

``` bash
pip install nbsphinx --proxy=http://127.0.0.1:7890
```

install packages in requirements.txt with proxy

``` bash
pip install -r requirements.txt --proxy=http://127.0.0.1:7890
```

pip clean cache
``` bash
pip cache purge
```

## Conda

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

