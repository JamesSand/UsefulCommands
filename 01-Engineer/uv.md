### uv install

```
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### uv usage

创建 uv 环境

```
uv venv
```

uv 的 env 都是安装在对应的 repo 目录下边的 `.venv` ，应该不用软链接到别的地方了

uv 导出环境所需要的包到 requirement txt . ref link https://github.com/astral-sh/uv/issues/6007#issuecomment-2303810114 

```
uv pip freeze > requirements.txt
```


### conda 环境下的 uv

我想这么用 uv

1. 创建一个 conda 环境
2. pip install uv

但是有的时候这样调用的 uv 仍然是全局的 uv

所以这个时候要 python -m uv sync

才能用 conda 里边的 uv

之后 run 的时候得这么 run

```python 
python -m uv run python your_script.py
```




### uv 激活环境 / 取消激活环境

每次 uv 激活环境需要这样

```
source .venv/bin/activate
```

取消激活环境只需要

```
deactivate
```

就行了，不用别的





### Trouble shooting

在用 uv 装环境的时候遇到了这个问题

```
fatal error: Python.h: No such file or directory
```

看到了一个解答，

https://stackoverflow.com/questions/21530577/fatal-error-python-h-no-such-file-or-directory 

要这么搞

```
sudo apt install python-dev   # for python2.x installs
sudo apt install python3-dev  # for python3.x installs
```

但是我没有 sudo。。。

> 真实够神奇的，这个 bug 在 conda 里边就没有