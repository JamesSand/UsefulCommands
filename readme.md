# Useful Commands

> By JamesSand



```bash
python examples/data_preprocess/test_gsm8k.py
python examples/data_preprocess/test_math500.py
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

