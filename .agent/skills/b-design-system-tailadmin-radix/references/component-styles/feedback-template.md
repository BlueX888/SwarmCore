# Feedback — Alert / Notification / Spinner

## Alert

**源**：`ui/alert/Alert.tsx`

正交轴：

| 轴 | 取值 |
|---|---|
| `severity` | success / error / warning / info / neutral |
| `appearance` | subtle（默认）/ filled / outlined |
| `variant` | **已废弃别名** → `severity` |

可选：`closable` + `onClose`、`action` slot、`showIcon={false}`  
PR-E：`collapsible` + `defaultCollapsed` — 内容区 `grid-rows` 动画收起/展开

可复制模板：`templates/ui/alert.tsx`

暗色 `appearance="subtle"` 须用 `dark:bg-*-500/15` + `dark:border-*-500/30`，勿继续套用浅色 `*-50` 实底。

```tsx
<Alert severity="warning" appearance="outlined" closable onClose={() => {}} action={<Button size="sm">撤销</Button>}>
  <AlertTitle>需要审批</AlertTitle>
  <AlertDescription>生产环境变更将在 30 分钟后执行。</AlertDescription>
</Alert>

```tsx
<Alert severity="info" collapsible defaultCollapsed>
  <AlertTitle>变更说明</AlertTitle>
  <AlertDescription>展开查看详细影响范围与回滚步骤。</AlertDescription>
</Alert>
```

## Notification / Toast {#notification-toast}

**源**：`ui/notification/Notfication.tsx`  
推荐：**Sonner** + Skill 模板 `templates/sonner-theme.tsx`

```tsx
// App 根节点
import { TailAdminToaster, toasterPositionPresets } from "@/components/ui/sonner-theme";
<TailAdminToaster {...toasterPositionPresets["top-right"]} />
```

**六位置 preset**（PR-E）：`toasterPositionPresets` — `top-left` / `top-center` / `top-right` / `bottom-left` / `bottom-center` / `bottom-right`。

| 场景 | 推荐位置 | 说明 |
|---|---|---|
| Message（操作反馈） | `top-center` | 居中短提示，不打断阅读 |
| Notification（系统事件） | `top-right` / `bottom-right` | 可堆叠多条 |

`ClipboardButton` 复制成功默认 `toast.success("已复制到剪贴板")`。

## Spinner

**源**：`ui/spinner/*`

TailAdmin 多圈 spinner；Skill 模板可用 `Loader2` + `animate-spin` 或自定义 `Spinner`。

可复制模板：`templates/ui/spinner.tsx`

## Skeleton

**源**：无独立组件 → shadcn `Skeleton`

`variant`: rectangular（默认）/ text / circular — `animate-pulse` + `bg-gray-200 dark:bg-gray-800`

可复制模板：`templates/ui/skeleton.tsx`

## Progress（线性 + 环形）

**源**：`ui/progressbar/ProgressBar.tsx`

- 线性：`Progress`（Radix `@radix-ui/react-progress`）
- 环形：`ProgressCircle` — `size` sm/md/lg、`indeterminate`、`label`

可复制模板：`templates/ui/progress.tsx`

## EmptyState / ResultState

**源**：antd Empty / Result — 列表空态与操作结果页预设。

- `EmptyState`：`preset="default"|"simple"`
- `ResultState`：`status` success / error / info / warning / 404 / 403 / 500

可复制模板：`templates/ui/content-state.tsx`（`ContentState` 基座 + 预设封装）
