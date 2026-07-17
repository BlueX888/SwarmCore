import * as Dialog from "@radix-ui/react-dialog";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@radix-ui/react-tooltip";
import { useQuery } from "@tanstack/react-query";
import {
  Activity, Bot, Boxes, ChartNoAxesCombined, ChevronLeft, ChevronRight, Clock3, Cpu,
  ExternalLink, Inbox, LayoutDashboard, Menu, Moon, Network, Plus, Rocket, ScrollText, Sun, Workflow, Wrench, X,
} from "lucide-react";
import * as React from "react";
import { Link, Outlet, useLocation } from "react-router";
import { api } from "@/api/client";
import { Button } from "@/components/ui/button";
import { useTheme } from "@/context/theme-context";
import { useWorkspaceScope } from "@/lib/demo-scope";
import { cn } from "@/lib/utils";

interface NavigationProps { collapsed?: boolean; onNavigate?: () => void; }
interface NavItem { label: string; to: string; icon: React.ComponentType<{ className?: string; "aria-hidden"?: boolean }>; active: (path: string) => boolean; badge?: number; }

export function Navigation({ collapsed = false, onNavigate }: NavigationProps) {
  const { tenantId, projectId, workspacePath } = useWorkspaceScope();
  const location = useLocation();
  const relativePath = workspacePath && location.pathname.startsWith(workspacePath)
    ? location.pathname.slice(workspacePath.length) || "/"
    : location.pathname;
  const approvals = useQuery({ queryKey: ["approvals", tenantId, projectId, "all"], queryFn: () => api.listApprovals(tenantId, projectId), refetchInterval: 10000 });
  const inputs = useQuery({ queryKey: ["inputs", tenantId, projectId, "all"], queryFn: () => api.listInputs(tenantId, projectId), refetchInterval: 10000 });
  const pendingActions = (approvals.data?.total ?? 0) + (inputs.data?.total ?? 0);
  const groups: Array<{ label: string; items: NavItem[] }> = [
    { label: "总览", items: [
      { label: "工作台", to: `${workspacePath}/overview`, icon: LayoutDashboard, active: (path) => path.startsWith("/overview") },
    ] },
    { label: "运行管理", items: [
      { label: "运行记录", to: `${workspacePath}/runs`, icon: Activity, active: (path) => path.startsWith("/runs") && path !== "/runs/new" },
      { label: "新建运行", to: `${workspacePath}/runs/new`, icon: Rocket, active: (path) => path === "/runs/new" },
      { label: "待办中心", to: `${workspacePath}/actions`, icon: Inbox, active: (path) => path.startsWith("/actions"), badge: pendingActions },
    ] },
    { label: "构建", items: [
      { label: "策略管理", to: `${workspacePath}/strategies`, icon: Workflow, active: (path) => path.startsWith("/strategies") },
      { label: "编排画布", to: `${workspacePath}/canvas`, icon: Network, active: (path) => path.startsWith("/canvas") },
      { label: "能力目录", to: `${workspacePath}/capabilities`, icon: Boxes, active: (path) => path.startsWith("/capabilities") },
      { label: "智能体配置", to: `${workspacePath}/agents`, icon: Bot, active: (path) => path.startsWith("/agents") },
      { label: "工具配置", to: `${workspacePath}/tools`, icon: Wrench, active: (path) => path.startsWith("/tools") },
      { label: "模型配置", to: `${workspacePath}/models`, icon: Cpu, active: (path) => path.startsWith("/models") },
    ] },
    { label: "治理", items: [
      { label: "审计日志", to: `${workspacePath}/audit-logs`, icon: ScrollText, active: (path) => path.startsWith("/audit-logs") },
    ] },
  ];

  return <nav aria-label="主导航" className="space-y-5">
    {groups.map((group) => <div key={group.label}>
      {collapsed ? null : <p className="mb-2 px-3 text-[11px] font-semibold uppercase tracking-[0.14em] text-gray-400">{group.label}</p>}
      <div className="space-y-1">{group.items.map((item) => <NavigationLink key={item.label} item={item} active={item.active(relativePath)} collapsed={collapsed} onNavigate={onNavigate} />)}</div>
    </div>)}
    <div>
      {collapsed ? null : <p className="mb-2 px-3 text-[11px] font-semibold uppercase tracking-[0.14em] text-gray-400">观测</p>}
      <div className="space-y-1">
        <ExternalNavigationLink label="Temporal" href={api.temporalUiUrl} icon={Clock3} collapsed={collapsed} />
        <ExternalNavigationLink label="Phoenix" href={api.phoenixUrl} icon={ChartNoAxesCombined} collapsed={collapsed} />
      </div>
    </div>
  </nav>;
}

