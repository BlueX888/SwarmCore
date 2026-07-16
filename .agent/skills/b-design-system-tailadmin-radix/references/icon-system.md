# 图标系统

TailAdmin React Pro v2.3.1 在 `src/icons` 提供 **121 个 SVG**，并通过 `src/icons/index.ts` 以 `?react` 方式导出 React 组件。这批图标已完整同步到 `templates/icons/`（121 个 SVG 与 `templates/icons/index.ts` barrel），本仓库不再 vendoring 源项目。

本 Skill 当前仍允许使用 `lucide-react`，但当目标是还原 TailAdmin 风格、构建中后台通用能力库、DevOps/PaaS/BI/监控大屏页面时，应优先查本文件和 `templates/icons/`，避免临时搜索或混用不一致图标。

## 引入策略

| 场景 | 首选 | 备选 | 规则 |
|---|---|---|---|
| 复刻 TailAdmin 导航、卡片、指标、菜单 | TailAdmin SVG barrel | lucide 同义图标 | 需要 TailAdmin 视觉一致性时优先源 SVG。 |
| 通用动作按钮 | TailAdmin SVG barrel | lucide-react | 如果源 SVG 有等价动作图标，先用源 SVG。 |
| shadcn/Radix 基础组件内部图标 | lucide-react | TailAdmin SVG | Select、Calendar、Dialog close 等可沿用 lucide，保持生态一致。 |
| 运维、监控、PaaS、BI、DevOps 场景页 | TailAdmin SVG semantic map | lucide fallback | 先按业务语义选择，缺少才补 fallback。 |
| 品牌、项目专属图标 | 项目 SVG barrel | TailAdmin SVG | 不把项目品牌写入通用 Skill。 |

推荐适配方式：

```tsx
import { ReactComponent as DataBaseIcon } from "@/icons/data-base.svg?react";

export function MetricIcon() {
  return <DataBaseIcon className="size-5 text-brand-500" aria-hidden />;
}
```

若宿主项目没有 SVGR，可使用 `lucide-react` fallback，但必须在实现说明中记录原因。

## Skill 内置资产

| 路径 | 内容 | 用途 |
|---|---|---|
| `templates/icons/*.svg` | 121 个 TailAdmin 源 SVG | 可复制到宿主项目的 `src/icons/` 或统一资产目录。 |
| `templates/icons/index.ts` | React barrel export | 适用于 Vite + `vite-plugin-svgr` 的 `?react` 导入方式。 |

使用本 Skill 创建或迁移项目时，如果目标项目需要 TailAdmin 图标风格，应把 `templates/icons/` 复制到宿主项目，并配置 SVGR。不要引用已删除的 vendored 源项目路径。

## 尺寸与状态

| 用途 | 尺寸 | 颜色 |
|---|---:|---|
| 表格行内、Dropdown、输入框 prefix/suffix | `size-4` | `text-gray-500 dark:text-gray-400` |
| Button、Toolbar、Header action | `size-5` | 跟随按钮 variant |
| Sidebar / App navigation | `size-6` | active `text-brand-500`，inactive `text-gray-500` |
| 指标卡、空态、设置入口 | `size-8` ~ `size-10` | 语义色或浅色底容器 |
| 大屏、拓扑、状态节点 | `size-8` ~ `size-12` | 可用 success/warning/error/brand 状态色 |

图标按钮必须有 `aria-label` 或可见 tooltip。可点击图标至少 `size-10` touch target，不能只给 SVG 本身绑定点击。

## 语义分类矩阵

