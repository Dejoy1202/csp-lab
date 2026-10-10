---
name: "CSP Lab"
description: "面向长期作答的自托管 CSP 模拟考试界面"
colors:
  primary: "#2463b3"
  primary-hover: "#1d5094"
  primary-soft: "#edf3fb"
  page: "#f7f7f8"
  surface: "#ffffff"
  inset: "#f0f1f3"
  ink: "#262626"
  ink-secondary: "#61656b"
  ink-muted: "#666b73"
  border: "#e2e4e8"
  divider: "#eef0f3"
  success: "#216740"
  success-soft: "#e8f5ee"
  error: "#b33939"
  error-soft: "#fce8e8"
  warning: "#886009"
  warning-soft: "#fef6e0"
  compile-error: "#7441c5"
  dark-page: "#191a1c"
  dark-surface: "#222427"
  dark-inset: "#2c2f33"
  dark-ink: "#ececee"
  dark-ink-secondary: "#b4b8bf"
  dark-ink-muted: "#a4a9b2"
  dark-border: "#3c3f44"
  dark-divider: "#32353a"
  dark-link: "#5ba8d5"
  dark-link-hover: "#4a96c3"
  dark-link-soft: "#243246"
  dark-success: "#3da868"
  dark-success-soft: "#1a2e22"
  dark-error: "#e05555"
  dark-error-soft: "#2e1a1a"
  dark-warning: "#e8a820"
  dark-warning-soft: "#2e2a1a"
  dark-compile-error: "#b89af4"
typography:
  display:
    fontFamily: "-apple-system, BlinkMacSystemFont, \"Segoe UI\", \"PingFang SC\", \"Microsoft YaHei\", Arial, sans-serif"
    fontSize: "clamp(32px, 3.2vw, 46px)"
    fontWeight: 650
    lineHeight: 1.4
    letterSpacing: "-0.025em"
  headline:
    fontFamily: "-apple-system, BlinkMacSystemFont, \"Segoe UI\", \"PingFang SC\", \"Microsoft YaHei\", Arial, sans-serif"
    fontSize: "26px"
    fontWeight: 650
    letterSpacing: "-0.025em"
  title:
    fontFamily: "-apple-system, BlinkMacSystemFont, \"Segoe UI\", \"PingFang SC\", \"Microsoft YaHei\", Arial, sans-serif"
    fontSize: "16px"
    fontWeight: 600
  body:
    fontFamily: "-apple-system, BlinkMacSystemFont, \"Segoe UI\", \"PingFang SC\", \"Microsoft YaHei\", Arial, sans-serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.6
  statement:
    fontFamily: "-apple-system, BlinkMacSystemFont, \"Segoe UI\", \"PingFang SC\", \"Microsoft YaHei\", Arial, sans-serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.85
  label:
    fontFamily: "-apple-system, BlinkMacSystemFont, \"Segoe UI\", \"PingFang SC\", \"Microsoft YaHei\", Arial, sans-serif"
    fontSize: "14px"
    fontWeight: 500
  code:
    fontFamily: "\"Consolas\", \"Courier New\", monospace"
    fontSize: "14px"
    lineHeight: "22px"
rounded:
  control: "4px"
  action: "6px"
  panel: "8px"
  paper: "10px"
  pill: "12px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "12px"
  lg: "16px"
  panel: "20px"
  section: "24px"
  page: "32px"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.surface}"
    typography: "{typography.label}"
    rounded: "{rounded.action}"
    padding: "8px 16px"
  button-primary-hover:
    backgroundColor: "{colors.primary-hover}"
  button-secondary:
    backgroundColor: "{colors.inset}"
    textColor: "{colors.ink}"
    typography: "{typography.label}"
    rounded: "{rounded.control}"
    padding: "8px 16px"
  button-danger:
    backgroundColor: "{colors.error}"
    textColor: "{colors.surface}"
    typography: "{typography.label}"
    rounded: "{rounded.control}"
    padding: "8px 16px"
  input:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    padding: "8px 12px"
  navigation:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink-secondary}"
    height: "58px"
  readiness:
    backgroundColor: "{colors.success-soft}"
    textColor: "{colors.success}"
    rounded: "{rounded.control}"
    padding: "3px 8px"
  card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.panel}"
    padding: "20px"
  paper-row:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    padding: "24px"
  exam-tab:
    textColor: "{colors.ink-secondary}"
    rounded: "{rounded.action}"
    padding: "9px 14px"
  confirmation-dialog:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.panel}"
    width: "min(440px, calc(100vw - 32px))"
---
# Design System: CSP Lab

## Overview

**Creative North Star: "专注作答的考试桌"**

以用户确认的 LeetCode 式操作界面为参照：中性纸面与炭灰主题、系统无衬线字体、清晰边界和少量蓝色动作，服务长时间阅读与编写代码。界面的层次来自字号、留白、细分隔和状态文字，不依赖装饰动画。

