# 组件索引

技术栈：**React + shadcn/ui + Radix + Tailwind v4**。详情见 `component-styles/` 分类文件。

## 读取顺序

0. 不确定任务类型或检索路径 → `agent-retrieval-guide.md`（DOCS-005）
0b. MS-09～13 业务页部署冒烟 → `business-validation-checklist.md`（DOCS-006）
0c. UI 漂移评审 / PR 前抽检 → `ui-drift-review-checklist.md`（DOCS-007）+ `scene-ui-drift-review-checklist.md`（DOCS-034）
0c2. Agent 失败模式评审 / PR 前抽检 → `agent-failure-patterns-review-checklist.md`（DOCS-036）+ `scene-agent-failure-review-checklist.md`（DOCS-036）
0c3. UiElements 键盘/hover/focus 评审 → `ui-elements-keyboard-hover-focus-review-checklist.md`（DOCS-037）+ `scene-ui-elements-keyboard-hover-focus-review-checklist.md`（DOCS-037）
0c4. UiElements empty/error/loading 评审 → `ui-elements-empty-error-loading-review-checklist.md`（DOCS-038）+ `scene-ui-elements-empty-error-loading-review-checklist.md`（DOCS-038）
0c5. UiElements 变体/交互态评审 → `ui-elements-variant-interaction-review-checklist.md`（DOCS-039）+ `scene-ui-elements-variant-interaction-review-checklist.md`（DOCS-039）
0c6. BI 图表深度交互评审 → `bi-chart-interaction-review-checklist.md`（DOCS-040）+ `scene-bi-chart-interaction-review-checklist.md`（DOCS-040）
0c7. 页面族视觉回归评审 → `page-family-visual-regression-review-checklist.md`（DOCS-041）+ `scene-page-family-visual-regression-review-checklist.md`（DOCS-041）
0c8. 复杂表单视觉回归评审 → `complex-form-visual-regression-review-checklist.md`（DOCS-042）+ `scene-complex-form-visual-regression-review-checklist.md`（DOCS-042）
0c9. 场景页面视觉回归评审 → `scenario-page-visual-regression-review-checklist.md`（DOCS-043）+ `scene-scenario-page-visual-regression-review-checklist.md`（DOCS-043）
0ca. 场景域独立截图评审 → `scenario-domain-independent-screenshot-review-checklist.md`（DOCS-044）+ `scene-scenario-domain-independent-screenshot-review-checklist.md`（DOCS-044）
0cb. 场景域 light/dark 独立截图评审 → `scenario-domain-light-dark-screenshot-review-checklist.md`（DOCS-045）+ `scene-scenario-domain-light-dark-screenshot-review-checklist.md`（DOCS-045）
0cc. 场景域 tablet/mobile light/dark 独立截图评审 → `scenario-domain-viewport-light-dark-screenshot-review-checklist.md`（DOCS-046）+ `scene-scenario-domain-viewport-light-dark-screenshot-review-checklist.md`（DOCS-046）
0cd. 场景域交互态打开态 tablet/mobile light/dark 独立截图评审 → `scenario-domain-interactive-open-viewport-light-dark-screenshot-review-checklist.md`（DOCS-047）+ `scene-scenario-domain-interactive-open-viewport-light-dark-screenshot-review-checklist.md`（DOCS-047）
0ce. 场景域 Dropdown/Popover/Command 交互态打开态 tablet/mobile light/dark 独立截图评审 → `scenario-domain-dropdown-popover-command-interactive-open-viewport-light-dark-screenshot-review-checklist.md`（DOCS-048）+ `scene-scenario-domain-dropdown-popover-command-interactive-open-viewport-light-dark-screenshot-review-checklist.md`（DOCS-048）
0cf. 场景域 Tooltip/Context Menu 交互态打开态 tablet/mobile light/dark 独立截图评审 → `scenario-domain-tooltip-context-menu-interactive-open-viewport-light-dark-screenshot-review-checklist.md`（DOCS-049）+ `scene-scenario-domain-tooltip-context-menu-interactive-open-viewport-light-dark-screenshot-review-checklist.md`（DOCS-049）
0cg. 场景域 Hover 轻量浮层 tablet/mobile light/dark 独立截图评审 → `scenario-domain-hover-viewport-light-dark-screenshot-review-checklist.md`（DOCS-050）+ `scene-scenario-domain-hover-viewport-light-dark-screenshot-review-checklist.md`（DOCS-050）
0ch. 场景域 Focus/键盘导航 tablet/mobile light/dark 独立截图评审 → `scenario-domain-focus-keyboard-viewport-light-dark-screenshot-review-checklist.md`（DOCS-051）+ `scene-scenario-domain-focus-keyboard-viewport-light-dark-screenshot-review-checklist.md`（DOCS-051）
0ci. 场景域 disabled/loading tablet/mobile light/dark 独立截图评审 → `scenario-domain-disabled-loading-viewport-light-dark-screenshot-review-checklist.md`（DOCS-052）+ `scene-scenario-domain-disabled-loading-viewport-light-dark-screenshot-review-checklist.md`（DOCS-052）
0cj. 场景域 empty/error tablet/mobile light/dark 独立截图评审 → `scenario-domain-empty-error-viewport-light-dark-screenshot-review-checklist.md`（DOCS-053）+ `scene-scenario-domain-empty-error-viewport-light-dark-screenshot-review-checklist.md`（DOCS-053）
0ck. 场景域 partial/retry tablet/mobile light/dark 独立截图评审 → `scenario-domain-partial-retry-viewport-light-dark-screenshot-review-checklist.md`（DOCS-054）+ `scene-scenario-domain-partial-retry-viewport-light-dark-screenshot-review-checklist.md`（DOCS-054）
0cl. 场景域 refetch/pending tablet/mobile light/dark 独立截图评审 → `scenario-domain-refetch-pending-viewport-light-dark-screenshot-review-checklist.md`（DOCS-055）+ `scene-scenario-domain-refetch-pending-viewport-light-dark-screenshot-review-checklist.md`（DOCS-055）
0cm. 场景域 stale/optimistic tablet/mobile light/dark 独立截图评审 → `scenario-domain-stale-optimistic-viewport-light-dark-screenshot-review-checklist.md`（DOCS-056）+ `scene-scenario-domain-stale-optimistic-viewport-light-dark-screenshot-review-checklist.md`（DOCS-056）
0cn. 场景域 conflict/merge tablet/mobile light/dark 独立截图评审 → `scenario-domain-conflict-merge-viewport-light-dark-screenshot-review-checklist.md`（DOCS-058）+ `scene-scenario-domain-conflict-merge-viewport-light-dark-screenshot-review-checklist.md`（DOCS-058）
0co. 场景域 offline/sync conflict tablet/mobile light/dark 独立截图评审 → `scenario-domain-offline-sync-conflict-viewport-light-dark-screenshot-review-checklist.md`（DOCS-059）+ `scene-scenario-domain-offline-sync-conflict-viewport-light-dark-screenshot-review-checklist.md`（DOCS-059）
0cs. 场景域 SSE 重连/背压释放 tablet/mobile light/dark 独立截图评审 → `scenario-domain-sse-reconnect-backpressure-viewport-light-dark-screenshot-review-checklist.md`（DOCS-063）+ `scene-scenario-domain-sse-reconnect-backpressure-viewport-light-dark-screenshot-review-checklist.md`（DOCS-063）
0ct. 场景域长轮询/流式订阅 tablet/mobile light/dark 独立截图评审 → `scenario-domain-long-polling-stream-subscription-viewport-light-dark-screenshot-review-checklist.md`（DOCS-064）+ `scene-scenario-domain-long-polling-stream-subscription-viewport-light-dark-screenshot-review-checklist.md`（DOCS-064）
0cw. 场景域推送通道背压/队列积压 tablet/mobile light/dark 独立截图评审 → `scenario-domain-push-channel-backpressure-queue-viewport-light-dark-screenshot-review-checklist.md`（DOCS-067）+ `scene-scenario-domain-push-channel-backpressure-queue-viewport-light-dark-screenshot-review-checklist.md`（DOCS-067）
0cx. 场景域推送通道重试/死信队列 tablet/mobile light/dark 独立截图评审 → `scenario-domain-push-channel-retry-dead-letter-viewport-light-dark-screenshot-review-checklist.md`（DOCS-068）+ `scene-scenario-domain-push-channel-retry-dead-letter-viewport-light-dark-screenshot-review-checklist.md`（DOCS-068）
0cy. 场景域推送通道订阅确认/幂等重放 tablet/mobile light/dark 独立截图评审 → `scenario-domain-push-channel-subscription-confirm-idempotent-replay-viewport-light-dark-screenshot-review-checklist.md`（DOCS-069）+ `scene-scenario-domain-push-channel-subscription-confirm-idempotent-replay-viewport-light-dark-screenshot-review-checklist.md`（DOCS-069）
0cz. 场景域推送通道后续异步韧性 tablet/mobile light/dark 独立截图评审 → `scenario-domain-push-channel-async-resilience-viewport-light-dark-screenshot-review-checklist.md`（DOCS-070）+ `scene-scenario-domain-push-channel-async-resilience-viewport-light-dark-screenshot-review-checklist.md`（DOCS-070）
0db. 场景域推送通道后续审计追踪 tablet/mobile light/dark 独立截图评审 → `scenario-domain-push-channel-audit-tracking-viewport-light-dark-screenshot-review-checklist.md`（DOCS-072）+ `scene-scenario-domain-push-channel-audit-tracking-viewport-light-dark-screenshot-review-checklist.md`（DOCS-072）
0da. 场景域推送通道后续生命周期 tablet/mobile light/dark 独立截图评审 → `scenario-domain-push-channel-lifecycle-viewport-light-dark-screenshot-review-checklist.md`（DOCS-075）+ `scene-scenario-domain-push-channel-lifecycle-viewport-light-dark-screenshot-review-checklist.md`（DOCS-075）
0db. 场景域推送通道后续退役 tablet/mobile light/dark 独立截图评审 → `scenario-domain-push-channel-retirement-viewport-light-dark-screenshot-review-checklist.md`（DOCS-076）+ `scene-scenario-domain-push-channel-retirement-viewport-light-dark-screenshot-review-checklist.md`（DOCS-076）
0dc. 场景域推送通道后续清理 tablet/mobile light/dark 独立截图评审 → `scenario-domain-push-channel-cleanup-viewport-light-dark-screenshot-review-checklist.md`（DOCS-078）+ `scene-scenario-domain-push-channel-cleanup-viewport-light-dark-screenshot-review-checklist.md`（DOCS-078）
0dd. 场景域推送通道后续销毁 tablet/mobile light/dark 独立截图评审 → `scenario-domain-push-channel-destruction-viewport-light-dark-screenshot-review-checklist.md`（DOCS-077）+ `scene-scenario-domain-push-channel-destruction-viewport-light-dark-screenshot-review-checklist.md`（DOCS-077）
0db. 场景域推送通道后续归档 tablet/mobile light/dark 独立截图评审 → `scenario-domain-push-channel-archive-viewport-light-dark-screenshot-review-checklist.md`（DOCS-074）+ `scene-scenario-domain-push-channel-archive-viewport-light-dark-screenshot-review-checklist.md`（DOCS-074）
0dc. 场景域推送通道后续合规留痕 tablet/mobile light/dark 独立截图评审 → `scenario-domain-push-channel-compliance-trace-viewport-light-dark-screenshot-review-checklist.md`（DOCS-073）+ `scene-scenario-domain-push-channel-compliance-trace-viewport-light-dark-screenshot-review-checklist.md`（DOCS-073）
0da. 场景域推送通道后续补偿/对账 tablet/mobile light/dark 独立截图评审 → `scenario-domain-push-channel-compensation-reconciliation-viewport-light-dark-screenshot-review-checklist.md`（DOCS-071）+ `scene-scenario-domain-push-channel-compensation-reconciliation-viewport-light-dark-screenshot-review-checklist.md`（DOCS-071）
0cv. 场景域推送通道熔断/限流 tablet/mobile light/dark 独立截图评审 → `scenario-domain-push-channel-circuit-breaker-rate-limit-viewport-light-dark-screenshot-review-checklist.md`（DOCS-066）+ `scene-scenario-domain-push-channel-circuit-breaker-rate-limit-viewport-light-dark-screenshot-review-checklist.md`（DOCS-066）
0cu. 场景域推送通道降级/恢复 tablet/mobile light/dark 独立截图评审 → `scenario-domain-push-channel-degradation-recovery-viewport-light-dark-screenshot-review-checklist.md`（DOCS-065）+ `scene-scenario-domain-push-channel-degradation-recovery-viewport-light-dark-screenshot-review-checklist.md`（DOCS-065）
0cr. 场景域 WebSocket 重连/熔断恢复 tablet/mobile light/dark 独立截图评审 → `scenario-domain-websocket-reconnect-circuit-breaker-viewport-light-dark-screenshot-review-checklist.md`（DOCS-062）+ `scene-scenario-domain-websocket-reconnect-circuit-breaker-viewport-light-dark-screenshot-review-checklist.md`（DOCS-062）
0cq. 场景域断连重试/心跳超时 tablet/mobile light/dark 独立截图评审 → `scenario-domain-disconnect-retry-heartbeat-timeout-viewport-light-dark-screenshot-review-checklist.md`（DOCS-061）+ `scene-scenario-domain-disconnect-retry-heartbeat-timeout-viewport-light-dark-screenshot-review-checklist.md`（DOCS-061）
0cp. 场景域 network partition/recovery tablet/mobile light/dark 独立截图评审 → `scenario-domain-network-partition-recovery-viewport-light-dark-screenshot-review-checklist.md`（DOCS-060）+ `scene-scenario-domain-network-partition-recovery-viewport-light-dark-screenshot-review-checklist.md`（DOCS-060）
0co. 场景域 mutation pending/rollback tablet/mobile light/dark 独立截图评审 → `scenario-domain-mutation-rollback-viewport-light-dark-screenshot-review-checklist.md`（DOCS-057）+ `scene-scenario-domain-mutation-rollback-viewport-light-dark-screenshot-review-checklist.md`（DOCS-057）
0d. 首次接入 / vendoring 冒烟 → `adoption-onboarding-checklist.md`（DOCS-008）
0d2. 业务 copy 后改组件 / 回流本尊 → `upstream-contribution-guide.md`（DOCS-044）
0e. SSR / 微前端接入冒烟 → `ssr-microfrontend-adoption-checklist.md`（DOCS-009）
0f. 可访问性评审 / PR 前抽检 → `accessibility-review-checklist.md`（DOCS-010）+ `scene-accessibility-review-checklist.md`（DOCS-026）
0g. 响应式评审 / PR 前抽检 → `responsive-review-checklist.md`（DOCS-011）+ `scene-responsive-review-checklist.md`（DOCS-027）
0h. 异步状态评审 / PR 前抽检 → `async-state-review-checklist.md`（DOCS-012）+ `scene-async-state-review-checklist.md`（DOCS-025）
0i. 交互与动效评审 / PR 前抽检 → `interaction-motion-review-checklist.md`（DOCS-013）+ `scene-interaction-review-checklist.md`（DOCS-023）
0j. 中文示例文案评审 / PR 前抽检 → `chinese-copy-review-checklist.md`（DOCS-014）+ `scene-chinese-copy-review-checklist.md`（DOCS-029）
0k. 视觉 Token 与密度评审 / PR 前抽检 → `visual-token-review-checklist.md`（DOCS-015）+ `scene-visual-token-review-checklist.md`（DOCS-024）
0l. 表单校验与逻辑完备评审 / PR 前抽检 → `form-validation-logic-review-checklist.md`（DOCS-016）
0l2. 产品逻辑完备评审 / PR 前抽检 → `logic-completeness-review-checklist.md`（DOCS-022）+ `scene-logic-completeness-review-checklist.md`（DOCS-035）
0m. 类型完整与 API 契约评审 / PR 前抽检 → `type-api-contract-review-checklist.md`（DOCS-017）+ `scene-type-api-contract-review-checklist.md`（DOCS-033）
0n. 生成一致性评审 / PR 前抽检 → `generation-consistency-review-checklist.md`（DOCS-018）+ `scene-generation-consistency-review-checklist.md`（DOCS-030）
0o. 组件覆盖率评审 / PR 前抽检 → `component-coverage-review-checklist.md`（DOCS-019）+ `scene-component-coverage-review-checklist.md`（DOCS-031）
0p. 模式覆盖评审 / PR 前抽检 → `pattern-coverage-review-checklist.md`（DOCS-020）+ `scene-pattern-coverage-review-checklist.md`（DOCS-032）
0q. 约束遵守评审 / PR 前抽检 → `constraint-compliance-review-checklist.md`（DOCS-021）+ `scene-constraint-compliance-review-checklist.md`（DOCS-028）
1. 本索引定位类别与 shadcn 映射
2. `component-styles/_index.md` 选分类模板
3. 对应 `*-template.md` 或内联 detail
4. `token-index.md` 查 Token
5. `state-index.md` 查状态覆盖
6. `extension-audit.md` 查复杂组件扩展性审计（AUDIT-001）
7. `api-contracts.md` 查公开 API 契约与破坏性风险（COMPAT-001/002）
8. `version-pinning-guide.md` 固定 Skill 快照；`migration-playbook.md` 路由 MS-01～13；`upgrade-troubleshooting.md` 升级故障排查；`migration-scenarios.md` 查预防性迁移详情
9. `merge-options-guide.md` 判断浅 merge / deep merge（DOCS-002）
10. `api-override-recipes.md` 查可复制 override 片段（AUDIT-002）
11. `scenario-override-recipes.md` 查 BI/DevOps/PaaS 场景组合 override（AUDIT-003）

