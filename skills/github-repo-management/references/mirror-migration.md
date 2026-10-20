# Mirror 迁移

## 基本流程

```bash
git clone --mirror <source-url> repo.git
cd repo.git
git remote -v
git remote set-url origin <target-url>
git push --mirror origin
```

建议使用空目标仓库。如果目标仓库非空，必须先确认 `push --mirror` 对现有 refs 的影响。
`git clone --mirror` 创建 bare repository 是预期行为。

---

## 不会迁移的内容

`git push --mirror` 只同步 git refs。以下内容需要单独处理：

- issues、PR、discussions、releases、wiki、projects
- branch protection/rulesets、collaborators/teams、secrets、variables、Actions history
- GitHub Pages、packages、webhooks、deploy keys
- forks、stars、watchers
- 如果仓库使用 Git LFS，还需要迁移并验证 LFS 对象

---

## 注意事项

- `git push --mirror` 会推送所有 refs，并可能删除目标端已有 refs。只有明确影响后才能执行。
- 迁移第三方仓库前核对许可证和 attribution；改 private 不等于取得版权或再分发权。
- 推送后按需恢复默认分支、visibility、About/topics、branch protection、secrets 和 Actions 权限。
- 迁移完成后建议做一次全新 clone，确认分支、tag、子模块和大文件能正常检出。
