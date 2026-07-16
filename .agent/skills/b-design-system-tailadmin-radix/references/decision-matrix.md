# 组件与页面选型决策矩阵

本文件用于提升 Agent 查找组件、选择页面模板和纠正错选的准确度。它不是静态清单，而是随 SOP 自我演化持续更新的决策账本。

## 使用原则

1. 先判断业务意图，再选择组件，禁止只按外观相似选择。
2. 能用专用组件时，不退回普通 `Input`、`Table`、`Card` 或临时样式。
3. 每次 preview、代码评审或业务落地发现错选，必须把规则写回本文件。
4. 若本文件没有覆盖某个高频场景，下一轮演化应补充矩阵，而不是让 Agent 临场猜测。
5. 本文件只沉淀通用能力，不写具体项目品牌、路由或专有文案。

## 表单与输入选型

| 业务意图 | 优先组件 | 不要使用 | 判断规则 |
|---|---|---|---|
| 普通短文本 | `Input` | 自定义 div input | 单行、无特殊格式即可用。 |
| 搜索 | `AdvancedInput type="search"` 或 `Input type="search"` | 普通 text + 手写图标 | 需要 prefix 图标、clearable、debounce 时优先 AdvancedInput。 |
| 密码 | `PasswordInput` 或 `AdvancedInput type="password"` | 普通 Input 明文 | 登录密码用 PasswordInput；API Key/token 用 SecretInput。 |
| 邮箱/URL | `AdvancedInput type="email/url"` | 普通 text | 需要语义 keyboard、校验和错误提示。 |
| 金额 | `NumericInput format="currency"` | 普通 Input | 需要千分位、小数位、货币符号、stepper。 |
| 百分比/比例 | `NumericInput format="percent"` | 普通 Input | 需要 min/max、精度、单位。 |
| 手机号/证件/IP/CIDR | `MaskedInput` | 普通 Input | 有格式化、粘贴归一化或 mask hint。 |
| OTP/验证码 | `OtpInput` | 多个普通 Input 临时拼 | 需要自动跳格、粘贴、错误态和过期态。 |
| API Key/token/密钥 | `SecretInput` 或 `ApiKeyRevealPanel` | 普通 Input | 需要 mask/reveal/copy once/rotate/revoke/audit。 |
| 轻量复制（链接/ID/短文本） | `ClipboardButton` | 手写 `navigator.clipboard` | 复制成功 Sonner toast；重密文/API Key 用 SecretInput。 |
| 异步唯一性/连通性检测 | `AsyncField` | 手写 spinner 贴边 | 需要 validating/success/warning/error/retry。 |

## 表单页面形态选型

| 业务意图 | 优先模式 | 不要使用 | 判断规则 |
|---|---|---|---|
| 简单创建/编辑 | 独立页简单表单或 Dialog 短表单 | 多 Tab/复杂 Drawer | 1-8 个字段、单一提交目标。 |
| 中等复杂表单 | 分段 FormSection + sticky actions | 一个巨大卡片堆字段 | 8-20 个字段、2-4 个业务分组。 |
| 复杂配置 | Hub Tabs + Accordion + Advanced options | 单页长表单无导航 | 20+ 字段、权限/高级配置/依赖字段。 |
| 列表行编辑 | Drawer/Sheet 表单 | 居中 Dialog | 需要保留列表上下文或右侧详情。 |
| 移动端筛选/批量配置 | Bottom Sheet | 桌面 Dialog 直搬 | 移动端高度受限，操作轻量。 |
| 分步接入/部署 | Wizard/Stepper | 一页提交全部字段 | 步骤之间有依赖、测试、确认。 |
| 查看态 | DescriptionList/DescriptionSection | disabled 表单 | 只读详情、配置摘要、审计展示。 |
| 可点设置行+尾部 Switch | `List` | DescriptionList + 手写 row | 通知/设置列表；行可点击，尾部放 Switch 或操作。 |
| 变更对比 | DescriptionDiff | 两份表单并排 | 配置变更、审批、回滚前后对比。 |
| 动态重复字段（联系人/规格行） | `FormList` + `useFormList` | 手写 `map` + index key | 需要 add/remove/move、min/max 约束、稳定 `field.id`。 |
| 长表单提交校验失败 | `scrollToFirstError` / `useFormSubmit` | toast-only 错误 | 提交后滚到首个 `[data-field-invalid]`；配合 FormField error 态。 |

## 变体与导航选型

| 业务意图 | 优先组件 | 不要使用 | 判断规则 |
|---|---|---|---|
| 校验错误呈现 | FormField + fieldState="error" | variant="error" 当外观 | 外观与校验态正交，见 primitive-template#variant-scale。 |
| 页内模式/粒度切换 | SegmentedControl | Tabs | 同一视图内切换日/周/月、详情/编辑/审计等模式。 |
| 不同内容面板切换 | Tabs | SegmentedControl | 切换独立面板内容区，非仅筛选粒度。 |
| 悬停轻量解释 | Tooltip | Popover / Dialog | 单行说明、disabled 按钮原因、截断文本补充。 |
| 点击展开详情/表单 | Popover | Tooltip | 需要点击触发或承载交互内容。 |
| 折叠 FAQ/高级选项 | Accordion | 多个 Card 堆叠 | 设置页、复杂表单 Advanced options。 |
| 视觉分组线 | Separator | border div | 表单分组、菜单分割、设置项分隔。 |
| 标签筛选 | Chip | Badge | 可关闭筛选标签，非状态 pill。 |
| 数字角标 | CountBadge | Badge | 叠在图标/头像上的 count/dot。 |
| 长设置页章节导航 | `AnchorNav` | Tabs / 手写锚点 | 长表单/设置页侧栏或顶栏锚点；配合 `AnchorSection` 与 `usePageNav`。 |

## 布尔与选择控件

| 业务意图 | 优先组件 | 不要使用 | 判断规则 |
|---|---|---|---|
| 单个开关配置 | `Switch` | Checkbox | 是/否立即生效或配置开关。 |
| 多项独立选择 | `Checkbox` | Switch 列表 | 多个可同时选中的非即时配置。 |
| 单选互斥 | `RadioGroup` | Select | 选项少且需要露出全部选择。 |
| 按钮式单选（分段外观） | `RadioButtonGroup` | 裸 Button 组 | antd `Radio.Button`；选项 2–5 个、需 outline 按钮外观。 |
| 选项很多的单选 | `Select` | RadioGroup | 选项多、需要搜索或节省空间。 |
| 多选标签 | `MultiSelect` | 多个 Checkbox 堆叠 | 选项多、需要搜索、tag 展示、清空。 |
| 可搜索单选/多选 | `Autocomplete` | 裸 Select + 手写 filter | 需要输入过滤、远程搜索、`freeSolo` 自定义值。 |
| 自由标签输入 | `TagsInput` | MultiSelect 冒充 | 用户自造 tag、Enter 创建、Backspace 删除末项。 |
| 数值范围 | `Slider` + `NumericInput` | 普通 Input | 需要连续值、范围调节或视觉反馈。 |
| 分步向导/审批进度 | `Steps` | 手写 div 序号 | 通用水平/垂直步骤条；CI 流水线用 `pipeline-stage-bar`。 |
| 省市区/路径级联 | Cascader | TreeSelect / Select | 列式多级路径；changeOnSelect 可选中间层 |
| 组织/权限树选择 | TreeSelect | Cascader / Tree | 深层树 + 可选 treeCheckable |
| 固定候选集批量分配 | Transfer | DataTable rowSelection | 双栏穿梭；权限/角色分配 |
| 仅时间/排班 | TimePicker | DatePicker / Input | 不含日期，仅时分（可选秒）；排班、营业时间。 |
| 日期+时间 | DatePicker `showTime` | TimePicker + DatePicker 分离 | 同一字段需日期与时间；Calendar 底部嵌入 TimePicker 列。 |
| 评论 @ 提及 | Mentions | Autocomplete / Textarea | `@` 触发候选列表；MR 评论、协作输入。 |
| NPS/应用评分 | Rating | 手写 Star 图标 | 星级评分；`allowHalf`、`readOnly`、键盘 Arrow 导航。 |
| 图表/标签/主题色 | ColorPicker | `Input type="color"` | preset 色块 + `react-colorful` 面板；主题定制。 |
| 表格内联重命名 | Editable | Input 切换 | 查看/编辑双态；Enter 提交、Esc 取消、`submitOnBlur`。 |

## 表格与数据展示选型

| 业务意图 | 优先组件/模式 | 不要使用 | 判断规则 |
|---|---|---|---|
| 简单静态表 | `Table` | DataTableCard 过度包装 | 无查询状态、无批量、无筛选。 |
| CRUD 列表 | `DataTableCard` | 普通 Table + 临时 toolbar | 需要搜索、筛选、操作、分页、空态/错误态。 |
| 大数据列表 | `DataTableCard` + 服务端分页模式 | 前端一次性渲染 | 行数多、筛选排序依赖服务端。 |
| 批量操作 | `DataTableCard selectedCount/bulkActions` | 行内按钮堆叠 | 有勾选、批量删除、导出、变更状态。 |
| 行选择/展开/排序联动 | `DataTable` + `onChange` | 手写 checkbox 列 | 需要全选半选、展开行、分页排序统一回调。 |
| 列头筛选 | `DataTable` `columns[].filter` + `DataTableColumnFilter` | toolbar 全局筛选冒充列筛 | antd `filterDropdown`；select/text 两种；`virtual` 时忽略列 filter。 |
| 缩略图大图预览 | `ImagePreview` | 新窗口打开 / 裸 `<img>` | 表格附件、头像、商品图；Radix Dialog 灯箱。 |
| 树形资源 | `Tree` / `ResourceTable` | 扁平 Table | 组织、目录、命名空间等层级数据。 |
| KPI/统计 | `StatMetric` / `MetricCard` | 普通 Card 手写数字 | 需要 loading、zero、delta、mask、error。 |
| KPI 涨跌展示 | `StatTrend` | 手写箭头 + 色值 | `direction: up/down/flat` + 语义色；可放入 `StatMetric` `trend` slot。 |
| 图表分析 | `ChartPanel` / `ChartBuilderLayout` | 静态假图 | 需要 loading/empty/error/forbidden 和指标口径。 |
| 仪表盘全局筛选 | `FilterBar` scope=global | 每图各自日期控件 | 需要 chips、清除全部、联动优先级。 |
| 图表点击联动 | `CrossFilterDashboard` | 手写 onClick 无 chips | 需要 cross-filter 来源可见与清除路径。 |
| 图表下钻汇总 | `DrillDownDashboard` view=chart | 直接跳明细表 | 需要面包屑 + 筛选上下文保留。 |
| 行级 BI 明细 | `DrillDetailTable` | 普通 Table | 需要分页、导出、列显隐、权限错误态。 |
| 通用审计/活动流 | `Timeline` | Steps / 手写 ul | 操作日志、活动记录、事件时间轴；CI 审批用 `ApprovalTimeline`。 |

## 浮层与编辑流选型

| 业务意图 | 优先组件 | 不要使用 | 判断规则 |
|---|---|---|---|
| 简短确认 | `AlertDialog` / destructive Dialog | 普通 Dialog | 删除、吊销、回滚等危险动作。 |
| 锚点旁轻量二次确认 | `Popconfirm` | 居中 Dialog | 删除行、撤销发布等，需保留列表上下文。 |
| 简单表单弹窗 | `Dialog` | Drawer | 字段少、上下文不复杂、居中确认。 |
| 复杂编辑/详情 | `Sheet` / Drawer | 居中 Dialog | 字段多、需要保留列表上下文、右侧编辑。 |
| 底部移动端操作 | bottom Sheet | 居中 Dialog | 移动端批量操作或筛选。 |
| 行级菜单 | `DropdownMenu` | Popover | 操作列表、更多菜单。 |
| 小块解释/提示 | `Tooltip` / `Popover` | Dialog | 信息轻量，无复杂表单。 |
| 悬停多行详情/头像卡片 | `HoverCard` | Tooltip | 需要多行摘要、操作区，Tooltip 容量不足。 |
| 左右可调分栏 | `Splitter` | 手写 flex + resize | 文件树+详情、日志+面板等需拖拽比例。 |
| 三层工作台 | `three-column-workspace` | Splitter 随意嵌套 | 固定三栏用语义布局；临时调试可用 Splitter 嵌套。 |
| 固定高度内滚动 | `ScrollArea` | `overflow-auto` div | 侧栏、日志流、表格内嵌滚动条样式一致。 |
| 命令搜索 | `Command` / `SearchCommand` | Select | 全局跳转、动作搜索、快捷键。 |
| 只读代码展示 | `CodeBlock` | `CodeEditor` | 日志、生成结果、复制即可。 |
| 可编辑代码 + 预览 | `CodeEditor` | 两个独立 Textarea + pre | 需要实时 Prism 高亮与 split/edit/preview。 |
| AI 代码生成整页 | `AiCodeGeneratorShell` | 散落 prompt + editor | `/code-generator` 路由。 |
| 首次引导/新功能 | `Tour` | 多个 Dialog | 多步 Onboarding；单字段说明用 Tooltip / ToggleTip。 |
| 快捷键展示 | `Kbd` | 纯文本 `<code>` | 菜单/命令面板/Tooltip 内展示 ⌘K、Ctrl+S 等组合键。 |
| 移动端帮助点击 | `ToggleTip` | Tooltip hover | 触屏无 hover；点击图标展开 Popover 说明。 |
| 表格多选底部浮条 | `ActionBar` | 固定底栏 div | 勾选 >0 时自底部滑入「已选 N 项」+ 批量 actions。 |
| 套餐/部署整卡选择 | `ChoiceCard` | 裸 Checkbox/Radio | 整卡可点、选中 ring-brand；radio 须包 RadioGroup。 |
| 命令式确认 | `useConfirm` + `ConfirmHost` | `window.confirm` / 散落 AlertDialog | 根节点挂 ConfirmHost；`confirm()` 返回 Promise<boolean>。 |
| 万级行表格 | `DataTable` `virtual` | 全量 DOM 渲染 | `@tanstack/react-virtual` peer；`stickyHeader` 同开时 sticky 降级。 |

## 页面与场景选型

| 场景 | 页面模板 | 关键组件 |
|---|---|---|
| SaaS 设置中心 | `HubTabsLayout` | FormField、SecretInput、DataTableCard、Switch |
| 简单创建/编辑表单 | `form-composition.md` 简单表单 | FormSection、FormField、FormActions |
| 复杂配置表单 | `form-composition.md` 复杂表单 | HubTabsLayout、Accordion、Advanced options、DangerZone |
| 表格行查看/编辑 | `form-composition.md` Drawer 表单 | FormDrawer、DescriptionList、DataTableCard |
| 只读详情/配置摘要 | `form-composition.md` 描述列表 | DescriptionSection、DescriptionItem、DescriptionDiff |
| 控制平面 / 网关 | `ControlPlaneHub` | DeploymentModeMatrix、BalanceQuotaSummary、SyncHealthPanel、EndpointProbeTable |
| CI/CD 运行详情 | `CicdRunDetail` | PipelineStageBar、LogStreamPanel、ArtifactTable、ApprovalTimeline |
| MR/PR 详情 | `MrDetailShell` | FileBrowser、DiffViewer、ApprovalTimeline |
| 代码仓库浏览 | `ThreeColumnWorkspace` 或 `FileBrowser` | FileTree、CodeViewer、DiffViewer |
| AI 代码生成 | `AiCodeGeneratorShell` | CodeEditor、CodeBlock | 提示词 + 分屏编辑 + 生成/保存 |
| BI 图表编辑 | `ChartBuilderLayout` | FieldListPanel、ChartPanel、ChartConfigPanel |
| BI 仪表盘 | `DashboardGrid` | MetricCard、ChartPanel、FilterBar |
| BI 筛选联动 | `CrossFilterDashboard` | FilterBar、FilterChip、DashboardGrid |
| BI 下钻明细 | `DrillDownDashboard` | DrillBreadcrumb、DrillDetailTable、FilterBar |
| BI 导出订阅 | `ExportSubscriptionDashboard` | ExportMenu、ExportJobPanel、定时订阅列表 |
| BI 分享嵌入 | `ShareAccessDashboard` | ShareEmbedDialog、view/edit/public/embed、iframe、租户隔离 |
| BI 单行导出 | `DrillDetailTable` exportStatus | ExportMenu 全格式异步任务 | 明细表快捷 CSV，大数据用 ExportJobPanel |
| 数据大屏 | `DataScreenCanvas` + 专用大屏模板 | BigNumberTile、GeoMapPanel、告警、日志、拓扑 |
| PaaS 资源管理 | `ResourceTable` + `MasterDetailOps` | StatusBadge、ConfigDiff、LogStreamPanel、PaasOpsDangerFlow |
| 治理安全 | `PermissionMatrix` / `AuditLogTable` / `AuthProviderWizard` | RBAC、AuditLog、SecretKeyPanel、ComplianceAlert |

## 图标选型

| 业务意图 | 优先图标来源 | 不要使用 | 判断规则 |
|---|---|---|---|
| TailAdmin 风格还原 | `references/icon-system.md` 中 TailAdmin SVG barrel | 随机 lucide 替换 | 源项目已有同义 SVG 时优先保持视觉一致。 |
| shadcn/Radix 基础控件内部 | lucide-react | 手写 SVG | Select、Calendar、Dialog close 等生态默认图标可沿用 lucide。 |
| 运维/监控/PaaS/BI/DevOps 场景页 | TailAdmin SVG 语义矩阵 | 临时搜索图标 | 先按业务语义选组合，缺少再写 fallback。 |
| 项目品牌或专属对象 | 项目 SVG barrel | 写入通用 Skill | 通用 Skill 只记录抽象规则，不沉淀项目品牌。 |
| 图标按钮 | `size-5` 图标 + `size-10` touch target + `aria-label` | 只给 SVG 绑定点击 | 必须可访问、可点击、hover/focus 可见。 |


- BI 仪表盘、数据大屏的 KPI/图例默认使用中文标签；仅 API、CI/CD、K8s、P95 等技术术语可保留英文。

## 什么时候用 / 不什么时候用（G36–G40 能力包）

| 组件/模式 | 什么时候用 | 不什么时候用 |
|---|---|---|
| `FilterBar` scope=global | 仪表盘/大屏需要统一时间、租户、区域筛选并联动多图 | 单图独立筛选、字段少于 3 个的轻量列表 |
| `CrossFilterDashboard` | 点击图表后需要 chips 可见、可清除的 cross-filter | 仅跳转明细、不需要保留筛选上下文 |
| `DrillDownDashboard` | 汇总→明细需要面包屑、筛选上下文保留 | 单表 CRUD、无层级下钻 |
| `DrillDetailTable` | 下钻后的分页明细、导出、列显隐、权限错误态 | 简单静态表、无导出/权限边界 |
| `ExportMenu` | 图表/仪表盘/大屏/表格需要 PNG/PDF/Excel/CSV 异步导出 | 仅复制链接、无文件导出需求 |
| `ExportJobPanel` | 导出任务 queued/exporting/ready/failed/expired 需可见 | 同步小文件直接下载即可 |
| `ExportSubscriptionDashboard` | 定时报表订阅 + 导出任务组合页 | 单次导出、无订阅 |
| `ShareEmbedDialog` | 仪表盘/大屏需要 view/edit/public/embed 分享与 iframe | 仅内部 RBAC、无外链/嵌入 |
| `ShareAccessDashboard` | 分享入口 + 租户隔离 + 撤销链接组合 | 单用户私有视图 |
| `CodeBlock` | 日志、生成结果、只读代码片段 + copy | 需要实时编辑与预览 |
| `CodeEditor` | 可编辑代码 + Prism 高亮 + split/edit/preview | 只读展示、无保存/脏态 |
| `AiCodeGeneratorShell` | AI 代码生成整页（提示词 + 编辑 + 保存） | 散落 prompt + textarea 临时拼 |
| `PermissionMatrix` | RBAC 批量勾选、继承/自定义/禁用、冲突提示 | 简单 Switch 列表冒充权限 |
| `AuditLogTable` | 审计日志时间范围、操作者、对象、导出、详情抽屉 | 普通操作历史 Table 无筛选 |
| `AuthProviderWizard` | LDAP/OAuth/OIDC/SAML 分步接入与连通性测试 | 单页表单硬塞全部认证配置 |
| `SecretKeyPanel` | 治理密钥 mask/copy/rotate/revoke + 审计 | 普通 Input 明文展示密钥 |
| `ResourceTable` | K8s/ES/MySQL/Redis/Host 资源列表 + 状态列 | 无资源类型语义的一般 CRUD |
| `ConfigDiff` | 参数变更 before/after + 重启/风险提示 | 两份 JSON 并排无审批语义 |
| `PaasOpsDangerFlow` | 伸缩/重启/故障转移需二次确认与影响范围 | 普通 Button 直接执行危险操作 |

## 反例规则

- 金额、百分比、配额、用量不要用普通 `Input`。
- API Key、token、License 不要用明文普通 `Input`。
- 查看态不要用 disabled 表单冒充，应使用描述列表。
- 复杂表单不要堆成单页长表单，应使用 Tab、分组、折叠或向导。
- 字段较多的编辑不要塞进居中 Dialog，应使用独立页或 Drawer。
- 大数据列表不要用裸 `Table`。
- 复杂编辑流不要塞进居中 Dialog。
- 删除、吊销、回滚不要用普通 Button 直接执行。
- 大屏不要用空容器、假柱状条或普通 Dashboard 卡片凑数。
- 图标不要临时搜索拼接，应先查 `icon-system.md`；图标错选或风格漂移必须写回本矩阵。
- 中文中后台项目不要默认使用英文 mock、placeholder 或状态文案。

## 自我演化回写规则

每轮 P4/P5 必须检查：

1. 新增页面是否有“业务意图 → 组件/页面模板”的明确选择理由。
2. preview 或截图失败是否由组件选型错误导致。
3. 业务落地或评审发现的错选是否已写回本矩阵。
4. 新增组件是否补充“什么时候用 / 不什么时候用”。
5. `component-index.md`、`pattern-index.md`、`domain-scenarios.md` 是否能从业务意图检索到对应模板。

若发现错选但没有更新本文件，生成一致性最高 90，逻辑完备最高 88。

## 预防性场景组合（MS-09～13）

> G54 补强。业务升级 pin 前必须确认页面组合使用受控 props；错选写回本表与 `agent-retrieval-guide.md`。