## api-contracts

公开 API 契约注册表见 `api-contracts.md`（COMPAT-001）。

| 稳定性 | 数量 | 范围 |
|---|---:|---|
| stable / theme-only | 37 | Chart、FullCalendar、Kanban、Maps、Vector Maps、Carousel、DatePicker、MultiSelect、FileUpload、FileDropzone、ThemeToggle、Command、Transfer、TreeTable、Tree、ContextMenu、DialogHost / useDialog、useSortableList、OrderList、ImageCompare、InputGroup、StatCountdown、Prose / Blockquote、SkipNav / VisuallyHidden、Image、Listbox、**ConfirmHost** / **useConfirm**、**useFormList** / **FormList**、**useScrollToFirstError**、**RadioButtonGroup**、**PasswordInput**、**FormFieldset**、**DataTableColumnFilter**、**ImagePreview**、**StatTrend**、**ClipboardButton** |
| evolving | 33 | Cascader、TreeSelect、Timeline、AnchorNav、Tour、List、TimePicker、Mentions、Rating、ColorPicker、Editable、Kbd、ToggleTip、ActionBar、ChoiceCard、RichTextEditor `toolbar=full`、PR-F 浮层/展示批次（PaginationBar、SplitButton、BlockUi、FloatLabel、MeterGroup、FloatingPanel、Highlight、AvatarPersona、FloatButton、Watermark、Masonry、QrCode、OrganizationChart）等 |

