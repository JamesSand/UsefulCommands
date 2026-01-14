import os
from huggingface_hub import HfApi

# get your token here
# https://huggingface.co/settings/tokens

local_folder = "/fast/sliu/zhizhou/workspace/rotation-project/shared_folder/fsdp_converted/llama-muon-muonlr1e-4-spectral_norm-muonadamlr1e-6-20260110_005142-global_step_200"

basename = os.path.basename(local_folder)

api = HfApi(token=os.getenv("HF_TOKEN"))

repo_id = f"JameSand/{basename}"

api.create_repo(
    repo_id=repo_id,
    repo_type="model",
    private=False,   # 按需：True/False
    exist_ok=True   # 关键：已存在就跳过
)


api.upload_folder(
    folder_path=local_folder,
    repo_id=repo_id,
    repo_type="model",
)



