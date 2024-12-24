
docker run \
    -itd \
    --shm-size 32g \
    --gpus all \
    --name sglang_zhizhou \
    -v /opt/dlami/nvme/.cache:/root/.cache \
    -v /opt/dlami/nvme/zhizhou/sgl-workspace:/sgl-workspace \
    lmsysorg/sglang:latest \
    /bin/bash