同一套视觉语言覆盖登录、选卷、四小时作答与成绩复盘。题面采用本地 KaTeX 排版，代码使用本地 Monaco；主题切换不改变信息结构，也不把数学变量排成程序标识符。

**Key Characteristics:**

- 中性浅色与炭灰深色保持相同的信息层次。
- 蓝色承载操作；绿、红、黄与紫分别说明判题状态。
- 系统字体阅读题面，等宽字体编辑代码，数学公式使用 KaTeX。
- 细边框与平面容器组织信息；明确的键盘焦点保留可操作性。

这是实现后的设计记录：界面已有 44 个历史批次目录、220 个题名；201312 与 202403 两套已开放完整模拟，其余 42 套保留“建设中”状态。这是当前内容状态，不是视觉规范对未来覆盖范围的限制。

## Colors

配色以纸白、冷灰和炭灰为底，动作蓝与语义色承担信息表达。上方 frontmatter 是具体色值的规范来源；CSS 实现通过同名角色的主题变量切换。

### Primary

- **操作蓝**：主要按钮、浅色链接和轻量选中背景；对应 primary、primary-hover、primary-soft。
- **深色阅读蓝**：对应 dark-link、dark-link-hover、dark-link-soft，用于暗色界面内链接和轻量强调；主要按钮仍沿用操作蓝。

### Neutral

- **纸面与嵌入灰**：page、surface、inset 区分页面、内容面板与样例或辅助区域。
- **正文与辅助墨色**：ink、ink-secondary、ink-muted 按信息重要程度递减；不降低正文对比度来制造层次。
- **细边界**：border 用于容器和输入框，divider 用于同一容器内部的行分隔。
- **炭灰对应组**：dark-page 至 dark-divider 逐一对应上述角色，保持布局及阅读层次。

通过绿、错误红、提醒黄和编译紫属于语义状态，不作为第二套品牌色。通过和错误轻背景承载短标签；TLE、MLE、OLE 共用提醒色；CE 独立使用编译色。深色状态采用对应 dark-* 变量。

**The State With Text Rule.** 判题、建设状态与计时提醒同时给出文字；颜色与圆点辅助识别，不独立承担状态含义。

**The Action Contrast Rule.** 主要按钮始终使用独立的深蓝按钮变量与白字。深色模式只提高链接和轻量强调色亮度，不让浅蓝链接变量直接成为白字按钮底色。

## Typography

**Body Font:** 系统无衬线栈：Apple 系统字体、Segoe UI、PingFang SC、Microsoft YaHei、Arial。
**Label/Mono Font:** 代码和样例使用 Consolas，并回退 Courier New 与 monospace。
**Mathematical Font:** 本地 KaTeX 字体及其标准数学排版。

字体以清晰阅读和稳定的中英混排为目的，不引入展示字体。界面标题略重，辅助文字稍小；题面段落使用更疏朗的行距。

### Hierarchy

- **Display**：登录简介标题使用响应式展示角色；小屏另设较小标题。
- **Headline**：选卷页标题使用 headline 角色；登录表单与复盘标题为相近的 24px。
- **Title**：试卷标题及内容小标题使用 title 角色；作答题目标题桌面为 22px，小屏为 19px。
- **Body**：默认正文使用 body；题面使用 statement，更宽的行距与最多 75ch 的段落宽度。
- **Label**：按钮和登录字段使用 label；主导航为 14px，说明与辅助控件主要为 12–13px。
- **Code**：Monaco 使用 code 角色；题面样例为较小等宽字号。
- **Math**：行内公式与正文对齐；题面公式字号为正文的 1.08 倍，显示公式允许横向滚动。

题面工具提供 15、16、18、20px 阅读字号。计时、分数采用等宽数字特性，避免数字变化引起布局跳动。

**The Three Writing Systems Rule.** 题面正文、程序代码和数学公式各用自己的排版体系；数学下标、矩阵及关系符号交由 KaTeX，代码块保留字面字符。

## Layout

公共顶栏为紧凑单行结构，高度为 58px。品牌、主导航与账户工具有明确分组，当前导航用文字加重与底部细线标记。小屏保留主操作，缩短品牌展示并隐藏长账户名称。

选卷和历史记录居中，内容最大宽度为 1140px；桌面页面留白使用 32px 横向内边距，列表采用有序行而不是相互竞争的卡片网格。列表行默认 24px 内边距，以日期、标题与状态、题名、开始按钮形成横向层次。

桌面作答区占据顶栏下方剩余视口高度。题面默认约 46% 宽，可水平调整且最多占 70%；题面与代码编辑器分别滚动，面板间隙为 8px，编辑动作留在代码面板底部。题面段落与章节保留清晰的阅读间隔。

重复间距以 4、8、12、16、20、24、32px 为主；这些是现有布局采用的节奏，不要求将内容强行对齐某个网格。

- 在 900px 以下，作答标题和题签缩短，次要计分说明隐藏。
- 在 760px 以下，登录从双列变成单列，表单保持完整标签。
- 在 720px 以下，试卷行换行，五个题名纵向排列，按钮仍与所属试卷对应。
- 在 640px 以下，作答改为题面在上、编辑器在下；题面最高 48dvh，编辑面板为 55dvh 且保留至少 420px 高度。题签可横向滚动，样例输入输出改为单列。

