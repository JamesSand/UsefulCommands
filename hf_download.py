from huggingface_hub import snapshot_download
local_dir = snapshot_download(
    repo_id="Qwen/Qwen2.5-0.5B-Instruct",
    local_dir="/ssd2/zhizhou/workspace/verl/models/Qwen2.5-0.5B-Instruct",
    local_dir_use_symlinks=False
)
print("model saved to:", local_dir)