function NavigationLink({ item, active, collapsed, onNavigate }: { item: NavItem; active: boolean; collapsed: boolean; onNavigate?: () => void }) {
  const Icon = item.icon;
  const link = <Link
    to={item.to}
    aria-label={item.label}
    aria-current={active ? "page" : undefined}
    onClick={onNavigate}
    className={cn("menu-item relative", active ? "menu-item-active" : "menu-item-inactive", collapsed && "justify-center px-0")}
  >
    <Icon aria-hidden className="size-5 shrink-0" />
    {collapsed ? null : <><span className="min-w-0 flex-1">{item.label}</span>{item.badge ? <span className="min-w-6 rounded-full bg-brand-500 px-1.5 py-0.5 text-center text-[11px] font-semibold text-white">{item.badge}</span> : null}</>}
    {collapsed && item.badge ? <span aria-label={`${item.badge} 项待处理`} className="absolute right-2 top-1.5 size-2 rounded-full bg-error-500" /> : null}
  </Link>;
  return collapsed ? <Tooltip><TooltipTrigger asChild>{link}</TooltipTrigger><TooltipContent side="right" className="z-99999 rounded-lg bg-gray-900 px-3 py-2 text-xs text-white">{item.label}{item.badge ? ` · ${item.badge}` : ""}</TooltipContent></Tooltip> : link;
}

function ExternalNavigationLink({ label, href, icon: Icon, collapsed }: { label: string; href: string; icon: NavItem["icon"]; collapsed: boolean }) {
  const link = <a href={href} target="_blank" rel="noreferrer" aria-label={`${label}（在新标签页打开）`} className={cn("menu-item menu-item-inactive", collapsed && "justify-center px-0")}><Icon aria-hidden className="size-5 shrink-0" />{collapsed ? null : <><span className="flex-1">{label}</span><ExternalLink aria-hidden className="size-3.5 text-gray-400" /></>}</a>;
  return collapsed ? <Tooltip><TooltipTrigger asChild>{link}</TooltipTrigger><TooltipContent side="right" className="z-99999 rounded-lg bg-gray-900 px-3 py-2 text-xs text-white">{label}</TooltipContent></Tooltip> : link;
}

function Brand({ collapsed, homePath }: { collapsed?: boolean; homePath: string }) {
  return <Link to={homePath} aria-label="SwarmCore 工作台" className={cn("flex h-20 items-center gap-3 font-semibold text-gray-900 dark:text-white", collapsed && "justify-center")}><span className="grid size-10 shrink-0 place-items-center rounded-xl bg-brand-500 text-white shadow-theme-xs"><Bot /></span>{collapsed ? null : <div><span>SwarmCore</span><p className="mt-0.5 text-[11px] font-normal text-gray-500">本地工作区</p></div>}</Link>;
}

function currentPage(pathname: string) {
  if (pathname.includes("/overview")) return "工作台";
  if (pathname.endsWith("/runs/new") || pathname === "/runs/new") return "新建运行";
  if (pathname.includes("/actions")) return "待办中心";
  if (pathname.includes("/canvas")) return "编排画布";
  if (pathname.includes("/capabilities")) return "能力目录";
  if (pathname.includes("/agents")) return "智能体配置";
  if (pathname.includes("/tools")) return "工具配置";
  if (pathname.includes("/models")) return "模型配置";
  if (pathname.includes("/audit-logs")) return "审计日志";
  if (pathname.includes("/strategies")) return "策略管理";
  return "执行控制台";
}