| MS | 业务意图 | 正选 | 常见误选 | 降级路径 | 首次接入（G57） | 业务验证（G55） | 漂移评审（G56） | SSR/微前端（G58） | 可访问性（G59） | 响应式（G60） | 异步状态（G61） | 交互与动效（G62） | 中文文案（G63） | 视觉 Token（G64） | 逻辑完备（G65） | 类型完整（G66） | 生成一致性（G67） | 组件覆盖率（G68） | 模式覆盖（G69） | 约束遵守（G70） |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| MS-09 | 企业网关 / License / 同步 / 端点探测 | `ControlPlaneHub` + 子面板受控 props | 散落 Card + 硬编码 mock 数据 | SOR-05 降级块；SEL-05 | `adoption-onboarding-checklist.md#adopt-05` + ADOPT-04 pin | `business-validation-checklist.md#ms-09` | `ui-drift-review-checklist.md#rev-03` | `ssr-microfrontend-adoption-checklist.md#ssr-05` + MFE-05 pin 一致 | `accessibility-review-checklist.md#a11y-03` 端点探测 Dialog + 表格行操作 aria-label | `responsive-review-checklist.md#resp-02` 四 KPI desktop 4 列 / tablet 2×2 | `async-state-review-checklist.md#async-04` 端点探测 onProbe loading→结果 + 面板独立 error/retry | `interaction-motion-review-checklist.md#inter-02` 端点探测 Dialog fade+scale + 表格行 hover | `chinese-copy-review-checklist.md#copy-04` License/端点/配额 mock 中文 + 探测 Dialog 按钮 | `visual-token-review-checklist.md#vis-03` KPI 四列栅格 + brand Token 主操作 + 表格 `py-4` | `form-validation-logic-review-checklist.md#logic-04` 端点 probe 分步结果 + License 吊销确认 Dialog | `type-api-contract-review-checklist.md#type-03` ControlPlaneHub 子面板受控 props 类型 + `onProbe` 回调签名 | `generation-consistency-review-checklist.md#gen-05` ControlPlaneHub 组合 + 受控 props；非散落 mock Card | `component-coverage-review-checklist.md#cov-05` ControlPlaneHub + `templates/gateway/*` 子面板齐全；preview gateway-patterns | `pattern-coverage-review-checklist.md#pat-05` 网关控制平面场景；`domain-scenarios.md` + gateway layout；preview gateway-patterns | `constraint-compliance-review-checklist.md#con-05` 网关受控 props + 语义 Token + Radix 浮层 + 中文 mock；preview gateway-patterns |
| MS-10 | CI/CD 运行详情 / 流水线阶段 | `CicdRunDetail` 或 PipelineStageBar + ArtifactTable | 纯 `KanbanBoard` 冒充发布看板 | SOR-02；SEL-02 | `adoption-onboarding-checklist.md#adopt-05` + ADOPT-03 壳层 | `business-validation-checklist.md#ms-10` | `ui-drift-review-checklist.md#rev-03` | `ssr-microfrontend-adoption-checklist.md#mfe-03` basename + SSR-02 LogStream client | `accessibility-review-checklist.md#a11y-01` 阶段条键盘可达 + LogStream loading aria-live | `responsive-review-checklist.md#resp-04` 日志区固定高度 + 表格横向滚动 | `async-state-review-checklist.md#async-02` LogStream 流式 loading + ArtifactTable 翻页不丢态 | `interaction-motion-review-checklist.md#inter-05` 阶段条 hover/active + LogStream 尾部 loading 动画 | `chinese-copy-review-checklist.md#copy-04` 阶段/日志/制品中文；CI/CD 缩写可保留 | `visual-token-review-checklist.md#vis-04` 阶段条圆角阴影 + 日志区固定高度层级 | `form-validation-logic-review-checklist.md#logic-02` Rollback/Approve 确认 + 阶段依赖不可跳步 | `type-api-contract-review-checklist.md#type-05` PipelineStageBar `stages` 受控 + LogStream 流式 props 类型闭合 | `generation-consistency-review-checklist.md#gen-01` CicdRunDetail 正选；禁止 Kanban 冒充 CI/CD | `component-coverage-review-checklist.md#cov-05` CicdRunDetail + PipelineStageBar/LogStream/ArtifactTable `templates/devops/*`；preview devops-patterns | `pattern-coverage-review-checklist.md#pat-05` `cicd-release.md` + master-detail-ops；preview devops-patterns | `constraint-compliance-review-checklist.md#con-05` LogStream client 边界 + 阶段中文 + Radix Dialog；preview devops-patterns |
| MS-11 | BI 全局筛选 + 图表联动 | `CrossFilterDashboard` + FilterBar chips | 单图 + 无 chips 的 onClick | SOR-01；SEL-01 → DrillDownDashboard | `adoption-onboarding-checklist.md#adopt-02` Token/Chart | `business-validation-checklist.md#ms-11` | `ui-drift-review-checklist.md#rev-05` | `ssr-microfrontend-adoption-checklist.md#ssr-02` Chart dynamic + MFE-04 无重复壳层 | `accessibility-review-checklist.md#a11y-05` 筛选 chip 可键盘清除 + 图表区降级可读 | `responsive-review-checklist.md#resp-05` FilterBar 窄屏换行 + ChartPanel 最小高度 | `async-state-review-checklist.md#async-05` Chart lazy 占位 + 筛选不阻塞全页 | `interaction-motion-review-checklist.md#inter-05` 筛选 chip 增删过渡 + Chart cross-filter hover/tooltip | `chinese-copy-review-checklist.md#copy-04` 指标/维度/chip 中文；P95/QPS 可保留 | `visual-token-review-checklist.md#vis-05` KPI 数字对齐 + `chartPaletteCssVars` 色板 | `form-validation-logic-review-checklist.md#logic-05` 筛选→图表因果链 + 下钻面包屑可返回 | `type-api-contract-review-checklist.md#type-02` `getBaseChartOptions(overrides?)` + FilterBar chips 受控类型联动 | `generation-consistency-review-checklist.md#gen-02` FilterBar + Chart Token/密度与 golden 一致 | `component-coverage-review-checklist.md#cov-05` CrossFilterDashboard + FilterBar `templates/bi/*`；Chart theme lib + preview bi-filter-linkage | `pattern-coverage-review-checklist.md#pat-05` `bi-filter-linkage.md` + bi-dashboard-builder；preview bi-filter-linkage | `constraint-compliance-review-checklist.md#con-05` Chart dynamic + `chartPaletteCssVars` + 筛选 chips 中文；preview bi-filter-linkage |
| MS-12 | PaaS 资源列表 + 地图/热力 | `ResourceTable` + Maps/Vector 同一地理语义 | 扁平 Table 硬塞地图 Card | SOR-03；SEL-03 | `adoption-onboarding-checklist.md#adopt-05` 首页选型 | `business-validation-checklist.md#ms-12` | `ui-drift-review-checklist.md#rev-03` | `ssr-microfrontend-adoption-checklist.md#ssr-02` Maps client-only + MFE-02 Token 同步 | `accessibility-review-checklist.md#a11y-04` 地图 iframe `title` + 行操作 icon 标签 | `responsive-review-checklist.md#resp-04` ResourceTable overflow-x + mobile 地图降级 | `async-state-review-checklist.md#async-02` 表格 loading/空态/筛选无结果 + 地图失败降级 | `interaction-motion-review-checklist.md#inter-01` 表格行 hover + 行操作 Dropdown 打开过渡 | `chinese-copy-review-checklist.md#copy-04` 资源/备份/伸缩中文；K8s/MySQL 可保留 | `visual-token-review-checklist.md#vis-03` 表格密度 + 地图 Card `rounded-xl` 边框层级 | `form-validation-logic-review-checklist.md#logic-02` 恢复/伸缩确认 Dialog + ConfigDiff 审批闭环 | `type-api-contract-review-checklist.md#type-03` ResourceTable row type + `mergeMapLibreOptions` center/zoom override | `generation-consistency-review-checklist.md#gen-01` ResourceTable + Maps 正选；表格/地图语义一致 | `component-coverage-review-checklist.md#cov-05` ResourceTable + Maps theme `templates/paas/*`；preview paas-patterns | `pattern-coverage-review-checklist.md#pat-05` `paas-resource.md` + table-list；preview paas-patterns | `constraint-compliance-review-checklist.md#con-05` Maps client-only + 表格密度 + 恢复 Dialog 中文；preview paas-patterns |
| MS-13 | RBAC + 审计 + 认证接入 | `PermissionMatrix` + `AuditLogTable` + Auth Wizard | Switch 列表冒充权限矩阵 | SOR-04；SEL-04 | `adoption-onboarding-checklist.md#adopt-05` + ADOPT-04 | `business-validation-checklist.md#ms-13` | `ui-drift-review-checklist.md#rev-03` | `ssr-microfrontend-adoption-checklist.md#mfe-05` 跨子应用 pin + SSR-04 Wizard Dialog | `accessibility-review-checklist.md#a11y-02` Wizard 逐步 Label + 矩阵非纯 Switch | `responsive-review-checklist.md#resp-03` mobile Wizard 用 bottom Sheet / 矩阵横向滚动 | `async-state-review-checklist.md#async-03` Wizard 提交 loading + AuditLogTable 搜索/翻页异步态 | `interaction-motion-review-checklist.md#inter-03` 矩阵勾选过渡 + Wizard 步骤切换动效 | `chinese-copy-review-checklist.md#copy-05` 权限/审计/吊销 Dialog 中文 + Wizard 步骤标题 | `visual-token-review-checklist.md#vis-02` dark 矩阵边框 + Wizard Dialog `rounded-3xl` | `form-validation-logic-review-checklist.md#logic-03` 矩阵保存 + 角色切换刷新审计 + Wizard 逐步校验 | `type-api-contract-review-checklist.md#type-05` PermissionMatrix `onChange` 快照 + Auth Wizard 分步 data 类型 | `generation-consistency-review-checklist.md#gen-05` PermissionMatrix + AuditLogTable 组合；非 Switch 列表 | `component-coverage-review-checklist.md#cov-05` PermissionMatrix + AuditLogTable + Auth Wizard `templates/governance/*`；preview security-governance | `pattern-coverage-review-checklist.md#pat-05` auth-provider-wizard + governance 安全场景；preview security-governance | `constraint-compliance-review-checklist.md#con-05` 矩阵非 Switch + Wizard Radix + 审计中文；preview security-governance |

## SSR / 微前端壳层选型（G58）

| 业务意图 | 优先模式 | 不要使用 | 判断规则 |
|---|---|---|---|
| 独立 SSR 后台子应用 | 完整 `AppLayout` + client 边界分包 | Server Component 直渲 Chart/Maps | SSR-01～02；见 `ssr-microfrontend-adoption-checklist.md` |
| 微前端全量子应用 | 子应用内完整 `AppSidebar` + `AppHeader` | 主应用与子应用各一套完整壳层叠放 | MFE-04 全量模式 |
| 微前端内容区嵌入 | `FormPageShell` / `HubTabsLayout` 无重复顶栏 | 嵌入块再套完整 AppLayout | MFE-04 嵌入模式 |
| BI/地图/看板在 SSR | dynamic import + loading 占位 | 构建期 import ApexCharts/MapLibre | SSR-02；`extension-audit.md` 降级列 |
| 跨子应用 MS 组合 | 主应用注入租户/用户 props | 子应用写死 mock 数据 | MFE-05；`business-validation-checklist.md` |

## 可访问性选型（G59）

| 业务意图 | 优先模式 | 不要使用 | 判断规则 |
|---|---|---|---|
| 图标-only 顶栏/表格操作 | `aria-label` 中文 + 可选 Tooltip | 裸 `<button><Icon/></button>` 无名称 | A11Y-04；`icon-system.md` |
| 短确认 / 危险操作 | `AlertDialog` + 标题 + 焦点回焦 | 无标题 div 弹层 | A11Y-03 |
| RBAC / 权限矩阵 | `PermissionMatrix` 行列语义 + 标签 | Switch 列表无行列标题 | A11Y-02 · MS-13 |
| 地图 / 大屏嵌入 | 容器 `role="application"` 或 iframe `title` | 无标题地图块 | A11Y-04 · MS-12 |
| 异步表格 / 日志流 | loading `aria-busy` 或区域 `aria-live` | 静默空白无反馈 | A11Y-05 · MS-10 |

## 响应式选型（G60）

| 业务意图 | 优先模式 | 不要使用 | 判断规则 |
|---|---|---|---|
| 概览 KPI 栅格 | desktop 4 列 / tablet 2×2 / mobile 1 列 | tablet 仍 4 列或 1 列堆 4 卡 | RESP-02；`golden-screens.md` |
| 移动筛选/短编辑 | bottom Sheet / Drawer | 居中 Dialog 直搬 mobile | RESP-03 · `form-composition.md` |
| 宽表格列表 | 容器内 `overflow-x-auto` + 关键列 sticky | 表格撑破壳层或裁切列 | RESP-04 · MS-12 |
| Master-Detail | `< lg` 详情入 Drawer/全屏 | 列表与详情同屏挤压 | RESP-04 · `master-detail-ops.md` |
| BI / 大屏画布 | 比例缩放 + FilterBar 换行 | 空容器 / 假柱状条占位 | RESP-05 · `decision-matrix.md#反例` |

## 异步状态选型（G61）

| 业务意图 | 优先模式 | 不要使用 | 判断规则 |
|---|---|---|---|
| 页面首屏数据 | QueryShell Skeleton → content / error+retry | 长时间空白无反馈 | ASYNC-01 · `state-index.md` |
| 表格翻页/筛选 | 表级 loading + 筛选无结果与真 empty 区分 | 翻页丢选中或静默失败 | ASYNC-02 · `prd/F02-data-state.md` |
| 表单提交/危险操作 | 按钮 loading + 二次确认 Dialog | 可双提交或无错误映射 | ASYNC-03 · `form-composition.md` |
| 多面板 Hub 页 | 各子面板独立 loading/error/retry | 一错全页白屏 | ASYNC-04 · MS-09 |
| Chart/Maps/Kanban | dynamic import + 占位 + 降级文案 | 重组件白屏阻塞全页 | ASYNC-05 · `extension-audit.md` |

## 交互与动效选型（G62）

| 业务意图 | 优先模式 | 不要使用 | 判断规则 |
|---|---|---|---|
| 主按钮/菜单 hover | Token 背景过渡 150–200ms | 瞬时跳色或无 hover | INTER-01 · `interaction-motion.md` |
| 确认/危险 Dialog | Radix fade+scale + Esc 关闭 | 手写 div 无过渡 | INTER-02 · `state-index.md` |
| 权限矩阵/开关列表 | Switch/Checkbox 轨道内滑动 | 纯 Switch 列表冒充矩阵 | INTER-03 · MS-13 |
| 提交/流式加载 | 按钮内 Spinner + 表级 Skeleton | Spinner 溢出或双态重叠 | INTER-04 · ASYNC-03 |
| BI 筛选/图表联动 | chip 增删过渡 + chart tooltip | 无反馈的 onClick 硬切 | INTER-05 · MS-11 |

## 中文文案选型（G63）

| 业务意图 | 优先模式 | 不要使用 | 判断规则 |
|---|---|---|---|
| 表单 placeholder/helper | 中文业务语义 + props 可覆盖 | 英文 `Enter`/`Search` 作默认 | COPY-01 · `quality-rubric.md` |
| 空态/错误/加载 | 中文标题+说明+CTA | 裸 `No data` / `Error` | COPY-02 · `state-index.md` |
| 壳层/页面标题 | 中文领域名与面包屑 | `Dashboard`/`Settings` 直译菜单 | COPY-03 · `route-index.md` |
| 领域 mock 数据 | 网关/DevOps/PaaS/BI/治理中文 | 英文 SaaS 电商 placeholder 套用到政企页 | COPY-04 · MS-09～13 |
| Dialog/图标可读文案 | 中文标题+按钮+`aria-label` | `OK`/`Cancel`/`Copied` 无 i18n | COPY-05 · A11Y-04 |

## 视觉 Token 选型（G64）

| 业务意图 | 优先模式 | 不要使用 | 判断规则 |
|---|---|---|---|
| 主操作/状态色 | `brand-*` / `success-*` / `error-*` 语义 Token | 页面内 `#hex` 或 `blue-500` 默认色 | VIS-01 · `token-index.md` |
| Dark 对比与边框 | `dark:border-white/[0.05]` + 语义灰阶 | 仅改背景不改边框 | VIS-02 · `visual-language.md` |
| KPI/表格密度 | desktop 4 列 KPI + 表格 `py-4` | 首屏大面积空白或过挤堆叠 | VIS-03 · `golden-screens.md` |
| 圆角/阴影/浮层层级 | `rounded-xl` 面板 + `z-99999` 浮层 | 默认 `z-50` 或随意 `shadow-xl` | VIS-04 · `state-index.md` |
| 数字/KPI/大屏层次 | `font-semibold` + tabular-nums + 真实信息层次 | 假柱状条或空容器占位 | VIS-05 · MS-11 |

## 逻辑完备选型（G65）

| 业务意图 | 优先模式 | 不要使用 | 判断规则 |
|---|---|---|---|
| 表单校验反馈 | blur + submit 内联 `FormMessage` | toast-only 错误或 silent fail | LOGIC-01 · `crud-flow.md` |
| 删除/吊销/回滚 | AlertDialog + destructive 按钮 + 中文后果说明 | 无确认直接 `onClick` 删除 | LOGIC-02 · `danger-zone.tsx` |
| RBAC / 只读 | `PermissionMatrix` + disabled + tooltip | Switch 列表或无门禁按钮 | LOGIC-03 · SEL-04 |
| 接入/部署向导 | 分步局部校验 + probe 结果态 | 一页提交全部字段 | LOGIC-04 · MS-09/13 |
| 列表 CRUD | 新建/编辑/删除闭环 + dirty 关闭确认 | 只有列表无编辑或关闭丢数据 | LOGIC-05 · `form-dialog.tsx` |

## 类型完整选型（G66）

| 业务意图 | 优先模式 | 不要使用 | 判断规则 |
|---|---|---|---|
| 组件 props | 文档导出名 + 显式 interface | 本地 rename 或 `any` 绕过 | TYPE-01 · `api-contracts.md` |
| Chart/Calendar override | `getBaseChartOptions(overrides?)` deep merge | 手写 spread 丢嵌套 series | TYPE-02 · MER-02 |
| 复杂受控组件 | `columns`/`value`/`onChange` 成对 + 数据模型类型 | 非受控内部 state 冒充 API | TYPE-03 · `extension-audit.md` |
| 升级兼容 | additive props + MN/deprecated wrapper | silent 删 props 或无 migration note | TYPE-04 · TS-* |
| MS 场景组合 | 子面板受控 props 与模板契约一致 | 硬编码 mock 且无类型出口 | TYPE-05 · VAL-* |

## 生成一致性选型（G67）

| 业务意图 | 优先模式 | 不要使用 | 判断规则 |
|---|---|---|---|
| 组件/页面选型 | decision-matrix 正选 + component-index 模板 | 无矩阵依据的随机 Card 拼凑 | GEN-01 · SEL-* |
| Token/密度 | `token-index.md` 语义色 + golden 栅格密度 | 页面内 hex 或同类页间距不一致 | GEN-02 · VIS-* |
| 状态矩阵 | `state-index.md` loading/empty/error 统一模式 | 同类控件 loading/hover 表现不同 | GEN-03 · ASYNC-* |
| Agent 检索 | `agent-retrieval-guide.md` ≤3 跳路由 | 无差别扫描整个 templates/ | GEN-04 · RUN-04 |
| MS 场景组合 | MS 表正选模板 + 受控 props | Kanban/Switch 列表冒充领域页 | GEN-05 · VAL-* |

## 组件覆盖率选型（G68）

| 业务意图 | 优先模式 | 不要使用 | 判断规则 |
|---|---|---|---|
| 主路径组件 | `component-index.md` 登记 + `templates/` 可复制 | 仅 preview CSS mock 无模板 | COV-01 · extension-audit |
| 复杂组件 | extension-audit 14/14 + theme lib/override | partial 或 evolving 无降级路径 | COV-02 · AUDIT-001 |
| preview 验收 | golden-screens 注册 + 模板路径文案 | 主路径模板无 preview section | COV-03 · PREVIEW-* |
| 高频变体 | Form/Buttons/Overlays/DataTable 矩阵可交互 | 单一状态或静态 mock | COV-04 · G42 |
| MS 场景模板 | 领域 `templates/*/` 组合 + SOR 食谱 | 散落 Card 拼凑领域页 | COV-05 · VAL-* |

## 模式覆盖选型（G69）

| 业务意图 | 优先模式 | 不要使用 | 判断规则 |
|---|---|---|---|
| 新应用/页面 | from-zero → route-index → pattern-index → layout | 无 output mode 随机扫 templates/ | PAT-01 · GEN-04 |
| 页面模式 | dashboard/table-list/form-flow/detail 有 layout pattern | 孤立 Card 堆叠无页面模式 | PAT-02 · pattern-index |
| 布局组合 | Hub Tabs / Master-Detail / 三栏 / 向导有 layout 文件 | 设置页无 Hub、列表详情同屏挤压 | PAT-03 · form-composition |
| 状态模式 | loading/empty/error/permission/dirty 走 state-index | 只有 happy path | PAT-04 · ASYNC-* |
| MS 场景页 | 领域 layout + 完整页面组合 + preview 场景 frame | 占位画布或假数据 Card 拼凑 | PAT-05 · VAL-* |

## 约束遵守选型（G70）

| 业务意图 | 优先模式 | 不要使用 | 判断规则 |
|---|---|---|---|
| 语义色/密度 | `token-index.md` 语义 Token + golden 密度 | 页面内 `#hex`、裸 Tailwind 色阶作默认 | CON-01 · VIS-* |
| 浮层/交互 | Radix Dialog/Dropdown + `cn()` + `cva` | 手写 portal div 弹层、模板字符串拼 class | CON-02 · RUN-03 |
| 导入/SSR 边界 | `@/` 别名 + Chart/Maps dynamic import | 深层相对路径、SSR 直渲重组件 | CON-03 · SSR-* |
| 文案/红线 | 中文默认 mock + 无品牌硬编码 | 英文 placeholder、项目路由写入默认规则 | CON-04 · COPY-* |
| MS 场景工程 | MS 表 CON-05 列：Token+API+文案组合合规 | 领域页只满足局部维度、忽视工程边界 | CON-05 · VAL-* |

## 场景 Agent 失败选型（G85）

> 与 `agent-failure-patterns-review-checklist.md`（FAIL-01～05）组合使用；完整 Agent 失败评审 = FAIL-01～10。详见 `scene-agent-failure-review-checklist.md`。

| 业务意图 | 优先模式 | 不要使用 | 判断规则 |
|---|---|---|---|
| BI Token 与色板 | FilterBar + `getBaseChartOptions` + `chartPaletteCssVars` + data-state 切换 | 页面内 `#hex`、Chart 裸色或假占位画布 | FAIL-06 · CON-06 |
| DevOps/Gateway 中文 mock | PipelineStageBar/LogStream/EndpointProbe 中文 mock + 危险 Dialog 可交互 | 英文阶段/日志/mock 或 Rollback 不可操作 | FAIL-07 · COPY-07 |
| PaaS 浮层层级 | ResourceTable + 危险 Dialog 不遮挡关键列 + Drawer focus trap | 恢复 Dialog 遮挡表格或 Maps 压扁 | FAIL-08 · REV-09 |
| MS 状态矩阵 | QueryShell loading/empty/error + live gates data-state 切换 | 仅 happy path、error 无重试 CTA | FAIL-09 · ASYNC-06 |
| MS Agent 失败束 | MS 表 FAIL-01～10 组合闭环 + `verify:runtime` 可交互验收 | 静态 mock、无打开态截图或 Specimen 不可点击 | FAIL-10 · VAL-* |

## 场景 UiElements 键盘 / Hover / Focus 选型（G86）

> 与 `ui-elements-keyboard-hover-focus-review-checklist.md`（KBF-01～05）组合使用；完整 UiElements 键盘/hover/focus 评审 = KBF-01～10。详见 `scene-ui-elements-keyboard-hover-focus-review-checklist.md`。

| 业务意图 | 优先模式 | 不要使用 | 判断规则 |
|---|---|---|---|
| Focus 环与 Tab | shadcn Button/Input + `focus-visible:ring-*` + 合理 Tab 顺序 | 鼠标点击也出粗环或主任务区无法 Tab 到达 | KBF-01 · A11Y-01 |
| 方向键导航 | Radix Tabs/DropdownMenu + Arrow 键 roving tabindex | 仅鼠标可切换菜单/分段/标签 | KBF-02 · INTER-01 |
| Esc 关闭浮层 | Radix Dialog/Popover + Esc 关闭 + 焦点回触发器 | 手写 div 浮层无 Esc 或焦点丢失 | KBF-03 · FAIL-05 |
| Hover 反馈 | Token 化 hover 背景/边框 + disabled 无 hover | 无 hover 反馈或 disabled 仍高亮 | KBF-04 · INTER-01 |
| 错误/禁用焦点 | `aria-invalid` + 中文错误文案 + disabled 不可操作 | 错误输入无提示或 loading 可双提交 | KBF-05 · LOGIC-01 |
| Overlay Specimen | ui-modals/dropdowns + live gates + `ui-elements-keyboard-hover-focus-gates.png` | Specimen 仅静态图无键盘路径 | KBF-06 · FAIL-10 |
| Navigation Specimen | ui-tabs/breadcrumb/pagination 键盘可达 + mobile 不丢焦点 | Tabs 无 roving 或分页不可键盘激活 | KBF-07 · A11Y-01 |
| Boolean Specimen | Switch/Checkbox/Radio focus 环 + 圆点不错位 | 布尔控件 hover/focus 错位或 disabled 仍 hover | KBF-08 · INTER-03 |
| 失败态 Specimen | empty/error/loading 中文 + Skeleton/Spinner + 焦点不陷阱 | 仅 happy path 或英文 failure copy | KBF-09 · ASYNC-02 |
| Specimen 22 页束 | `verifyUiElementSourceSpecimens` + KBF gates runtime 全过 | 22 源页缺截图或键盘束未跑 | KBF-10 · COV-05 |

## 场景 UiElements Variant / Interaction 选型（G88）

> 与 `ui-elements-variant-interaction-review-checklist.md`（VAR-01～05）组合使用；完整 UiElements 变体/交互评审 = VAR-01～10。详见 `scene-ui-elements-variant-interaction-review-checklist.md`。

| 业务意图 | 优先模式 | 不要使用 | 判断规则 |
|---|---|---|---|
| 变体数量下限 | 关键模板 ≥3 变体 + `ui-var-count` runtime 可切换 | 单一样式冒充多变体或 placeholder 灰块 | VAR-01 · COV-02 |
| 语义变体切换 | Badge/Button semantic tones + `data-state` 跟随 | 仅改文案不改视觉或英文变体标签 | VAR-02 · COPY-02 |
| Segmented / Tabs active | segmented active 背景 + 方向键/点击可切换 | 无 active 态或切换跳布局 | VAR-03 · KBF-02 |
| Overlay 打开态 | Dialog/Drawer/Dropdown open 截图 + Esc/关闭路径 | 仅 closed 态或 open 遮挡后续门禁 | VAR-04 · INTER-01 |
| 源 catalog 对齐 | `uiElementSpecimens` variants≥2 + element screenshots | catalog 声明变体但 preview 不可见 | VAR-05 · COV-05 |
| Action Specimen | ui-buttons/badges/group + `ui-elements-variant-interaction-gates.png` | Buttons 仅 primary 或缺 loading/disabled | VAR-06 · COV-06 |
| Display Specimen | ui-cards/lists/avatars hover + 布局变体 | 卡片仅 plain 或列表无行 hover | VAR-07 · PAT-06 |
| Overlay Specimen | ui-modals/dropdowns + live gates open 态 | Modals 无 open 截图或 Tooltip 永久遮挡 | VAR-08 · REV-08 |
| Media Specimen | Carousel runtime slide 切换 + 可见媒体区 | 轮播假条或无 next/prev 交互 | VAR-09 · INTER-09 |
| Specimen 22 页束 | `uiElementVariantInteractionStates` + 三门禁串联 | 22 源页缺 VAR 门禁或 variants<2 | VAR-10 · VAL-* |

