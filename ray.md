## Ray

ray debug, 参考 verl 的文档 https://verl.readthedocs.io/en/latest/start/ray_debug_tutorial.html 

我用里边的 vscode 调通了，需要安装扩展 `Ray Distributed Debugger`。直接在 ray 里边加 breakpoint 就行，需要 export 一个环境变量
```bash
export RAY_DEBUG_POST_MORTEM=1
```

注意在 `Ray Distributed Debugger` 的路径要设置成项目路径，否则会找不到 debug 对应的文件





