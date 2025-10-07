
from huggingface_hub import snapshot_download

model_name = "Qwen/Qwen2.5-Math-1.5B"
local_dir = f"models/{model_name}"

local_dir = snapshot_download(
    repo_id=model_name,
    local_dir=local_dir,
    local_dir_use_symlinks=False
)
print("model saved to:", local_dir)