## 场景 BI Chart Interaction 选型（G89）

> 与 `bi-chart-interaction-review-checklist.md`（CHART-01～05）组合使用；完整 BI 图表深度交互评审 = CHART-01～10。详见 `scene-bi-chart-interaction-review-checklist.md`。

| 业务意图 | 优先模式 | 不要使用 | 判断规则 |
|---|---|---|---|
| 数据点悬停 | ApexCharts tooltip + marker hover + `bi-chart-hover-state` active | 静态图无 tooltip 或英文占位 | CHART-01 · INTER-01 |
| 图例系列切换 | `.apexcharts-legend-series` 点击隐藏系列 + data-state | 图例不可点击或假按钮切换 | CHART-02 · INTER-02 |
| 刷选 / 缩放 | chart brush/selection 拖拽选区 + 中文范围标签 | 无选区或刷选遮挡 tooltip | CHART-03 · INTER-03 |
| 下钻明细 | dataPointSelection + 面包屑/路径 + 返回上级 | 点击柱条无路径或英文 drill label | CHART-04 · LOGIC-04 |
| Runtime 10 类图 | `RuntimeChartsGallery` + interaction/state 双门禁 | 仅 CSS mock 柱状条冒充图表 | CHART-05 · COV-05 |
| Chart Builder 深度交互 | state gates + interaction gates 同页四项交互 | Builder 仅展示图无真实 ApexCharts 事件 | CHART-06 · COV-06 |
| Cross-filter 联动 | 多 runtime 图 + 筛选 chips + 表格上下文 | 单图无筛选或 tooltip 样式漂移 | CHART-07 · PAT-06 |
| 指标页矩阵 | 10 类 `apexcharts-*` marker + line/bar 悬停抽检 | 缺 horizontal/stacked/funnel 等类型 | CHART-08 · COV-08 |
| 下钻仪表盘 | drill-breadcrumb + drill-detail-table 组合 | 无返回路径或明细表缺分页态 | CHART-09 · LOGIC-09 |
| BI 交互束 | `biChartInteractionStates` + 双门禁截图 | interaction gates 与 gallery 互相遮挡 | CHART-10 · VAL-* |

## 场景 Complex Form Visual Regression 选型（G91）

> 与 `complex-form-visual-regression-review-checklist.md`（CFVR-01～05）组合使用；完整复杂表单视觉回归评审 = CFVR-01～10。详见 `scene-complex-form-visual-regression-review-checklist.md`。

| 业务意图 | 优先模式 | 不要使用 | 判断规则 |
|---|---|---|---|
| Sticky 操作栏 | FormPageShell 底部 sticky actions 贴容器底 | 漂浮操作栏遮挡字段 | CFVR-01 · LOGIC-02 |
| Drawer 行编辑 | FormDrawer 右滑入 + 列表上下文保留 | 全屏覆盖丢失列表 | CFVR-02 · PAT-03 |
| Dialog 短确认 | FormDialog 居中 + 危险文案完整 | 复杂配置塞进 modal | CFVR-03 · LOGIC-03 |
| 向导开通 | 4 步指示器均衡 + async test | 单页长表单堆所有步骤 | CFVR-04 · PAT-04 |
| 校验错误 | 错误提示在字段下方，不与操作栏重叠 | 错误被裁切或英文 placeholder | CFVR-05 · COPY-01 |
| 5 flow 矩阵 | `complexFormFlows = 5` tab 可切换 | 复杂表单堆在单页无 tab | CFVR-06 · COV-06 |
| Drawer live overlay | `complex-form-drawer-guard.png` + focus trap | Drawer 无 open state 截图 | CFVR-07 · INTER-07 |
| Dialog live overlay | `complex-form-dialog-guard.png` + submitting | Dialog 无 dirty guard | CFVR-08 · LOGIC-08 |
| Wizard 四步 | step-wizard-activation 每步可回退 | 步骤指示器挤压重叠 | CFVR-09 · RESP-09 |
| 视觉回归束 | `complexFormVisualRegressionStates` + 五门禁截图 | 缺 visual regression gates 仅 live overlay | CFVR-10 · VAL-* |

## 场景 Scenario Page Visual Regression 选型（G92）

> 与 `scenario-page-visual-regression-review-checklist.md`（SPVR-01～05）组合使用；完整场景页面视觉回归评审 = SPVR-01～10。详见 `scene-scenario-page-visual-regression-review-checklist.md`。

| 业务意图 | 优先模式 | 不要使用 | 判断规则 |
|---|---|---|---|
| BI KPI 密度 | 4 列 KPI 栅格 + 图表区 ≥70% 宽度 | KPI 稀疏堆叠或首屏大面积空白 | SPVR-01 · PAT-01 |
| DevOps 流水线 | PipelineStageBar 等宽 + LogStream 固定高度 | 阶段条错位或日志 loading 贴边 | SPVR-02 · PAT-02 |
| Gateway Hub | DeploymentModeMatrix 2×2 + 4 列 KPI 对齐 | 子面板拥挤或探测 Dialog 遮挡 Tabs | SPVR-03 · PAT-03 |
| Governance 表格 | PermissionMatrix/AuditLogTable 行列对齐 | 合规横幅永久遮挡表格首屏 | SPVR-04 · PAT-04 |
| PaaS 容量 | CapacityCard 三列 + ResourceTable ≥85% 列宽 | 容量卡片挤压或危险 Dialog 遮挡关键列 | SPVR-05 · PAT-05 |
| BI 多页面工作台 | `tailadmin-bi-analytics` tab + Chart Builder ≥10 runtime | BI 压成单页占位画布 | SPVR-06 · COV-06 |
| DevOps 发布详情 | PipelineStageBar + LogStream + ApprovalTimeline | Kanban 冒充 CI/CD 视觉 | SPVR-07 · REV-07 |
| Gateway 控制平面 | DeploymentModeMatrix + EndpointProbeTable | Hub 子面板 hex 硬编码 | SPVR-08 · REV-08 |
| Governance 治理审计 | PermissionMatrix + AuditLogTable + ComplianceAlert | 权限矩阵缺行列对齐 | SPVR-09 · REV-09 |
| 视觉回归束 | `scenarioPageVisualRegressionStates` + 五门禁截图 | 缺 scenario visual regression gates | SPVR-10 · VAL-* |

## 场景域独立截图选型（G93）

> 与 `scenario-domain-independent-screenshot-review-checklist.md`（SDIS-01～05）组合使用；完整场景域独立截图评审 = SDIS-01～10。详见 `scene-scenario-domain-independent-screenshot-review-checklist.md`。

| 业务意图 | 优先模式 | 不要使用 | 判断规则 |
|---|---|---|---|
| BI 独立截图 | `scenario-bi-domain.png` + Data Screen tab 画布 | 仅引用合并 `scenario-page-visual-regression-gates.png` | SDIS-01 · REV-01 |
| DevOps 独立截图 | `scenario-devops-domain.png` + PipelineStageBar 首屏 | DevOps 场景缺 `data-audit="scenario-devops"` | SDIS-02 · REV-02 |
| Gateway 独立截图 | `scenario-gateway-domain.png` + DeploymentModeMatrix | Gateway 场景缺独立 golden | SDIS-03 · REV-03 |
| Governance 独立截图 | `scenario-governance-domain.png` + PermissionMatrix | Governance 场景缺独立 golden | SDIS-04 · REV-04 |
| PaaS 独立截图 | `scenario-paas-domain.png` + CapacityCard 三列 | PaaS 场景缺独立 golden | SDIS-05 · REV-05 |
| BI 截图矩阵 | `tailadmin-bi-analytics` + `scenario-bi-domain.png` | BI 独立截图 framing 错位或裁切 | SDIS-06 · RESP-06 |
| DevOps 截图矩阵 | `scenario-devops` + `.pipeline` 画布可见 | 流水线首屏不可见或日志区裁切 | SDIS-07 · VIS-07 |
| Gateway 截图矩阵 | `scenario-gateway` + `.matrix-cards` 画布可见 | 部署矩阵首屏不可见 | SDIS-08 · RESP-08 |
| Governance 截图矩阵 | `scenario-governance` + `.permission-grid` 画布可见 | 权限矩阵首屏不可见 | SDIS-09 · VIS-09 |
| 独立截图束 | `scenarioDomainScreenshotStates.domainCount = 5` + 5 张截图 | 缺任一域独立截图或仅合并门禁 | SDIS-10 · VAL-* |

## 场景域 light/dark 独立截图选型（G94）

> 与 `scenario-domain-light-dark-screenshot-review-checklist.md`（SDLD-01～05）组合使用；完整场景域 light/dark 独立截图评审 = SDLD-01～10。详见 `scene-scenario-domain-light-dark-screenshot-review-checklist.md`。

| 业务意图 | 优先模式 | 不要使用 | 判断规则 |
|---|---|---|---|
| BI light/dark 独立截图 | `scenario-bi-domain.png` + `scenario-bi-domain-dark.png` + Data Screen tab | 仅 light 截图或缺 dark golden | SDLD-01 · VIS-05 |
| DevOps light/dark 独立截图 | `scenario-devops-domain.png` + `scenario-devops-domain-dark.png` + PipelineStageBar | DevOps dark 截图缺 `.app.dark` 或流水线不可见 | SDLD-02 · VIS-05 |
| Gateway light/dark 独立截图 | `scenario-gateway-domain.png` + `scenario-gateway-domain-dark.png` + DeploymentModeMatrix | Gateway dark 下部署矩阵边框/背景层级丢失 | SDLD-03 · VIS-05 |
| Governance light/dark 独立截图 | `scenario-governance-domain.png` + `scenario-governance-domain-dark.png` + PermissionMatrix | Governance dark 下权限矩阵对比度不足 | SDLD-04 · VIS-05 |
| PaaS light/dark 独立截图 | `scenario-paas-domain.png` + `scenario-paas-domain-dark.png` + CapacityCard 三列 | PaaS dark 下容量卡片/KPI 不可辨认 | SDLD-05 · VIS-05 |
| BI light/dark 截图矩阵 | `tailadmin-bi-analytics` + 双主题截图 | BI dark 截图 framing 错位或 chart grid 丢失 | SDLD-06 · VIS-06 |
| DevOps light/dark 截图矩阵 | `scenario-devops` + 双主题 `.pipeline` 画布可见 | DevOps dark 日志区等宽字体不可读 | SDLD-07 · VIS-07 |
| Gateway light/dark 截图矩阵 | `scenario-gateway` + 双主题 `.matrix-cards` 画布可见 | Gateway dark KPI 栅格对齐异常 | SDLD-08 · RESP-08 |
| Governance light/dark 截图矩阵 | `scenario-governance` + 双主题 `.permission-grid` 画布可见 | Governance dark 审计表密度不一致 | SDLD-09 · VIS-09 |
| light/dark 独立截图束 | `scenarioDomainLightDarkScreenshotStates.themeMatrixComplete = true` + 10 张截图 | 缺任一域 dark 截图或仅 light 五张 | SDLD-10 · VAL-* |

## 场景域 tablet/mobile light/dark 独立截图选型（G95）

> 与 `scenario-domain-viewport-light-dark-screenshot-review-checklist.md`（SDTM-01～05）组合使用；完整场景域 tablet/mobile light/dark 独立截图评审 = SDTM-01～10。详见 `scene-scenario-domain-viewport-light-dark-screenshot-review-checklist.md`。

| 业务意图 | 优先模式 | 不要使用 | 判断规则 |
|---|---|---|---|
| BI tablet light/dark 独立截图 | `scenario-bi-domain-tablet.png` + `scenario-bi-domain-tablet-dark.png` + Data Screen tab | 仅 desktop 截图或缺 tablet golden | SDTM-01 · RESP-06 |
| BI mobile light/dark 独立截图 | `scenario-bi-domain-mobile.png` + `scenario-bi-domain-mobile-dark.png` + Data Screen tab | mobile 首屏 KPI 不可见或文本裁切 | SDTM-01 · RESP-07 |
| DevOps tablet/mobile light/dark 独立截图 | `scenario-devops-domain-{tablet,mobile}{,-dark}.png` + PipelineStageBar | DevOps mobile dark 流水线不可见 | SDTM-02 · VIS-07 |
| Gateway tablet/mobile light/dark 独立截图 | `scenario-gateway-domain-{tablet,mobile}{,-dark}.png` + DeploymentModeMatrix | Gateway mobile dark 部署矩阵层级丢失 | SDTM-03 · RESP-08 |
| Governance tablet/mobile light/dark 独立截图 | `scenario-governance-domain-{tablet,mobile}{,-dark}.png` + PermissionMatrix | Governance mobile dark 权限矩阵对比度不足 | SDTM-04 · VIS-09 |
| PaaS tablet/mobile light/dark 独立截图 | `scenario-paas-domain-{tablet,mobile}{,-dark}.png` + CapacityCard 三列 | PaaS mobile dark 容量卡片不可辨认 | SDTM-05 · RESP-05 |
| BI tablet/mobile 截图矩阵 | `tailadmin-bi-analytics` + 四视口双主题截图 | BI mobile dark 截图 framing 错位 | SDTM-06 · VIS-06 |
| DevOps tablet/mobile 截图矩阵 | `scenario-devops` + 四视口 `.pipeline` 画布可见 | DevOps mobile dark 日志区等宽字体不可读 | SDTM-07 · VIS-07 |
| Gateway tablet/mobile 截图矩阵 | `scenario-gateway` + 四视口 `.matrix-cards` 画布可见 | Gateway mobile dark KPI 栅格对齐异常 | SDTM-08 · RESP-08 |
| Governance tablet/mobile 截图矩阵 | `scenario-governance` + 四视口 `.permission-grid` 画布可见 | Governance mobile dark 审计表密度不一致 | SDTM-09 · VIS-09 |
| tablet/mobile light/dark 独立截图束 | `scenarioDomainViewportLightDarkScreenshotStates.viewportMatrixComplete = true` + 20 张截图 | 缺任一域 tablet/mobile dark 截图 | SDTM-10 · VAL-* |

## 场景域交互态打开态 tablet/mobile light/dark 独立截图选型（G96）

> 与 `scenario-domain-interactive-open-viewport-light-dark-screenshot-review-checklist.md`（SDIO-01～05）组合使用；完整场景域交互态打开态 tablet/mobile light/dark 独立截图评审 = SDIO-01～10。详见 `scene-scenario-domain-interactive-open-viewport-light-dark-screenshot-review-checklist.md`。

| 业务意图 | 优先模式 | 不要使用 | 判断规则 |
|---|---|---|---|
| BI ShareEmbedDialog tablet/mobile 打开态截图 | `scenario-bi-domain-tablet-open.png` + `scenario-bi-domain-mobile-dark-open.png` + Data Screen tab | 仅关闭态截图或缺打开态 golden | SDIO-01 · INTER-06 |
| DevOps RollbackDialog tablet/mobile 打开态截图 | `scenario-devops-domain-{tablet,mobile}{,-dark}-open.png` + 回滚确认 Dialog | DevOps mobile dark 打开态危险文案不可读 | SDIO-02 · INTER-07 |
| Gateway ApiKeyReveal tablet/mobile 打开态截图 | `scenario-gateway-domain-{tablet,mobile}{,-dark}-open.png` + 密钥轮换 Dialog | Gateway mobile dark 打开态按钮层级丢失 | SDIO-03 · RESP-08 |
| Governance AuditLog Drawer tablet/mobile 打开态截图 | `scenario-governance-domain-{tablet,mobile}{,-dark}-open.png` + 导出 Drawer | Governance mobile dark Drawer 关闭路径缺失 | SDIO-04 · INTER-09 |
| PaaS OpsDangerFlow tablet/mobile 打开态截图 | `scenario-paas-domain-{tablet,mobile}{,-dark}-open.png` + 伸缩确认 Dialog | PaaS mobile dark 危险操作 Dialog 不可辨认 | SDIO-05 · RESP-05 |
| BI ShareEmbed 打开态截图矩阵 | `tailadmin-bi-analytics` + 四视口双主题打开态截图 | BI mobile dark 打开态 Dialog framing 错位 | SDIO-06 · VIS-06 |
| DevOps Rollback 打开态截图矩阵 | `scenario-devops` + 四视口打开态 overlay 可见 | DevOps mobile dark 打开态无法关闭 | SDIO-07 · INTER-07 |
| Gateway ApiKey 打开态截图矩阵 | `scenario-gateway` + 四视口打开态 Dialog 可见 | Gateway mobile dark 打开态 KPI 被完全遮挡 | SDIO-08 · RESP-08 |
| Governance Audit 打开态截图矩阵 | `scenario-governance` + 四视口打开态 Drawer 可见 | Governance mobile dark Drawer footer 不可读 | SDIO-09 · INTER-09 |
| 交互态打开态 tablet/mobile light/dark 独立截图束 | `scenarioDomainInteractiveOpenViewportLightDarkScreenshotStates.openStateMatrixComplete = true` + 20 张 `-open.png` | 缺任一域 tablet/mobile dark 打开态截图 | SDIO-10 · VAL-* |

## 场景域 Dropdown/Popover/Command 交互态打开态 tablet/mobile light/dark 独立截图选型（G97）

> 与 `scenario-domain-dropdown-popover-command-interactive-open-viewport-light-dark-screenshot-review-checklist.md`（SDPC-01～05）组合使用；完整场景域 Dropdown/Popover/Command 交互态打开态 tablet/mobile light/dark 独立截图评审 = SDPC-01～10。详见 `scene-scenario-domain-dropdown-popover-command-interactive-open-viewport-light-dark-screenshot-review-checklist.md`。

| 业务意图 | 优先模式 | 不要使用 | 判断规则 |
|---|---|---|---|
| BI 导出 Dropdown tablet/mobile 打开态截图 | `scenario-bi-domain-tablet-dropdown-open.png` + `scenario-bi-domain-mobile-dark-dropdown-open.png` | 用 Dialog 代替导出菜单或缺 dropdown golden | SDPC-01 · INTER-06 |
| DevOps 流水线 Popover tablet/mobile 打开态截图 | `scenario-devops-domain-{tablet,mobile}{,-dark}-popover-open.png` + 流水线说明 Popover | DevOps mobile dark popover 说明文案不可读 | SDPC-02 · INTER-07 |
| Gateway Command Palette tablet/mobile 打开态截图 | `scenario-gateway-domain-{tablet,mobile}{,-dark}-command-open.png` + 快速命令面板 | Gateway mobile dark command 搜索框层级丢失 | SDPC-03 · RESP-08 |
| Governance 审计筛选 Dropdown tablet/mobile 打开态截图 | `scenario-governance-domain-{tablet,mobile}{,-dark}-dropdown-open.png` + 审计筛选菜单 | Governance mobile dark dropdown 关闭路径缺失 | SDPC-04 · INTER-09 |
| PaaS 容量 Popover tablet/mobile 打开态截图 | `scenario-paas-domain-{tablet,mobile}{,-dark}-popover-open.png` + 容量阈值说明 | PaaS mobile dark popover 列表项不可辨认 | SDPC-05 · RESP-05 |
| BI 导出 Dropdown 打开态截图矩阵 | `tailadmin-bi-analytics` + 四视口双主题 dropdown 打开态截图 | BI mobile dark dropdown framing 错位 | SDPC-06 · VIS-06 |
| DevOps Popover 打开态截图矩阵 | `scenario-devops` + 四视口 popover 浮层可见 | DevOps mobile dark popover 无法关闭 | SDPC-07 · INTER-07 |
| Gateway Command 打开态截图矩阵 | `scenario-gateway` + 四视口 command 浮层可见 | Gateway mobile dark command 面板越界 | SDPC-08 · RESP-08 |
| Governance Dropdown 打开态截图矩阵 | `scenario-governance` + 四视口 dropdown 浮层可见 | Governance mobile dark dropdown 菜单裁切 | SDPC-09 · INTER-09 |
| Dropdown/Popover/Command 交互态打开态 tablet/mobile light/dark 独立截图束 | `scenarioDomainFloatingInteractiveOpenViewportLightDarkScreenshotStates.floatingOpenStateMatrixComplete = true` + 20 张浮层 `-open.png` | 缺任一域 tablet/mobile dark 浮层打开态截图 | SDPC-10 · VAL-* |

## 场景域 Tooltip/Context Menu 交互态打开态 tablet/mobile light/dark 独立截图选型（G98）

> 与 `scenario-domain-tooltip-context-menu-interactive-open-viewport-light-dark-screenshot-review-checklist.md`（SDTC-01～05）组合使用；完整场景域 Tooltip/Context Menu 交互态打开态 tablet/mobile light/dark 独立截图评审 = SDTC-01～10。详见 `scene-scenario-domain-tooltip-context-menu-interactive-open-viewport-light-dark-screenshot-review-checklist.md`。

| 业务意图 | 优先模式 | 不要使用 | 判断规则 |
|---|---|---|---|
| BI 指标 Tooltip tablet/mobile 打开态截图 | `scenario-bi-domain-tablet-tooltip-open.png` + `scenario-bi-domain-mobile-dark-tooltip-open.png` | 用 Popover 代替指标口径 Tooltip 或缺 tooltip golden | SDTC-01 · INTER-06 |
| DevOps 流水线 Context Menu tablet/mobile 打开态截图 | `scenario-devops-domain-{tablet,mobile}{,-dark}-context-menu-open.png` + 流水线右键菜单 | DevOps mobile dark context-menu 菜单项不可读 | SDTC-02 · INTER-07 |
| Gateway 端点 Tooltip tablet/mobile 打开态截图 | `scenario-gateway-domain-{tablet,mobile}{,-dark}-tooltip-open.png` + 端点探测说明 | Gateway mobile dark tooltip 说明层级丢失 | SDTC-03 · RESP-08 |
| Governance 审计行 Context Menu tablet/mobile 打开态截图 | `scenario-governance-domain-{tablet,mobile}{,-dark}-context-menu-open.png` + 审计行操作菜单 | Governance mobile dark context-menu 关闭路径缺失 | SDTC-04 · INTER-09 |
| PaaS 容量 Tooltip tablet/mobile 打开态截图 | `scenario-paas-domain-{tablet,mobile}{,-dark}-tooltip-open.png` + 容量阈值说明 | PaaS mobile dark tooltip 列表项不可辨认 | SDTC-05 · RESP-05 |
| BI 指标 Tooltip 打开态截图矩阵 | `tailadmin-bi-analytics` + 四视口双主题 tooltip 打开态截图 | BI mobile dark tooltip framing 错位 | SDTC-06 · VIS-06 |
| DevOps Context Menu 打开态截图矩阵 | `scenario-devops` + 四视口 context-menu 浮层可见 | DevOps mobile dark context-menu 无法关闭 | SDTC-07 · INTER-07 |
| Gateway Tooltip 打开态截图矩阵 | `scenario-gateway` + 四视口 tooltip 浮层可见 | Gateway mobile dark tooltip 面板越界 | SDTC-08 · RESP-08 |
| Governance Context Menu 打开态截图矩阵 | `scenario-governance` + 四视口 context-menu 浮层可见 | Governance mobile dark context-menu 菜单裁切 | SDTC-09 · INTER-09 |
| Tooltip/Context Menu 交互态打开态 tablet/mobile light/dark 独立截图束 | `scenarioDomainTooltipContextMenuInteractiveOpenViewportLightDarkScreenshotStates.tooltipContextOpenStateMatrixComplete = true` + 20 张 `-tooltip-open.png`/`-context-menu-open.png` | 缺任一域 tablet/mobile dark Tooltip/Context Menu 打开态截图 | SDTC-10 · VAL-* |

## 场景域 Hover 轻量浮层 tablet/mobile light/dark 独立截图选型（G99）

> 与 `scenario-domain-hover-viewport-light-dark-screenshot-review-checklist.md`（SDHO-01～05）组合使用；完整场景域 Hover 轻量浮层 tablet/mobile light/dark 独立截图评审 = SDHO-01～10。详见 `scene-scenario-domain-hover-viewport-light-dark-screenshot-review-checklist.md`。

