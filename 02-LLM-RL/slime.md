### slime

thudm 依旧伟大

#### docker 启动

```bash
# 拉取最新镜像
docker pull slimerl/slime:latest

# 启动容器 有目录挂载版本的
docker run --privileged --gpus all --ipc=host --shm-size=16g \
  --ulimit memlock=-1 --ulimit stack=67108864 \
  -v /ssd2/zhizhou/workspace/rotation-project/slime:/root/slime \
  -v /ssd2/zhizhou/workspace/rotation-project/shared_folder:/root/shared_folder \
  -v /ssd2/zhizhou/tmp:/tmp \
  -v ~/.tmux.conf:/root/.tmux.conf \
  --name slime_zhizhou \
  -itd slimerl/slime:latest /bin/bash
  
 # 每次连接到正在运行的容器
docker exec -it slime_zhizhou bash

# 删除这个 docker 
docker rm -f slime_zhizhou

```



#### 终端用户名调颜色

```
export PS1="\[\e[32m\]\u@vita2\[\e[0m\]:\[\e[38;5;39m\]\w\[\e[0m\]\$ "
```





#### docker instance 更新环境之后，怎么保存到 image 里边并且迁移到另一个服务器上

需要给现在的 docker commit 一下，然后保存成 tar 传给别的 server

不要关闭 docker ，直接在宿主机上运行

```
docker commit slime_zhizhou slimerl/slime:szz

# 查看现在的所有镜像
docker images
```



传输镜像到别的机器上

```
docker save slimerl/slime:szz | gzip > slime_szz.tar.gz

scp slime_szz.tar.gz root@目标机器IP:/root/

zcat /root/slime_szz.tar.gz | docker load
```



传输到 docker hub 上边

```
# 首先要改 docker 的 name
docker tag slimerl/slime:szz slimerl/slime:szz-rl

# 删除旧标签
docker rmi slimerl/slime:szz

docker tag slimerl/slime:szz-rl jamessand42/slime:szz-rl

docker push jamessand42/slime:szz-rl

docker pull jamessand42/slime:szz-rl
```







#### slime 基础测试

```bash
# 下载模型权重 (GLM-Z1-9B)
hf download Qwen/Qwen3-0.6B --local-dir /root/shared_folder/Qwen3-0.6B

hf download unsloth/Llama-3.2-3B-Instruct --local-dir /root/shared_folder/Llama-3.2-3B-Instruct

# 下载训练数据集 (dapo-math-17k)
hf download --repo-type dataset zhuzilin/dapo-math-17k \
  --local-dir /root/shared_folder

# 下载评估数据集 (aime-2024)
hf download --repo-type dataset zhuzilin/aime-2024 \
  --local-dir /root/shared_folder/aime-2024
```



```bash
cd /root/slime
source scripts/models/qwen3-0.6B.sh
```



```bash
PYTHONPATH=/root/Megatron-LM python tools/convert_hf_to_torch_dist.py \
    ${MODEL_ARGS[@]} \
    --hf-checkpoint $hf_folder/GLM-Z1-9B-0414 \
    --save $hf_folder/GLM-Z1-9B-0414_torch_dist
```



#### search R1 的 slime 实现

https://thudm.github.io/slime/zh/_examples_synced/search-r1/README.html 





检查当前 8000 端口的占用

```
lsof -i :8000
```







#### 基本概念

- world size 总共多少张卡
- global rank 全局的编号，对于每个 gpu 唯一
- local rank 本机的 gpu 编号 0-7











