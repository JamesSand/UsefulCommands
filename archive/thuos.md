记录一下我在 thu os 上踩的坑

ch6 的代码一开始不知道为什么编译一直不通过，调了两天

最后是卸掉重装解决了问题，虽然我到现在也不知道是为什么导致的

重装的话除了要重新 clone tsinghua git 上的仓库，还需要 clone 一份测例，需要使用下边的代码
```bash
git clone https://github.com/LearningOS/uCore-Tutorial-Test-2025S.git user
```

每次切换一个分支之后，都需要彻底 clean，以防不同分支之间的东西互相干扰

```bash
make clean
make user clean
```