| 业务意图 | 优先模式 | 不要使用 | 判断规则 |
|---|---|---|---|
| BI 指标 Hover tablet/mobile 截图 | `scenario-bi-domain-tablet-hover.png` + `scenario-bi-domain-mobile-dark-hover.png` | 用 click-open Tooltip 代替 hover 轻量提示或缺 hover golden | SDHO-01 · INTER-06 |
| DevOps 阶段 Hover tablet/mobile 截图 | `scenario-devops-domain-{tablet,mobile}{,-dark}-hover.png` + 阶段说明 hover | DevOps mobile dark hover 提示不可读 | SDHO-02 · INTER-07 |
| Gateway 端点 Hover tablet/mobile 截图 | `scenario-gateway-domain-{tablet,mobile}{,-dark}-hover.png` + 端点状态摘要 | Gateway mobile dark hover 说明层级丢失 | SDHO-03 · RESP-08 |
| Governance 审计行 Hover tablet/mobile 截图 | `scenario-governance-domain-{tablet,mobile}{,-dark}-hover.png` + 审计行摘要 | Governance mobile dark hover 移出后仍残留面板 | SDHO-04 · INTER-09 |
| PaaS 容量 Hover tablet/mobile 截图 | `scenario-paas-domain-{tablet,mobile}{,-dark}-hover.png` + 容量阈值摘要 | PaaS mobile dark hover 列表项不可辨认 | SDHO-05 · RESP-05 |
| BI 指标 Hover 截图矩阵 | `tailadmin-bi-analytics` + 四视口双主题 hover 截图 | BI mobile dark hover framing 错位 | SDHO-06 · VIS-06 |
| DevOps Hover 截图矩阵 | `scenario-devops` + 四视口 hover 浮层可见 | DevOps mobile dark hover 移出后不消失 | SDHO-07 · INTER-07 |
| Gateway Hover 截图矩阵 | `scenario-gateway` + 四视口 hover 浮层可见 | Gateway mobile dark hover 面板越界 | SDHO-08 · RESP-08 |
| Governance Hover 截图矩阵 | `scenario-governance` + 四视口 hover 浮层可见 | Governance mobile dark hover 提示裁切 | SDHO-09 · INTER-09 |
| Hover 轻量浮层 tablet/mobile light/dark 独立截图束 | `scenarioDomainHoverViewportLightDarkScreenshotStates.hoverStateMatrixComplete = true` + 20 张 `-hover.png` | 缺任一域 tablet/mobile dark Hover 截图 | SDHO-10 · VAL-* |

## 场景域 Focus/键盘导航 tablet/mobile light/dark 独立截图选型（G100）

> 与 `scenario-domain-focus-keyboard-viewport-light-dark-screenshot-review-checklist.md`（SDFK-01～05）组合使用；完整场景域 Focus/键盘导航 tablet/mobile light/dark 独立截图评审 = SDFK-01～10。详见 `scene-scenario-domain-focus-keyboard-viewport-light-dark-screenshot-review-checklist.md`。

| 业务意图 | 优先模式 | 不要使用 | 判断规则 |
|---|---|---|---|
| BI 指标 Focus tablet/mobile 截图 | `scenario-bi-domain-tablet-focus.png` + `scenario-bi-domain-mobile-dark-focus.png` | 用 hover-only 提示代替 Tab 聚焦导航或缺 focus golden | SDFK-01 · A11Y-06 |
| DevOps 阶段 Focus tablet/mobile 截图 | `scenario-devops-domain-{tablet,mobile}{,-dark}-focus.png` + 阶段导航 focus | DevOps mobile dark focus 导航不可读 | SDFK-02 · INTER-07 |
| Gateway 端点 Focus tablet/mobile 截图 | `scenario-gateway-domain-{tablet,mobile}{,-dark}-focus.png` + 端点状态摘要 | Gateway mobile dark focus 说明层级丢失 | SDFK-03 · RESP-08 |
| Governance 审计行 Focus tablet/mobile 截图 | `scenario-governance-domain-{tablet,mobile}{,-dark}-focus.png` + 审计行摘要 | Governance mobile dark focus Esc 后仍残留面板 | SDFK-04 · A11Y-09 |
| PaaS 容量 Focus tablet/mobile 截图 | `scenario-paas-domain-{tablet,mobile}{,-dark}-focus.png` + 容量阈值摘要 | PaaS mobile dark focus 列表项不可辨认 | SDFK-05 · RESP-05 |
| BI 指标 Focus 截图矩阵 | `tailadmin-bi-analytics` + 四视口双主题 focus 截图 | BI mobile dark focus framing 错位 | SDFK-06 · VIS-06 |
| DevOps Focus 截图矩阵 | `scenario-devops` + 四视口 focus 浮层可见 | DevOps mobile dark focus Esc 后不消失 | SDFK-07 · INTER-07 |
| Gateway Focus 截图矩阵 | `scenario-gateway` + 四视口 focus 浮层可见 | Gateway mobile dark focus 面板越界 | SDFK-08 · RESP-08 |
| Governance Focus 截图矩阵 | `scenario-governance` + 四视口 focus 浮层可见 | Governance mobile dark focus 提示裁切 | SDFK-09 · A11Y-09 |
| Focus/键盘导航 tablet/mobile light/dark 独立截图束 | `scenarioDomainFocusKeyboardViewportLightDarkScreenshotStates.focusStateMatrixComplete = true` + 20 张 `-focus.png` | 缺任一域 tablet/mobile dark Focus 截图 | SDFK-10 · VAL-* |

## 场景域 disabled/loading tablet/mobile light/dark 独立截图选型（G101）

> 与 `scenario-domain-disabled-loading-viewport-light-dark-screenshot-review-checklist.md`（SDDL-01～05）组合使用；完整场景域 disabled/loading tablet/mobile light/dark 独立截图评审 = SDDL-01～10。详见 `scene-scenario-domain-disabled-loading-viewport-light-dark-screenshot-review-checklist.md`。

| 业务意图 | 优先模式 | 不要使用 | 判断规则 |
|---|---|---|---|
| BI 指标 disabled/loading tablet/mobile 截图 | `scenario-bi-domain-tablet-disabled.png` + `scenario-bi-domain-mobile-dark-loading.png` | 用静态文案代替真实 disabled/loading 态或缺 golden | SDDL-01 · LOGIC-06 |
| DevOps 阶段 disabled/loading tablet/mobile 截图 | `scenario-devops-domain-{tablet,mobile}{,-dark}-{disabled,loading}.png` + 阶段禁用/加载摘要 | DevOps mobile dark loading spinner 不可辨认 | SDDL-02 · ASYNC-07 |
| Gateway 端点 disabled/loading tablet/mobile 截图 | `scenario-gateway-domain-{tablet,mobile}{,-dark}-{disabled,loading}.png` + 端点状态摘要 | Gateway mobile dark disabled 按钮仍可点击 | SDDL-03 · LOGIC-08 |
| Governance 审计行 disabled/loading tablet/mobile 截图 | `scenario-governance-domain-{tablet,mobile}{,-dark}-{disabled,loading}.png` + 审计行摘要 | Governance mobile dark loading 文案裁切 | SDDL-04 · COPY-09 |
| PaaS 容量 disabled/loading tablet/mobile 截图 | `scenario-paas-domain-{tablet,mobile}{,-dark}-{disabled,loading}.png` + 容量阈值摘要 | PaaS mobile dark disabled 列表项不可辨认 | SDDL-05 · RESP-05 |
| BI 指标 disabled/loading 截图矩阵 | `tailadmin-bi-analytics` + 八视口双主题 disabled/loading 截图 | BI mobile dark loading framing 错位 | SDDL-06 · VIS-06 |
| DevOps disabled/loading 截图矩阵 | `scenario-devops` + 八视口 disabled/loading 可见 | DevOps mobile dark loading 无 spinner | SDDL-07 · ASYNC-07 |
| Gateway disabled/loading 截图矩阵 | `scenario-gateway` + 八视口 disabled/loading 可见 | Gateway mobile dark disabled 对比度不足 | SDDL-08 · A11Y-08 |
| Governance disabled/loading 截图矩阵 | `scenario-governance` + 八视口 disabled/loading 可见 | Governance mobile dark loading 面板越界 | SDDL-09 · RESP-09 |
| disabled/loading tablet/mobile light/dark 独立截图束 | `scenarioDomainDisabledLoadingViewportLightDarkScreenshotStates.disabledLoadingStateMatrixComplete = true` + 40 张 `-disabled.png`/`-loading.png` | 缺任一域 tablet/mobile dark disabled 或 loading 截图 | SDDL-10 · VAL-* |

## 场景域 empty/error tablet/mobile light/dark 独立截图选型（G102）

> 与 `scenario-domain-empty-error-viewport-light-dark-screenshot-review-checklist.md`（SDEE-01～05）组合使用；完整场景域 empty/error tablet/mobile light/dark 独立截图评审 = SDEE-01～10。详见 `scene-scenario-domain-empty-error-viewport-light-dark-screenshot-review-checklist.md`。

| 业务意图 | 优先模式 | 不要使用 | 判断规则 |
|---|---|---|---|
| BI 指标 empty/error tablet/mobile 截图 | `scenario-bi-domain-tablet-empty.png` + `scenario-bi-domain-mobile-dark-error.png` | 用静态文案代替真实 empty/error 态或缺 golden | SDEE-01 · LOGIC-06 |
| DevOps 阶段 empty/error tablet/mobile 截图 | `scenario-devops-domain-{tablet,mobile}{,-dark}-{empty,error}.png` + 阶段空态/错误摘要 | DevOps mobile dark error alert 不可辨认 | SDEE-02 · ASYNC-07 |
| Gateway 端点 empty/error tablet/mobile 截图 | `scenario-gateway-domain-{tablet,mobile}{,-dark}-{empty,error}.png` + 端点空态/错误摘要 | Gateway mobile dark empty 虚线边框丢失 | SDEE-03 · LOGIC-08 |
| Governance 审计行 empty/error tablet/mobile 截图 | `scenario-governance-domain-{tablet,mobile}{,-dark}-{empty,error}.png` + 审计空态/错误摘要 | Governance mobile dark error 文案裁切 | SDEE-04 · COPY-09 |
| PaaS 容量 empty/error tablet/mobile 截图 | `scenario-paas-domain-{tablet,mobile}{,-dark}-{empty,error}.png` + 容量空态/错误摘要 | PaaS mobile dark empty 列表项不可辨认 | SDEE-05 · RESP-05 |
| BI 指标 empty/error 截图矩阵 | `tailadmin-bi-analytics` + 八视口双主题 empty/error 截图 | BI mobile dark error framing 错位 | SDEE-06 · VIS-06 |
| DevOps empty/error 截图矩阵 | `scenario-devops` + 八视口 empty/error 可见 | DevOps mobile dark error 无重试 CTA | SDEE-07 · ASYNC-07 |
| Gateway empty/error 截图矩阵 | `scenario-gateway` + 八视口 empty/error 可见 | Gateway mobile dark empty 对比度不足 | SDEE-08 · A11Y-08 |
| Governance empty/error 截图矩阵 | `scenario-governance` + 八视口 empty/error 可见 | Governance mobile dark error 面板越界 | SDEE-09 · RESP-09 |
| empty/error tablet/mobile light/dark 独立截图束 | `scenarioDomainEmptyErrorViewportLightDarkScreenshotStates.emptyErrorStateMatrixComplete = true` + 40 张 `-empty.png`/`-error.png` | 缺任一域 tablet/mobile dark empty 或 error 截图 | SDEE-10 · VAL-* |

## 场景域 partial/retry tablet/mobile light/dark 独立截图选型（G103）

> 与 `scenario-domain-partial-retry-viewport-light-dark-screenshot-review-checklist.md`（SDPR-01～05）组合使用；完整场景域 partial/retry tablet/mobile light/dark 独立截图评审 = SDPR-01～10。详见 `scene-scenario-domain-partial-retry-viewport-light-dark-screenshot-review-checklist.md`。

| 业务意图 | 优先模式 | 不要使用 | 判断规则 |
|---|---|---|---|
| BI 指标 partial/retry tablet/mobile 截图 | `scenario-bi-domain-tablet-partial.png` + `scenario-bi-domain-mobile-dark-retry.png` | 用静态文案代替真实 partial/retry 态或缺 golden | SDPR-01 · LOGIC-06 |
| DevOps 阶段 partial/retry tablet/mobile 截图 | `scenario-devops-domain-{tablet,mobile}{,-dark}-{partial,retry}.png` + 阶段 partial warning/重试摘要 | DevOps mobile dark retry alert 不可辨认 | SDPR-02 · ASYNC-07 |
| Gateway 端点 partial/retry tablet/mobile 截图 | `scenario-gateway-domain-{tablet,mobile}{,-dark}-{partial,retry}.png` + 端点 partial/retry 摘要 | Gateway mobile dark partial warning 对比度不足 | SDPR-03 · LOGIC-08 |
| Governance 审计行 partial/retry tablet/mobile 截图 | `scenario-governance-domain-{tablet,mobile}{,-dark}-{partial,retry}.png` + 审计 partial/retry 摘要 | Governance mobile dark retry 文案裁切 | SDPR-04 · COPY-09 |
| PaaS 容量 partial/retry tablet/mobile 截图 | `scenario-paas-domain-{tablet,mobile}{,-dark}-{partial,retry}.png` + 容量 partial/retry 摘要 | PaaS mobile dark partial 列表项不可辨认 | SDPR-05 · RESP-05 |
| BI 指标 partial/retry 截图矩阵 | `tailadmin-bi-analytics` + 八视口双主题 partial/retry 截图 | BI mobile dark retry framing 错位 | SDPR-06 · VIS-06 |
| DevOps partial/retry 截图矩阵 | `scenario-devops` + 八视口 partial/retry 可见 | DevOps mobile dark retry 无重试 CTA | SDPR-07 · ASYNC-07 |
| Gateway partial/retry 截图矩阵 | `scenario-gateway` + 八视口 partial/retry 可见 | Gateway mobile dark partial warning 层级丢失 | SDPR-08 · A11Y-08 |
| Governance partial/retry 截图矩阵 | `scenario-governance` + 八视口 partial/retry 可见 | Governance mobile dark retry 面板越界 | SDPR-09 · RESP-09 |
| partial/retry tablet/mobile light/dark 独立截图束 | `scenarioDomainPartialRetryViewportLightDarkScreenshotStates.partialRetryStateMatrixComplete = true` + 40 张 `-partial.png`/`-retry.png` | 缺任一域 tablet/mobile dark partial 或 retry 截图 | SDPR-10 · VAL-* |

## 场景域 refetch/pending tablet/mobile light/dark 独立截图选型（G104）

> 与 `scenario-domain-refetch-pending-viewport-light-dark-screenshot-review-checklist.md`（SDRP-01～05）组合使用；完整场景域 refetch/pending tablet/mobile light/dark 独立截图评审 = SDRP-01～10。详见 `scene-scenario-domain-refetch-pending-viewport-light-dark-screenshot-review-checklist.md`。

| 业务意图 | 优先模式 | 不要使用 | 判断规则 |
|---|---|---|---|
| BI 指标 refetch/pending tablet/mobile 截图 | `scenario-bi-domain-tablet-pending.png` + `scenario-bi-domain-mobile-dark-refetch.png` | 用静态文案代替真实 refetch/pending 态或缺 golden | SDRP-01 · LOGIC-06 |
| DevOps 阶段 refetch/pending tablet/mobile 截图 | `scenario-devops-domain-{tablet,mobile}{,-dark}-{pending,refetch}.png` + 阶段 pending spinner/后台刷新摘要 | DevOps mobile dark refetch banner 不可辨认 | SDRP-02 · ASYNC-07 |
| Gateway 端点 refetch/pending tablet/mobile 截图 | `scenario-gateway-domain-{tablet,mobile}{,-dark}-{pending,refetch}.png` + 端点 refetch/pending 摘要 | Gateway mobile dark pending spinner 对比度不足 | SDRP-03 · LOGIC-08 |
| Governance 审计行 refetch/pending tablet/mobile 截图 | `scenario-governance-domain-{tablet,mobile}{,-dark}-{pending,refetch}.png` + 审计 refetch/pending 摘要 | Governance mobile dark refetch 文案裁切 | SDRP-04 · COPY-09 |
| PaaS 容量 refetch/pending tablet/mobile 截图 | `scenario-paas-domain-{tablet,mobile}{,-dark}-{pending,refetch}.png` + 容量 refetch/pending 摘要 | PaaS mobile dark pending 列表项不可辨认 | SDRP-05 · RESP-05 |
| BI 指标 refetch/pending 截图矩阵 | `tailadmin-bi-analytics` + 八视口双主题 refetch/pending 截图 | BI mobile dark refetch framing 错位 | SDRP-06 · VIS-06 |
| DevOps refetch/pending 截图矩阵 | `scenario-devops` + 八视口 refetch/pending 可见 | DevOps mobile dark refetch 无刷新 CTA | SDRP-07 · ASYNC-07 |
| Gateway refetch/pending 截图矩阵 | `scenario-gateway` + 八视口 refetch/pending 可见 | Gateway mobile dark pending spinner 层级丢失 | SDRP-08 · A11Y-08 |
| Governance refetch/pending 截图矩阵 | `scenario-governance` + 八视口 refetch/pending 可见 | Governance mobile dark refetch 面板越界 | SDRP-09 · RESP-09 |
| refetch/pending tablet/mobile light/dark 独立截图束 | `scenarioDomainRefetchPendingViewportLightDarkScreenshotStates.refetchPendingStateMatrixComplete = true` + 40 张 `-pending.png`/`-refetch.png` | 缺任一域 tablet/mobile dark pending 或 refetch 截图 | SDRP-10 · VAL-* |

## 场景域 stale/optimistic tablet/mobile light/dark 独立截图选型（G105）

> 与 `scenario-domain-stale-optimistic-viewport-light-dark-screenshot-review-checklist.md`（SDSO-01～05）组合使用；完整场景域 stale/optimistic tablet/mobile light/dark 独立截图评审 = SDSO-01～10。详见 `scene-scenario-domain-stale-optimistic-viewport-light-dark-screenshot-review-checklist.md`。

| 业务意图 | 优先模式 | 不要使用 | 判断规则 |
|---|---|---|---|
| BI 指标 stale/optimistic tablet/mobile 截图 | `scenario-bi-domain-tablet-stale.png` + `scenario-bi-domain-mobile-dark-optimistic.png` | 用静态文案代替真实 stale/optimistic 态或缺 golden | SDSO-01 · LOGIC-06 |
| DevOps 阶段 stale/optimistic tablet/mobile 截图 | `scenario-devops-domain-{tablet,mobile}{,-dark}-{stale,optimistic}.png` + 阶段 stale banner/乐观更新摘要 | DevOps mobile dark optimistic banner 不可辨认 | SDSO-02 · ASYNC-07 |
| Gateway 端点 stale/optimistic tablet/mobile 截图 | `scenario-gateway-domain-{tablet,mobile}{,-dark}-{stale,optimistic}.png` + 端点 stale/optimistic 摘要 | Gateway mobile dark stale 同步指示器对比度不足 | SDSO-03 · LOGIC-08 |
| Governance 审计行 stale/optimistic tablet/mobile 截图 | `scenario-governance-domain-{tablet,mobile}{,-dark}-{stale,optimistic}.png` + 审计 stale/optimistic 摘要 | Governance mobile dark optimistic 文案裁切 | SDSO-04 · COPY-09 |
| PaaS 容量 stale/optimistic tablet/mobile 截图 | `scenario-paas-domain-{tablet,mobile}{,-dark}-{stale,optimistic}.png` + 容量 stale/optimistic 摘要 | PaaS mobile dark stale 列表项不可辨认 | SDSO-05 · RESP-05 |
| BI 指标 stale/optimistic 截图矩阵 | `tailadmin-bi-analytics` + 八视口双主题 stale/optimistic 截图 | BI mobile dark optimistic framing 错位 | SDSO-06 · VIS-06 |
| DevOps stale/optimistic 截图矩阵 | `scenario-devops` + 八视口 stale/optimistic 可见 | DevOps mobile dark optimistic 无撤销 CTA | SDSO-07 · ASYNC-07 |
| Gateway stale/optimistic 截图矩阵 | `scenario-gateway` + 八视口 stale/optimistic 可见 | Gateway mobile dark stale 同步指示器层级丢失 | SDSO-08 · A11Y-08 |
| Governance stale/optimistic 截图矩阵 | `scenario-governance` + 八视口 stale/optimistic 可见 | Governance mobile dark optimistic 面板越界 | SDSO-09 · RESP-09 |
| stale/optimistic tablet/mobile light/dark 独立截图束 | `scenarioDomainStaleOptimisticViewportLightDarkScreenshotStates.staleOptimisticStateMatrixComplete = true` + 40 张 `-stale.png`/`-optimistic.png` | 缺任一域 tablet/mobile dark stale 或 optimistic 截图 | SDSO-10 · VAL-* |

## 场景域长轮询/流式订阅 tablet/mobile light/dark 独立截图选型（G113）

> 与 `scenario-domain-long-polling-stream-subscription-viewport-light-dark-screenshot-review-checklist.md`（SDLPS-01～05）组合使用；完整场景域长轮询/流式订阅 tablet/mobile light/dark 独立截图评审 = SDLPS-01～10。详见 `scene-scenario-domain-long-polling-stream-subscription-viewport-light-dark-screenshot-review-checklist.md`。

| 业务意图 | 优先模式 | 不要使用 | 判断规则 |
|---|---|---|---|
| BI 指标长轮询/流式订阅 tablet/mobile 截图 | `scenario-bi-domain-tablet-long-polling.png` + `scenario-bi-domain-mobile-dark-stream-subscribed.png` | 用静态文案代替真实 long-polling/stream-subscribed 态或缺 golden | SDLPS-01 · LOGIC-06 |
| DevOps 阶段长轮询/流式订阅 tablet/mobile 截图 | `scenario-devops-domain-{tablet,mobile}{,-dark}-{long-polling,stream-subscribed}.png` + 阶段挂起 banner/订阅完成摘要 | DevOps mobile dark subscribed banner 不可辨认 | SDLPS-02 · ASYNC-07 |
| Gateway 端点长轮询/流式订阅 tablet/mobile 截图 | `scenario-gateway-domain-{tablet,mobile}{,-dark}-{long-polling,stream-subscribed}.png` + 端点 long-polling/subscribed 摘要 | Gateway mobile dark long-polling banner 对比度不足 | SDLPS-03 · LOGIC-08 |
| Governance 审计行长轮询/流式订阅 tablet/mobile 截图 | `scenario-governance-domain-{tablet,mobile}{,-dark}-{long-polling,stream-subscribed}.png` + 审计 long-polling/subscribed 摘要 | Governance mobile dark subscribed 文案裁切 | SDLPS-04 · COPY-09 |
| PaaS 容量长轮询/流式订阅 tablet/mobile 截图 | `scenario-paas-domain-{tablet,mobile}{,-dark}-{long-polling,stream-subscribed}.png` + 容量 long-polling/subscribed 摘要 | PaaS mobile dark long-polling 列表项不可辨认 | SDLPS-05 · RESP-05 |
| BI 指标长轮询/流式订阅截图矩阵 | `tailadmin-bi-analytics` + 八视口双主题 long-polling/stream-subscribed 截图 | BI mobile dark subscribed framing 错位 | SDLPS-06 · VIS-06 |
| DevOps 长轮询/流式订阅截图矩阵 | `scenario-devops` + 八视口 long-polling/stream-subscribed 可见 | DevOps mobile dark subscribed 无查看订阅详情 CTA | SDLPS-07 · ASYNC-07 |
| Gateway 长轮询/流式订阅截图矩阵 | `scenario-gateway` + 八视口 long-polling/stream-subscribed 可见 | Gateway mobile dark long-polling banner 层级丢失 | SDLPS-08 · A11Y-08 |
| Governance 长轮询/流式订阅截图矩阵 | `scenario-governance` + 八视口 long-polling/stream-subscribed 可见 | Governance mobile dark subscribed 面板越界 | SDLPS-09 · RESP-09 |
| 长轮询/流式订阅 tablet/mobile light/dark 独立截图束 | `scenarioDomainLongPollingStreamSubscriptionViewportLightDarkScreenshotStates.longPollingStreamSubscriptionStateMatrixComplete = true` + 40 张 `-long-polling.png`/`-stream-subscribed.png` | 缺任一域 tablet/mobile dark long-polling 或 stream-subscribed 截图 | SDLPS-10 · VAL-* |

## 场景域推送通道重试/死信队列 tablet/mobile light/dark 独立截图选型（G117）

> 与 `scenario-domain-push-channel-retry-dead-letter-viewport-light-dark-screenshot-review-checklist.md`（SDPCRDL-01～05）组合使用；完整场景域推送通道重试/死信队列 tablet/mobile light/dark 独立截图评审 = SDPCRDL-01～10。详见 `scene-scenario-domain-push-channel-retry-dead-letter-viewport-light-dark-screenshot-review-checklist.md`。

