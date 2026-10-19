# CHANGELOG

## 文件底部：版本链接

每个 version tag 在文件底部给出 GitHub 链接：

```markdown
[v1.2.0]: https://github.com/OWNER/REPO/releases/tag/v1.2.0
```

最新版本放顶部还是底部都可以，但整个文件只用一种顺序。

## Earlier History

早期提交没有 tag 时，把这段 git log 收进二级标题 `Earlier History`，不要为它编造版本号。

## 版本标签不一致

如果某条 commit message 声称的版本与实际 tag 不符：

1. 先与作者确认是笔误，还是当时的评估偏差。
2. 确认是评估偏差时，在 `Historical version-label note` 二级标题下解释当时的判断。
3. 不要改写历史条目，也不要悄悄把版本号改掉。

## 已发布版本不可修改

已经发布的版本小节内容不再改动。后来发现描述有误时，在新版本里说明，或记入 `Historical version-label note`。

## 未发布的改动

工作区中未提交的改动属于"下一代版本"，写进 `## [Unreleased]`，不要塞进已发布的版本小节。发布日期未知时不要预填日期。

## 语气

- 条目描述"做了什么、影响谁"，不写营销语。
- 破坏性变更单独分组，并给出迁移方法。
- 分类用 Added / Changed / Fixed / Removed / Security，顺序固定。
