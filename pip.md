

### pip 里边怎么装 uv

这个不是正规安装 uv 的办法。uv 也可以做环境管理器，所以正常的 uv 使用要参考 `uv.md` 



原来只需要 

```
pip install uv
```

就可以了



### pip install -e ./"[gui,rag,code_interpreter,mcp]"

看不懂这些是什么意思

TODO: 这个搞了一半没搞完



### conda 的 pip 用的是根目录下的 pip 怎么办

pip 的问题真的是千奇百怪。这个应该是 codex 乱改我的 init file，搞出问题了

我在 conda env 里边，无论怎么 which pip 用的都是 local 目录下的 pip，实际上我想要的 pip 是 conda  env 里边的 pip

在 CSDN 上找到了老哥的解答

https://blog.csdn.net/weixin_41712499/article/details/105430471 



### Pip install 设置 Proxy

我的电脑上开了梯子之后会遇到 pip 不能 install 的问题，通过如下指令配置代理可以解决
```bash
pip install -r requirements.txt --proxy="http://127.0.0.1:7890"
```

如果遇到了 setuptools 不行，导致不能 install package 的话，用以下这个命令升级 setuptools

```bash
python -m pip install --upgrade pip setuptools --proxy="http://127.0.0.1:7890"
```

pip clean cache
``` bash
pip cache purge
```
