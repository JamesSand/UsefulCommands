

### Claude Code Permission

如果我想允许 claude code 的所有操作的，按时不允许 rm 操作，我可以这么配置文件


```json

{
  "permissions": {
    "allow": [
      "*"
    ],
    "deny": [],
    "ask": [
      "Bash(*rm *)",
      "Bash(*rmdir*)"
    ]
  }
}

```

如果想要是全局生效的话，我可以把这个文件放到

`~/.claude/settings.json` 



如果你在你的 folder 下边新从头开始执行 claude code 的话，要把上边这些东西放到 `settings.local.json` 文件里边去




### Claude Code installation

安装 claude code

```bash
# Linux
curl -fsSL https://claude.ai/install.sh | bash

# Windows powershell
irm https://claude.ai/install.ps1 | iex
```



一些基本用法，

/init 让 claude read through 这个仓库的代码

/usage 监控 token usage。claude 有每天，每周，每月的限制



### 不同 Claude 模型

Claude模型按能力分为三个层级：

1. **Haiku**（俳句）- 最快速、最经济的模型
   - 适合简单任务、快速响应场景
   - 成本最低，速度最快
2. **Sonnet**（十四行诗）- 平衡型模型
   - 在能力和速度之间取得平衡
   - 适合大多数日常任务
3. **Opus**（交响乐）- 最强大的模型
   - 处理复杂任务能力最强
   - 推理和创造能力最出色
   - 成本较高，速度相对较慢







