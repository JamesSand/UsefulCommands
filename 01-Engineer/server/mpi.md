shiwei 那边的 server

### 基本信息

cisco vpn

cisco的vpn链接 vpngw.tuebingen.mpg.de
1:12
用户名是sliu
密码 7549848lsWlsW!

Zihang Liu
  凌晨 1:13
然后还需要他给一个6位验证码，每次登录都得找他要

登陆上去以后就直接
ssh sliu@login.cluster.is.localnet
就可以


vpngw.tuebingen.mpg.de



ssh sliu@login.cluster.is.localnet



sliu

7549848lsWlsW!



### 删掉 除了 100 step 和 200 step 的 ckpt

```
# 这个是真的把 checkpoints 删掉了
find . -maxdepth 1 -type d -name 'global_step_*' ! -name 'global_step_100' ! -name 'global_step_200' -exec rm -rf {} +

# 这个是一个 dry run
find . -maxdepth 1 -type d -name 'global_step_*' ! -name 'global_step_100' ! -name 'global_step_200' -exec echo {} +

# 看每个 folder 下边有多大
du -h --max-depth=1

```





### 申请节点

第零步，申请一个 cpu 节点配环境

```
condor_submit_bid 25 -i -append request_cpus=8 -append request_memory=80000
```

mpi 机器上的 conda always has problems with its lock.

So we can must use --no-lock at each conda operation

```
conda create -n slime python=3.12 pip -c conda-forge -y --no-lock
```

pip also has lots of weired problems. This is basically /tmp dir is too small

```
# 在 Lustre 上创建一个临时目录
mkdir -p /lustre/home/sliu/zhizhou/pip_cache

# 设置环境变量，让 pip 使用这个新目录
export PIP_CACHE_DIR="/lustre/home/sliu/zhizhou/pip_cache"
export TMPDIR="/lustre/home/sliu/zhizhou/pip_cache"

# 重新安装
pip install <包名>
```

第一步，申请一个计算节点

```
condor_submit_bid 25 -i \
  -append "request_gpus=2" \
  -append "request_cpus=8" \
  -append "request_memory=80000" \
  -append 'requirements = (Target.CUDADeviceName == "NVIDIA A100-SXM4-80GB")'
```



### singularity 配置 docker 的环境

1 singularity 下载 docker

```
HOME=/fast/sliu/zhizhou

# 设置构建镜像时的临时目录
export SINGULARITY_TMPDIR=${HOME}/singularity_tmp
# 设置下载层文件的缓存目录
export SINGULARITY_CACHEDIR=${HOME}/singularity_cache

singularity_sif_dir=${HOME}/sif

mkdir -p ${SINGULARITY_TMPDIR}
mkdir -p ${SINGULARITY_CACHEDIR}
mkdir -p ${singularity_sif_dir}

# 配置 verl 的 docker verlai/verl:vllm011.latest
singularity pull ${singularity_sif_dir}/verl.sif docker://verlai/verl:vllm011.latest

singularity pull ${singularity_sif_dir}/slime_szz_rl_muon.sif docker://jamessand42/slime:szz-rl-muon


# 将脚本转换为可写入的 sandbox 模式
# 将只读的 sif 转换成可写的文件夹目录 (Sandbox)
singularity build --sandbox slime_zhizhou_rl_muon/ slime_szz_rl_muon.sif

```



2 singularity 运行 docker

```
# --nv 代表调用 GPU
singularity shell --nv /fast/sliu/zhizhou/sif/slime_szz_rl_muon.sif

# 使用 verl 的 image
singularity shell --nv /fast/sliu/zhizhou/sif/verl.sif

# 交互式进入
singularity shell --nv --writable slime_zhizhou_rl_muon/

# 进入后，你可以直接修改环境
# 如果普通 pip install 报错，尝试：
pip install --user <package_name> 
# 或者直接：
pip install <package_name>

```



3 singularity 后台运行 docker

```bash
# 启动后台实例 (注意必须指向文件夹并加 --writable)
singularity instance start --nv --writable slime_zhizhou_rl_muon/ slime_zhizhou

# 随时进入查看
singularity shell instance://slime_zhizhou

# 停止后台实例
singularity instance stop slime_zhizhou

```





4 singularity 检查现在正在运行的 ，以及所有可用的 images

```
# inspect all running instance
singularity instance list

# check all available images
ls *.sif
```

5 打包提交到 dockerhub 上边去

```
# 1. 将修改后的文件夹重新打包成一个新的 .sif 文件
singularity build updated_slime.sif slime_zhizhou_rl_muon/

# 2. 登录 Docker Hub (只需登录一次)
singularity remote login -u <你的DockerHub用户名> docker://docker.io

# 3. 推送到 Docker Hub (Singularity 会自动处理格式转换)
singularity push updated_slime.sif docker://<你的DockerHub用户名>/<仓库名>:<新标签>
```







### 集群使用文档 Docs Notion Docs



这个是 cluster 的文档

https://atlas.is.localnet/confluence/spaces/IT/pages/172985282/Containers+in+the+cluster 



https://www.notion.so/MPI-Cluster-291446fced0580e99bf5ec8514ea5dba?source=copy_link 



