# Skill Evals

## 用例范围

`cases.yaml` 为每个 skill 保存 direct、indirect、incomplete、negative 和 edge 五类请求，以及预期的
触发结果和关键行为。

---

## CI 检查

`scripts/validate_skill_evals.py` 只检查用例数据合法、skill 名存在和类别覆盖完整。它不调用模型，也不
证明 skill 在真实对话中会正确触发或执行。

---

## 行为验证

重大 description、路由或安全规则变更后，使用隔离工作区逐条运行相关用例，记录实际触发的 skill、
生成或修改的文件、执行的验证和偏差。评估时不给执行者预期答案之外的修复提示，避免把结论泄露给
被测流程。
