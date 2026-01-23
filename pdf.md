



windows 上百年安装这个就能进行 pdf 压缩

https://www.ghostscript.com/releases/gsdnld.html 

这个是 pdf 压缩的指令

```
gswin64c -sDEVICE=pdfwrite -o I20-out.pdf -dCompatibilityLevel='1.4' -dNOPAUSE -dQUIET -dBATCH  I20.pdf


gswin64c -sDEVICE=pdfwrite -o visa-stampe-20260108-out.pdf -dCompatibilityLevel='1.4' -dNOPAUSE -dQUIET -dBATCH  visa-stampe-20260108.pdf

gswin64c -sDEVICE=pdfwrite -o visa-photo-out.pdf -dCompatibilityLevel='1.4' -dNOPAUSE -dQUIET -dBATCH  visa-photo.pdf
```



这个是 pdf merge 的指令

```
gswin64c -dNOPAUSE -sDEVICE=pdfwrite -sOUTPUTFILE="combine.pdf" -sPAPERSIZE=letter -dBATCH visa-photo-out.pdf F1-visa-out.pdf I20-out.pdf I94-20260108.pdf visa-stampe-20260108-out.pdf
```

