# 布局模式 — BI 权限、分享与嵌入式

典型路由：`/bi/dashboards/:id/share`、`/bi/embed/:token`

关联：`bi-dashboard-builder.md`、`bi-export-subscription.md`、`templates/bi/share-embed-dialog.tsx`、`templates/bi/share-access-dashboard.tsx`

## 适用场景

- **团队内分享**：view / edit 权限，登录用户访问
- **公开链接**：无需登录的只读外链，带过期时间
- **iframe 嵌入**：嵌入企业门户、Wiki、OA 工作台
- **租户隔离**：多租户 SaaS 下分享范围限定在当前 tenant
- **撤销共享**：链接过期、手动撤销、域名白名单变更

## 权限矩阵

| 权限 | 标识 | 能力 | 典型受众 |
|---|---|---|---|
| 只读查看 | `view` | 查看图表与筛选，不可编辑 | 同租户成员 |
| 可编辑 | `edit` | 修改布局、筛选、图表配置 | 协作者 |
| 公开链接 | `public` | 持有链接者可只读访问 | 外部合作方 |
| 嵌入式 | `embed` | iframe 嵌入外部页面 | 门户 / Wiki |

## ShareEmbedDialog 能力

| 能力 | 说明 |
|---|---|
| 权限选择 | Radio 四选一：view / edit / public / embed |
| 链接生成 | 生成带 token 的 URL，`active` 状态可复制 |
| 过期时间 | 7 天 / 30 天 / 自定义日期；过期后 `expired` |
| 域名白名单 | embed 模式下列出允许 iframe 的域名 |
| iframe code | 可复制 `<iframe src="…" …>` 片段 |
| 撤销共享 | 将链接标记为 `revoked`，立即失效 |
| 租户隔离 | `tenantId` 展示与校验，跨租户不可见 |

```tsx
<ShareEmbedDialog
  open={shareOpen}
  onOpenChange={setShareOpen}
  resourceName="经营分析仪表盘"
  tenantId="tenant-acme"
  permission={permission}
  onPermissionChange={setPermission}
  links={shareLinks}
  expiry="7 天"
  allowedDomains="portal.example.com"
  onGenerate={handleGenerate}
  onRevoke={handleRevoke}
  onCopyLink={handleCopyLink}
  onCopyEmbed={handleCopyEmbed}
/>
```

## ShareLink 状态机

| 状态 | UI | 用户动作 |
|---|---|---|
| `active` | success badge + 可复制 URL | 复制、撤销 |
| `expired` | secondary badge | 重新生成 |
| `revoked` | destructive badge | 仅历史记录 |

**过期规则**：`public` / `embed` 默认 7 天；`expiresAt` 展示相对或绝对时间。

## 组合式用法

```tsx
<ShareAccessDashboard
  title="经营分析仪表盘"
  tenantId="tenant-acme"
  links={shareLinks}
  shareOpen={shareOpen}
  onShareOpenChange={setShareOpen}
  permission={permission}
  onPermissionChange={setPermission}
  onGenerateShare={handleGenerate}
  onRevokeShare={handleRevoke}
  renderMain={() => <DashboardGrid … />}
/>
```

或 Dashboard 顶栏独立入口：

```tsx
<Button variant="outline" onClick={() => setShareOpen(true)}>分享</Button>
<ShareEmbedDialog … />
```

## 与 ExportMenu 分工

- `ExportMenu`：导出文件（PNG/PDF/Excel/CSV）与定时订阅
- `ShareEmbedDialog`：在线访问权限、公开链接、iframe 嵌入
- 二者可并存于 Dashboard 顶栏 actions

## 视觉规则

- 权限选项使用带边框的 Radio 卡片，选中态 `border-brand-500`
- 公开/embed 配置区使用浅灰底 `bg-gray-50/50` 分组
- iframe code 使用 `font-mono` + `Textarea` 只读
- 撤销按钮使用 `text-error-500` ghost 样式
- 租户 ID 使用 `code` 内联展示

## 反例

- 不要把分享配置塞进普通 FormDialog 无权限说明
- 公开链接不得无过期时间（安全风险）
- embed 不得省略域名白名单说明（即使允许留空）
- 不要用英文 placeholder 作为默认分享文案
- 跨租户分享不得在同一对话框省略 tenant 上下文

## Agent 检索

- 组件索引 → `ShareEmbedDialog` / `ShareAccessDashboard`
- 选型矩阵 → BI 分享 vs ExportMenu 导出
- preview → `#bi-share-embed`
