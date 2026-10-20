# 分支、提交与测试规划

根据实际 diff 和仓库已有约定给出建议。说明使用中文，推荐的 branch 名和 commit message
使用英语。默认不创建分支、不 staging、不 commit。

## 仓库约定

没有更具体的仓库约定时使用：

```text
feature/<your-feature-name>
fix/<issue-description>
docs/<update>
<type>(<scope>): <subject>
```

type 使用 `feat`、`fix`、`docs`、`refactor`、`perf`、`test` 或 `chore`，scope 取稳定的模块或
skill 名称。

---

## 输出要求

建议至少包含：

1. branch 名及选择理由。
2. 按顺序排列的 commit 英语 message、包含范围和分组理由。
3. 仓库已有的 smoke test 和与改动相关的检查；如果没有定义 smoke test，明确说明。

建议让每个 commit 可以独立审查和回退。实现、对应测试与直接相关文档通常放在同一批；生成文件
和 lockfile 通常与其来源同批。如果发现缓存、环境目录、构建产物或凭据，应单独警告。确有必要
拆分同一文件时，可建议使用 `git add -p`。
