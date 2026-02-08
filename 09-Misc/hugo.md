
hugo 是一个 blog 网站，但是目前我已经弃用了

Install Hugo

using winget. Official quick start [link](https://gohugo.io/installation/windows/)

```
# install
winget install Hugo.Hugo.Extended

# uninstall
winget uninstall --name "Hugo (Extended)"
```

我猜制定 hugo theme 应该要这么做

```
# download theme as git submodule
git submodule add https://github.com/adityatelange/hugo-PaperMod.git themes/PaperMod

# add to toml, if already have, need to change
echo "theme = 'PaperMod'" >> hugo.toml
```

launch hugo
```
hugo serve

# if want to include draft, use
hugo serve -D
```








