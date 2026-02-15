
### installation

这里是用 conda + uv 安装的

```
conda create -n gpt-dlm python=3.12 -y
conda activate gpt-dlm
pip install --upgrade uv
uv pip install vllm --torch-backend=auto

```



