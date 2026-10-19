# CI 日志

## 脱敏

GitHub Actions 会尝试在日志中遮蔽已登记 secret 的原值。把原值赋给 shell 变量不会仅凭这一步绕过遮蔽；风险来自编码、截断、拼接或其他变换，因为派生值可能不再与已登记值匹配。

```bash
# 原值通常仍会被遮蔽，但没有必要输出它
token="${{ secrets.TOKEN }}"
echo "token is $token"

# 更安全：只在消费位置传入，不主动写日志
curl -H "Authorization: Bearer ${{ secrets.TOKEN }}" https://example.com
```

确实要输出或传递派生值时，在它第一次可能进入日志之前手动打码：

```bash
derived="$(printf '%s' "${{ secrets.TOKEN }}" | base64)"
echo "::add-mask::$derived"
echo "$derived"
```

`add-mask` 只对之后输出的行生效；必须在派生值出现之前执行。

## 压缩体积

```bash
curl -s -o /dev/null -w "%{http_code}\n" "$URL"
grep "ERROR" logs/production.log | head -20
some-command > /dev/null 2>&1
```

只在失败时输出完整日志，平时只留关键行：

```bash
if ! ./run.sh > build.log 2>&1; then
  tail -200 build.log
  exit 1
fi
```

`tail` 而不是 `cat`：几百 MB 的日志会让网页卡死，也会让真正的错误滚出视野。

## 高亮

```bash
echo "::error file=src/main.py,line=42::unexpected token"
echo "::warning::cache miss, rebuilding"
echo "::notice::using fallback mirror"
```

`file=` / `line=` 会让错误在 PR 的 diff 里可点击跳转。信息里不要带换行，换行会截断注解。

## 分组

```bash
echo "::group::build"
./scripts/build.sh
echo "::endgroup::"
```

长步骤默认展开时会把后面所有内容推走。group 之后默认折叠，失败时用户再点开。

## 输出到 job summary

需要长期保留的结果（测试统计、性能对比）写到 `$GITHUB_STEP_SUMMARY`，比埋在日志里更容易找到：

```bash
{
  echo "## Test summary"
  echo "| suite | passed | failed |"
  echo "| --- | --- | --- |"
  echo "| unit | ${PASSED} | ${FAILED} |"
} >> "$GITHUB_STEP_SUMMARY"
```