export function AppShell() {
  const [collapsed, setCollapsed] = React.useState(false);
  const [mobileOpen, setMobileOpen] = React.useState(false);
  const { theme, toggleTheme } = useTheme();
  const { workspacePath } = useWorkspaceScope();
  const location = useLocation();
  return <TooltipProvider>
    <div className="min-h-screen overflow-x-hidden bg-gray-50 dark:bg-gray-900">
      <aside className={cn("fixed inset-y-0 left-0 z-40 hidden flex-col border-r border-gray-200 bg-white px-4 transition-[width] xl:flex dark:border-gray-800 dark:bg-gray-900", collapsed ? "w-[90px]" : "w-[290px]")}>
        <Brand collapsed={collapsed} homePath={`${workspacePath}/overview`} />
        <div className="min-h-0 flex-1 overflow-y-auto pb-20"><Navigation collapsed={collapsed} /></div>
        <Tooltip><TooltipTrigger asChild><Button variant="ghost" size="icon" aria-label={collapsed ? "展开侧边栏" : "收起侧边栏"} onClick={() => setCollapsed((value) => !value)} className="absolute right-4 bottom-5">{collapsed ? <ChevronRight /> : <ChevronLeft />}</Button></TooltipTrigger><TooltipContent side="right" className="z-99999 rounded-lg bg-gray-900 px-3 py-2 text-xs text-white">{collapsed ? "展开侧边栏" : "收起侧边栏"}</TooltipContent></Tooltip>
      </aside>
      <div className={cn("transition-[margin]", collapsed ? "xl:ml-[90px]" : "xl:ml-[290px]")}>
        <header className="z-30 sticky top-0 flex h-16 items-center justify-between gap-3 border-b border-gray-200 bg-white/95 px-4 backdrop-blur md:px-6 dark:border-gray-800 dark:bg-gray-900/95">
          <div className="flex min-w-0 items-center gap-3"><Button variant="ghost" size="icon" aria-label="打开导航" className="shrink-0 xl:hidden" onClick={() => setMobileOpen(true)}><Menu /></Button><div className="min-w-0"><p className="truncate text-sm font-medium text-gray-800 dark:text-white/90">{currentPage(location.pathname)}</p><p className="hidden text-xs text-gray-500 sm:block">可靠、耐久的多智能体运行管理</p></div></div>
          <div className="flex items-center gap-2"><Button asChild variant="outline" size="sm" className="hidden md:inline-flex"><Link to={`${workspacePath}/canvas`}><Network />编排画布</Link></Button><Button asChild size="sm" className="hidden sm:inline-flex"><Link to={`${workspacePath}/runs/new`}><Plus />新建运行</Link></Button><Button variant="outline" size="icon" aria-label="切换颜色主题" onClick={toggleTheme}>{theme === "dark" ? <Sun /> : <Moon />}</Button></div>
        </header>
        <main className="mx-auto w-full max-w-(--breakpoint-2xl) p-4 pb-20 md:p-6 md:pb-24"><Outlet /></main>
      </div>
      <Dialog.Root open={mobileOpen} onOpenChange={setMobileOpen}><Dialog.Portal><Dialog.Overlay className="z-99999 fixed inset-0 bg-gray-900/50" /><Dialog.Content aria-describedby={undefined} className="z-99999 fixed inset-y-0 left-0 w-[310px] max-w-[88vw] overflow-y-auto bg-white px-5 shadow-theme-sm focus:outline-hidden dark:bg-gray-900"><Dialog.Title className="sr-only">导航</Dialog.Title><div className="flex items-center justify-between"><Brand homePath={`${workspacePath}/overview`} /><Dialog.Close asChild><Button variant="ghost" size="icon" aria-label="关闭导航"><X /></Button></Dialog.Close></div><Navigation onNavigate={() => setMobileOpen(false)} /></Dialog.Content></Dialog.Portal></Dialog.Root>
    </div>
  </TooltipProvider>;
}
