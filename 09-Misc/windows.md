### 卓越性能模式

参考 tacc md


### WSL

在我的电脑上安装 wsl 的时候一直遇到这个报错

```
Installing, this may take a few minutes...
WslRegisterDistribution failed with error: 0x8000000d
Error: 0x8000000d ???????????

Press any key to continue...
```

https://github.com/microsoft/WSL/issues/4084#issuecomment-1790653610

这个 solution 能够帮我解决

```
wsl --list --all
wsl --unregister <distro name>
```

问题在于我用 windows 命令行安装了一个，然后又在 microsoft store 里安装了一个，这两个是冲突的。所以必须要把 windows 的卸载了之后再用 microsoft 的装一遍就成功了


### 执行的路径

windows 下边没有 `which` 这个指令。有的只是

```
gcm python
```

是 Get-Command 的缩写