### 看现在还有多少空的机器



condor_submit_bid 35 



```
condor_status -constraint 'CUDADeviceName=="NVIDIA H100"'
condor_status -constraint 'CUDADeviceName=="NVIDIA H100"' -constraint 'PartitionableSlot && Gpus > 0'

condor_status -constraint 'CUDADeviceName=="NVIDIA H100 80GB HBM3"'
condor_status -constraint 'CUDADeviceName=="NVIDIA H100 80GB HBM3"' -constraint 'PartitionableSlot && Gpus > 0'
```



### condor 交 job

```
condor_submit_bid 25 condor.sub

# 查看所有 job
condor_q sliu

# condor 链接到一个 job 上看是啥情况
condor_ssh_to_job <job id>

# condor 删除一个 job
condor_rm <job id>

# 查看一个 job 为什么起不来

# 最完整的排查方案
job_id=16773518.0

condor_q -better-analyze $job_id
condor_q -long $job_id | egrep -i 'Requirements|RequestCpus|RequestMemory|RequestDisk|RequestGpus'
condor_status -af Name State Activity GPUs Memory | head


```





### cluster quota & credit system

```
# 查看集群存储配置
cluster_quota
```

credit 要去这里查

这是 banking 的网址

https://logger.cluster.is.localnet/htcondor/banking 

查看当前账户有多少 job 在跑

```
condor_q sliu

condor_rm <job id>
```









### pip install 的时候 no space on device

```
export PIP_CACHE_DIR=/fast/sliu/pip_cache
export TMPDIR=/fast/sliu/pip_tmp
export TEMP=$TMPDIR
export TMP=$TMPDIR
mkdir -p "$PIP_CACHE_DIR" "$TMPDIR"
```



### conda OSError('Tunnel connection failed: 503 Service Unavailable')

要这样修

```
conda config --set channel_alias https://conda.anaconda.org
```



### conda no lock

集群创建conda 的时候要用

```
conda create -n <env> python=3.10 --no-lock -y
```







### best176 安装指令

```
export PIP_CACHE_DIR=/fast/sliu/pip_cache
export TMPDIR=/fast/sliu/pip_tmp
export TEMP=$TMPDIR
export TMP=$TMPDIR
mkdir -p "$PIP_CACHE_DIR" "$TMPDIR"

pip install --no-cache-dir "vllm==0.11.0"

echo "2. install basic packages"
pip install "transformers[hf_xet]>=4.51.0" accelerate datasets peft hf-transfer \
    "numpy<2.0.0" "pyarrow>=15.0.0" pandas "tensordict>=0.8.0,<=0.10.0,!=0.9.0" torchdata \
    ray[default] codetiming hydra-core pylatexenc qwen-vl-utils wandb dill pybind11 liger-kernel mathruler \
    pytest py-spy pre-commit ruff tensorboard 

echo "pyext is lack of maintainace and cannot work with python 3.12."
echo "if you need it for prime code rewarding, please install using patched fork:"
echo "pip install git+https://github.com/ShaohonChen/PyExt.git@py311support"

pip install "nvidia-ml-py>=12.560.30" "fastapi[standard]>=0.115.0" "optree>=0.13.0" "pydantic>=2.9" "grpcio>=1.62.1"

# torch version==2.8.0
flash_attn-2.8.3+cu12torch2.8cxx11abiTRUE-cp312-cp312-linux_x86_64.whl

pip install --no-cache-dir flashinfer-python==0.6.0

```





### best177 安装指令

```
conda create -n best177 python=3.10 --no-lock -y

pip install --no-cache-dir "vllm==0.8.5.post1" "torch==2.6.0" "torchvision==0.21.0" "torchaudio==2.6.0" "tensordict==0.6.2" torchdata

echo "2. install basic packages"
pip install "transformers[hf_xet]>=4.51.0" accelerate datasets peft hf-transfer \
    "numpy<2.0.0" "pyarrow>=15.0.0" pandas \
    ray[default] codetiming hydra-core pylatexenc qwen-vl-utils wandb dill pybind11 liger-kernel mathruler \
    pytest py-spy pyext pre-commit ruff tensorboard 

pip install "nvidia-ml-py>=12.560.30" "fastapi[standard]>=0.115.0" "optree>=0.13.0" "pydantic>=2.9" "grpcio>=1.62.1"



flash attention 2.8.3
https://github.com/Dao-AILab/flash-attention/releases/tag/v2.8.3 


falshinfer 0.4.0
https://github.com/flashinfer-ai/flashinfer/releases/tag/v0.4.0

```











### misc

login2 节点的网速好像贼快，可以在这个节点上装包



### backup

okok I need to cool down. 

First thing is that why sglang server is done? Try 2 GPU case if it work?

potential case
1 CPU number 尝试过了不是
2 proxy 有可能 ray instance 没有继承 no proxy 的性质 就是这个原因



sglang server 的问题



| gpu memory | concurrenct | results |
| :--------: | :---------: | :-----: |
|    0.7     |     512     |   bad   |
|    0.7     |      8      |  good   |
|   March    |    $420     |         |









1 fix sglang engine too much load error
2 llama settings
3 llama train time
4 ds setting
5 ds train time







