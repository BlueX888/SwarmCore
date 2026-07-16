# 表单组合与描述列表模式

本文件定义 TailAdmin-Radix 在中后台项目中的表单页面形态。表单不是单个控件集合，必须根据复杂度、承载容器和查看/编辑状态选择合适模式。

## 表单复杂度分级

| 复杂度 | 适用场景 | 推荐结构 | 不要使用 |
|---|---|---|---|
| 简单表单 | 1-8 个字段、单一提交目标 | 单列/双列 `FormSection` + 底部 actions | 多 Tab、复杂 Drawer |
| 中等表单 | 8-20 个字段、2-4 个业务分组 | 分段卡片、折叠分组、sticky actions | 一个巨大卡片堆满字段 |
| 复杂表单 | 20+ 字段、权限/高级配置/依赖字段 | Hub Tabs、Accordion、Advanced options、分步校验 | 单页长表单无导航 |
| 向导表单 | 有顺序依赖、需要测试/预览/确认 | Stepper/Wizard + 每步局部校验 | 一次性提交全部字段 |
| 设置表单 | 可分区保存、部分开关即时生效 | Hub Tabs + section form + dirty state | 居中弹窗承载大量设置 |

## 承载容器选型

| 容器 | 适用 | 关键规则 |
|---|---|---|
| 独立页面 | 创建、编辑、设置、向导、复杂配置 | 需要标题、面包屑、分组、提交区；长表单可用 sticky actions。 |
| 居中弹窗 Dialog | 字段少、确认性强、上下文简单 | 建议 1-6 个字段；不承载复杂依赖和长内容。 |
| 右侧抽屉 Drawer/Sheet | 从列表进入编辑、需要保留上下文 | 支持详情/编辑切换、局部保存、关闭确认。 |
| 底部 Sheet | 移动端筛选、批量操作、轻量编辑 | 移动端优先；内容高度受控。 |
| 内联展开 | 表格行快速编辑、小块配置 | 不影响主流程，必须有取消/保存状态。 |

## 复杂表单规则

- 多业务域：优先 `HubTabsLayout`。
- 字段依赖多：使用 Accordion/Collapsible 分组。
- 低频配置：放入“高级选项”折叠区。
- 危险配置：独立 Danger Zone，不和普通字段混排。
- 保存逻辑复杂：明确 dirty、saving、saved、error、partial saved。

## 查看态描述列表

任何创建/编辑表单，都应有对应查看态。查看态不要复用 disabled 表单冒充详情页，优先使用描述列表。

| 查看复杂度 | 推荐结构 | 适用 |
|---|---|---|
| 简单描述列表 | `DescriptionList` 两列 label/value | 基础资料、账户信息 |
| 分组描述列表 | 多个 `DescriptionSection` | 资源详情、配置详情 |
| Tab 描述列表 | Hub Tabs + DescriptionSection | 设置中心、网关、PaaS 资源 |
| 抽屉详情 | Drawer + DescriptionList + actions | 表格行详情 |
| 对比描述列表 | Before/After DescriptionDiff | 配置变更、审批、回滚 |

## 编辑态与查看态切换

- 详情页默认查看态，点击“编辑”进入表单态。
- Drawer 可用顶部 segmented control 切换“详情 / 编辑 / 审计”。
- 保存失败时留在编辑态并聚焦第一个错误字段。
- 关闭有 dirty state 的抽屉/弹窗时必须二次确认。
- 应用根节点须挂载 `<ConfirmHost />`（`templates/ui/confirm-host.tsx`），以支持 `FormDialog` / `FormDrawer` 的 Promise 式关闭确认（`confirm()` 来自 `templates/lib/use-confirm.ts`）。

## 决策规则

- 字段少不代表必须用 Dialog；如果需要保留列表上下文，优先 Drawer。
- 字段多不代表堆成一页；超过 20 个字段必须有 Tab、分组或折叠。
- disabled 表单不是详情页；查看态使用描述列表。
- 高级选项默认折叠，危险操作放 Danger Zone。
- 表单和描述列表必须共享字段分组命名，避免编辑/查看心智不一致。

## 模板清单

| 模板 | 说明 | 状态 |
|---|---|---|
| `templates/layout/form-page-shell.tsx` | 独立页面表单壳 + sticky actions | done |
| `templates/ui/form-section.tsx` | 表单分组容器 | done |
| `templates/ui/description-list.tsx` | 查看态描述列表 | done |
| `templates/ui/description-diff.tsx` | 变更前后对比 | done |
| `templates/ui/form-drawer.tsx` | Drawer 内查看/编辑切换 | done |
| `templates/ui/form-dialog.tsx` | Dialog 短表单 | done |
