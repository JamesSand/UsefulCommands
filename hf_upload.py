import os
from huggingface_hub import HfApi

# get your token here
# https://huggingface.co/settings/tokens

local_folder = "/ssd2/zhizhou/workspace/Lucky_RL/fsdp_merged/llama-step200-fp32"

api = HfApi(token=os.getenv("HF_TOKEN"))
api.upload_folder(
    folder_path=local_folder,
    repo_id="JameSand/Llama-FP32-math-step200",
    repo_type="model",
)




