---
name: frontend-quality
description: 编写或审查 HTML/CSS 界面时使用，包括收敛设计取值、用截图确认真实渲染效果、检查可访问性与浏览器兼容性。适用于静态页面和小型前端；不涉及组件库 API 设计或前端框架选型。
metadata:
  short-description: 界面取值收敛、渲染验证与可访问性
---

# 前端界面

## 源码

- 压缩后的 CSS 是合法代码，但不能作为唯一源码。至少保留一份可编辑的源文件，产物另存并能在构建时重新生成。
- 圆角、间距、字号、阴影、颜色收敛成一组 CSS 变量。新增取值前先确认现有 token 不够用。
- 用 [scripts/audit-css-values.sh](scripts/audit-css-values.sh) 统计现有取值分布，把低频值作为人工审查线索；有明确语义或组件约束的值可以保留。
- 新增 `!important` 前先排查层叠顺序、作用域和第三方样式边界。覆盖不可控的内联样式或外部组件时，`!important` 可能是合理的局部选择。

## 渲染验证

不要靠脑补判断布局。启动本地服务后截图：

```bash
python3 -m http.server 8000 --directory ./dist &
"<skill-dir>/scripts/screenshot.sh" http://localhost:8000 1440x900 out/desktop.png
"<skill-dir>/scripts/screenshot.sh" http://localhost:8000 390x844 out/mobile.png
```

- 根据目标设备至少检查一个代表性宽屏和窄屏尺寸；存在明确断点时覆盖断点两侧。
- 截图后实际打开图片检查：溢出、遮挡、文字被截断、字号过小、对比度不足。
- 静态截图覆盖不到 hover、focus、disabled 等状态，需要单独检查对应 CSS 规则。
- 暗色模式单独截一轮，不要假设反色即可用。

## 可访问性

- 正文与背景对比度达到 WCAG AA（4.5:1），大字号 3:1。
- 所有可交互元素可键盘聚焦，`:focus-visible` 有可见样式；不要全局 `outline: none`。
- 图片有 `alt`；纯装饰图用 `alt=""` 而不是省略属性。
- 不用颜色单独传递状态。错误、成功同时给出文字或图标。
- 表单控件有可关联的 `<label>`，不要只靠 placeholder。

## 兼容性

- 使用特性前查 caniuse，确认目标浏览器范围。
- 需要兼容旧浏览器时用 `@supports` 给回退样式，不要静默降级成错乱的布局。
- 避免依赖单一引擎的实现细节（例如只在 Chromium 生效的滚动条样式）。