破坏性变更须同步 `backward-compatibility.md` + `migration-note-template.md` + `migration-scenarios.md`（若属常见预防场景）。

升级 pin 前运行 `create-design-system/scripts/audit_compat_contracts.py`。

## api-override-recipes

14 项复杂组件的可复制 override 片段见 `api-override-recipes.md`（G45）；场景级组合见 `scenario-override-recipes.md`（G49 SOR-01～05；G52 MS-11～13 路由闭环）；嵌套 merge 选型见 `merge-options-guide.md`（G50）。

| 覆盖 | 说明 |
|---|---|
| theme lib | Chart、FullCalendar、Maps、Vector Maps、Carousel — helper `overrides` / `merge*` |
| React 模板 | Kanban、Editor、DatePicker、MultiSelect、FileUpload、ThemeToggle、Command、Dropdowns — 受控 props / className |


## extension-audit

14 项第三方/复杂组件扩展性审计总表见 `extension-audit.md`。

| 审计状态 | 数量 | 组件 |
|---|---:|---|
| pass | 14 | Chart、FullCalendar、Kanban、Maps、Vector Maps、Carousel、DatePicker、MultiSelect、FileUpload、FileDropzone、Editor、ThemeToggle、Command、UserDropdown、NotificationDropdown |
| partial | 0 | — |

## Primitives（基础控件）