| 业务意图 | 优先模式 | 不要使用 | 判断规则 |
|---|---|---|---|
| BI 指标推送通道重试/死信队列 tablet/mobile 截图 | `scenario-bi-domain-tablet-retry-active.png` + `scenario-bi-domain-mobile-dark-dead-letter-drained.png` | 用静态文案代替真实 retry-active/dead-letter-drained 态或缺 golden | SDPCRDL-01 · LOGIC-06 |
| DevOps 阶段推送通道重试/死信队列 tablet/mobile 截图 | `scenario-devops-domain-{tablet,mobile}{,-dark}-{retry-active,dead-letter-drained}.png` + 阶段重试 banner/死信队列排空摘要 | DevOps mobile dark dead-letter-drained banner 不可辨认 | SDPCRDL-02 · ASYNC-07 |
| Gateway 端点推送通道重试/死信队列 tablet/mobile 截图 | `scenario-gateway-domain-{tablet,mobile}{,-dark}-{retry-active,dead-letter-drained}.png` + 端点 retry-active/dead-letter-drained 摘要 | Gateway mobile dark retry-active banner 对比度不足 | SDPCRDL-03 · LOGIC-08 |
| Governance 审计行推送通道重试/死信队列 tablet/mobile 截图 | `scenario-governance-domain-{tablet,mobile}{,-dark}-{retry-active,dead-letter-drained}.png` + 审计 retry-active/dead-letter-drained 摘要 | Governance mobile dark dead-letter-drained 文案裁切 | SDPCRDL-04 · COPY-09 |
| PaaS 容量推送通道重试/死信队列 tablet/mobile 截图 | `scenario-paas-domain-{tablet,mobile}{,-dark}-{retry-active,dead-letter-drained}.png` + 容量 retry-active/dead-letter-drained 摘要 | PaaS mobile dark retry-active 列表项不可辨认 | SDPCRDL-05 · RESP-05 |
| BI 指标推送通道重试/死信队列截图矩阵 | `tailadmin-bi-analytics` + 八视口双主题 retry-active/dead-letter-drained 截图 | BI mobile dark dead-letter-drained framing 错位 | SDPCRDL-06 · VIS-06 |
| DevOps 推送通道重试/死信队列截图矩阵 | `scenario-devops` + 八视口 retry-active/dead-letter-drained 可见 | DevOps mobile dark dead-letter-drained 无死信队列排空详情 CTA | SDPCRDL-07 · ASYNC-07 |
| Gateway 推送通道重试/死信队列截图矩阵 | `scenario-gateway` + 八视口 retry-active/dead-letter-drained 可见 | Gateway mobile dark retry-active banner 层级丢失 | SDPCRDL-08 · A11Y-08 |
| Governance 推送通道重试/死信队列截图矩阵 | `scenario-governance` + 八视口 retry-active/dead-letter-drained 可见 | Governance mobile dark dead-letter-drained 面板越界 | SDPCRDL-09 · RESP-09 |
| 推送通道重试/死信队列 tablet/mobile light/dark 独立截图束 | `scenarioDomainPushChannelRetryDeadLetterViewportLightDarkScreenshotStates.pushChannelRetryDeadLetterStateMatrixComplete = true` + 40 张 `-retry-active.png`/`-dead-letter-drained.png` | 缺任一域 tablet/mobile dark retry-active 或 dead-letter-drained 截图 | SDPCRDL-10 · VAL-* |

## 场景域推送通道后续审计追踪 tablet/mobile light/dark 独立截图选型（G121）

> 与 `scenario-domain-push-channel-audit-tracking-viewport-light-dark-screenshot-review-checklist.md`（SDPCAT-01～05）组合使用；完整场景域推送通道后续审计追踪 tablet/mobile light/dark 独立截图评审 = SDPCAT-01～10。详见 `scene-scenario-domain-push-channel-audit-tracking-viewport-light-dark-screenshot-review-checklist.md`。

| 场景 | 正例 | 反例 | 症状路由 |
|---|---|---|---|
| BI 指标推送通道后续审计追踪 tablet/mobile 截图 | `scenario-bi-domain-tablet-audit-tracking-pending.png` + `scenario-bi-domain-mobile-dark-audit-tracking-complete.png` | 用静态文案代替真实 audit-tracking-pending/audit-tracking-complete 态或缺 golden | SDPCAT-01 · LOGIC-06 |
| DevOps 阶段推送通道后续审计追踪 tablet/mobile 截图 | `scenario-devops-domain-{tablet,mobile}{,-dark}-{audit-tracking-pending,audit-tracking-complete}.png` + 阶段审计追踪 banner/完成摘要 | DevOps mobile dark audit-tracking-complete banner 不可辨认 | SDPCAT-02 · ASYNC-07 |
| Gateway 端点推送通道后续审计追踪 tablet/mobile 截图 | `scenario-gateway-domain-{tablet,mobile}{,-dark}-{audit-tracking-pending,audit-tracking-complete}.png` + 端点 audit-tracking-pending/audit-tracking-complete 摘要 | Gateway mobile dark audit-tracking-pending banner 对比度不足 | SDPCAT-03 · LOGIC-08 |
| Governance 审计行推送通道后续审计追踪 tablet/mobile 截图 | `scenario-governance-domain-{tablet,mobile}{,-dark}-{audit-tracking-pending,audit-tracking-complete}.png` + 审计 audit-tracking-pending/audit-tracking-complete 摘要 | Governance mobile dark audit-tracking-complete 文案裁切 | SDPCAT-04 · COPY-09 |
| PaaS 容量推送通道后续审计追踪 tablet/mobile 截图 | `scenario-paas-domain-{tablet,mobile}{,-dark}-{audit-tracking-pending,audit-tracking-complete}.png` + 容量 audit-tracking-pending/audit-tracking-complete 摘要 | PaaS mobile dark audit-tracking-pending 列表项不可辨认 | SDPCAT-05 · RESP-05 |
| BI 指标推送通道后续审计追踪截图矩阵 | `tailadmin-bi-analytics` + 八视口双主题 audit-tracking-pending/audit-tracking-complete 截图 | BI mobile dark audit-tracking-complete framing 错位 | SDPCAT-06 · VIS-06 |
| DevOps 推送通道后续审计追踪截图矩阵 | `scenario-devops` + 八视口 audit-tracking-pending/audit-tracking-complete 可见 | DevOps mobile dark audit-tracking-complete 无审计追踪详情 CTA | SDPCAT-07 · ASYNC-07 |
| Gateway 推送通道后续审计追踪截图矩阵 | `scenario-gateway` + 八视口 audit-tracking-pending/audit-tracking-complete 可见 | Gateway mobile dark audit-tracking-pending banner 层级丢失 | SDPCAT-08 · A11Y-08 |
| Governance 推送通道后续审计追踪截图矩阵 | `scenario-governance` + 八视口 audit-tracking-pending/audit-tracking-complete 可见 | Governance mobile dark audit-tracking-complete 面板越界 | SDPCAT-09 · RESP-09 |
| 推送通道后续审计追踪 tablet/mobile light/dark 独立截图束 | `scenarioDomainPushChannelAuditTrackingViewportLightDarkScreenshotStates.pushChannelAuditTrackingStateMatrixComplete = true` + 40 张 `-audit-tracking-pending.png`/`-audit-tracking-complete.png` | 缺任一域 tablet/mobile dark audit-tracking-pending 或 audit-tracking-complete 截图 | SDPCAT-10 · VAL-* |

## 场景域推送通道后续退役 tablet/mobile light/dark 独立截图选型（G125）

> 与 `scenario-domain-push-channel-retirement-viewport-light-dark-screenshot-review-checklist.md`（SDPCRET-01～05）组合使用；完整场景域推送通道后续退役 tablet/mobile light/dark 独立截图评审 = SDPCRET-01～10。详见 `scene-scenario-domain-push-channel-retirement-viewport-light-dark-screenshot-review-checklist.md`。

| 场景 | 正例 | 反例 | 症状路由 |
|---|---|---|---|
| BI 指标推送通道后续退役 tablet/mobile 截图 | `scenario-bi-domain-tablet-channel-retirement-pending.png` + `scenario-bi-domain-mobile-dark-channel-retirement-complete.png` | 用静态文案代替真实 channel-retirement-pending/channel-retirement-complete 态或缺 golden | SDPCRET-01 · LOGIC-06 |
| DevOps 阶段推送通道后续退役 tablet/mobile 截图 | `scenario-devops-domain-{tablet,mobile}{,-dark}-{channel-retirement-pending,channel-retirement-complete}.png` + 阶段退役 banner/完成摘要 | DevOps mobile dark channel-retirement-complete banner 不可辨认 | SDPCRET-02 · ASYNC-07 |
| Gateway 端点推送通道后续退役 tablet/mobile 截图 | `scenario-gateway-domain-{tablet,mobile}{,-dark}-{channel-retirement-pending,channel-retirement-complete}.png` + 端点 channel-retirement-pending/channel-retirement-complete 摘要 | Gateway mobile dark channel-retirement-pending banner 对比度不足 | SDPCRET-03 · LOGIC-08 |
| Governance 审计行推送通道后续退役 tablet/mobile 截图 | `scenario-governance-domain-{tablet,mobile}{,-dark}-{channel-retirement-pending,channel-retirement-complete}.png` + 审计 channel-retirement-pending/channel-retirement-complete 摘要 | Governance mobile dark channel-retirement-complete 文案裁切 | SDPCRET-04 · COPY-09 |
| PaaS 容量推送通道后续退役 tablet/mobile 截图 | `scenario-paas-domain-{tablet,mobile}{,-dark}-{channel-retirement-pending,channel-retirement-complete}.png` + 容量 channel-retirement-pending/channel-retirement-complete 摘要 | PaaS mobile dark channel-retirement-pending 列表项不可辨认 | SDPCRET-05 · RESP-05 |
| BI 指标推送通道后续退役截图矩阵 | `tailadmin-bi-analytics` + 八视口双主题 channel-retirement-pending/channel-retirement-complete 截图 | BI mobile dark channel-retirement-complete framing 错位 | SDPCRET-06 · VIS-06 |
| DevOps 推送通道后续退役截图矩阵 | `scenario-devops` + 八视口 channel-retirement-pending/channel-retirement-complete 可见 | DevOps mobile dark channel-retirement-complete 无退役详情 CTA | SDPCRET-07 · ASYNC-07 |
| Gateway 推送通道后续退役截图矩阵 | `scenario-gateway` + 八视口 channel-retirement-pending/channel-retirement-complete 可见 | Gateway mobile dark channel-retirement-pending banner 层级丢失 | SDPCRET-08 · A11Y-08 |
| Governance 推送通道后续退役截图矩阵 | `scenario-governance` + 八视口 channel-retirement-pending/channel-retirement-complete 可见 | Governance mobile dark channel-retirement-complete 面板越界 | SDPCRET-09 · RESP-09 |
| 推送通道后续退役 tablet/mobile light/dark 独立截图束 | `scenarioDomainPushChannelRetirementViewportLightDarkScreenshotStates.pushChannelRetirementStateMatrixComplete = true` + 40 张 `-channel-retirement-pending.png`/`-channel-retirement-complete.png` | 缺任一域 tablet/mobile dark channel-retirement-pending 或 channel-retirement-complete 截图 | SDPCRET-10 · VAL-* |

## 场景域推送通道后续清理 tablet/mobile light/dark 独立截图选型（G127）

> 与 `scenario-domain-push-channel-cleanup-viewport-light-dark-screenshot-review-checklist.md`（SDPCCLN-01～05）组合使用；完整场景域推送通道后续清理 tablet/mobile light/dark 独立截图评审 = SDPCCLN-01～10。详见 `scene-scenario-domain-push-channel-cleanup-viewport-light-dark-screenshot-review-checklist.md`。

| 场景 | 正例 | 反例 | 症状路由 |
|---|---|---|---|
| BI 指标推送通道后续清理 tablet/mobile 截图 | `scenario-bi-domain-tablet-channel-cleanup-pending.png` + `scenario-bi-domain-mobile-dark-channel-cleanup-complete.png` | 用静态文案代替真实 channel-cleanup-pending/channel-cleanup-complete 态或缺 golden | SDPCCLN-01 · LOGIC-06 |
| DevOps 阶段推送通道后续清理 tablet/mobile 截图 | `scenario-devops-domain-{tablet,mobile}{,-dark}-{channel-cleanup-pending,channel-cleanup-complete}.png` + 阶段清理 banner/完成摘要 | DevOps mobile dark channel-cleanup-complete banner 不可辨认 | SDPCCLN-02 · ASYNC-07 |
| Gateway 端点推送通道后续清理 tablet/mobile 截图 | `scenario-gateway-domain-{tablet,mobile}{,-dark}-{channel-cleanup-pending,channel-cleanup-complete}.png` + 端点 channel-cleanup-pending/channel-cleanup-complete 摘要 | Gateway mobile dark channel-cleanup-pending banner 对比度不足 | SDPCCLN-03 · LOGIC-08 |
| Governance 审计行推送通道后续清理 tablet/mobile 截图 | `scenario-governance-domain-{tablet,mobile}{,-dark}-{channel-cleanup-pending,channel-cleanup-complete}.png` + 审计 channel-cleanup-pending/channel-cleanup-complete 摘要 | Governance mobile dark channel-cleanup-complete 文案裁切 | SDPCCLN-04 · COPY-09 |
| PaaS 容量推送通道后续清理 tablet/mobile 截图 | `scenario-paas-domain-{tablet,mobile}{,-dark}-{channel-cleanup-pending,channel-cleanup-complete}.png` + 容量 channel-cleanup-pending/channel-cleanup-complete 摘要 | PaaS mobile dark channel-cleanup-pending 列表项不可辨认 | SDPCCLN-05 · RESP-05 |
| BI 指标推送通道后续清理截图矩阵 | `tailadmin-bi-analytics` + 八视口双主题 channel-cleanup-pending/channel-cleanup-complete 截图 | BI mobile dark channel-cleanup-complete framing 错位 | SDPCCLN-06 · VIS-06 |
| DevOps 推送通道后续清理截图矩阵 | `scenario-devops` + 八视口 channel-cleanup-pending/channel-cleanup-complete 可见 | DevOps mobile dark channel-cleanup-complete 无清理详情 CTA | SDPCCLN-07 · ASYNC-07 |
| Gateway 推送通道后续清理截图矩阵 | `scenario-gateway` + 八视口 channel-cleanup-pending/channel-cleanup-complete 可见 | Gateway mobile dark channel-cleanup-pending banner 层级丢失 | SDPCCLN-08 · A11Y-08 |
| Governance 推送通道后续清理截图矩阵 | `scenario-governance` + 八视口 channel-cleanup-pending/channel-cleanup-complete 可见 | Governance mobile dark channel-cleanup-complete 面板越界 | SDPCCLN-09 · RESP-09 |
| 推送通道后续清理 tablet/mobile light/dark 独立截图束 | `scenarioDomainPushChannelCleanupViewportLightDarkScreenshotStates.pushChannelCleanupStateMatrixComplete = true` + 40 张 `-channel-cleanup-pending.png`/`-channel-cleanup-complete.png` | 缺任一域 tablet/mobile dark channel-cleanup-pending 或 channel-cleanup-complete 截图 | SDPCCLN-10 · VAL-* |

## 场景域推送通道后续销毁 tablet/mobile light/dark 独立截图选型（G126）

> 与 `scenario-domain-push-channel-destruction-viewport-light-dark-screenshot-review-checklist.md`（SDPCDEST-01～05）组合使用；完整场景域推送通道后续销毁 tablet/mobile light/dark 独立截图评审 = SDPCDEST-01～10。详见 `scene-scenario-domain-push-channel-destruction-viewport-light-dark-screenshot-review-checklist.md`。

| 场景 | 正例 | 反例 | 症状路由 |
|---|---|---|---|
| BI 指标推送通道后续销毁 tablet/mobile 截图 | `scenario-bi-domain-tablet-channel-destruction-pending.png` + `scenario-bi-domain-mobile-dark-channel-destruction-complete.png` | 用静态文案代替真实 channel-destruction-pending/channel-destruction-complete 态或缺 golden | SDPCDEST-01 · LOGIC-06 |
| DevOps 阶段推送通道后续销毁 tablet/mobile 截图 | `scenario-devops-domain-{tablet,mobile}{,-dark}-{channel-destruction-pending,channel-destruction-complete}.png` + 阶段销毁 banner/完成摘要 | DevOps mobile dark channel-destruction-complete banner 不可辨认 | SDPCDEST-02 · ASYNC-07 |
| Gateway 端点推送通道后续销毁 tablet/mobile 截图 | `scenario-gateway-domain-{tablet,mobile}{,-dark}-{channel-destruction-pending,channel-destruction-complete}.png` + 端点 channel-destruction-pending/channel-destruction-complete 摘要 | Gateway mobile dark channel-destruction-pending banner 对比度不足 | SDPCDEST-03 · LOGIC-08 |
| Governance 审计行推送通道后续销毁 tablet/mobile 截图 | `scenario-governance-domain-{tablet,mobile}{,-dark}-{channel-destruction-pending,channel-destruction-complete}.png` + 审计 channel-destruction-pending/channel-destruction-complete 摘要 | Governance mobile dark channel-destruction-complete 文案裁切 | SDPCDEST-04 · COPY-09 |
| PaaS 容量推送通道后续销毁 tablet/mobile 截图 | `scenario-paas-domain-{tablet,mobile}{,-dark}-{channel-destruction-pending,channel-destruction-complete}.png` + 容量 channel-destruction-pending/channel-destruction-complete 摘要 | PaaS mobile dark channel-destruction-pending 列表项不可辨认 | SDPCDEST-05 · RESP-05 |
| BI 指标推送通道后续销毁截图矩阵 | `tailadmin-bi-analytics` + 八视口双主题 channel-destruction-pending/channel-destruction-complete 截图 | BI mobile dark channel-destruction-complete framing 错位 | SDPCDEST-06 · VIS-06 |
| DevOps 推送通道后续销毁截图矩阵 | `scenario-devops` + 八视口 channel-destruction-pending/channel-destruction-complete 可见 | DevOps mobile dark channel-destruction-complete 无销毁详情 CTA | SDPCDEST-07 · ASYNC-07 |
| Gateway 推送通道后续销毁截图矩阵 | `scenario-gateway` + 八视口 channel-destruction-pending/channel-destruction-complete 可见 | Gateway mobile dark channel-destruction-pending banner 层级丢失 | SDPCDEST-08 · A11Y-08 |
| Governance 推送通道后续销毁截图矩阵 | `scenario-governance` + 八视口 channel-destruction-pending/channel-destruction-complete 可见 | Governance mobile dark channel-destruction-complete 面板越界 | SDPCDEST-09 · RESP-09 |
| 推送通道后续销毁 tablet/mobile light/dark 独立截图束 | `scenarioDomainPushChannelDestructionViewportLightDarkScreenshotStates.pushChannelDestructionStateMatrixComplete = true` + 40 张 `-channel-destruction-pending.png`/`-channel-destruction-complete.png` | 缺任一域 tablet/mobile dark channel-destruction-pending 或 channel-destruction-complete 截图 | SDPCDEST-10 · VAL-* |

## 场景域推送通道后续生命周期 tablet/mobile light/dark 独立截图选型（G124）

> 与 `scenario-domain-push-channel-lifecycle-viewport-light-dark-screenshot-review-checklist.md`（SDPCLF-01～05）组合使用；完整场景域推送通道后续生命周期 tablet/mobile light/dark 独立截图评审 = SDPCLF-01～10。详见 `scene-scenario-domain-push-channel-lifecycle-viewport-light-dark-screenshot-review-checklist.md`。

| 场景 | 正例 | 反例 | 症状路由 |
|---|---|---|---|
| BI 指标推送通道后续生命周期 tablet/mobile 截图 | `scenario-bi-domain-tablet-channel-lifecycle-pending.png` + `scenario-bi-domain-mobile-dark-channel-lifecycle-complete.png` | 用静态文案代替真实 channel-lifecycle-pending/channel-lifecycle-complete 态或缺 golden | SDPCLF-01 · LOGIC-06 |
| DevOps 阶段推送通道后续生命周期 tablet/mobile 截图 | `scenario-devops-domain-{tablet,mobile}{,-dark}-{channel-lifecycle-pending,channel-lifecycle-complete}.png` + 阶段生命周期 banner/闭合摘要 | DevOps mobile dark channel-lifecycle-complete banner 不可辨认 | SDPCLF-02 · ASYNC-07 |
| Gateway 端点推送通道后续生命周期 tablet/mobile 截图 | `scenario-gateway-domain-{tablet,mobile}{,-dark}-{channel-lifecycle-pending,channel-lifecycle-complete}.png` + 端点 channel-lifecycle-pending/channel-lifecycle-complete 摘要 | Gateway mobile dark channel-lifecycle-pending banner 对比度不足 | SDPCLF-03 · LOGIC-08 |
| Governance 审计行推送通道后续生命周期 tablet/mobile 截图 | `scenario-governance-domain-{tablet,mobile}{,-dark}-{channel-lifecycle-pending,channel-lifecycle-complete}.png` + 审计 channel-lifecycle-pending/channel-lifecycle-complete 摘要 | Governance mobile dark channel-lifecycle-complete 文案裁切 | SDPCLF-04 · COPY-09 |
| PaaS 容量推送通道后续生命周期 tablet/mobile 截图 | `scenario-paas-domain-{tablet,mobile}{,-dark}-{channel-lifecycle-pending,channel-lifecycle-complete}.png` + 容量 channel-lifecycle-pending/channel-lifecycle-complete 摘要 | PaaS mobile dark channel-lifecycle-pending 列表项不可辨认 | SDPCLF-05 · RESP-05 |
| BI 指标推送通道后续生命周期截图矩阵 | `tailadmin-bi-analytics` + 八视口双主题 channel-lifecycle-pending/channel-lifecycle-complete 截图 | BI mobile dark channel-lifecycle-complete framing 错位 | SDPCLF-06 · VIS-06 |
| DevOps 推送通道后续生命周期截图矩阵 | `scenario-devops` + 八视口 channel-lifecycle-pending/channel-lifecycle-complete 可见 | DevOps mobile dark channel-lifecycle-complete 无生命周期详情 CTA | SDPCLF-07 · ASYNC-07 |
| Gateway 推送通道后续生命周期截图矩阵 | `scenario-gateway` + 八视口 channel-lifecycle-pending/channel-lifecycle-complete 可见 | Gateway mobile dark channel-lifecycle-pending banner 层级丢失 | SDPCLF-08 · A11Y-08 |
| Governance 推送通道后续生命周期截图矩阵 | `scenario-governance` + 八视口 channel-lifecycle-pending/channel-lifecycle-complete 可见 | Governance mobile dark channel-lifecycle-complete 面板越界 | SDPCLF-09 · RESP-09 |
| 推送通道后续生命周期 tablet/mobile light/dark 独立截图束 | `scenarioDomainPushChannelLifecycleViewportLightDarkScreenshotStates.pushChannelLifecycleStateMatrixComplete = true` + 40 张 `-channel-lifecycle-pending.png`/`-channel-lifecycle-complete.png` | 缺任一域 tablet/mobile dark channel-lifecycle-pending 或 channel-lifecycle-complete 截图 | SDPCLF-10 · VAL-* |

## 场景域推送通道后续归档 tablet/mobile light/dark 独立截图选型（G123）

> 与 `scenario-domain-push-channel-archive-viewport-light-dark-screenshot-review-checklist.md`（SDPCARCH-01～05）组合使用；完整场景域推送通道后续归档 tablet/mobile light/dark 独立截图评审 = SDPCARCH-01～10。详见 `scene-scenario-domain-push-channel-archive-viewport-light-dark-screenshot-review-checklist.md`。

| 场景 | 正例 | 反例 | 症状路由 |
|---|---|---|---|
| BI 指标推送通道后续归档 tablet/mobile 截图 | `scenario-bi-domain-tablet-channel-archive-pending.png` + `scenario-bi-domain-mobile-dark-channel-archive-complete.png` | 用静态文案代替真实 channel-archive-pending/channel-archive-complete 态或缺 golden | SDPCARCH-01 · LOGIC-06 |
| DevOps 阶段推送通道后续归档 tablet/mobile 截图 | `scenario-devops-domain-{tablet,mobile}{,-dark}-{channel-archive-pending,channel-archive-complete}.png` + 阶段归档 banner/完成摘要 | DevOps mobile dark channel-archive-complete banner 不可辨认 | SDPCARCH-02 · ASYNC-07 |
| Gateway 端点推送通道后续归档 tablet/mobile 截图 | `scenario-gateway-domain-{tablet,mobile}{,-dark}-{channel-archive-pending,channel-archive-complete}.png` + 端点 channel-archive-pending/channel-archive-complete 摘要 | Gateway mobile dark channel-archive-pending banner 对比度不足 | SDPCARCH-03 · LOGIC-08 |
| Governance 审计行推送通道后续归档 tablet/mobile 截图 | `scenario-governance-domain-{tablet,mobile}{,-dark}-{channel-archive-pending,channel-archive-complete}.png` + 审计 channel-archive-pending/channel-archive-complete 摘要 | Governance mobile dark channel-archive-complete 文案裁切 | SDPCARCH-04 · COPY-09 |
| PaaS 容量推送通道后续归档 tablet/mobile 截图 | `scenario-paas-domain-{tablet,mobile}{,-dark}-{channel-archive-pending,channel-archive-complete}.png` + 容量 channel-archive-pending/channel-archive-complete 摘要 | PaaS mobile dark channel-archive-pending 列表项不可辨认 | SDPCARCH-05 · RESP-05 |
| BI 指标推送通道后续归档截图矩阵 | `tailadmin-bi-analytics` + 八视口双主题 channel-archive-pending/channel-archive-complete 截图 | BI mobile dark channel-archive-complete framing 错位 | SDPCARCH-06 · VIS-06 |
| DevOps 推送通道后续归档截图矩阵 | `scenario-devops` + 八视口 channel-archive-pending/channel-archive-complete 可见 | DevOps mobile dark channel-archive-complete 无归档详情 CTA | SDPCARCH-07 · ASYNC-07 |
| Gateway 推送通道后续归档截图矩阵 | `scenario-gateway` + 八视口 channel-archive-pending/channel-archive-complete 可见 | Gateway mobile dark channel-archive-pending banner 层级丢失 | SDPCARCH-08 · A11Y-08 |
| Governance 推送通道后续归档截图矩阵 | `scenario-governance` + 八视口 channel-archive-pending/channel-archive-complete 可见 | Governance mobile dark channel-archive-complete 面板越界 | SDPCARCH-09 · RESP-09 |
| 推送通道后续归档 tablet/mobile light/dark 独立截图束 | `scenarioDomainPushChannelArchiveViewportLightDarkScreenshotStates.pushChannelArchiveStateMatrixComplete = true` + 40 张 `-channel-archive-pending.png`/`-channel-archive-complete.png` | 缺任一域 tablet/mobile dark channel-archive-pending 或 channel-archive-complete 截图 | SDPCARCH-10 · VAL-* |