| 类别 | TailAdmin SVG | 业务用途 | lucide fallback |
|---|---|---|---|
| 导航与布局 | `GridIcon`、`DashboardAltIcon`、`LayoutIcon`、`PageIcon`、`TableIcon`、`ListIcon`、`MenuIcon`、`HorizontalSlideIcon` | Dashboard、布局、列表、表格、侧栏折叠 | `LayoutDashboard`、`PanelLeft`、`Table2`、`List` |
| 用户与组织 | `UserIcon`、`UserAltIcon`、`UserCircleIcon`、`GroupIcon`、`MultiUserIcon`、`ProfileAltIcon`、`UserMoneyIcon` | 用户、组织、客户、账号、权限主体 | `User`、`Users`、`CircleUser` |
| 动作 | `PlusIcon`、`PlusLineIcon`、`EditIcon`、`PencilIcon`、`TrashBinIcon`、`DownloadIcon`、`UploadIcon`、`CopyIcon`、`CopySmIcon`、`SearchIcon`、`CloseIcon`、`CloseLineIcon` | 新增、编辑、删除、导入导出、复制、搜索、关闭 | `Plus`、`Pencil`、`Trash2`、`Download`、`Upload`、`Copy`、`Search`、`X` |
| 方向与展开 | `AngleUpIcon`、`AngleDownIcon`、`ChevronLeftIcon`、`ChevronDownIcon`、`ChevronUpIcon`、`ArrowUpIcon`、`ArrowDownIcon`、`ArrowRightIcon` | 折叠、排序、分页、趋势 | `ChevronUp`、`ChevronDown`、`ArrowUp`、`ArrowDown` |
| 状态与反馈 | `CheckCircleIcon`、`CheckLineIcon`、`CheckSmIcon`、`AlertIcon`、`AlertHexaIcon`、`InfoIcon`、`ErrorIcon`、`ErrorHexaIcon`、`BoltIcon`、`FlashIcon` | 成功、告警、信息、错误、异常、即时状态 | `CircleCheck`、`TriangleAlert`、`Info`、`CircleX`、`Zap` |
| 安全与密钥 | `LockIcon`、`KeyIcon`、`EyeIcon`、`EyeCloseIcon`、`Shield` fallback | API Key、Token、密码、权限、审计 | `Lock`、`KeyRound`、`Eye`、`EyeOff`、`ShieldCheck` |
| 文件与仓库 | `FolderIcon`、`FolderAltIcon`、`FileIcon`、`FilesIcon`、`DocsIcon`、`PaperClipIcon`、`StarFill`、`StarLine` | 代码仓库、文件浏览、附件、文档、收藏 | `Folder`、`File`、`Files`、`Paperclip`、`Star` |
| DevOps / 集成 | `PlugInIcon`、`IntegrationAltIcon`、`SystemIcon`、`ChipIcon`、`StackIcon`、`CubeAltIcon`、`BoxCubeIcon`、`BoxIcon` | 集成、流水线、系统、组件、镜像、制品 | `Plug`、`Workflow`、`Cpu`、`Layers`、`Boxes` |
| PaaS / 基础设施 | `DataBaseIcon`、`GlobeIcon`、`MapIcon`、`ClockIcon`、`TelescopeIcon`、`BoxMoving` | 数据库、网络、区域、定时任务、观测、资源迁移 | `Database`、`Globe`、`Map`、`Clock`、`Telescope` |
| BI / 数据分析 | `ChartAltIcon`、`PieChartIcon`、`DollarIcon`、`DollarLineIcon`、`UserMoneyIcon`、`HorizontalSlideIcon` | 图表、指标、财务、收入、筛选配置 | `ChartNoAxesCombined`、`PieChart`、`DollarSign`、`SlidersHorizontal` |
| 通信与通知 | `BellAltIcon`、`MailIcon`、`EnvelopeIcon`、`ChatIcon`、`CallIcon`、`HeadphoneAltIcon` | 通知、邮件、消息、客服、呼叫 | `Bell`、`Mail`、`MessageSquare`、`Phone`、`Headphones` |
| AI / 多媒体 | `AiIcon`、`BrainIcon`、`SparkIcon`、`AudioIcon`、`Sound`、`Mute`、`MicrophoneIcon`、`VideoIcon`、`PlayIcon` | AI 控台、语音、视频、播放、智能分析 | `Bot`、`Brain`、`Sparkles`、`Mic`、`Video`、`Play` |
| 商业与订单 | `CartIcon`、`TruckDelivery`、`BoxTapped`、`DollarIcon`、`LikeIcon`、`DislikeIcon` | 电商、物流、包裹、反馈、账单 | `ShoppingCart`、`Truck`、`Package`、`ThumbsUp` |

## 页面场景建议

| 场景 | 推荐图标组合 |
|---|---|
| 运维监控 | `DashboardAltIcon`、`BoltIcon`、`AlertHexaIcon`、`ClockIcon`、`GlobeIcon`、`DataBaseIcon` |
| CI/CD 发布 | `PlugInIcon`、`StackIcon`、`BoxCubeIcon`、`CheckCircleIcon`、`ErrorHexaIcon`、`DownloadIcon` |
| 代码仓库管理 | `FolderIcon`、`FileIcon`、`DocsIcon`、`EditIcon`、`CopyIcon`、`StarLine` |
| K8s / PaaS 资源 | `CubeAltIcon`、`ChipIcon`、`SystemIcon`、`DataBaseIcon`、`GlobeIcon`、`FlashIcon` |
| BI 仪表盘 | `ChartAltIcon`、`PieChartIcon`、`HorizontalSlideIcon`、`DollarLineIcon`、`UserMoneyIcon` |
| 安全治理 | `LockIcon`、`KeyIcon`、`AlertHexaIcon`、`InfoIcon`、`EyeIcon`、`EyeCloseIcon` |

## Preview 验收

图标展厅不得只展示少量占位图标。最低要求：

- 至少 60 个图标或覆盖源 SVG 的 50% 以上；如果只展示摘要，必须给出完整 source map 链接。
- 按导航、动作、状态、安全、文件、DevOps、PaaS、BI、通信、AI/媒体、商业分组。
- 展示 `16 / 20 / 24 / 32` 尺寸、active/hover/disabled/selected 状态。
- light/dark 截图都要可读，不能出现图标与背景对比度不足。
- hover、selected、copy/import 示例应有真实交互或可复现脚本截图。

若图标体系缺少业务类别矩阵，组件覆盖率最高 90；若 preview 仍只有十几个图标且没有场景分组，综合美学最高 88。