| TailAdmin 源 | shadcn | 源文件 | Detail |
|---|---|---|---|
| Button / IconButton / CloseButton / DownloadTrigger | `Button` recipe | `ui/button/Button.tsx` | `component-styles/primitive-template.md#button` |
| Badge | `Badge` | `ui/badge/Badge.tsx` | `primitive-template.md#badge` · `templates/ui/badge.tsx` · PR-4：`outline` / `subtle` / `surface` |
| Chip | `Chip` | — | `primitive-template.md#chip` · `templates/ui/chip.tsx` |
| CountBadge | `CountBadge` | — | `primitive-template.md#countbadge` · `templates/ui/count-badge.tsx` |
| InputField | `Input` | `form/input/InputField.tsx` | `primitive-template.md#input` |
| FormField | `FormField` | — | `form-controls.md` · `templates/ui/form-field.tsx` |
| FormContext | `FormProvider` / `useFormContext` | — | `form-controls.md#form-layout-级联` · `templates/ui/form-context.tsx` · PR-E：`scrollToFirstError` |
| useFormList / FormList | `FormList` compound | — | `form-controls.md#formlist` · `templates/lib/use-form-list.ts` · `templates/ui/form-list.tsx` |
| useScrollToFirstError | `scrollToFirstError` / `useFormSubmit` | — | `form-controls.md#scrolltofirsterror` · `templates/lib/use-scroll-to-first-error.ts` |
| FormFieldset | `FormFieldset` | — | `form-controls.md#formfieldset` · `templates/ui/form-fieldset.tsx` |
| InputGroup | `InputGroup` | — | `form-controls.md#inputgroup` · `templates/ui/input-group.tsx` · PR-GH |
| NumericInput | `NumericInput` | — | `form-controls.md#numericinput` · `templates/ui/numeric-input.tsx` |
| MaskedInput | `MaskedInput` | — | `form-controls.md#maskedinput` · `templates/ui/masked-input.tsx` |
| OtpInput | `OtpInput` | `components/auth/OtpForm.tsx` | `form-controls.md#otpinput` · `templates/ui/otp-input.tsx` |
| SecretInput | `SecretInput` | — | `form-controls.md#secretinput` · `templates/ui/secret-input.tsx` |
| PasswordInput | `PasswordInput` | — | `form-controls.md#passwordinput` · `templates/ui/password-input.tsx` · 登录密码；重密文用 SecretInput |
| ClipboardButton | `ClipboardButton` | — | `decision-matrix.md` · `templates/ui/clipboard-button.tsx` · 轻量复制 + Sonner toast |
| AsyncField | `AsyncField` | — | `form-controls.md#asyncfield` · `templates/ui/async-field.tsx` |
| TextArea | `Textarea` | `form/input/TextArea.tsx` | `primitive-template.md#textarea` · PR-4：`autosize` + `minRows`/`maxRows` |
| Checkbox | `Checkbox` | `form/input/Checkbox.tsx` | `primitive-template.md#checkbox` · PR-4：`indeterminate` 半选态 |
| Kbd | `Kbd` | — | `primitive-template.md#kbd` · `templates/ui/kbd.tsx` |
| ChoiceCard | `ChoiceCard` | — | `form-controls.md#choicecard` · `templates/ui/choice-card.tsx` |
| Radio | `RadioGroup` | `form/input/Radio.tsx` | `primitive-template.md#radio` |
| RadioButtonGroup | `RadioButtonGroup` | — | `form-controls.md#radiobuttongroup` · `templates/ui/radio-button-group.tsx` · antd `Radio.Button` |
| Switch | `Switch` | `form/switch/Switch.tsx` | `primitive-template.md#switch` · PR-F：`loading` |
| Select | `Select` | `form/Select.tsx` | `primitive-template.md#select` |
| Cascader | `Cascader` | — | `form-controls.md#cascader` · `templates/ui/hierarchical-picker/cascader.tsx` |
| TreeSelect | `TreeSelect` | — | `form-controls.md#treeselect` · `templates/ui/hierarchical-picker/tree-select.tsx` |
| TimePicker | `TimePicker` | — | `form-controls.md#timepicker` · `templates/ui/time-picker.tsx` |
| Mentions | `Mentions` | — | `form-controls.md#mentions` · `templates/ui/mentions.tsx` |
| Rating | `Rating` | — | `form-controls.md#rating` · `templates/ui/rating.tsx` |
| ColorPicker | `ColorPicker` | — | `form-controls.md#colorpicker` · `templates/ui/color-picker.tsx` |
| Editable | `Editable` | — | `form-controls.md#editable` · `templates/ui/editable.tsx` |
| Slider | `Slider` | — | `primitive-template.md#slider` · `templates/ui/slider.tsx` |
| Steps | `Steps` | `devops/pipeline-stage-bar.tsx`（领域特化） | `primitive-template.md#steps` · `navigation-template.md#steps-mobile` · `templates/ui/steps.tsx` · PR-4：`type: navigation \| dot` · PR-E：`mobileVariant` / `responsive` |
| Label | `Label` | `form/Label.tsx` | primitive |
| Avatar | `Avatar` | `ui/avatar/Avatar.tsx` | `primitive-template.md#avatar` · PR-4：`AvatarGroup` + `shape: circle \| square` |
| Link | 自定义或 `Button variant="link"` | `ui/link/index.tsx` | primitive |
| Icon System | TailAdmin SVG barrel / lucide | `templates/icons/index.ts` | `references/icon-system.md` · `templates/icons/icon-registry.tsx` |
| FormSection | `FormSection` | — | `layout-patterns/form-composition.md` · `templates/ui/form-section.tsx` |
| DescriptionList | `DescriptionList` | — | `layout-patterns/form-composition.md` · `templates/ui/description-list.tsx` |
| DescriptionDiff | `DescriptionDiff` | — | `layout-patterns/form-composition.md` · `templates/ui/description-diff.tsx` |
| FormDrawer | `FormDrawer` | — | `layout-patterns/form-composition.md` · `templates/ui/form-drawer.tsx` |
| FormDialog | `FormDialog` | — | `layout-patterns/form-composition.md` · `overlay-template.md#formdialog-fullscreen` · `templates/ui/form-dialog.tsx` · PR-E：`fullScreen` / `size="full"` |

## Overlay（浮层）

| TailAdmin 源 | shadcn | 源文件 | Detail |
|---|---|---|---|
| Modal | `Dialog` | `ui/modal/index.tsx` | `component-styles/overlay-template.md` |
| Drawer | `Sheet` | — | `overlay-template.md#drawer` · `navigation-template.md#sheet-variant` · `templates/ui/sheet.tsx` · PR-E：`variant: temporary \| persistent \| mini` |
| Dropdown | `DropdownMenu` | `ui/dropdown/Dropdown.tsx` | overlay |
| Popover | `Popover` | `ui/popover/Popover.tsx` | overlay |
| Popconfirm | `Popconfirm` | — | `overlay-template.md#popconfirm` · `templates/ui/popconfirm.tsx` |
| Tooltip | `Tooltip` | `ui/tooltip/Tooltip.tsx` | `overlay-template.md#tooltip` · `templates/ui/tooltip.tsx` |
| ToggleTip | `ToggleTip` | — | `overlay-template.md#toggletip` · `templates/ui/toggle-tip.tsx` |
| ConfirmHost | `ConfirmHost` | — | `layout-patterns/form-composition.md` · `templates/ui/confirm-host.tsx` + `templates/lib/use-confirm.ts` |
| DialogHost | `DialogHost` | — | `overlay-template.md#dialog-host` · `templates/ui/dialog-host.tsx` + `templates/lib/use-dialog.ts` |
| ContextMenu | `ContextMenu` | — | `overlay-template.md#context-menu` · `templates/ui/context-menu.tsx` |
| ScrollArea | `ScrollArea` | — | `overlay-template.md#scroll-area` · `templates/ui/scroll-area.tsx` |
| Tour | `Tour` | — | `overlay-template.md#tour` · `templates/ui/tour.tsx` |

## Navigation（导航）

| 组件 | shadcn | 源文件 | Detail |
|---|---|---|---|
| AppSidebar | 自定义 + `Collapsible` | `layout/AppSidebar.tsx` | `navigation-template.md` · `templates/layout/app-sidebar.tsx` |
| AppHeader | 自定义 | `layout/AppHeader.tsx` | `navigation-template.md` · `templates/layout/app-header.tsx` |
| AppLayout | 自定义 | `layout/AppLayout.tsx` | `templates/layout/app-layout.tsx` |
| Breadcrumb | `Breadcrumb` | `ui/breadcrumb/*` | `navigation-template.md#breadcrumb` |
| Tabs | `Tabs` | `ui/tabs/*` | `navigation-template.md#tabs` · `navigation-template.md#tabs-editable` · `templates/ui/tabs.tsx` · PR-E：`editable` / `onEdit` |
| SegmentedControl | `ToggleGroup` | `ui/buttons-group/*` | `primitive-template.md#segmentedcontrol` · `templates/ui/segmented-control.tsx` |
| Separator | `Separator` | — | `primitive-template.md#separator` · `templates/ui/separator.tsx` |
| Accordion | `Accordion` | sidebar Collapsible | `primitive-template.md#accordion` · `templates/ui/accordion.tsx` |
| Pagination | `Pagination` | `ui/pagination/*` | `navigation-template.md#pagination` |
| AnchorNav | `AnchorNav` | — | `navigation-template.md#anchor-nav` · `templates/ui/anchor-nav.tsx` |
| SkipNav | `SkipNav` | — | `navigation-template.md#skip-nav` · `templates/ui/skip-nav.tsx` |

