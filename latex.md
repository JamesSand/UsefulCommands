### Linux 上装 latex 渲染器

```
sudo apt update
sudo apt install texlive-full
sudo apt-get install texlive-pictures texlive-science texlive-latex-extra latexmk
```

上边是安装指令

> 组里的 postdoc 哥帮忙装的，他太牛了

### 测试 latex 好不好使

```
touch test.tex
vim test.tex
```

粘贴这个进去

```
\documentclass{article}
\begin{document}
Hello, LaTeX!
\end{document}
```

最后编译一下

```
pdflatex test.tex
```











