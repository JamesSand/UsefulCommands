# AGENTS.md

## Git 提交信息规则（强制）

当你创建 git commit（或生成 commit message）时，必须在提交信息末尾追加 co-author trailer。

- 必须在提交信息最后一行添加且只添加这一行：
  Co-authored-by: OpenAI Codex <codex@openai.com>

格式要求：
- trailer 前必须有一个空行（即正文结束后空一行再写 trailer）。
- 如果提交信息里已经存在 `Co-authored-by:`，则不要重复添加（避免重复）。
- 不要改动人类已经写好的 trailers；只在缺失时补上 Codex 的 trailer。