## Data Display（数据展示）

| 组件 | 源文件 | Detail |
|---|---|---|
| QueryShell | `QueryShell` | — | `content-state-contract.md` · `templates/ui/query-shell.tsx` |
| ContentState | `ContentState` | — | `content-state-contract.md` · `templates/ui/content-state.tsx` |
| EmptyState / ResultState | 预设封装 | — | `content-state-contract.md` · `templates/ui/content-state.tsx` |
| DataTableCard | `DataTableCard` | — | `content-state-contract.md` · `templates/ui/data-table-card.tsx` |
| DataTable | `DataTable` | — | `data-display-template.md#datatable-contract` · `templates/ui/data-table.tsx` · PR-4：`virtual` + `data-table-virtual-body.tsx` · PR-E：列头 `filter` |
| DataTableColumnFilter | `DataTableColumnFilter` | — | `data-display-template.md#datatable-column-filter` · `templates/ui/data-table-column-filter.tsx` |
| ImagePreview | `ImagePreview` | — | `data-display-template.md#imagepreview` · `templates/ui/image-preview.tsx` |
| StatTrend | `StatTrend` | — | `data-display-template.md#stattrend` · `templates/ui/stat-trend.tsx` · `StatMetric` `trend` slot |
| ActionBar | `ActionBar` | — | `data-display-template.md#actionbar` · `templates/ui/action-bar.tsx` |
| Autocomplete | `Autocomplete` | — | `decision-matrix.md` · `templates/ui/autocomplete.tsx` · PR-4：`groupBy` + `virtual` |
| TagsInput | `TagsInput` | — | `decision-matrix.md` · `templates/ui/tags-input.tsx` |
| Tree | `Tree` | — | `templates/ui/tree.tsx` · PR-GH：`draggable` / `onDrop` |
| TreeTable | `TreeTable` | — | `data-display-template.md#treetable` · `templates/ui/tree-table.tsx` · `tree-table-virtual-body.tsx` · PR-GH：`virtual` / 列 `filter` |
| Transfer | `Transfer` | — | `data-display-template.md#transfer` · `templates/ui/transfer.tsx` · PR-GH：`targetSortable` |
| OrderList | `OrderList` | — | `layout-patterns/order-list.md` · `templates/ui/order-list.tsx` |
| ImageCompare | `ImageCompare` | — | `layout-patterns/image-compare.md` · `templates/ui/image-compare.tsx` |
| Image | `Image` | — | `data-display-template.md#image` · `templates/ui/image.tsx` |
| Listbox | `Listbox` | — | `form-controls.md#listbox` · `templates/ui/listbox.tsx` |
| Prose | `Prose` | — | `data-display-template.md#prose` · `templates/ui/prose.tsx` |
| Blockquote | `Blockquote` | — | `templates/ui/blockquote.tsx` |
| StatCountdown | `StatCountdown` | — | `data-display-template.md#statcountdown` · `templates/ui/stat-countdown.tsx` |
| Timeline | `Timeline` | — | `data-display-template.md#timeline` · `templates/ui/timeline.tsx` |
| List | `List` | — | `data-display-template.md#list` · `templates/ui/list.tsx` |
| Splitter | `Splitter` | — | `react-resizable-panels` · `templates/ui/splitter.tsx` |
| HoverCard | `HoverCard` | — | `overlay-template.md#hovercard` · `templates/ui/hover-card.tsx` |
| Status | `Status` | — | `templates/ui/status.tsx` |
| Surface | `Surface` | — | `templates/ui/surface.tsx` |
| ButtonGroup | `ButtonGroup` | — | `templates/ui/button-group.tsx` |
| StatMetric | `StatMetric` | — | `content-state-contract.md` · `templates/ui/stat-metric.tsx` |
| Table primitives | `Table` | `ui/table/index.tsx` | `data-display-template.md#table` |
| Pagination | `Pagination` | `ui/pagination/PaginationWithIcon.tsx` | `navigation-template.md#pagination` |
| PaginationBar | `PaginationBar` | — | `navigation-template.md#pagination-bar` · `templates/ui/pagination-bar.tsx` |
| BasicTable 1–5 | `tables/BasicTables/*` | data-display |
| DataTable 1–3 | `tables/DataTables/*` | data-display |
| Card / ComponentCard | `Card` | `common/ComponentCard.tsx` | `data-display-template.md#componentcard` · PR-4：`CardActionArea` + `CardActions` |
| ProgressBar | `Progress` | `ui/progressbar/*` | `data-display-template.md#progressbar` |
| Charts (ApexCharts) | `components/charts/*` | `chart-theme.md` · `templates/lib/chart-theme.ts` |
| ChartPanel | — | `layout-patterns/bi-chart-builder.md` · `templates/bi/chart-panel.tsx` |
| MetricCard (BI) | — | `layout-patterns/bi-dashboard-builder.md` · `templates/bi/metric-card.tsx` |
| FieldListPanel | — | `layout-patterns/bi-chart-builder.md` · `templates/bi/field-list-panel.tsx` |
| ChartConfigPanel | — | `layout-patterns/bi-chart-builder.md` · `templates/bi/chart-config-panel.tsx` |
| ChartBuilderLayout | — | `layout-patterns/bi-chart-builder.md` · `templates/bi/chart-builder-layout.tsx` |
| DashboardGrid | — | `layout-patterns/bi-dashboard-builder.md` · `templates/bi/dashboard-grid.tsx` |
| DataScreenCanvas | — | `layout-patterns/bi-data-screen.md` · `templates/bi/data-screen-canvas.tsx` |
| DatasetBrowser | — | `layout-patterns/bi-dataset-management.md` · `templates/bi/dataset-browser.tsx` |
| FilterBar | — | `layout-patterns/bi-filter-linkage.md` · `templates/bi/filter-bar.tsx` |
| CrossFilterDashboard | — | `layout-patterns/bi-filter-linkage.md` · `templates/bi/cross-filter-dashboard.tsx` |
| DrillBreadcrumb | — | `layout-patterns/bi-drill-down.md` · `templates/bi/drill-breadcrumb.tsx` |
| DrillDetailTable | — | `layout-patterns/bi-drill-down.md` · `templates/bi/drill-detail-table.tsx` |
| DrillDownDashboard | — | `layout-patterns/bi-drill-down.md` · `templates/bi/drill-down-dashboard.tsx` |
| ExportMenu | — | `layout-patterns/bi-export-subscription.md` · `templates/bi/export-menu.tsx` |
| ExportJobPanel | — | `layout-patterns/bi-export-subscription.md` · `templates/bi/export-job-panel.tsx` |
| ExportSubscriptionDashboard | — | `layout-patterns/bi-export-subscription.md` · `templates/bi/export-subscription-dashboard.tsx` |
| ShareEmbedDialog | — | `layout-patterns/bi-share-embed.md` · `templates/bi/share-embed-dialog.tsx` |
| ShareAccessDashboard | — | `layout-patterns/bi-share-embed.md` · `templates/bi/share-access-dashboard.tsx` |

