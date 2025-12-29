
如何在 server 上下载 google drive 的数据。

比如说我有这个链接 https://drive.google.com/file/d/1o_dCMzwjaA2azbGOxAE7-4E7NbJkgdgO/view?usp=drive_link 

其中的 id 是 `1o_dCMzwjaA2azbGOxAE7-4E7NbJkgdgO`

```bash
pip install gdown

gdown 1o_dCMzwjaA2azbGOxAE7-4E7NbJkgdgO
```

创建一个用户

```bash
# 切到 root 用户
sudo su
# 新增用户，比如用户名是 abc
useradd -m abc
# 给用户 abc 设置密码
passwd abc
# 编辑 root 权限，将新增用户加入，新增一行 abc ALL=(ALL:ALL) ALL
vim /etc/sudoers

# 进入用户 abc 的界面
su abc

# 配置你的 public key，然后就可以正常登录了
```

vim 跳转到文件的最后一行
`$ + G`

也可以使用 Shift + G

vim 的查找快捷键 `/`

Cgroup 可以控制进程组的系统资源使用量


如何将命令行转成 bash
```bash
# 查看当前的 SHELL 使用的是什么
echo $SHELL
#  如果输出结果为`/bin/bash`，表示当前已经使用的是bash解释器

# 否则，输入一下命令将终端切换为 bash
chsh -s /bin/bash

# 新开一个窗口，或者用以下命令重启当前终端
exec bash
```

.cache 软连接
```bash
# 检查目录大小
cd ~
du -d 1 -h

# 移动并创建软连接
mv ~/.cache /opt/dlami/nvme/<your_account>/
ln -s /opt/dlami/nvme/<your_account>/.cache .cache
```







