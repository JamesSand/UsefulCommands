
## Pip install 设置 Proxy

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
