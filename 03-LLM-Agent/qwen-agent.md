### qwen-agent

现在换到 vita2 上开发了。



启动 vllm backend 的 args

```
vllm serve Qwen/Qwen3-8B --port 8000 --max-model-len 40960 --reasoning-parser qwen3
```

这个 enable reasoning 不知道是不是能加，这是原始的启动指令

```
vllm serve Qwen/Qwen3-8B --port 8000 --max-model-len 40960 --enable-reasoning --reasoning-parser qwen3
```





qwen agent 安装

```
git clone https://github.com/QwenLM/Qwen-Agent.git
cd Qwen-Agent
pip install -e ./"[gui,rag,code_interpreter,mcp]"
# 或者，使用 `pip install -e ./` 安装最小依赖。
```







