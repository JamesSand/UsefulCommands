
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
git config --global http.proxy 'socks5://127.0.0.1:1080'
git config --global https.proxy 'socks5://127.0.0.1:1080'
## 取消
git config --global --unset http.proxy
git config --global --unset https.proxy
```

更换远程 origin 仓库 url

```bash
git remote set-url origin https://github.com/username/repo.git
```

如果 git 远程仓库有很多 branches，想要一下子全部拉去 branch，一般可以使用 

```bash
git fetch origin
```

这部分可以参考[清华贵系的 OS 课程里边相关的内容](https://learningos.cn/uCore-Tutorial-Guide-2025S/chapter4/0intro.html#github)


