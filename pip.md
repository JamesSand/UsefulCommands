
## Pip install 设置 Proxy

```bash
pip install -r .\requirements.txt --proxy="http://127.0.0.1:7890"
```

如果遇到了 setuptools 不行，导致不能 install package 的话，用以下这个命令升级 setuptools

```bash
python -m pip install --upgrade pip setuptools --proxy="http://127.0.0.1:7890"
```
