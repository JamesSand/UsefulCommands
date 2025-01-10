
# 使用 huggingface mirror

``bash
export HF_ENDPOINT=https://hf-mirror.com
```

# 如何查看本地下载的所有 huggingface 模型

想必大家都遇到过写了一段代码，想用一个 huggingface 的模型测试一下，但是不知道本地已经下载了哪些模型

这里我们介绍一种查看本地下载过的所有 huggingface 模型的方法

```bash
# 用 huggingface cli 扫描本地下载过的所有模型
huggingface-cli scan-cache
```

如果想要删除其中的某一个模型
```bash
pip install huggingface_hub[cli]

huggingface-cli delete-cache
```