## 场景域推送通道后续合规留痕 tablet/mobile light/dark 独立截图选型（G122）

> 与 `scenario-domain-push-channel-compliance-trace-viewport-light-dark-screenshot-review-checklist.md`（SDPCCT-01～05）组合使用；完整场景域推送通道后续合规留痕 tablet/mobile light/dark 独立截图评审 = SDPCCT-01～10。详见 `scene-scenario-domain-push-channel-compliance-trace-viewport-light-dark-screenshot-review-checklist.md`。

| 场景 | 正例 | 反例 | 症状路由 |
|---|---|---|---|
| BI 指标推送通道后续合规留痕 tablet/mobile 截图 | `scenario-bi-domain-tablet-compliance-trace-pending.png` + `scenario-bi-domain-mobile-dark-compliance-trace-complete.png` | 用静态文案代替真实 compliance-trace-pending/compliance-trace-complete 态或缺 golden | SDPCCT-01 · LOGIC-06 |
| DevOps 阶段推送通道后续合规留痕 tablet/mobile 截图 | `scenario-devops-domain-{tablet,mobile}{,-dark}-{compliance-trace-pending,compliance-trace-complete}.png` + 阶段合规留痕 banner/完成摘要 | DevOps mobile dark compliance-trace-complete banner 不可辨认 | SDPCCT-02 · ASYNC-07 |
| Gateway 端点推送通道后续合规留痕 tablet/mobile 截图 | `scenario-gateway-domain-{tablet,mobile}{,-dark}-{compliance-trace-pending,compliance-trace-complete}.png` + 端点 compliance-trace-pending/compliance-trace-complete 摘要 | Gateway mobile dark compliance-trace-pending banner 对比度不足 | SDPCCT-03 · LOGIC-08 |
| Governance 审计行推送通道后续合规留痕 tablet/mobile 截图 | `scenario-governance-domain-{tablet,mobile}{,-dark}-{compliance-trace-pending,compliance-trace-complete}.png` + 审计 compliance-trace-pending/compliance-trace-complete 摘要 | Governance mobile dark compliance-trace-complete 文案裁切 | SDPCCT-04 · COPY-09 |
| PaaS 容量推送通道后续合规留痕 tablet/mobile 截图 | `scenario-paas-domain-{tablet,mobile}{,-dark}-{compliance-trace-pending,compliance-trace-complete}.png` + 容量 compliance-trace-pending/compliance-trace-complete 摘要 | PaaS mobile dark compliance-trace-pending 列表项不可辨认 | SDPCCT-05 · RESP-05 |
| BI 指标推送通道后续合规留痕截图矩阵 | `tailadmin-bi-analytics` + 八视口双主题 compliance-trace-pending/compliance-trace-complete 截图 | BI mobile dark compliance-trace-complete framing 错位 | SDPCCT-06 · VIS-06 |
| DevOps 推送通道后续合规留痕截图矩阵 | `scenario-devops` + 八视口 compliance-trace-pending/compliance-trace-complete 可见 | DevOps mobile dark compliance-trace-complete 无合规留痕详情 CTA | SDPCCT-07 · ASYNC-07 |
| Gateway 推送通道后续合规留痕截图矩阵 | `scenario-gateway` + 八视口 compliance-trace-pending/compliance-trace-complete 可见 | Gateway mobile dark compliance-trace-pending banner 层级丢失 | SDPCCT-08 · A11Y-08 |
| Governance 推送通道后续合规留痕截图矩阵 | `scenario-governance` + 八视口 compliance-trace-pending/compliance-trace-complete 可见 | Governance mobile dark compliance-trace-complete 面板越界 | SDPCCT-09 · RESP-09 |
| 推送通道后续合规留痕 tablet/mobile light/dark 独立截图束 | `scenarioDomainPushChannelComplianceTraceViewportLightDarkScreenshotStates.pushChannelComplianceTraceStateMatrixComplete = true` + 40 张 `-compliance-trace-pending.png`/`-compliance-trace-complete.png` | 缺任一域 tablet/mobile dark compliance-trace-pending 或 compliance-trace-complete 截图 | SDPCCT-10 · VAL-* |

## 场景域推送通道后续补偿/对账 tablet/mobile light/dark 独立截图选型（G120）

> 与 `scenario-domain-push-channel-compensation-reconciliation-viewport-light-dark-screenshot-review-checklist.md`（SDPCCR-01～05）组合使用；完整场景域推送通道后续补偿/对账 tablet/mobile light/dark 独立截图评审 = SDPCCR-01～10。详见 `scene-scenario-domain-push-channel-compensation-reconciliation-viewport-light-dark-screenshot-review-checklist.md`。

| 场景 | 正例 | 反例 | 症状路由 |
|---|---|---|---|
| BI 指标推送通道后续补偿/对账 tablet/mobile 截图 | `scenario-bi-domain-tablet-compensation-pending.png` + `scenario-bi-domain-mobile-dark-reconciliation-complete.png` | 用静态文案代替真实 compensation-pending/reconciliation-complete 态或缺 golden | SDPCCR-01 · LOGIC-06 |
| DevOps 阶段推送通道后续补偿/对账 tablet/mobile 截图 | `scenario-devops-domain-{tablet,mobile}{,-dark}-{compensation-pending,reconciliation-complete}.png` + 阶段补偿对账 banner/完成摘要 | DevOps mobile dark reconciliation-complete banner 不可辨认 | SDPCCR-02 · ASYNC-07 |
| Gateway 端点推送通道后续补偿/对账 tablet/mobile 截图 | `scenario-gateway-domain-{tablet,mobile}{,-dark}-{compensation-pending,reconciliation-complete}.png` + 端点 compensation-pending/reconciliation-complete 摘要 | Gateway mobile dark compensation-pending banner 对比度不足 | SDPCCR-03 · LOGIC-08 |
| Governance 审计行推送通道后续补偿/对账 tablet/mobile 截图 | `scenario-governance-domain-{tablet,mobile}{,-dark}-{compensation-pending,reconciliation-complete}.png` + 审计 compensation-pending/reconciliation-complete 摘要 | Governance mobile dark reconciliation-complete 文案裁切 | SDPCCR-04 · COPY-09 |
| PaaS 容量推送通道后续补偿/对账 tablet/mobile 截图 | `scenario-paas-domain-{tablet,mobile}{,-dark}-{compensation-pending,reconciliation-complete}.png` + 容量 compensation-pending/reconciliation-complete 摘要 | PaaS mobile dark compensation-pending 列表项不可辨认 | SDPCCR-05 · RESP-05 |
| BI 指标推送通道后续补偿/对账截图矩阵 | `tailadmin-bi-analytics` + 八视口双主题 compensation-pending/reconciliation-complete 截图 | BI mobile dark reconciliation-complete framing 错位 | SDPCCR-06 · VIS-06 |
| DevOps 推送通道后续补偿/对账截图矩阵 | `scenario-devops` + 八视口 compensation-pending/reconciliation-complete 可见 | DevOps mobile dark reconciliation-complete 无补偿对账详情 CTA | SDPCCR-07 · ASYNC-07 |
| Gateway 推送通道后续补偿/对账截图矩阵 | `scenario-gateway` + 八视口 compensation-pending/reconciliation-complete 可见 | Gateway mobile dark compensation-pending banner 层级丢失 | SDPCCR-08 · A11Y-08 |
| Governance 推送通道后续补偿/对账截图矩阵 | `scenario-governance` + 八视口 compensation-pending/reconciliation-complete 可见 | Governance mobile dark reconciliation-complete 面板越界 | SDPCCR-09 · RESP-09 |
| 推送通道后续补偿/对账 tablet/mobile light/dark 独立截图束 | `scenarioDomainPushChannelCompensationReconciliationViewportLightDarkScreenshotStates.pushChannelCompensationReconciliationStateMatrixComplete = true` + 40 张 `-compensation-pending.png`/`-reconciliation-complete.png` | 缺任一域 tablet/mobile dark compensation-pending 或 reconciliation-complete 截图 | SDPCCR-10 · VAL-* |

## 场景域推送通道后续异步韧性 tablet/mobile light/dark 独立截图选型（G119）

> 与 `scenario-domain-push-channel-async-resilience-viewport-light-dark-screenshot-review-checklist.md`（SDPCAR-01～05）组合使用；完整场景域推送通道后续异步韧性 tablet/mobile light/dark 独立截图评审 = SDPCAR-01～10。详见 `scene-scenario-domain-push-channel-async-resilience-viewport-light-dark-screenshot-review-checklist.md`。

| 场景 | 正例 | 反例 | 症状路由 |
|---|---|---|---|
| BI 指标推送通道后续异步韧性 tablet/mobile 截图 | `scenario-bi-domain-tablet-async-pending.png` + `scenario-bi-domain-mobile-dark-async-recovered.png` | 用静态文案代替真实 async-pending/async-recovered 态或缺 golden | SDPCAR-01 · LOGIC-06 |
| DevOps 阶段推送通道后续异步韧性 tablet/mobile 截图 | `scenario-devops-domain-{tablet,mobile}{,-dark}-{async-pending,async-recovered}.png` + 阶段异步韧性监测 banner/恢复摘要 | DevOps mobile dark async-recovered banner 不可辨认 | SDPCAR-02 · ASYNC-07 |
| Gateway 端点推送通道后续异步韧性 tablet/mobile 截图 | `scenario-gateway-domain-{tablet,mobile}{,-dark}-{async-pending,async-recovered}.png` + 端点 async-pending/async-recovered 摘要 | Gateway mobile dark async-pending banner 对比度不足 | SDPCAR-03 · LOGIC-08 |
| Governance 审计行推送通道后续异步韧性 tablet/mobile 截图 | `scenario-governance-domain-{tablet,mobile}{,-dark}-{async-pending,async-recovered}.png` + 审计 async-pending/async-recovered 摘要 | Governance mobile dark async-recovered 文案裁切 | SDPCAR-04 · COPY-09 |
| PaaS 容量推送通道后续异步韧性 tablet/mobile 截图 | `scenario-paas-domain-{tablet,mobile}{,-dark}-{async-pending,async-recovered}.png` + 容量 async-pending/async-recovered 摘要 | PaaS mobile dark async-pending 列表项不可辨认 | SDPCAR-05 · RESP-05 |
| BI 指标推送通道后续异步韧性截图矩阵 | `tailadmin-bi-analytics` + 八视口双主题 async-pending/async-recovered 截图 | BI mobile dark async-recovered framing 错位 | SDPCAR-06 · VIS-06 |
| DevOps 推送通道后续异步韧性截图矩阵 | `scenario-devops` + 八视口 async-pending/async-recovered 可见 | DevOps mobile dark async-recovered 无异步韧性恢复详情 CTA | SDPCAR-07 · ASYNC-07 |
| Gateway 推送通道后续异步韧性截图矩阵 | `scenario-gateway` + 八视口 async-pending/async-recovered 可见 | Gateway mobile dark async-pending banner 层级丢失 | SDPCAR-08 · A11Y-08 |
| Governance 推送通道后续异步韧性截图矩阵 | `scenario-governance` + 八视口 async-pending/async-recovered 可见 | Governance mobile dark async-recovered 面板越界 | SDPCAR-09 · RESP-09 |
| 推送通道后续异步韧性 tablet/mobile light/dark 独立截图束 | `scenarioDomainPushChannelAsyncResilienceViewportLightDarkScreenshotStates.pushChannelAsyncResilienceStateMatrixComplete = true` + 40 张 `-async-pending.png`/`-async-recovered.png` | 缺任一域 tablet/mobile dark async-pending 或 async-recovered 截图 | SDPCAR-10 · VAL-* |

## 场景域推送通道订阅确认/幂等重放 tablet/mobile light/dark 独立截图选型（G118）

> 与 `scenario-domain-push-channel-subscription-confirm-idempotent-replay-viewport-light-dark-screenshot-review-checklist.md`（SDPCSCIR-01～05）组合使用；完整场景域推送通道订阅确认/幂等重放 tablet/mobile light/dark 独立截图评审 = SDPCSCIR-01～10。详见 `scene-scenario-domain-push-channel-subscription-confirm-idempotent-replay-viewport-light-dark-screenshot-review-checklist.md`。

| 场景 | 正例 | 反例 | 症状路由 |
|---|---|---|---|
| BI 指标推送通道订阅确认/幂等重放 tablet/mobile 截图 | `scenario-bi-domain-tablet-subscription-confirm.png` + `scenario-bi-domain-mobile-dark-idempotent-replay.png` | 用静态文案代替真实 subscription-confirm/idempotent-replay 态或缺 golden | SDPCSCIR-01 · LOGIC-06 |
| DevOps 阶段推送通道订阅确认/幂等重放 tablet/mobile 截图 | `scenario-devops-domain-{tablet,mobile}{,-dark}-{subscription-confirm,idempotent-replay}.png` + 阶段订阅确认 banner/幂等重放摘要 | DevOps mobile dark idempotent-replay banner 不可辨认 | SDPCSCIR-02 · ASYNC-07 |
| Gateway 端点推送通道订阅确认/幂等重放 tablet/mobile 截图 | `scenario-gateway-domain-{tablet,mobile}{,-dark}-{subscription-confirm,idempotent-replay}.png` + 端点 subscription-confirm/idempotent-replay 摘要 | Gateway mobile dark subscription-confirm banner 对比度不足 | SDPCSCIR-03 · LOGIC-08 |
| Governance 审计行推送通道订阅确认/幂等重放 tablet/mobile 截图 | `scenario-governance-domain-{tablet,mobile}{,-dark}-{subscription-confirm,idempotent-replay}.png` + 审计 subscription-confirm/idempotent-replay 摘要 | Governance mobile dark idempotent-replay 文案裁切 | SDPCSCIR-04 · COPY-09 |
| PaaS 容量推送通道订阅确认/幂等重放 tablet/mobile 截图 | `scenario-paas-domain-{tablet,mobile}{,-dark}-{subscription-confirm,idempotent-replay}.png` + 容量 subscription-confirm/idempotent-replay 摘要 | PaaS mobile dark subscription-confirm 列表项不可辨认 | SDPCSCIR-05 · RESP-05 |
| BI 指标推送通道订阅确认/幂等重放截图矩阵 | `tailadmin-bi-analytics` + 八视口双主题 subscription-confirm/idempotent-replay 截图 | BI mobile dark idempotent-replay framing 错位 | SDPCSCIR-06 · VIS-06 |
| DevOps 推送通道订阅确认/幂等重放截图矩阵 | `scenario-devops` + 八视口 subscription-confirm/idempotent-replay 可见 | DevOps mobile dark idempotent-replay 无幂等重放详情 CTA | SDPCSCIR-07 · ASYNC-07 |
| Gateway 推送通道订阅确认/幂等重放截图矩阵 | `scenario-gateway` + 八视口 subscription-confirm/idempotent-replay 可见 | Gateway mobile dark subscription-confirm banner 层级丢失 | SDPCSCIR-08 · A11Y-08 |
| Governance 推送通道订阅确认/幂等重放截图矩阵 | `scenario-governance` + 八视口 subscription-confirm/idempotent-replay 可见 | Governance mobile dark idempotent-replay 面板越界 | SDPCSCIR-09 · RESP-09 |
| 推送通道订阅确认/幂等重放 tablet/mobile light/dark 独立截图束 | `scenarioDomainPushChannelSubscriptionConfirmIdempotentReplayViewportLightDarkScreenshotStates.pushChannelSubscriptionConfirmIdempotentReplayStateMatrixComplete = true` + 40 张 `-subscription-confirm.png`/`-idempotent-replay.png` | 缺任一域 tablet/mobile dark subscription-confirm 或 idempotent-replay 截图 | SDPCSCIR-10 · VAL-* |

## 场景域推送通道背压/队列积压 tablet/mobile light/dark 独立截图选型（G116）

> 与 `scenario-domain-push-channel-backpressure-queue-viewport-light-dark-screenshot-review-checklist.md`（SDPCBQ-01～05）组合使用；完整场景域推送通道背压/队列积压 tablet/mobile light/dark 独立截图评审 = SDPCBQ-01～10。详见 `scene-scenario-domain-push-channel-backpressure-queue-viewport-light-dark-screenshot-review-checklist.md`。

| 业务意图 | 优先模式 | 不要使用 | 判断规则 |
|---|---|---|---|
| BI 指标推送通道背压/队列积压 tablet/mobile 截图 | `scenario-bi-domain-tablet-backpressure-active.png` + `scenario-bi-domain-mobile-dark-queue-drained.png` | 用静态文案代替真实 backpressure-active/queue-drained 态或缺 golden | SDPCBQ-01 · LOGIC-06 |
| DevOps 阶段推送通道背压/队列积压 tablet/mobile 截图 | `scenario-devops-domain-{tablet,mobile}{,-dark}-{backpressure-active,queue-drained}.png` + 阶段背压 banner/队列排空摘要 | DevOps mobile dark queue-drained banner 不可辨认 | SDPCBQ-02 · ASYNC-07 |
| Gateway 端点推送通道背压/队列积压 tablet/mobile 截图 | `scenario-gateway-domain-{tablet,mobile}{,-dark}-{backpressure-active,queue-drained}.png` + 端点 backpressure-active/queue-drained 摘要 | Gateway mobile dark backpressure-active banner 对比度不足 | SDPCBQ-03 · LOGIC-08 |
| Governance 审计行推送通道背压/队列积压 tablet/mobile 截图 | `scenario-governance-domain-{tablet,mobile}{,-dark}-{backpressure-active,queue-drained}.png` + 审计 backpressure-active/queue-drained 摘要 | Governance mobile dark queue-drained 文案裁切 | SDPCBQ-04 · COPY-09 |
| PaaS 容量推送通道背压/队列积压 tablet/mobile 截图 | `scenario-paas-domain-{tablet,mobile}{,-dark}-{backpressure-active,queue-drained}.png` + 容量 backpressure-active/queue-drained 摘要 | PaaS mobile dark backpressure-active 列表项不可辨认 | SDPCBQ-05 · RESP-05 |
| BI 指标推送通道背压/队列积压截图矩阵 | `tailadmin-bi-analytics` + 八视口双主题 backpressure-active/queue-drained 截图 | BI mobile dark queue-drained framing 错位 | SDPCBQ-06 · VIS-06 |
| DevOps 推送通道背压/队列积压截图矩阵 | `scenario-devops` + 八视口 backpressure-active/queue-drained 可见 | DevOps mobile dark queue-drained 无队列排空详情 CTA | SDPCBQ-07 · ASYNC-07 |
| Gateway 推送通道背压/队列积压截图矩阵 | `scenario-gateway` + 八视口 backpressure-active/queue-drained 可见 | Gateway mobile dark backpressure-active banner 层级丢失 | SDPCBQ-08 · A11Y-08 |
| Governance 推送通道背压/队列积压截图矩阵 | `scenario-governance` + 八视口 backpressure-active/queue-drained 可见 | Governance mobile dark queue-drained 面板越界 | SDPCBQ-09 · RESP-09 |
| 推送通道背压/队列积压 tablet/mobile light/dark 独立截图束 | `scenarioDomainPushChannelBackpressureQueueViewportLightDarkScreenshotStates.pushChannelBackpressureQueueStateMatrixComplete = true` + 40 张 `-backpressure-active.png`/`-queue-drained.png` | 缺任一域 tablet/mobile dark backpressure-active 或 queue-drained 截图 | SDPCBQ-10 · VAL-* |

## 场景域推送通道熔断/限流 tablet/mobile light/dark 独立截图选型（G115）

> 与 `scenario-domain-push-channel-circuit-breaker-rate-limit-viewport-light-dark-screenshot-review-checklist.md`（SDPCBRL-01～05）组合使用；完整场景域推送通道熔断/限流 tablet/mobile light/dark 独立截图评审 = SDPCBRL-01～10。详见 `scene-scenario-domain-push-channel-circuit-breaker-rate-limit-viewport-light-dark-screenshot-review-checklist.md`。

| 业务意图 | 优先模式 | 不要使用 | 判断规则 |
|---|---|---|---|
| BI 指标推送通道熔断/限流 tablet/mobile 截图 | `scenario-bi-domain-tablet-channel-breaker-open.png` + `scenario-bi-domain-mobile-dark-rate-limit-released.png` | 用静态文案代替真实 channel-breaker-open/rate-limit-released 态或缺 golden | SDPCBRL-01 · LOGIC-06 |
| DevOps 阶段推送通道熔断/限流 tablet/mobile 截图 | `scenario-devops-domain-{tablet,mobile}{,-dark}-{channel-breaker-open,rate-limit-released}.png` + 阶段熔断 banner/限流解除摘要 | DevOps mobile dark rate-limit-released banner 不可辨认 | SDPCBRL-02 · ASYNC-07 |
| Gateway 端点推送通道熔断/限流 tablet/mobile 截图 | `scenario-gateway-domain-{tablet,mobile}{,-dark}-{channel-breaker-open,rate-limit-released}.png` + 端点 channel-breaker-open/rate-limit-released 摘要 | Gateway mobile dark channel-breaker-open banner 对比度不足 | SDPCBRL-03 · LOGIC-08 |
| Governance 审计行推送通道熔断/限流 tablet/mobile 截图 | `scenario-governance-domain-{tablet,mobile}{,-dark}-{channel-breaker-open,rate-limit-released}.png` + 审计 channel-breaker-open/rate-limit-released 摘要 | Governance mobile dark rate-limit-released 文案裁切 | SDPCBRL-04 · COPY-09 |
| PaaS 容量推送通道熔断/限流 tablet/mobile 截图 | `scenario-paas-domain-{tablet,mobile}{,-dark}-{channel-breaker-open,rate-limit-released}.png` + 容量 channel-breaker-open/rate-limit-released 摘要 | PaaS mobile dark channel-breaker-open 列表项不可辨认 | SDPCBRL-05 · RESP-05 |
| BI 指标推送通道熔断/限流截图矩阵 | `tailadmin-bi-analytics` + 八视口双主题 channel-breaker-open/rate-limit-released 截图 | BI mobile dark rate-limit-released framing 错位 | SDPCBRL-06 · VIS-06 |
| DevOps 推送通道熔断/限流截图矩阵 | `scenario-devops` + 八视口 channel-breaker-open/rate-limit-released 可见 | DevOps mobile dark rate-limit-released 无限流解除详情 CTA | SDPCBRL-07 · ASYNC-07 |
| Gateway 推送通道熔断/限流截图矩阵 | `scenario-gateway` + 八视口 channel-breaker-open/rate-limit-released 可见 | Gateway mobile dark channel-breaker-open banner 层级丢失 | SDPCBRL-08 · A11Y-08 |
| Governance 推送通道熔断/限流截图矩阵 | `scenario-governance` + 八视口 channel-breaker-open/rate-limit-released 可见 | Governance mobile dark rate-limit-released 面板越界 | SDPCBRL-09 · RESP-09 |
| 推送通道熔断/限流 tablet/mobile light/dark 独立截图束 | `scenarioDomainPushChannelCircuitBreakerRateLimitViewportLightDarkScreenshotStates.pushChannelCircuitBreakerRateLimitStateMatrixComplete = true` + 40 张 `-channel-breaker-open.png`/`-rate-limit-released.png` | 缺任一域 tablet/mobile dark channel-breaker-open 或 rate-limit-released 截图 | SDPCBRL-10 · VAL-* |

## 场景域推送通道降级/恢复 tablet/mobile light/dark 独立截图选型（G114）

> 与 `scenario-domain-push-channel-degradation-recovery-viewport-light-dark-screenshot-review-checklist.md`（SDPCDR-01～05）组合使用；完整场景域推送通道降级/恢复 tablet/mobile light/dark 独立截图评审 = SDPCDR-01～10。详见 `scene-scenario-domain-push-channel-degradation-recovery-viewport-light-dark-screenshot-review-checklist.md`。

