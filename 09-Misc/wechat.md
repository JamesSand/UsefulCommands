关于如何从微信里边提取聊天数据出来

保存微信历史版本的仓库

https://github.com/cscnk52/wechat-windows-versions/releases?page=2 

现在 wechatmsg 只适配到了 4.0 版本的。适配的方法是 decrypt sql 的 key 但是这涉及到内存布局



4.0.3.11 的版本是可以的



### 运行记录

首先运行

```
python .\example\1-decrypt.py
```

解锁数据库



第二步是导出所有联系人

```
python .\example\2-contact.py --db_dir ./wxid_lvoshukxr2ya32/db_storage
```



第三步是 export 指定联系人的 data


跟着教程一步一步来就行了


最后实现的效果，能够把微信记录导出。如果导出成 html 的话，可以显示表情包和一些小红书 link 的预览。

总的来说其实是把微信数据库解密了。