## Feedback（反馈）

| 组件 | shadcn | 源文件 | Detail |
|---|---|---|---|
| Alert | `Alert` | `ui/alert/Alert.tsx` | `feedback-template.md#alert` · PR-E：`collapsible` / `defaultCollapsed` |
| Notification | `Sonner` 或自定义 | `ui/notification/*` | `feedback-template.md#notification-toast` · `templates/sonner-theme.tsx` · PR-E：`toasterPositionPresets` |
| Spinner | 自定义 / `Loader2` | `ui/spinner/*` | `feedback-template.md#spinner` |
| Skeleton | `Skeleton` | — | `feedback-template.md#skeleton` |
| CookieConsent | 自定义 Banner | `ui/notification/CookieConsent.tsx` | feedback |

## Composite（复合）

| 组件 | 源文件 | Detail |
|---|---|---|
| Search（Header） | `layout/AppHeader.tsx` | `composite-template.md` · `templates/ui/search-command.tsx` |
| Command Palette | shadcn `Command` | — | `templates/ui/command.tsx` |
| UserDropdown | `header/UserDropdown.tsx` | `composite-template.md` · `templates/layout/user-dropdown.tsx` |
| NotificationDropdown | `header/NotificationDropdown.tsx` | `composite-template.md` · `templates/layout/notification-dropdown.tsx` |
| MultiSelect | `form/MultiSelect.tsx` | composite · `templates/ui/multi-select.tsx` |
| DatePicker | `form/date-picker.tsx` | composite · `templates/ui/date-picker.tsx` · `showTime` 扩展（日期+时间） |
| FileUpload | `form/input/FileInput.tsx` | composite · `templates/ui/file-upload.tsx` |
| ThemeToggle | `common/ThemeToggleButton.tsx` | layout · `templates/layout/theme-toggle.tsx`（导出 `ThemeToggle` + `ThemeToggleButton`，见 MN-01） |
| Deprecated wrappers | — | `templates/ui/deprecated/`（ThemeToggle alias、SearchCommandStatic、KanbanLegacyShell） |

## Layout（布局壳）

| 组件 | 源文件 |
|---|---|
| AppLayout | `layout/AppLayout.tsx` |
| AlternativeLayout | `layout/AlternativeLayout.tsx` |
| Backdrop | `layout/Backdrop.tsx` | `templates/layout/backdrop.tsx` |
| SidebarContext | `context/SidebarContext.tsx` |
| ThemeContext | `context/ThemeContext.tsx` | `templates/context/theme-context.tsx` |

## 按任务选组件

| 任务 | 组件组合 |
|---|---|
| 仪表盘 KPI | ComponentCard + 指标 typography + Chart |
| 图标选择 | 先按业务语义查 `references/icon-system.md`，再决定 TailAdmin SVG 或 lucide fallback |
| BI 图表构建 | ChartBuilderLayout + FieldListPanel + ChartConfigPanel + ChartPanel |
| BI 仪表盘 | DashboardGrid + MetricCard + ChartPanel + FilterBar |
| BI 数据大屏 | DataScreenCanvas + BigNumberTile + GeoMapPanel |
| BI 数据集管理 | DatasetBrowser + FieldListPanel |
| CI/CD Run Detail | CicdRunDetail + PipelineStageBar + LogStreamPanel + ArtifactTable |
| MR/PR Detail | MrDetailShell + FileBrowser + DiffViewer |
| 发布审批 | ApprovalTimeline + DangerZone + RollbackDialog |
| BI 筛选联动 | FilterBar + CrossFilterDashboard | 每图各自筛选时用独立 DatePicker — `decision-matrix.md#FilterBar` |
| BI 下钻明细 | DrillDownDashboard + DrillDetailTable | 无层级时用普通 Table — `decision-matrix.md#DrillDownDashboard` |
| BI 导出订阅 | ExportMenu + ExportJobPanel | 单次小文件导出用 Dropdown 直接下载 — `decision-matrix.md#ExportMenu` |
| BI 分享嵌入 | ShareEmbedDialog + ShareAccessDashboard | 仅内部 RBAC 时用 PermissionMatrix — `decision-matrix.md#ShareEmbedDialog` |
| AI 代码生成 | AiCodeGeneratorShell + CodeEditor | 只读代码用 CodeBlock — `decision-matrix.md#CodeEditor` |
| 治理权限矩阵 | PermissionMatrix | 简单开关列表用 Switch — `decision-matrix.md#PermissionMatrix` |
| 审计日志 | AuditLogTable | 无筛选导出需求用 DataTableCard — `decision-matrix.md#AuditLogTable` |
| PaaS 资源列表 | ResourceTable + MasterDetailOps | 无资源类型语义用 DataTableCard — `decision-matrix.md#ResourceTable` |
| PaaS 危险操作 | PaasOpsDangerFlow | 不可逆操作用 AlertDialog 二次确认 — `decision-matrix.md#PaasOpsDangerFlow` |
| CRUD 列表 | Table + Pagination + toolbar Input + Button → `layout-patterns/crud-flow.md` |
| 表单页 | Label + Input + Select + Switch + Button primary | 复杂表单见 `decision-matrix.md#表单` → FormPageShell + FormSection |
| 查看态详情 | DescriptionList / DescriptionSection | 不要用 disabled 表单冒充详情 — `decision-matrix.md#查看态` |
| 表格行编辑 | FormDrawer + DescriptionList | 保留列表上下文时用 Drawer，不用居中 Dialog |
| 配置变更对比 | DescriptionDiff | 审批、回滚、审计前后对比 |
| 设置页 | Tabs + Card sections + Form |
| 确认删除 | Dialog + destructive Button |
| 空列表 | Card + 居中 empty 文案 + outline Button |

## 第三方 / 复合（无单一 shadcn 组件）

| 场景 | 参考 | 源文件 |
|---|---|---|
| DatePicker | `third-party-template.md#datepicker` · `templates/ui/date-picker.tsx` | `form/date-picker.tsx` |
| MultiSelect | `third-party-template.md#multiselect` | `form/MultiSelect.tsx` · `templates/ui/multi-select.tsx` |
| FileUpload | `composite-template.md#fileupload` | `form/input/FileInput.tsx` · `templates/ui/file-upload.tsx` |
| ApexCharts | `chart-theme.md` · `templates/lib/chart-theme.ts` | `components/charts/*` |
| FullCalendar | `fullcalendar-theme.md` · `templates/lib/fullcalendar-theme.ts` | calendar 页 |
| Kanban | `kanban-theme.md` · `templates/ui/kanban-board.tsx` · `templates/ui/kanban-column-menu.tsx` | `task/kanban/*` |
| Maps | `maps-theme.md` · `templates/lib/maps-theme.ts` | `maps/others/*` |
| Vector Map | `vector-map-theme.md` · `templates/lib/vector-map-theme.ts` | `maps/vector-map/*` |
| Editor (Prism) | `editor-theme.md` · `templates/ui/code-block.tsx` · `templates/ui/code-editor.tsx` · `templates/lib/editor-theme.ts` · `code-editor-editable.md` | `components/ai/Codeblock.tsx` |
| FileDropzone | `composite-template.md#filedropzone` | `templates/ui/file-dropzone.tsx` |
| MetricDefinitionPanel | `layout-patterns/bi-semantic-layer.md` | `templates/bi/metric-definition-panel.tsx` |
| Carousel (Swiper) | `carousel-theme.md` · `templates/lib/carousel-theme.ts` | `ui/carousel/*` |
| Skeleton | `feedback-template.md#skeleton` | `templates/ui/skeleton.tsx` |