| 业务意图 | 优先模式 | 不要使用 | 判断规则 |
|---|---|---|---|
| BI 指标推送通道降级/恢复 tablet/mobile 截图 | `scenario-bi-domain-tablet-channel-degraded.png` + `scenario-bi-domain-mobile-dark-channel-recovered.png` | 用静态文案代替真实 channel-degraded/channel-recovered 态或缺 golden | SDPCDR-01 · LOGIC-06 |
| DevOps 阶段推送通道降级/恢复 tablet/mobile 截图 | `scenario-devops-domain-{tablet,mobile}{,-dark}-{channel-degraded,channel-recovered}.png` + 阶段降级 banner/恢复完成摘要 | DevOps mobile dark recovered banner 不可辨认 | SDPCDR-02 · ASYNC-07 |
| Gateway 端点推送通道降级/恢复 tablet/mobile 截图 | `scenario-gateway-domain-{tablet,mobile}{,-dark}-{channel-degraded,channel-recovered}.png` + 端点 channel-degraded/recovered 摘要 | Gateway mobile dark channel-degraded banner 对比度不足 | SDPCDR-03 · LOGIC-08 |
| Governance 审计行推送通道降级/恢复 tablet/mobile 截图 | `scenario-governance-domain-{tablet,mobile}{,-dark}-{channel-degraded,channel-recovered}.png` + 审计 channel-degraded/recovered 摘要 | Governance mobile dark recovered 文案裁切 | SDPCDR-04 · COPY-09 |
| PaaS 容量推送通道降级/恢复 tablet/mobile 截图 | `scenario-paas-domain-{tablet,mobile}{,-dark}-{channel-degraded,channel-recovered}.png` + 容量 channel-degraded/recovered 摘要 | PaaS mobile dark channel-degraded 列表项不可辨认 | SDPCDR-05 · RESP-05 |
| BI 指标推送通道降级/恢复截图矩阵 | `tailadmin-bi-analytics` + 八视口双主题 channel-degraded/channel-recovered 截图 | BI mobile dark recovered framing 错位 | SDPCDR-06 · VIS-06 |
| DevOps 推送通道降级/恢复截图矩阵 | `scenario-devops` + 八视口 channel-degraded/channel-recovered 可见 | DevOps mobile dark recovered 无查看恢复详情 CTA | SDPCDR-07 · ASYNC-07 |
| Gateway 推送通道降级/恢复截图矩阵 | `scenario-gateway` + 八视口 channel-degraded/channel-recovered 可见 | Gateway mobile dark channel-degraded banner 层级丢失 | SDPCDR-08 · A11Y-08 |
| Governance 推送通道降级/恢复截图矩阵 | `scenario-governance` + 八视口 channel-degraded/channel-recovered 可见 | Governance mobile dark recovered 面板越界 | SDPCDR-09 · RESP-09 |
| 推送通道降级/恢复 tablet/mobile light/dark 独立截图束 | `scenarioDomainPushChannelDegradationRecoveryViewportLightDarkScreenshotStates.pushChannelDegradationRecoveryStateMatrixComplete = true` + 40 张 `-channel-degraded.png`/`-channel-recovered.png` | 缺任一域 tablet/mobile dark channel-degraded 或 channel-recovered 截图 | SDPCDR-10 · VAL-* |

## 场景域 SSE 重连/背压释放 tablet/mobile light/dark 独立截图选型（G112）

> 与 `scenario-domain-sse-reconnect-backpressure-viewport-light-dark-screenshot-review-checklist.md`（SDSRB-01～05）组合使用；完整场景域 SSE 重连/背压释放 tablet/mobile light/dark 独立截图评审 = SDSRB-01～10。详见 `scene-scenario-domain-sse-reconnect-backpressure-viewport-light-dark-screenshot-review-checklist.md`。

| 业务意图 | 优先模式 | 不要使用 | 判断规则 |
|---|---|---|---|
| BI 指标 SSE 重连/背压释放 tablet/mobile 截图 | `scenario-bi-domain-tablet-sse-reconnecting.png` + `scenario-bi-domain-mobile-dark-backpressure-released.png` | 用静态文案代替真实 sse-reconnecting/backpressure-released 态或缺 golden | SDSRB-01 · LOGIC-06 |
| DevOps 阶段 SSE 重连/背压释放 tablet/mobile 截图 | `scenario-devops-domain-{tablet,mobile}{,-dark}-{sse-reconnecting,backpressure-released}.png` + 阶段重连 banner/背压释放摘要 | DevOps mobile dark released banner 不可辨认 | SDSRB-02 · ASYNC-07 |
| Gateway 端点 SSE 重连/背压释放 tablet/mobile 截图 | `scenario-gateway-domain-{tablet,mobile}{,-dark}-{sse-reconnecting,backpressure-released}.png` + 端点 sse-reconnecting/released 摘要 | Gateway mobile dark sse-reconnecting banner 对比度不足 | SDSRB-03 · LOGIC-08 |
| Governance 审计行 SSE 重连/背压释放 tablet/mobile 截图 | `scenario-governance-domain-{tablet,mobile}{,-dark}-{sse-reconnecting,backpressure-released}.png` + 审计 sse-reconnecting/released 摘要 | Governance mobile dark released 文案裁切 | SDSRB-04 · COPY-09 |
| PaaS 容量 SSE 重连/背压释放 tablet/mobile 截图 | `scenario-paas-domain-{tablet,mobile}{,-dark}-{sse-reconnecting,backpressure-released}.png` + 容量 sse-reconnecting/released 摘要 | PaaS mobile dark sse-reconnecting 列表项不可辨认 | SDSRB-05 · RESP-05 |
| BI 指标 SSE 重连/背压释放截图矩阵 | `tailadmin-bi-analytics` + 八视口双主题 sse-reconnecting/backpressure-released 截图 | BI mobile dark released framing 错位 | SDSRB-06 · VIS-06 |
| DevOps SSE 重连/背压释放截图矩阵 | `scenario-devops` + 八视口 sse-reconnecting/backpressure-released 可见 | DevOps mobile dark released 无查看重连详情 CTA | SDSRB-07 · ASYNC-07 |
| Gateway SSE 重连/背压释放截图矩阵 | `scenario-gateway` + 八视口 sse-reconnecting/backpressure-released 可见 | Gateway mobile dark sse-reconnecting banner 层级丢失 | SDSRB-08 · A11Y-08 |
| Governance SSE 重连/背压释放截图矩阵 | `scenario-governance` + 八视口 sse-reconnecting/backpressure-released 可见 | Governance mobile dark released 面板越界 | SDSRB-09 · RESP-09 |
| SSE 重连/背压释放 tablet/mobile light/dark 独立截图束 | `scenarioDomainSseReconnectBackpressureViewportLightDarkScreenshotStates.sseReconnectBackpressureStateMatrixComplete = true` + 40 张 `-sse-reconnecting.png`/`-backpressure-released.png` | 缺任一域 tablet/mobile dark sse-reconnecting 或 backpressure-released 截图 | SDSRB-10 · VAL-* |

## 场景域 WebSocket 重连/熔断恢复 tablet/mobile light/dark 独立截图选型（G111）

> 与 `scenario-domain-websocket-reconnect-circuit-breaker-viewport-light-dark-screenshot-review-checklist.md`（SDWRCB-01～05）组合使用；完整场景域 WebSocket 重连/熔断恢复 tablet/mobile light/dark 独立截图评审 = SDWRCB-01～10。详见 `scene-scenario-domain-websocket-reconnect-circuit-breaker-viewport-light-dark-screenshot-review-checklist.md`。

| 业务意图 | 优先模式 | 不要使用 | 判断规则 |
|---|---|---|---|
| BI 指标 WebSocket 重连/熔断恢复 tablet/mobile 截图 | `scenario-bi-domain-tablet-reconnecting.png` + `scenario-bi-domain-mobile-dark-circuit-closed.png` | 用静态文案代替真实 reconnecting/circuit-closed 态或缺 golden | SDWRCB-01 · LOGIC-06 |
| DevOps 阶段 WebSocket 重连/熔断恢复 tablet/mobile 截图 | `scenario-devops-domain-{tablet,mobile}{,-dark}-{reconnecting,circuit-closed}.png` + 阶段重连 banner/熔断闭合摘要 | DevOps mobile dark closed banner 不可辨认 | SDWRCB-02 · ASYNC-07 |
| Gateway 端点 WebSocket 重连/熔断恢复 tablet/mobile 截图 | `scenario-gateway-domain-{tablet,mobile}{,-dark}-{reconnecting,circuit-closed}.png` + 端点 reconnecting/closed 摘要 | Gateway mobile dark reconnecting banner 对比度不足 | SDWRCB-03 · LOGIC-08 |
| Governance 审计行 WebSocket 重连/熔断恢复 tablet/mobile 截图 | `scenario-governance-domain-{tablet,mobile}{,-dark}-{reconnecting,circuit-closed}.png` + 审计 reconnecting/closed 摘要 | Governance mobile dark closed 文案裁切 | SDWRCB-04 · COPY-09 |
| PaaS 容量 WebSocket 重连/熔断恢复 tablet/mobile 截图 | `scenario-paas-domain-{tablet,mobile}{,-dark}-{reconnecting,circuit-closed}.png` + 容量 reconnecting/closed 摘要 | PaaS mobile dark reconnecting 列表项不可辨认 | SDWRCB-05 · RESP-05 |
| BI 指标 WebSocket 重连/熔断恢复截图矩阵 | `tailadmin-bi-analytics` + 八视口双主题 reconnecting/circuit-closed 截图 | BI mobile dark closed framing 错位 | SDWRCB-06 · VIS-06 |
| DevOps WebSocket 重连/熔断恢复截图矩阵 | `scenario-devops` + 八视口 reconnecting/circuit-closed 可见 | DevOps mobile dark closed 无查看重连详情 CTA | SDWRCB-07 · ASYNC-07 |
| Gateway WebSocket 重连/熔断恢复截图矩阵 | `scenario-gateway` + 八视口 reconnecting/circuit-closed 可见 | Gateway mobile dark reconnecting banner 层级丢失 | SDWRCB-08 · A11Y-08 |
| Governance WebSocket 重连/熔断恢复截图矩阵 | `scenario-governance` + 八视口 reconnecting/circuit-closed 可见 | Governance mobile dark closed 面板越界 | SDWRCB-09 · RESP-09 |
| WebSocket 重连/熔断恢复 tablet/mobile light/dark 独立截图束 | `scenarioDomainWebsocketReconnectCircuitBreakerViewportLightDarkScreenshotStates.websocketReconnectCircuitBreakerStateMatrixComplete = true` + 40 张 `-reconnecting.png`/`-circuit-closed.png` | 缺任一域 tablet/mobile dark reconnecting 或 circuit-closed 截图 | SDWRCB-10 · VAL-* |

## 场景域断连重试/心跳超时 tablet/mobile light/dark 独立截图选型（G110）

> 与 `scenario-domain-disconnect-retry-heartbeat-timeout-viewport-light-dark-screenshot-review-checklist.md`（SDRHT-01～05）组合使用；完整场景域断连重试/心跳超时 tablet/mobile light/dark 独立截图评审 = SDRHT-01～10。详见 `scene-scenario-domain-disconnect-retry-heartbeat-timeout-viewport-light-dark-screenshot-review-checklist.md`。

| 业务意图 | 优先模式 | 不要使用 | 判断规则 |
|---|---|---|---|
| BI 指标断连重试/心跳超时 tablet/mobile 截图 | `scenario-bi-domain-tablet-retrying.png` + `scenario-bi-domain-mobile-dark-heartbeat-restored.png` | 用静态文案代替真实 retrying/heartbeat-restored 态或缺 golden | SDRHT-01 · LOGIC-06 |
| DevOps 阶段断连重试/心跳超时 tablet/mobile 截图 | `scenario-devops-domain-{tablet,mobile}{,-dark}-{retrying,heartbeat-restored}.png` + 阶段重试 banner/心跳恢复摘要 | DevOps mobile dark restored banner 不可辨认 | SDRHT-02 · ASYNC-07 |
| Gateway 端点断连重试/心跳超时 tablet/mobile 截图 | `scenario-gateway-domain-{tablet,mobile}{,-dark}-{retrying,heartbeat-restored}.png` + 端点 retrying/restored 摘要 | Gateway mobile dark retrying banner 对比度不足 | SDRHT-03 · LOGIC-08 |
| Governance 审计行断连重试/心跳超时 tablet/mobile 截图 | `scenario-governance-domain-{tablet,mobile}{,-dark}-{retrying,heartbeat-restored}.png` + 审计 retrying/restored 摘要 | Governance mobile dark restored 文案裁切 | SDRHT-04 · COPY-09 |
| PaaS 容量断连重试/心跳超时 tablet/mobile 截图 | `scenario-paas-domain-{tablet,mobile}{,-dark}-{retrying,heartbeat-restored}.png` + 容量 retrying/restored 摘要 | PaaS mobile dark retrying 列表项不可辨认 | SDRHT-05 · RESP-05 |
| BI 指标断连重试/心跳超时截图矩阵 | `tailadmin-bi-analytics` + 八视口双主题 retrying/heartbeat-restored 截图 | BI mobile dark restored framing 错位 | SDRHT-06 · VIS-06 |
| DevOps 断连重试/心跳超时截图矩阵 | `scenario-devops` + 八视口 retrying/heartbeat-restored 可见 | DevOps mobile dark restored 无查看重试详情 CTA | SDRHT-07 · ASYNC-07 |
| Gateway 断连重试/心跳超时截图矩阵 | `scenario-gateway` + 八视口 retrying/heartbeat-restored 可见 | Gateway mobile dark retrying banner 层级丢失 | SDRHT-08 · A11Y-08 |
| Governance 断连重试/心跳超时截图矩阵 | `scenario-governance` + 八视口 retrying/heartbeat-restored 可见 | Governance mobile dark restored 面板越界 | SDRHT-09 · RESP-09 |
| 断连重试/心跳超时 tablet/mobile light/dark 独立截图束 | `scenarioDomainDisconnectRetryHeartbeatViewportLightDarkScreenshotStates.disconnectRetryHeartbeatStateMatrixComplete = true` + 40 张 `-retrying.png`/`-heartbeat-restored.png` | 缺任一域 tablet/mobile dark retrying 或 heartbeat-restored 截图 | SDRHT-10 · VAL-* |

## 场景域 network partition/recovery tablet/mobile light/dark 独立截图选型（G109）

> 与 `scenario-domain-network-partition-recovery-viewport-light-dark-screenshot-review-checklist.md`（SDNPR-01～05）组合使用；完整场景域 network partition/recovery tablet/mobile light/dark 独立截图评审 = SDNPR-01～10。详见 `scene-scenario-domain-network-partition-recovery-viewport-light-dark-screenshot-review-checklist.md`。

| 业务意图 | 优先模式 | 不要使用 | 判断规则 |
|---|---|---|---|
| BI 指标 network partition/recovery tablet/mobile 截图 | `scenario-bi-domain-tablet-partitioned.png` + `scenario-bi-domain-mobile-dark-recovered.png` | 用静态文案代替真实 partitioned/recovered 态或缺 golden | SDNPR-01 · LOGIC-06 |
| DevOps 阶段 network partition/recovery tablet/mobile 截图 | `scenario-devops-domain-{tablet,mobile}{,-dark}-{partitioned,recovered}.png` + 阶段分区 banner/恢复完成摘要 | DevOps mobile dark recovered banner 不可辨认 | SDNPR-02 · ASYNC-07 |
| Gateway 端点 network partition/recovery tablet/mobile 截图 | `scenario-gateway-domain-{tablet,mobile}{,-dark}-{partitioned,recovered}.png` + 端点 partitioned/recovered 摘要 | Gateway mobile dark partitioned banner 对比度不足 | SDNPR-03 · LOGIC-08 |
| Governance 审计行 network partition/recovery tablet/mobile 截图 | `scenario-governance-domain-{tablet,mobile}{,-dark}-{partitioned,recovered}.png` + 审计 partitioned/recovered 摘要 | Governance mobile dark recovered 文案裁切 | SDNPR-04 · COPY-09 |
| PaaS 容量 network partition/recovery tablet/mobile 截图 | `scenario-paas-domain-{tablet,mobile}{,-dark}-{partitioned,recovered}.png` + 容量 partitioned/recovered 摘要 | PaaS mobile dark partitioned 列表项不可辨认 | SDNPR-05 · RESP-05 |
| BI 指标 network partition/recovery 截图矩阵 | `tailadmin-bi-analytics` + 八视口双主题 partitioned/recovered 截图 | BI mobile dark recovered framing 错位 | SDNPR-06 · VIS-06 |
| DevOps network partition/recovery 截图矩阵 | `scenario-devops` + 八视口 partitioned/recovered 可见 | DevOps mobile dark recovered 无查看恢复详情 CTA | SDNPR-07 · ASYNC-07 |
| Gateway network partition/recovery 截图矩阵 | `scenario-gateway` + 八视口 partitioned/recovered 可见 | Gateway mobile dark partitioned banner 层级丢失 | SDNPR-08 · A11Y-08 |
| Governance network partition/recovery 截图矩阵 | `scenario-governance` + 八视口 partitioned/recovered 可见 | Governance mobile dark recovered 面板越界 | SDNPR-09 · RESP-09 |
| network partition/recovery tablet/mobile light/dark 独立截图束 | `scenarioDomainNetworkPartitionRecoveryViewportLightDarkScreenshotStates.networkPartitionRecoveryStateMatrixComplete = true` + 40 张 `-partitioned.png`/`-recovered.png` | 缺任一域 tablet/mobile dark partitioned 或 recovered 截图 | SDNPR-10 · VAL-* |

## 场景域 offline/sync conflict tablet/mobile light/dark 独立截图选型（G108）

> 与 `scenario-domain-offline-sync-conflict-viewport-light-dark-screenshot-review-checklist.md`（SDOSC-01～05）组合使用；完整场景域 offline/sync conflict tablet/mobile light/dark 独立截图评审 = SDOSC-01～10。详见 `scene-scenario-domain-offline-sync-conflict-viewport-light-dark-screenshot-review-checklist.md`。

| 业务意图 | 优先模式 | 不要使用 | 判断规则 |
|---|---|---|---|
| BI 指标 offline/sync conflict tablet/mobile 截图 | `scenario-bi-domain-tablet-offline.png` + `scenario-bi-domain-mobile-dark-synced.png` | 用静态文案代替真实 offline/synced 态或缺 golden | SDOSC-01 · LOGIC-06 |
| DevOps 阶段 offline/sync conflict tablet/mobile 截图 | `scenario-devops-domain-{tablet,mobile}{,-dark}-{offline,synced}.png` + 阶段离线 banner/同步完成摘要 | DevOps mobile dark synced banner 不可辨认 | SDOSC-02 · ASYNC-07 |
| Gateway 端点 offline/sync conflict tablet/mobile 截图 | `scenario-gateway-domain-{tablet,mobile}{,-dark}-{offline,synced}.png` + 端点 offline/synced 摘要 | Gateway mobile dark offline banner 对比度不足 | SDOSC-03 · LOGIC-08 |
| Governance 审计行 offline/sync conflict tablet/mobile 截图 | `scenario-governance-domain-{tablet,mobile}{,-dark}-{offline,synced}.png` + 审计 offline/synced 摘要 | Governance mobile dark synced 文案裁切 | SDOSC-04 · COPY-09 |
| PaaS 容量 offline/sync conflict tablet/mobile 截图 | `scenario-paas-domain-{tablet,mobile}{,-dark}-{offline,synced}.png` + 容量 offline/synced 摘要 | PaaS mobile dark offline 列表项不可辨认 | SDOSC-05 · RESP-05 |
| BI 指标 offline/sync conflict 截图矩阵 | `tailadmin-bi-analytics` + 八视口双主题 offline/synced 截图 | BI mobile dark synced framing 错位 | SDOSC-06 · VIS-06 |
| DevOps offline/sync conflict 截图矩阵 | `scenario-devops` + 八视口 offline/synced 可见 | DevOps mobile dark synced 无查看同步详情 CTA | SDOSC-07 · ASYNC-07 |
| Gateway offline/sync conflict 截图矩阵 | `scenario-gateway` + 八视口 offline/synced 可见 | Gateway mobile dark offline banner 层级丢失 | SDOSC-08 · A11Y-08 |
| Governance offline/sync conflict 截图矩阵 | `scenario-governance` + 八视口 offline/synced 可见 | Governance mobile dark synced 面板越界 | SDOSC-09 · RESP-09 |
| offline/sync conflict tablet/mobile light/dark 独立截图束 | `scenarioDomainOfflineSyncConflictViewportLightDarkScreenshotStates.offlineSyncConflictStateMatrixComplete = true` + 40 张 `-offline.png`/`-synced.png` | 缺任一域 tablet/mobile dark offline 或 synced 截图 | SDOSC-10 · VAL-* |

## 场景域 conflict/merge tablet/mobile light/dark 独立截图选型（G107）

> 与 `scenario-domain-conflict-merge-viewport-light-dark-screenshot-review-checklist.md`（SDCM-01～05）组合使用；完整场景域 conflict/merge tablet/mobile light/dark 独立截图评审 = SDCM-01～10。详见 `scene-scenario-domain-conflict-merge-viewport-light-dark-screenshot-review-checklist.md`。

| 业务意图 | 优先模式 | 不要使用 | 判断规则 |
|---|---|---|---|
| BI 指标 conflict/merge tablet/mobile 截图 | `scenario-bi-domain-tablet-conflict.png` + `scenario-bi-domain-mobile-dark-merged.png` | 用静态文案代替真实 conflict/merged 态或缺 golden | SDCM-01 · LOGIC-06 |
| DevOps 阶段 conflict/merge tablet/mobile 截图 | `scenario-devops-domain-{tablet,mobile}{,-dark}-{conflict,merged}.png` + 阶段冲突 banner/合并完成摘要 | DevOps mobile dark merged banner 不可辨认 | SDCM-02 · ASYNC-07 |
| Gateway 端点 conflict/merge tablet/mobile 截图 | `scenario-gateway-domain-{tablet,mobile}{,-dark}-{conflict,merged}.png` + 端点 conflict/merge 摘要 | Gateway mobile dark conflict banner 对比度不足 | SDCM-03 · LOGIC-08 |
| Governance 审计行 conflict/merge tablet/mobile 截图 | `scenario-governance-domain-{tablet,mobile}{,-dark}-{conflict,merged}.png` + 审计 conflict/merge 摘要 | Governance mobile dark merged 文案裁切 | SDCM-04 · COPY-09 |
| PaaS 容量 conflict/merge tablet/mobile 截图 | `scenario-paas-domain-{tablet,mobile}{,-dark}-{conflict,merged}.png` + 容量 conflict/merge 摘要 | PaaS mobile dark conflict 列表项不可辨认 | SDCM-05 · RESP-05 |
| BI 指标 conflict/merge 截图矩阵 | `tailadmin-bi-analytics` + 八视口双主题 conflict/merged 截图 | BI mobile dark merged framing 错位 | SDCM-06 · VIS-06 |
| DevOps conflict/merge 截图矩阵 | `scenario-devops` + 八视口 conflict/merged 可见 | DevOps mobile dark merged 无查看详情 CTA | SDCM-07 · ASYNC-07 |
| Gateway conflict/merge 截图矩阵 | `scenario-gateway` + 八视口 conflict/merged 可见 | Gateway mobile dark conflict banner 层级丢失 | SDCM-08 · A11Y-08 |
| Governance conflict/merge 截图矩阵 | `scenario-governance` + 八视口 conflict/merged 可见 | Governance mobile dark merged 面板越界 | SDCM-09 · RESP-09 |
| conflict/merge tablet/mobile light/dark 独立截图束 | `scenarioDomainConflictMergeViewportLightDarkScreenshotStates.conflictMergeStateMatrixComplete = true` + 40 张 `-conflict.png`/`-merged.png` | 缺任一域 tablet/mobile dark conflict 或 merged 截图 | SDCM-10 · VAL-* |

## 场景域 mutation pending/rollback tablet/mobile light/dark 独立截图选型（G106）

> 与 `scenario-domain-mutation-rollback-viewport-light-dark-screenshot-review-checklist.md`（SDMR-01～05）组合使用；完整场景域 mutation pending/rollback tablet/mobile light/dark 独立截图评审 = SDMR-01～10。详见 `scene-scenario-domain-mutation-rollback-viewport-light-dark-screenshot-review-checklist.md`。

