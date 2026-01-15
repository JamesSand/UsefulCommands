
## torch

torch 还是有很多可以学的

### torch device mesh

中文文档

https://docs.pytorch.ac.cn/tutorials/recipes/distributed_device_mesh.html



```python

# 没有 device mesh 的时候需要用以下复杂的实现

import os

import torch
import torch.distributed as dist

# Understand world topology
rank = int(os.environ["RANK"])
world_size = int(os.environ["WORLD_SIZE"])
print(f"Running example on {rank=} in a world with {world_size=}")

# Create process groups to manage 2-D like parallel pattern
dist.init_process_group("nccl")
torch.cuda.set_device(rank)

# 这个相当于是模型的分片，显然这里的例子是一个机器 8 张卡
# 4 卡一个 shard group，所以模型保存了两份
# Create shard groups (e.g. (0, 1, 2, 3), (4, 5, 6, 7))
# and assign the correct shard group to each rank
num_node_devices = torch.cuda.device_count()
shard_rank_lists = list(range(0, num_node_devices // 2)), list(range(num_node_devices // 2, num_node_devices))
shard_groups = (
    dist.new_group(shard_rank_lists[0]),
    dist.new_group(shard_rank_lists[1]),
)
current_shard_group = (
    shard_groups[0] if rank in shard_rank_lists[0] else shard_groups[1]
)

# 这里实际上记录了模型是怎么重复的
# Create replicate groups (for example, (0, 4), (1, 5), (2, 6), (3, 7))
# and assign the correct replicate group to each rank
current_replicate_group = None
shard_factor = len(shard_rank_lists[0])
for i in range(num_node_devices // 2):
    replicate_group_ranks = list(range(i, num_node_devices, shard_factor))
    replicate_group = dist.new_group(replicate_group_ranks)
    if rank in replicate_group_ranks:
        current_replicate_group = replicate_group

```


```python

# 用 device mesh 可以简化实现

from torch.distributed.device_mesh import init_device_mesh
mesh_2d = init_device_mesh("cuda", (2, 4), mesh_dim_names=("replicate", "shard"))

# Users can access the underlying process group thru `get_group` API.
replicate_group = mesh_2d.get_group(mesh_dim="replicate")
shard_group = mesh_2d.get_group(mesh_dim="shard")
```




```python

# 用 HSDP 的时候，device mesh 是用来初始化 FSDP 的

import torch
import torch.nn as nn

from torch.distributed.device_mesh import init_device_mesh
from torch.distributed.fsdp import fully_shard as FSDP


class ToyModel(nn.Module):
    def __init__(self):
        super(ToyModel, self).__init__()
        self.net1 = nn.Linear(10, 10)
        self.relu = nn.ReLU()
        self.net2 = nn.Linear(10, 5)

    def forward(self, x):
        return self.net2(self.relu(self.net1(x)))


# HSDP: MeshShape(2, 4)
mesh_2d = init_device_mesh("cuda", (2, 4), mesh_dim_names=("dp_replicate", "dp_shard"))
model = FSDP(
    ToyModel(), device_mesh=mesh_2d
)

```

三维情况下的 device mesh

```python

# torchrun --nproc_per_node=6 decive_mesh_test.py

from torch.distributed.device_mesh import init_device_mesh
mesh_3d = init_device_mesh("cuda", (2, 2, 2), mesh_dim_names=("replicate", "shard", "tp"))

# Users can slice child meshes from the parent mesh.
hsdp_mesh = mesh_3d["replicate", "shard"]
tp_mesh = mesh_3d["tp"]

# Users can access the underlying process group thru `get_group` API.
replicate_group = hsdp_mesh["replicate"].get_group()
shard_group = hsdp_mesh["shard"].get_group()
tp_group = tp_mesh.get_group()

```

### tp 和 fsdp 的对比

tp 相当于是把每个矩阵按照维度进行切分

fsdp 相当于是把矩阵参数展平之后做切分，算的时候 all-gather 回来。

forward 的时候的显存占用有三部分
FSDP 只节省了参数和优化器状态，但每张卡都要存储该层完整的激活值，且通常需要 prefetch 下一层参数，所以是 Current Layer + Prefetch Layer + Activations。

对于多张卡来说，fsdp 的计算是冗余的，因为每一层的参数都被打碎了，分给了所有的 GPU。计算每一层的时候，所有 GPU 都需要 all-gather 并且算一次 forward，但是最后只保存属于自己部分的参数和优化器参数。

fsdp 和 tp 的对比在于，fsdp 的通信开销更少，只需要每一层 all-gather 一次，而 tp 需要每个矩阵乘法都 all-gather 一次。


### batch size

在深度学习中，为了优化显存和计算效率，我们通常把数据分为三层：

1. Global Batch Size: 算法层面的总 Batch。比如你希望模型每一步根据 128 个样本更新梯度。
2. Local Batch Size (Mini-batch): 分配到每一张 GPU 上的样本数。如果你有 8 张卡，每张卡分到 $128 / 8 = 16$ 个样本。
3. Micro-batch: 为了防止显存爆炸，你把这 16 个样本再拆细。比如每次只算 4 个样本，算 4 次。这 4 个样本 就是一个 Micro-batch。


### Device Mesh 3D Mesh 布局推演 (2, 2, 2)
当你定义 `init_device_mesh(..., (2, 2, 2), mesh_dim_names=("replicate", "shard", "tp"))` 时，系统按 **行优先 (Row-major)** 顺序分配全局 Rank：

| replicate (dim 0) | shard (dim 1) | tp (dim 2) | **Global Rank** |
| :--- | :--- | :--- | :--- |
| 0 | 0 | 0 | **0** |
| 0 | 0 | 1 | **1** |
| 0 | 1 | 0 | **2** |
| 0 | 1 | 1 | **3** |
| 1 | 0 | 0 | **4** |
| 1 | 0 | 1 | **5** |
| 1 | 1 | 0 | **6** |
| 1 | 1 | 1 | **7** |



---

### 3. 为什么 HSDP Mesh 是 `[[0, 2], [4, 6]]`？
当执行 `hsdp_mesh = mesh_3d["replicate", "shard"]` 时，发生了以下逻辑：

1.  **降维逻辑**：切片操作会保留你指定的维度（`replicate`, `shard`），而对于未指定的维度（`tp`），它默认选取 **index 0** 处的节点。
2.  **坐标筛选**：
    * 找 `tp = 0` 的所有组合。
    * 第一行 (`replicate=0`): 找 `(0, 0, 0)` $\rightarrow$ **Rank 0** 和 `(0, 1, 0)` $\rightarrow$ **Rank 2**。
    * 第二行 (`replicate=1`): 找 `(1, 0, 0)` $\rightarrow$ **Rank 4** 和 `(1, 1, 0)` $\rightarrow$ **Rank 6**。
3.  **最终矩阵**：
    ```python
    [[0, 2],
     [4, 6]]
    ```







