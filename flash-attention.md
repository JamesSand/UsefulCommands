### flash attention 安装

> 直接去问 Gemini，它比我擅长多了



比如说要用 no build isolation 的格式安装

```
pip install flash-attn==2.7.4.post1 --no-build-isolation
```

就是说在 build wheel 的时候不是用的单独的隔离环境，而是直接在 python 现在的环境里边安装



要装一些 support 的包

```
psutil numpy
```



要手动把 prebuild 的 whl 下载下来，然后安装

```
wget wget https://github.com/Dao-AILab/flash-attention/releases/download/v2.7.4.post1/flash_attn-2.7.4.post1+cu12torch2.6cxx11abiFALSE-cp312-cp312-linux_x86_64.whl

pip install ./flash_attn*.whl
```



whl 相当于是预编译好的包，不用去从头编译了，直接从 github 上拉下来就好了

所以总的来说，安装 flash attn 的时候，要开启 `--no-build-isolation` 这个参数，然后它会去 release 上找到对应的 whl，拉下来就可以直接 install









