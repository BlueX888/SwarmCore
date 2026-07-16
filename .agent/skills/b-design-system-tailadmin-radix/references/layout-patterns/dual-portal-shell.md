# 布局模式 — Dual Portal Shell

典型路由：`/portal/user/*`、`/portal/admin/*`、`/developer/*`

关联：`navigation-template.md`、`templates/layout/app-layout.tsx`、`hub-tabs.md`

## 适用场景

- 用户门户 vs 管理后台 vs 开发者控制台并存
- 同一产品多套导航树，共享 Token 与顶栏组件
- Gateway 用户自助 + 运维管控双入口

## 壳层矩阵

| 门户 | 侧栏宽度 | 导航重点 | 顶栏 |
|---|---|---|---|
| User | 290px | 用量、账单、API Keys | 简化搜索 + 通知 |
| Admin | 290px | 租户、策略、审计 | 全功能 Header |
| Developer | 90px 折叠 | 文档、SDK、沙箱 | API status pill |

## 路由与布局切换

```tsx
const portal = usePortal(); // "user" | "admin" | "developer"

<AppLayout
  sidebar={portalSidebars[portal]}
  header={portalHeaders[portal]}
  mainClassName={portal === "developer" ? "max-w-none" : undefined}
/>
```

## 共享规则

- `SidebarProvider` 每门户独立持久化 `localStorage` key：`sidebar:user`、`sidebar:admin`
- 主题 `ThemeProvider` 全局共享
- 门户切换入口：UserDropdown 底部「Switch to Admin」
- 无权限门户 → `403` ContentState + 返回链接

## 导航差异

- User：少层级，强调自助与文档外链
- Admin：Governance / Operations / Billing 分组
- Developer：图标优先窄栏，hover 展开 label

## 品牌克制

- 不把客户项目名写入默认侧栏；用占位「Workspace」「Organization」
- 门户 badge：`User` / `Admin` / `Developer` 用 light Badge

## 状态

| 状态 | 处理 |
|---|---|
| 门户加载中 | 全页 Spinner，不闪错误导航 |
| 权限不足 | 403 + 可申请权限 CTA |
| 会话过期 | 重定向登录，保留 `returnUrl` |

## 截图验收

- 至少两种门户壳层 framing 正常
- 窄栏 Developer 模式图标不裁切
- 门户切换 dropdown 打开态（若 preview 展示）