| 业务意图 | 优先模式 | 不要使用 | 判断规则 |
|---|---|---|---|
| BI 指标 mutation pending/rollback tablet/mobile 截图 | `scenario-bi-domain-tablet-mutation-pending.png` + `scenario-bi-domain-mobile-dark-rollback.png` | 用静态文案代替真实 mutation pending/rollback 态或缺 golden | SDMR-01 · LOGIC-06 |
| DevOps 阶段 mutation pending/rollback tablet/mobile 截图 | `scenario-devops-domain-{tablet,mobile}{,-dark}-{mutation-pending,rollback}.png` + 阶段提交 spinner/回滚摘要 | DevOps mobile dark rollback banner 不可辨认 | SDMR-02 · ASYNC-07 |
| Gateway 端点 mutation pending/rollback tablet/mobile 截图 | `scenario-gateway-domain-{tablet,mobile}{,-dark}-{mutation-pending,rollback}.png` + 端点 mutation pending/rollback 摘要 | Gateway mobile dark mutation-pending spinner 对比度不足 | SDMR-03 · LOGIC-08 |
| Governance 审计行 mutation pending/rollback tablet/mobile 截图 | `scenario-governance-domain-{tablet,mobile}{,-dark}-{mutation-pending,rollback}.png` + 审计 mutation pending/rollback 摘要 | Governance mobile dark rollback 文案裁切 | SDMR-04 · COPY-09 |
| PaaS 容量 mutation pending/rollback tablet/mobile 截图 | `scenario-paas-domain-{tablet,mobile}{,-dark}-{mutation-pending,rollback}.png` + 容量 mutation pending/rollback 摘要 | PaaS mobile dark mutation-pending 列表项不可辨认 | SDMR-05 · RESP-05 |
| BI 指标 mutation pending/rollback 截图矩阵 | `tailadmin-bi-analytics` + 八视口双主题 mutation pending/rollback 截图 | BI mobile dark rollback framing 错位 | SDMR-06 · VIS-06 |
| DevOps mutation pending/rollback 截图矩阵 | `scenario-devops` + 八视口 mutation pending/rollback 可见 | DevOps mobile dark rollback 无恢复 CTA | SDMR-07 · ASYNC-07 |
| Gateway mutation pending/rollback 截图矩阵 | `scenario-gateway` + 八视口 mutation pending/rollback 可见 | Gateway mobile dark mutation-pending spinner 层级丢失 | SDMR-08 · A11Y-08 |
| Governance mutation pending/rollback 截图矩阵 | `scenario-governance` + 八视口 mutation pending/rollback 可见 | Governance mobile dark rollback 面板越界 | SDMR-09 · RESP-09 |
| mutation pending/rollback tablet/mobile light/dark 独立截图束 | `scenarioDomainMutationRollbackViewportLightDarkScreenshotStates.mutationRollbackStateMatrixComplete = true` + 40 张 `-mutation-pending.png`/`-rollback.png` | 缺任一域 tablet/mobile dark mutation-pending 或 rollback 截图 | SDMR-10 · VAL-* |

## 场景 Page Family Visual Regression 选型（G90）

> 与 `page-family-visual-regression-review-checklist.md`（PFVR-01～05）组合使用；完整页面族视觉回归评审 = PFVR-01～10。详见 `scene-page-family-visual-regression-review-checklist.md`。

| 业务意图 | 优先模式 | 不要使用 | 判断规则 |
|---|---|---|---|
| 内容宽度利用 | 主内容区 ≥80% 宽度 + KPI/表格响应式展开 | 首屏窄列居中 + 右侧大面积空白 | PFVR-01 · RESP-01 |
| Framing 对齐 | 主内容不压入侧栏 + tab 切换后仍在主容器 | active section 左边界压入侧栏 | PFVR-02 · REV-02 |
| 文本裁切 | KPI/标题/按钮完整可见 + ellipsis 合理 | 数字或标签被遮挡、重叠、溢出 | PFVR-03 · REV-04 |
| 视口响应 | desktop 4 列 / tablet 2～3 列 / mobile 首屏可见 | 平板 KPI 全堆 1 列或移动主任务不可见 | PFVR-04 · RESP-03 |
| 主题对比 | light/dark 边框背景文字层级可辨认 | dark 下图表 grid/legend 丢失 | PFVR-05 · VIS-05 |
| 42 子页矩阵 | `verifyPageFamilyTabs` 42 tab + element screenshot | 页面族堆在单页或 tab 不可切换 | PFVR-06 · COV-06 |
| Dashboard 10 族 | 每族独立 KPI/图表/表格 + runtime chart | 10 套 dashboard 压成一个总览 | PFVR-07 · PAT-07 |
| Layout 移动层 | Layout Five Backdrop + 收起侧栏宽度扩展 | 移动层 framing 错位或内容压侧栏 | PFVR-08 · RESP-08 |
| BI Builder 首屏 | Chart Builder fullPage ≥80% 宽度 + 10 runtime | Builder 首屏大面积空白 | PFVR-09 · RESP-09 |
| 视觉回归束 | `pageFamilyVisualRegressionStates` + 五门禁截图 | 缺 visual regression gates 仅 tab 截图 | PFVR-10 · VAL-* |

## 场景 UiElements Empty / Error / Loading 选型（G87）

> 与 `ui-elements-empty-error-loading-review-checklist.md`（EEL-01～05）组合使用；完整 UiElements 失败态评审 = EEL-01～10。详见 `scene-ui-elements-empty-error-loading-review-checklist.md`。

| 业务意图 | 优先模式 | 不要使用 | 判断规则 |
|---|---|---|---|
| 空列表/空通知 | 中文标题 + 辅助说明 + 可选 CTA（新建/刷新） | 空白区域或英文 `No data` | EEL-01 · COPY-02 |
| 内联错误 | 中文原因 + 重试/关闭 + `aria-invalid`/`role="alert"` | `console.error` 静默或英文 `Error` | EEL-02 · ASYNC-01 |
| Loading 结构 | Skeleton 保留行高 + 按钮 disabled 内联 Spinner | 整页空白闪烁或 loading 可双提交 | EEL-03 · INTER-04 |
| 错误横幅 | 可关闭中文横幅 + `aria-live`；不永久遮挡主任务 | 永久红色条或无关闭路径 | EEL-04 · REV-05 |
| 表格 empty 区分 | 「暂无数据」vs「无匹配结果」+ 清除筛选 | empty 与筛选无结果同文案 | EEL-05 · ASYNC-02 |
| Feedback Specimen | ui-notifications/progress + live gates + `ui-elements-empty-error-loading-gates.png` | Specimen 仅 happy path | EEL-06 · FAIL-09 |
| Data Specimen | Ecommerce/Email live gates dataState 矩阵 | 表格 error 丢筛选或 loading 显示 empty | EEL-07 · ASYNC-02 |
| Chart Specimen | BI chart data empty/error + 面板非白屏 | Chart error 白屏无重试 | EEL-08 · ASYNC-05 |
| Form Specimen | async validating + submit checking + 字段 error 中文 | 提交无 checking 或字段 error 英文 | EEL-09 · ASYNC-03 |
| Specimen 22 页束 | `uiElementEmptyErrorLoadingStates` + MS live gates 矩阵 | 22 源页缺失败态门禁截图 | EEL-10 · COV-05 |

## 场景逻辑完备选型（G84）

> 与 `logic-completeness-review-checklist.md`（LOGIC-06～10 页面级）组合使用；完整场景逻辑完备评审 = LOGIC-01～10（表单 + 页面 + 场景）。详见 `scene-logic-completeness-review-checklist.md`。

| 业务意图 | 优先模式 | 不要使用 | 判断规则 |
|---|---|---|---|
| BI 筛选与下钻因果 | FilterBar chips + CrossFilterDashboard + DrillBreadcrumb 可返回 | 单图 onClick 冒充联动或下钻返回丢筛选 | LOGIC-06 · MS-11 |
| CI/CD 阶段与回滚闭环 | PipelineStageBar 阶段依赖 + LogStream/Artifact 联动 + Rollback 确认 | 阶段可跳步或 Rollback 无确认/审批流不可见 | LOGIC-07 · MS-10 |
| Gateway 探测与配额审批 | EndpointProbe 分步 + BalanceQuota 超限 disabled + License 吊销确认 | probe 无分步或配额超限仍可提交 | LOGIC-08 · MS-09 |
| PaaS 筛选与危险操作审批 | ResourceTable 筛选→地图/表一致 + ConfigDiff 对齐 + 恢复/伸缩 Dialog 审批 | 筛选与地图不一致或危险操作无 checking | LOGIC-09 · MS-12 |
| MS 场景逻辑完备束 | MS 表 LOGIC-01～10 组合闭环 + example runtime 因果链可复现 | 领域页缺 probe/审批/联动/审计闭环 | LOGIC-10 · VAL-* |

## 场景 UI 漂移选型（G83）

> 与 `ui-drift-review-checklist.md`（REV-01～05）组合使用；完整 UI 漂移评审 = REV-01～10。详见 `scene-ui-drift-review-checklist.md`。

| 业务意图 | 优先模式 | 不要使用 | 判断规则 |
|---|---|---|---|
| BI 筛选与图表视觉一致 | FilterBar chips + Chart 色板 + KPI 密度与 `bi-chart-state-gates.png` golden 一致 | KPI/Chart 密度突变、hex 硬编码或大屏占位画布 | REV-06 · DRIFT-01 |
| CI/CD 流水线场景 framing | PipelineStageBar + LogStream 固定高度 + 危险 Dialog 层级与 golden 一致 | 阶段条错位、日志 loading 贴边或 Kanban 冒充 CI/CD 视觉 | REV-07 · DRIFT-05 |
| Gateway Hub 子面板视觉 | ControlPlaneHub 子面板 KPI/表格密度 + 探测 Dialog 层级与 golden 一致 | Hub 子面板 hex 硬编码或探测 Dialog 遮挡 Tabs | REV-08 · DRIFT-03 |
| PaaS 资源与危险 Dialog 层级 | ResourceTable + Maps framing + 恢复/伸缩 Dialog 不遮挡关键列 | 恢复 Dialog 遮挡表格或 Maps/表格 framing 不一致 | REV-09 · DRIFT-02 |
| MS 场景 UI 漂移束 | MS 表 REV-01～10 组合闭环 + example runtime golden 对照 | 领域页与 runtime 截图明显不一致或 FAIL-01～10 稳定复现 | REV-10 · VAL-* |

## 场景类型完整选型（G82）

> 与 `type-api-contract-review-checklist.md`（TYPE-01～05）组合使用；完整类型契约评审 = TYPE-01～10。详见 `scene-type-api-contract-review-checklist.md`。

| 业务意图 | 优先模式 | 不要使用 | 判断规则 |
|---|---|---|---|
| BI 筛选与图表类型契约 | FilterBar chips 受控 + `getBaseChartOptions(overrides?)` + CrossFilter filter 类型联动 | Chart override 用 `any` 或 chips 裸 `string[]` 混用 | TYPE-06 · TYPE-02 |
| CI/CD 阶段与日志类型契约 | PipelineStageBar `stages` 受控 + LogStreamPanel 流式 props 类型闭合 | stages 非受控内部 state 或 LogStream 回调参数 `any` | TYPE-07 · TYPE-03 |
| Gateway Hub 子面板类型契约 | ControlPlaneHub 子面板受控 props + `onProbe` 回调类型与 api-contracts 一致 | 散落 mock 子面板无类型出口或 silent rename props | TYPE-08 · TYPE-03 |
| PaaS 资源与危险操作类型契约 | ResourceTable row type + Maps override + ConfigDiff + 危险 Dialog 回调类型齐全 | ResourceTable 无 row interface 或 Maps override 类型丢失 | TYPE-09 · TYPE-02 |
| MS 场景类型契约束 | MS 表 TYPE-01～10 组合闭环 + `audit_compat_contracts.py` exit 0 | 领域页硬编码 mock 无受控 props 类型或 `tsc` 报错 | TYPE-10 · VAL-* |

## 场景模式覆盖选型（G81）

> 与 `pattern-coverage-review-checklist.md`（PAT-01～05）组合使用；完整模式覆盖评审 = PAT-01～10。详见 `scene-pattern-coverage-review-checklist.md`。

| 业务意图 | 优先模式 | 不要使用 | 判断规则 |
|---|---|---|---|
| BI 筛选与图表布局 | `bi-filter-linkage` + CrossFilterDashboard + `data-screen-canvas` layout pattern | 散落 Card 无 layout pattern 或大屏占位画布 | PAT-06 · PAT-02 |
| CI/CD 流水线页面模式 | CicdRunDetail + master-detail-ops + PipelineStageBar 页面组合 | Kanban 冒充 CI/CD 或缺 pipeline 页面模式 | PAT-07 · PAT-05 |
| Gateway Hub 布局 | ControlPlaneHub + hub-tabs / 控制平面 layout pattern | 散落 mock Card 无 Hub 布局 | PAT-08 · PAT-03 |
| PaaS 资源与危险操作布局 | ResourceTable + detail-page + ops-danger-flow 页面模式 | 扁平表硬塞地图或每页自建 diff 区块 | PAT-09 · PAT-02 |
| MS 场景页面模式束 | MS 表 PAT-01～10 组合闭环 + preview/example runtime | 领域页缺完整 layout 或 preview 仅占位 | PAT-10 · VAL-* |

## 场景组件覆盖率选型（G80）

> 与 `component-coverage-review-checklist.md`（COV-01～05）组合使用；完整组件覆盖率评审 = COV-01～10。详见 `scene-component-coverage-review-checklist.md`。

| 业务意图 | 优先模式 | 不要使用 | 判断规则 |
|---|---|---|---|
| BI 筛选与图表模板 | FilterBar + CrossFilterDashboard/DrillDown + `templates/bi/*` + Chart theme lib | 散落 Card 无 `templates/` 路径或 Chart 仅 CSS mock | COV-06 · COV-02 |
| CI/CD 阶段与日志模板 | PipelineStageBar + LogStreamPanel + ArtifactTable `templates/devops/*` | Kanban 冒充 CI/CD 或缺领域模板 | COV-07 · COV-05 |
| Gateway probe/配额模板 | ControlPlaneHub 子面板 + `templates/gateway/*` 可复制 | 散落 mock Card 无索引登记 | COV-08 · COV-01 |
| PaaS 资源与危险操作模板 | ResourceTable + 可选 Maps + ConfigDiff + 危险 Dialog `templates/paas/*` | 扁平表硬塞地图或每页自建 destructive | COV-09 · COV-02 |
| MS 场景组件覆盖率束 | MS 表 COV-01～10 组合闭环 + preview/example runtime | 领域页缺 `templates/*/` 或 extension-audit partial | COV-10 · VAL-* |

## 场景生成一致性选型（G79）

> 与 `generation-consistency-review-checklist.md`（GEN-01～05）组合使用；完整生成一致性评审 = GEN-01～10。详见 `scene-generation-consistency-review-checklist.md`。

| 业务意图 | 优先模式 | 不要使用 | 判断规则 |
|---|---|---|---|
| BI 筛选与图表组合 | FilterBar + CrossFilterDashboard/DrillDown + chartPaletteCssVars | 单图 onClick 冒充联动或散落 Card 拼凑 | GEN-06 · SEL-01 |
| CI/CD 阶段与日志组合 | PipelineStageBar + LogStreamPanel + ArtifactTable | Kanban 或 Switch 列表冒充 CI/CD | GEN-07 · SEL-02 |
| Gateway probe/配额组合 | ControlPlaneHub 受控 props + EndpointProbeTable + BalanceQuota | 散落 mock Card 或非受控 Hub | GEN-08 · SEL-05 |
| PaaS 资源与危险操作组合 | ResourceTable + 可选 Maps + ConfigDiff + 危险 Dialog | 扁平表硬塞地图 Card 或每页自建 destructive | GEN-09 · SEL-03 |
| MS 场景生成一致性束 | MS 表 GEN-01～10 组合闭环 | 领域页模板组合/受控 props 与 MS 表不一致 | GEN-10 · VAL-* |

## 场景中文文案选型（G78）

> 与 `chinese-copy-review-checklist.md`（COPY-01～05）组合使用；完整中文文案评审 = COPY-01～10。详见 `scene-chinese-copy-review-checklist.md`。

| 业务意图 | 优先模式 | 不要使用 | 判断规则 |
|---|---|---|---|
| BI 筛选与图表 mock | FilterBar/KPI/图表标题中文 + 空态错误态中文 CTA | 英文 chips、`Chart Title` 占位、裸 `No data` | COPY-06 · MS-11 |
| CI/CD 阶段与日志 mock | 阶段/日志/制品/回滚 Dialog 中文；CI/CD 缩写可保留 | 英文阶段名、`Confirm`/`Rollback` 直译按钮 | COPY-07 · MS-10 |
| Gateway probe/配额 mock | License/端点/配额/探测 Dialog 中文 mock | 英文 License 状态或配额说明 | COPY-08 · MS-09 |
| PaaS 危险操作与 diff | ResourceTable/ConfigDiff/危险 Dialog 中文 | 英文列头、英文恢复/伸缩确认 | COPY-09 · MS-12 |
| MS 场景中文文案束 | MS 表 COPY-01～10 组合闭环 | 领域页 mock 文案与业务域不一致 | COPY-10 · VAL-* |

## 场景约束遵守选型（G77）

> 与 `constraint-compliance-review-checklist.md`（CON-01～05）组合使用；完整约束遵守评审 = CON-01～10。详见 `scene-constraint-compliance-review-checklist.md`。

| 业务意图 | 优先模式 | 不要使用 | 判断规则 |
|---|---|---|---|
| BI 筛选与图表 Token/边界 | FilterBar 语义 Token + Chart dynamic + `chartPaletteCssVars` | 筛选硬编码色或 Chart SSR 直渲 | CON-06 · MS-11 |
| CI/CD 阶段与日志边界 | Pipeline Radix + LogStream client-only + 阶段中文 | 手写 div 弹层或英文阶段文案 | CON-07 · MS-10 |
| Gateway probe/配额约束 | 受控 props + 探测表语义 Token + 配额中文 mock | 裸色值 badge 或非受控 Hub | CON-08 · MS-09 |
| PaaS 危险操作与 diff | Maps client-only + ConfigDiff 语义 Token + 危险 Dialog Radix | Maps SSR 直渲或 diff `#hex` 高亮 | CON-09 · MS-12 |
| MS 场景约束束 | MS 表 CON-01～10 组合闭环 | 领域页 Token+API+文案组合违规 | CON-10 · VAL-* |

## 场景响应式选型（G76）

> 与 `responsive-review-checklist.md`（RESP-01～05）组合使用；完整响应式评审 = RESP-01～10。详见 `scene-responsive-review-checklist.md`。

| 业务意图 | 优先模式 | 不要使用 | 判断规则 |
|---|---|---|---|
| BI 筛选与图表窄屏 | FilterBar 换行/横滚 + KPI 2×2 + ChartPanel 最小高度 | 筛选挤压图表或 tablet 仍 4 列 KPI | RESP-06 · MS-11 |
| CI/CD 阶段与日志密度 | PipelineStageBar 横滚/折行 + LogStream 等宽密度 + 制品纵向堆叠 | 阶段条溢出或日志撑破壳层 | RESP-07 · MS-10 |
| Gateway probe/配额窄屏 | EndpointProbe 横向滚动 + BalanceQuota 栅格 + mobile Dialog 边距 | 探测表撑破或配额卡片贴边 | RESP-08 · MS-09 |
| PaaS 危险操作与 diff | ResourceTable sticky + Capacity 栅格 + ConfigDiff 纵向滚动 | 行操作重叠或地图压扁 | RESP-09 · MS-12 |
| MS 场景响应式束 | MS 表 RESP-01～10 组合闭环 | 领域页窄屏 framing 反模式 | RESP-10 · VAL-* |

## 场景可访问性选型（G75）

> 与 `accessibility-review-checklist.md`（A11Y-01～05）组合使用；完整可访问性评审 = A11Y-01～10。详见 `scene-accessibility-review-checklist.md`。

| 业务意图 | 优先模式 | 不要使用 | 判断规则 |
|---|---|---|---|
| BI 筛选与图表键盘 | FilterBar chip 键盘清除 + KPI 标签 + chart 降级可读 | chip 仅鼠标可点或图表失败白屏 | A11Y-06 · MS-11 |
| CI/CD 阶段与日志读屏 | PipelineStageBar 键盘激活 + LogStream aria-live + Rollback Dialog 标题 | 阶段条不可键盘达或日志无动态反馈 | A11Y-07 · MS-10 |
| Gateway probe/配额 a11y | 探测 Dialog 标题 + 行操作 aria-label + 配额超限说明 | 探测 Dialog 无标题或 icon 按钮无名称 | A11Y-08 · MS-09 |
| PaaS 危险操作与地图 | 地图 iframe title + 危险 Dialog 焦点陷阱 + ConfigDiff 标题 | 地图无 title 或危险 Dialog 焦点不回 | A11Y-09 · MS-12 |
| MS 场景可访问性束 | MS 表 A11Y-01～10 组合闭环 | 领域页 RBAC 仅 Switch 或 Wizard 无 Label | A11Y-10 · VAL-* |

## 场景异步状态选型（G74）

> 与 `async-state-review-checklist.md`（ASYNC-01～05）组合使用；完整异步状态与韧性 = ASYNC-01～10。详见 `scene-async-state-review-checklist.md`。

| 业务意图 | 优先模式 | 不要使用 | 判断规则 |
|---|---|---|---|
| BI 筛选与 cross-filter | FilterBar chip → KPI/chart loading→刷新 + empty/error 重试 | 筛选后整页硬切或 chart 白屏 | ASYNC-06 · MS-11 |
| CI/CD 阶段与日志流 | PipelineStageBar 切换 + LogStream 尾部 loading + Rollback checking | 阶段切换日志不同步或无双提交防护 | ASYNC-07 · MS-10 |
| Gateway probe/配额 | EndpointProbe 分步 loading→结果 + BalanceQuota 刷新过渡 | probe 整表硬切或配额超限无反馈 | ASYNC-08 · MS-09 |
| PaaS 危险操作与恢复 | 恢复 Dialog checking + ResourceTable 翻页 loading + Capacity partial | 危险操作无 loading 或恢复静默失败 | ASYNC-09 · MS-12 |
| MS 场景异步束 | MS 表 ASYNC-01～10 组合闭环 | 领域页缺 observable loading→success 路径 | ASYNC-10 · VAL-* |

## 场景视觉 Token 选型（G73）

> 与 `visual-token-review-checklist.md`（VIS-01～05）组合使用；完整视觉 Token 与密度 = VIS-01～10。详见 `scene-visual-token-review-checklist.md`。

| 业务意图 | 优先模式 | 不要使用 | 判断规则 |
|---|---|---|---|
| BI 大屏色板与 KPI 密度 | chartPaletteCssVars + KPI tabular-nums + 真实信息层次 | 假柱状条或页面内 chart 裸色 | VIS-06 · MS-11 |
| CI/CD 阶段与日志密度 | 阶段条语义色 + LogStream 等宽密度 + Danger Zone 隔离色 | 阶段无色语义或日志行裁切 | VIS-07 · MS-10 |
| Gateway probe/配额视觉 | Probe 分步状态 badge + BalanceQuota Token 填充 | probe 状态灰一片或配额条无语义色 | VIS-08 · MS-09 |
| PaaS 危险操作与 diff | ConfigDiff 高亮 + destructive Dialog + Capacity 栅格 | diff 无高亮或危险区与主表单同色 | VIS-09 · MS-12 |
| MS 场景视觉束 | MS 表 VIS-01～10 组合闭环 | 领域页密度/色板与 golden 明显漂移 | VIS-10 · VAL-* |

## 场景交互与动效选型（G72）

> 与 `interaction-motion-review-checklist.md`（INTER-01～05）组合使用；完整交互与动效 = INTER-01～10。详见 `scene-interaction-review-checklist.md`。

| 业务意图 | 优先模式 | 不要使用 | 判断规则 |
|---|---|---|---|
| BI 大屏 KPI/图表刷新 | FilterBar chip 过渡 + chart cross-filter tooltip + KPI Skeleton→内容 | 筛选后整页硬切或假占位画布 | INTER-06 · MS-11 |
| CI/CD 阶段与日志 | PipelineStageBar active 过渡 + LogStream 尾部 loading | 阶段无 active 指示或日志无滚动反馈 | INTER-07 · MS-10 |
| Gateway probe/配额 | EndpointProbe 分步 loading→结果 + BalanceQuota 条填充过渡 | probe 整表硬切或配额超限无视觉反馈 | INTER-08 · MS-09 |
| PaaS 危险操作 | 恢复/伸缩 Dialog fade+scale + ConfigDiff 高亮过渡 | 危险操作无 Dialog 过渡或 diff 无高亮 | INTER-09 · MS-12 |
| MS 场景交互束 | MS 表 INTER-01～10 组合闭环 | 领域页只有控件级交互无场景动效 | INTER-10 · VAL-* |

## 产品逻辑完备选型（G71）

> 与 `form-validation-logic-review-checklist.md`（LOGIC-01～05）组合使用；完整逻辑完备 = LOGIC-01～10。详见 `logic-completeness-review-checklist.md`。

| 业务意图 | 优先模式 | 不要使用 | 判断规则 |
|---|---|---|---|
| 列表→详情→返回 | 面包屑 + 返回保留筛选/分页 | 详情返回后列表重置为默认 | LOGIC-06 · PAT-02 |
| 筛选→结果因果 | FilterBar chips + loading→刷新 | 筛选 silent no-op 或仅本地 state | LOGIC-07 · MS-11 |
| Master-Detail | 选中高亮 + 详情 Tab 保留 | 切换选中丢 Tab/翻页丢上下文 | LOGIC-08 · PAT-03 |
| 配额/审批/限制 | BalanceQuota + ApprovalTimeline | 超限仍可提交或无审批可见态 | LOGIC-09 · MS-09/10 |
| MS 业务逻辑束 | MS 表 LOGIC-01～10 组合闭环 | 领域页只有 happy path 无 probe/审计 | LOGIC-10 · VAL-* |

## CI 选型审计回写

### CI 审计 2026-06-28

- 未发现新增选型反例；example/runtime 模板引用检查通过。

### CI 审计 2026-06-28

- 未发现新增选型反例；example/runtime 模板引用检查通过。



### CI 审计 2026-06-28

- 未发现新增选型反例；example/runtime 模板引用检查通过。




