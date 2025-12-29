### Ray debug

ray debug, 参考 verl 的文档 https://verl.readthedocs.io/en/latest/start/ray_debug_tutorial.html 

我用里边的 vscode 调通了，需要安装扩展 `Ray Distributed Debugger`。直接在 ray 里边加 breakpoint 就行，需要 export 一个环境变量
```bash
export RAY_DEBUG_POST_MORTEM=1
```

注意在 `Ray Distributed Debugger` 的路径要设置成项目路径，否则会找不到 debug 对应的文件

vscode debugger 真好用，可以直接在 debug console 里边输入跟 terminal 一样的指令，而且还能自动补全



### Raylet filesystem full

```
(raylet) [2025-10-20 01:48:15,818 E 998594 998629] (raylet) file_system_monitor.cc:116: /tmp/ray/session_2025-10-20_01-47-33_454343_990302 is over 95% full, available space: 77.5226 GB; capacity: 1874.72 GB. Object creation will fail if spilling is required.
```

出现这个情况说明 file system 满了，可以给 ray 指定一个 temp dir

```bash
# setup ray temp dir
export TMPDIR="/ssd2/zhizhou/workspace/ray_temp"
```





### Raylet IO Error

如果遇到了这个奇怪的报错

```
[2025-10-11 16:10:27,420 E 2592010 2592010] core_worker_process.cc:223: Failed to register worker to Raylet: IOError: Failed to read data from the socket: End of file worker_id=01000000ffffffffffffffffffffffffffffffffffffffffffffffff
```

一般来说这是在 2.50.0 version 的 ray 会有这个报错，需要把 ray 降级到 2.49.2

```bash
pip install ray==2.49.2
```



