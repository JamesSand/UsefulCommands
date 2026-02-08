
## 使用 huggingface mirror

```bash

export HF_ENDPOINT=https://hf-mirror.com
```

## 如何查看本地下载的所有 huggingface 模型

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

## 如何从 huggingface 上下载一个模型到本地文件夹

我觉得直接使用 transformer，用一个 python 脚本下载是一个不错的主意

```python
from transformers import AutoModel, AutoTokenizer

# 指定模型名称和本地保存路径
model_name = "bert-base-uncased"
cache_dir = "./my_models/bert_base_uncased"

# 下载并保存模型和分词器到指定路径
model = AutoModel.from_pretrained(model_name, cache_dir=cache_dir)
tokenizer = AutoTokenizer.from_pretrained(model_name, cache_dir=cache_dir)

```