## DevOps / 代码平台

| 组件 | 参考 | 模板 |
|---|---|---|
| PipelineStageBar | `layout-patterns/cicd-release.md` · `devops-template.md` | `templates/devops/pipeline-stage-bar.tsx` |
| LogStreamPanel | `layout-patterns/cicd-release.md` · `devops-template.md` | `templates/devops/log-stream-panel.tsx` |
| ArtifactTable | `layout-patterns/cicd-release.md` · `devops-template.md` | `templates/devops/artifact-table.tsx` |
| ApprovalTimeline | `layout-patterns/cicd-release.md` · `devops-template.md` | `templates/devops/approval-timeline.tsx` |
| DangerZone / RollbackDialog | `layout-patterns/cicd-release.md` · `devops-template.md` | `templates/devops/danger-zone.tsx` |
| CicdRunDetail | `layout-patterns/cicd-release.md` | `templates/devops/cicd-run-detail.tsx` |
| FileTree / CodeViewer / FileBrowser | `layout-patterns/code-repository.md` · `devops-template.md` | `templates/devops/file-browser.tsx` |
| DiffViewer | `layout-patterns/code-repository.md` · `devops-template.md` | `templates/devops/diff-viewer.tsx` |
| MrDetailShell | `layout-patterns/code-repository.md` · `devops-template.md` | `templates/devops/mr-detail-shell.tsx` |

## 企业网关 / 控制平面

| 组件 | 参考 | 模板 |
|---|---|---|
| DeploymentModeMatrix | `deployment-mode-matrix.md` · `gateway-template.md` | `templates/gateway/deployment-mode-matrix.tsx` |
| LicenseIssuePanel | `layout-patterns/control-plane.md` · `gateway-template.md` | `templates/gateway/license-issue-panel.tsx` |
| SyncHealthPanel | `layout-patterns/control-plane.md` · `gateway-template.md` | `templates/gateway/sync-health-panel.tsx` |
| EndpointProbeTable | `layout-patterns/control-plane.md` · `gateway-template.md` | `templates/gateway/endpoint-probe-table.tsx` |
| ApiKeyRevealPanel | `layout-patterns/control-plane.md` · `gateway-template.md` | `templates/gateway/api-key-reveal-panel.tsx` |
| BalanceQuotaSummary | `layout-patterns/control-plane.md` · `gateway-template.md` | `templates/gateway/balance-quota-summary.tsx` |
| ControlPlaneHub | `layout-patterns/control-plane.md` | `templates/gateway/control-plane-hub.tsx` |

## 治理安全

| 组件 | 参考 | 模板 |
|---|---|---|
| PermissionMatrix | `governance-template.md` · `domain-scenarios.md` | `templates/governance/permission-matrix.tsx` |
| AuditLogTable | `governance-template.md` · `domain-scenarios.md` | `templates/governance/audit-log-table.tsx` |
| ComplianceAlert | `governance-template.md` | `templates/governance/compliance-alert.tsx` |
| AuthProviderWizard | `auth-provider-wizard.md` · `governance-template.md` | `templates/governance/auth-provider-wizard.tsx` |
| SecretKeyPanel | `governance-template.md` | `templates/governance/secret-key-panel.tsx` |
| ApiKeyRevealPanel | `governance-template.md` · `gateway-template.md` | `templates/gateway/api-key-reveal-panel.tsx` |

## PaaS 资源管理

| 组件 | 参考 | 模板 |
|---|---|---|
| ResourceTable | `layout-patterns/paas-resource.md` · `paas-template.md` | `templates/paas/resource-table.tsx` |
| CapacityCard | `layout-patterns/paas-resource.md` · `paas-template.md` | `templates/paas/capacity-card.tsx` |
| ConfigDiff | `layout-patterns/paas-resource.md` · `paas-template.md` | `templates/paas/config-diff.tsx` |
| BackupTable | `layout-patterns/paas-resource.md` · `paas-template.md` | `templates/paas/backup-table.tsx` |
| PaasOpsDangerFlow | `layout-patterns/paas-resource.md` · `paas-template.md` | `templates/paas/ops-danger-flow.tsx` |

## 代码模板

可复制宿主项目起点：

