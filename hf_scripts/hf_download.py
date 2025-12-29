
from huggingface_hub import snapshot_download

model_name = "Qwen/Qwen2.5-Math-1.5B"
local_dir = f"models/{model_name}"

local_dir = snapshot_download(
    repo_id=model_name,
    local_dir=local_dir,
    local_dir_use_symlinks=False
)
print("model saved to:", local_dir)


# download dataset
from huggingface_hub import snapshot_download

dataset_id = "Simia-Agent/Simia-Tau-SFT-90k-Hermes"
local_dir = "datasets/Simia-Tau-SFT-90k-Hermes"  # 随便起一个本地目录名

local_dir = snapshot_download(
    repo_id=dataset_id,
    repo_type="dataset",          
    local_dir=local_dir,
    local_dir_use_symlinks=False,
)
print("dataset saved to:", local_dir)