## Elevation & Depth

常规卡片和作答面板采用平面容器、背景明度与细边框表达层次。代码区域和题面等权，避免一侧悬浮成“主卡片”。原生对话框使用遮罩和集中投影，说明其临时覆盖关系；这里的投影不是常规容器样式。

### Shadow Vocabulary

- **确认对话框投影**：集中而柔和的覆盖层投影，完整值保存在 sidecar 的 shadows 扩展。
- **提交详情投影**：同一投影几何、略强的不透明度，用于较大的结果与源码对话框。

**The Flat First Rule.** 常规卡片与作答面板不加阴影。遮罩与投影只说明暂时覆盖内容的对话框、通知层级。

## Shapes

形态以细直边和轻圆角为主。输入框、次要按钮与短状态标记采用 control；主要按钮和样例容器采用 action；常规面板采用 panel；试卷列表外框及提交详情采用 paper。pill 用于小型标签，不用于大面积容器。

容器边界通常为 1px，选中导航与题签使用 2px 指示线。焦点轮廓为强调色的 2px 外描边，最终公共样式保留 3px 偏移。形状和边界区分结构，不能替代文本状态。

## Components

### Buttons

直接、可预测的操作控件。

- 主按钮使用独立按钮蓝与白字、轻圆角，默认内边距为 8px × 16px；悬停加深。
- 次按钮使用嵌入灰、正文色和细边框；悬停时背景靠近边界色。
- 危险按钮使用错误红与白字，用于需要确认的结束等操作。
- 小按钮缩为 4px × 10px；禁用时降低不透明度并改变光标，同时依靠页面文字解释原因。

### Chips

状态标记轻而短，不模拟可点击按钮。

- 已完成建设使用通过绿与浅绿背景；建设中使用中性背景与说明文字。
- 判题状态显示缩写或中文解释，并可配圆点；等待中圆点只表示任务仍在处理。
- 默认小圆角状态与小型 pill 标签并存，沿用各自既有组件，不强制统一成胶囊。

### Cards / Containers

容器承担组织，不争夺注意力。

- 白色或深色 surface、细边界、panel 圆角，无常驻阴影。
- 常规内容内边距为 20px；试卷列表行采用 24px。
- 样例容器以 inset 背景区分输入输出，不叠加厚边框。

### Inputs / Fields

完整标签优先于占位符。

- 普通输入框继承系统字体、surface 背景、正文色和细边界，内边距为 8px × 12px。
- 登录和账户表单控件保持 44px 高；登录控件采用 action 圆角。
- 焦点改变边界色并显示浅色光圈；键盘焦点保留清晰外轮廓。
- 错误放在相关表单内，用文字和错误色一起表达。

### Navigation

顶栏是稳定入口，模拟考试与考试记录是普通用户的核心导航；题库管理仅管理员可见。选中项保持中性强文本与底线，主题及退出操作放在右侧。窄屏减少品牌文字与账户名称，保留可访问标签。

### Historical Paper Row

每行呈现一个实际考试批次：日期、试卷标题、建设状态、五题题名与开始按钮。内容变化不改变层次；建设中按钮禁用，已验证试卷显示可模拟状态。当前完成数量通过文字明确表达。

### Exam Tabs and Panels

五个题签承担题目切换与分数概览。当前题签使用 surface 背景、正文色与底部指示线；得分是小型辅助信息。题面提供阅读字号控件；Monaco 与提交动作保持连续，不跟随左侧题面滚动。

### Dialogs

确认和提交详情均使用原生 dialog，遮罩内集中呈现内容。确认框默认聚焦取消，支持 Escape 取消和键盘焦点约束；操作文案描述实际结果。提交详情保留结果、测试点和历史源码的清楚分组，隐藏数据不作为页面输出展示。

## Do's and Don'ts

### Do:

- **Do** 保持浅色与深色主题的相同布局、状态文字和键盘焦点。
- **Do** 使用系统无衬线字体阅读题面，等宽字体编辑代码；通过 LaTeX 表达数学下标与公式。
- **Do** 在主操作上使用蓝色，在结果文字与轻背景上使用语义色。
- **Do** 保持题面与代码分别滚动，桌面作答面板占据剩余视口高度。
- **Do** 为加载、禁用、错误和建设中提供明确文字；继承减少动态效果偏好。

### Don't:

- **Don't** 在长时间作答区域加入粒子、渐变装饰或持续的背景动画。
- **Don't** 用颜色替代状态文字，或把未验证试卷展示成可完整评测。
- **Don't** 用原始 l_i 文本代替数学下标，也不要把源代码里的下划线转成数学排版。
- **Don't** 给所有容器添加阴影、扩大圆角或将常规控件升级成展示卡片。
- **Don't** 把已取消的工作台、错题本和普通题库导航重新带入主界面。

