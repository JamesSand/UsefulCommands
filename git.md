### 从一个分支给另一个分支挪文件夹

假设从 dev 的文件夹要移动到 main

```
git checkout main

git checkout dev -- my-folder/
```



### git submodule

给 git 仓库添加 submodule

```bash
git submodule add https://github.com/JamesSand/trl-test trl-test
# 添加指定的分支
git submodule add -b master https://github.com/JamesSand/trl-test trl-test

# 更新所有submodule ，让他们是最新的提交
git submodule update --remote --recursive
```





### 强行拉去远端仓库到本地

```
git fetch origin
git reset --hard origin/verl_new
```



### install git lfs

由于没有 server 的 sudo 权限，没法用 apt install git lfs。找到了一个用 conda install 的方法

```bash
conda install -c conda-forge git-lfs

# 用下边的指令可以验证
git lfs install
git lfs version
```

config global username and email
```bash
git config user.name "Zhizhou Sha"
git config --global user.email "zhizhousha@utexas.edu"
```

```bash
# 如果遇到了不能解决的问题，下边提供了一种暴力的解决方法
git push origin main --force
git reset --hard origin/main
```

setup proxy for git

```bash
# 设置http and https:
git config --global http.proxy http://127.0.0.1:7890
git config --global https.proxy https://127.0.0.1:7890
# 设置socks:
git config --global http.proxy 'socks5://127.0.0.1:7890'
git config --global https.proxy 'socks5://127.0.0.1:7890'
## 取消
git config --global --unset http.proxy
git config --global --unset https.proxy
```

更换远程 origin 仓库 url

```bash
git remote set-url origin https://github.com/username/repo.git
```

如果 git 远程仓库有很多 branches，想要一下子全部拉取 branch，一般可以使用 

```bash
git fetch origin
```

这部分可以参考[清华贵系的 OS 课程里边相关的内容](https://learningos.cn/uCore-Tutorial-Guide-2025S/chapter4/0intro.html#github)

### 只想 clone git repo 里边的某一个文件夹怎么办

```bash
# depth 1 表示只拉取最新的一次 commit
# filter blob none 表示只拉取元数据
# sparse 表示启用 sparse checkout 模式
git clone --depth 1 --filter=blob:none --sparse git@github.com:PKUanonym/REKCARC-TSC-UHT.git

cd <your repo>

git sparse-checkout set 大三下/数值分析/exam
```