- `templates/components.json` — shadcn 初始化
- `templates/icons/` — TailAdmin 121 个 SVG + `index.ts` barrel + `icon-registry.tsx` 语义注册表
- `templates/lib/utils.ts` — `cn()`
- `templates/ui/button.tsx` — 完整 `cva` Button
- `templates/ui/input.tsx` — 完整 `cva` Input（default/error/success）
- `templates/ui/form-field.tsx` — 字段包装（required/helper/error/success/warning/loading）
- `templates/lib/use-form-list.ts` — 动态字段数组 `add`/`remove`/`move`/`replace`
- `templates/lib/use-scroll-to-first-error.ts` — `scrollToFirstError` + `useFormSubmit`
- `templates/ui/form-list.tsx` — FormList compound（FormListItems / FormListAdd）
- `templates/ui/radio-button-group.tsx` — RadioButtonGroup + RadioButton（antd Radio.Button）
- `templates/ui/password-input.tsx` — 轻量密码框 + show/hide toggle
- `templates/ui/form-fieldset.tsx` — `<fieldset>` 语义分组
- `templates/ui/data-table-column-filter.tsx` — 列头 Popover filter（select / text）
- `templates/ui/image-preview.tsx` — 缩略图 + Dialog 灯箱
- `templates/ui/stat-trend.tsx` — KPI 涨跌箭头 + 语义色
- `templates/ui/clipboard-button.tsx` — 复制 + Sonner toast
- `templates/ui/advanced-input.tsx` — prefix/suffix/clearable/counter/copyable
- `templates/ui/numeric-input.tsx` — integer/decimal/currency/percent + stepper
- `templates/ui/masked-input.tsx` — phone/id/license/ip/cidr/custom mask
- `templates/ui/otp-input.tsx` — 4/6/8 位 OTP + 分组粘贴跳格
- `templates/ui/secret-input.tsx` — API Key mask/reveal/copy/rotate/revoke
- `templates/ui/async-field.tsx` — 异步校验 validating/success/warning/error/retry
- `templates/ui/form-section.tsx` — 表单分组卡片（1/2 列）
- `templates/ui/description-list.tsx` — 查看态描述列表（禁止 disabled 表单冒充详情）
- `templates/ui/description-diff.tsx` — 变更前后对比表
- `templates/ui/form-drawer.tsx` — Drawer 详情/编辑切换 + dirty 关闭确认
- `templates/ui/form-dialog.tsx` — Dialog 短表单（1-6 字段、关闭确认）
- `templates/governance/permission-matrix.tsx` — RBAC 权限矩阵
- `templates/governance/audit-log-table.tsx` — 审计日志表
- `templates/governance/compliance-alert.tsx` — 合规风险提示
- `templates/governance/auth-provider-wizard.tsx` — LDAP/OAuth/OIDC/SAML 认证源向导
- `templates/governance/secret-key-panel.tsx` — 治理密钥面板（mask/rotate/revoke）
- `templates/paas/resource-table.tsx` — K8s/ES/MySQL/Redis/Host 资源列表
- `templates/paas/capacity-card.tsx` — CPU/Memory/Disk/QPS/Latency/Replica 容量卡
- `templates/paas/config-diff.tsx` — 参数变更 diff + 风险提示
- `templates/paas/backup-table.tsx` — 备份列表 + 恢复确认
- `templates/paas/ops-danger-flow.tsx` — 伸缩/重启/故障转移危险操作流
- `templates/layout/form-page-shell.tsx` — 独立页表单壳 + breadcrumb + sticky actions
- `templates/icons/icon-registry.tsx` — semantic key → TailAdmin SVG → lucide fallback
- `templates/ui/textarea.tsx` — 完整 `cva` Textarea（default/error/success）
- `templates/ui/select.tsx` — 完整 Radix Select（Trigger/Content/Item）
- `templates/ui/checkbox.tsx` — Radix Checkbox（brand-500 checked）
- `templates/ui/radio-group.tsx` — Radix RadioGroup + RadioGroupItem
- `templates/ui/switch.tsx` — Radix Switch（h-6 w-11 track）
- `templates/ui/badge.tsx` — 完整 `cva` Badge（light/solid × 7 color）
- `templates/ui/alert.tsx` — 完整 `cva` Alert（success/error/warning/info）
- `templates/ui/table.tsx` — 完整 shadcn Table（rounded-xl wrapper + TailAdmin 密度）
- `templates/ui/pagination.tsx` — 组合式 Pagination（brand-500 当前页）
- `templates/ui/card.tsx` — ComponentCard 组合式 Card（rounded-2xl + header/footer）
- `templates/ui/progress.tsx` — Radix Progress（h-2 brand-500 填充）
- `templates/ui/skeleton.tsx` — shadcn Skeleton（animate-pulse gray-200/800）
- `templates/ui/spinner.tsx` — Loader2 Spinner（cva sm/md/lg + brand-500）
- `templates/ui/avatar.tsx` — Radix Avatar（cva size + status + name fallback）
- `templates/ui/breadcrumb.tsx` — Breadcrumb 组合式（Home 图标 + Chevron 分隔）
- `templates/ui/sheet.tsx` — Radix Sheet（TailAdmin overlay + filter/edit 宽度）
- `templates/context/theme-context.tsx` — ThemeProvider + useTheme（light/dark/auto）
- `templates/layout/theme-toggle.tsx` — 顶栏圆形主题切换按钮
- `templates/layout/app-sidebar.tsx` — 290/90px 导航壳 + Collapsible 子菜单
- `templates/layout/app-header.tsx` — sticky 顶栏 + HeaderSearch + ⌘K
- `templates/layout/app-layout.tsx` — 完整 AppLayout 壳层组合（默认 `<Backdrop />`）
- `templates/layout/backdrop.tsx` — 移动端 sidebar 遮罩 `z-40 bg-gray-900/50`
- `templates/layout/notification-dropdown.tsx` — 顶栏通知下拉（Radix DropdownMenu）
- `templates/layout/user-dropdown.tsx` — 顶栏用户菜单（Avatar + 菜单项）
- `templates/layout/hub-tabs-layout.tsx` — URL 同步 Hub Tabs（设置/配额/用量）
- `templates/layout/master-detail-ops.tsx` — 主从分栏 + 详情多 Tab 高度链
- `templates/layout/three-column-workspace.tsx` — 项目轨 + 资源树 + 主工作区
- `templates/ui/dropdown-menu.tsx` — shadcn DropdownMenu TailAdmin 视觉
- `templates/ui/command.tsx` — shadcn Command（cmdk）TailAdmin 视觉
- `templates/ui/popover.tsx` — shadcn Popover TailAdmin 视觉
- `templates/ui/file-upload.tsx` — 原生 file input + `file:` 伪元素样式
- `templates/ui/file-dropzone.tsx` — 拖拽上传 + 多文件预览 + 进度条
- `templates/ui/code-block.tsx` — Prism 只读代码块 + copy/edit toolbar
- `templates/ui/code-editor.tsx` — Textarea + 实时 Prism 预览，split/edit/preview 三模式
- `templates/devops/ai-code-generator-shell.tsx` — AI 代码生成页组合（提示词 + CodeEditor）
- `templates/bi/metric-definition-panel.tsx` — BI 语义层指标口径面板
- `templates/ui/multi-select.tsx` — Popover + Command 多选下拉
- `templates/ui/calendar.tsx` — react-day-picker TailAdmin 视觉
- `templates/ui/date-picker.tsx` — Popover + Calendar 日期/范围选择
- `templates/lib/chart-theme.ts` — ApexCharts 色板与 options 预设
- `templates/lib/fullcalendar-theme.ts` — FullCalendar CSS 覆盖与 options 预设
- `templates/lib/kanban-theme.ts` — Kanban 列布局、category 色、DnD 态 class
- `templates/ui/kanban-board.tsx` — Kanban 三列看板（受控 columns、HTML5 DnD、loading/empty/error）
- `templates/ui/kanban-column-menu.tsx` — Kanban 列头 ⋯ 菜单（Edit/Delete/Clear All）
- `templates/lib/maps-theme.ts` — Maps 卡壳、zoom 控件、MapLibre/Leaflet 默认 options
- `templates/lib/vector-map-theme.ts` — jVectorMap region/marker 预设、traffic/US heatmap、zoom handlers
- `templates/lib/editor-theme.ts` — Prism 代码块壳层、token CSS、语言导入列表
- `templates/lib/carousel-theme.ts` — Swiper 四 variant options、导航/分页 CSS 覆盖
- `templates/sonner-theme.tsx` — TailAdmin × Sonner Toaster 主题
- `templates/devops/pipeline-stage-bar.tsx` — CI/CD stage bar 六态
- `templates/devops/log-stream-panel.tsx` — 固定高度日志流
- `templates/devops/artifact-table.tsx` — 制品表 digest/download/scan
- `templates/devops/approval-timeline.tsx` — 审批时间线
- `templates/devops/danger-zone.tsx` — 危险操作区 + RollbackDialog
- `templates/devops/cicd-run-detail.tsx` — CI/CD Run Detail 页面组合
- `templates/devops/file-browser.tsx` — FileTree + CodeViewer split
- `templates/devops/diff-viewer.tsx` — MR/PR diff hunks
- `templates/devops/mr-detail-shell.tsx` — MR/PR 详情壳层
- `templates/gateway/deployment-mode-matrix.tsx` — 部署模式 chip 矩阵
- `templates/gateway/license-issue-panel.tsx` — License 签发/续期/一次性展示
- `templates/gateway/sync-health-panel.tsx` — 同步健康四轨
- `templates/gateway/endpoint-probe-table.tsx` — Endpoint 探测表 debounce
- `templates/gateway/api-key-reveal-panel.tsx` — API Key 一次性展示
- `templates/gateway/balance-quota-summary.tsx` — 余额/配额 KPI 行
- `templates/gateway/control-plane-hub.tsx` — 控制平面页面组合

## 缺组件时

读 `output-modes/missing-component.md`，按 Radix 基座选型，更新本索引与 `component-styles/`。
