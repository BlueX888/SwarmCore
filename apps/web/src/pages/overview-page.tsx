import { useQuery } from "@tanstack/react-query";
import {
  Activity, ArrowRight, Bot, Boxes, Cpu, Inbox, Network, Plus, RefreshCw, Rocket, ScrollText, Workflow, Wrench,
} from "lucide-react";
import type * as React from "react";
import { Link } from "react-router";
import { api } from "@/api/client";
import type { RunSnapshot } from "@/api/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusBadge } from "@/components/ui/status-badge";
import { useWorkspaceScope } from "@/lib/demo-scope";

const activeStatuses = new Set(["RUNNING", "QUEUED", "PAUSING", "CANCELLING"]);

export function OverviewPage() {
  const { tenantId, projectId, workspacePath } = useWorkspaceScope();
  const runs = useQuery({ queryKey: ["runs", tenantId, projectId], queryFn: () => api.listRuns(tenantId, projectId), refetchInterval: 5000 });
  const strategies = useQuery({ queryKey: ["strategies", tenantId, projectId], queryFn: () => api.listStrategies(tenantId, projectId) });
  const approvals = useQuery({ queryKey: ["approvals", tenantId, projectId, "all"], queryFn: () => api.listApprovals(tenantId, projectId), refetchInterval: 10000 });
  const inputs = useQuery({ queryKey: ["inputs", tenantId, projectId, "all"], queryFn: () => api.listInputs(tenantId, projectId), refetchInterval: 10000 });
  const capabilities = useQuery({ queryKey: ["capabilities", tenantId, projectId], queryFn: () => api.getCapabilities(tenantId, projectId) });
  const queries = [runs, strategies, approvals, inputs, capabilities];
  const refreshing = queries.some((query) => query.isFetching);
  const hasError = queries.some((query) => query.isError);
  const activeRuns = runs.data?.items.filter((run) => activeStatuses.has(run.status)).length ?? 0;
  const publishedStrategies = strategies.data?.items.filter((strategy) => strategy.latestVersion !== null).length ?? 0;
  const pendingApprovals = approvals.data?.total ?? 0;
  const pendingInputs = inputs.data?.total ?? 0;
  const capabilityTotal = capabilities.data
    ? capabilities.data.agents.length + capabilities.data.tools.length + capabilities.data.models.length
    : undefined;
  const refresh = () => void Promise.all(queries.map((query) => query.refetch()));

  const metrics: MetricProps[] = [
    { label: "全部运行", value: runs.data?.total, detail: `${activeRuns} 个正在执行`, to: `${workspacePath}/runs`, icon: Activity, tone: "brand" },
    { label: "项目策略", value: strategies.data?.total, detail: `${publishedStrategies} 个已有发布版本`, to: `${workspacePath}/strategies`, icon: Workflow, tone: "success" },
    { label: "待办事项", value: pendingApprovals + pendingInputs, detail: `${pendingApprovals} 项审批 · ${pendingInputs} 项输入`, to: `${workspacePath}/actions`, icon: Inbox, tone: "warning" },
    { label: "能力资源", value: capabilityTotal, detail: capabilities.data ? `${capabilities.data.agents.length} 个智能体 · ${capabilities.data.tools.length} 个工具 · ${capabilities.data.models.length} 个模型` : "正在读取能力目录", to: `${workspacePath}/capabilities`, icon: Boxes, tone: "brand" },
  ];

  return <div className="min-w-0 space-y-6">
    <div className="flex flex-wrap items-end justify-between gap-4">
      <div><p className="text-sm font-medium text-brand-500">项目总览</p><h1 className="mt-1 text-2xl font-semibold text-gray-900 dark:text-white">工作台</h1><p className="mt-1 text-sm text-gray-500">掌握当前项目状态，并快速进入常用操作。</p></div>
      <div className="flex flex-wrap gap-2"><Button variant="outline" onClick={refresh} loading={refreshing}><RefreshCw />刷新数据</Button><Button asChild variant="outline"><Link to={`${workspacePath}/canvas`}><Network />打开画布</Link></Button><Button asChild><Link to={`${workspacePath}/runs/new`}><Plus />新建运行</Link></Button></div>
    </div>

    {hasError ? <p role="alert" className="rounded-xl border border-warning-200 bg-warning-50 p-3 text-sm text-warning-700 dark:border-warning-500/30 dark:bg-warning-500/10">部分概览数据暂时无法加载，快捷入口仍可正常使用。</p> : null}

    <section aria-label="项目指标" className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      {metrics.map((metric) => <MetricCard key={metric.label} {...metric} />)}
    </section>

    <div className="grid min-w-0 gap-5 xl:grid-cols-[1.15fr_0.85fr]">
      <NavigationHub workspacePath={workspacePath} />
      <RecentRuns runs={runs.data?.items} loading={runs.isPending} error={runs.isError} workspacePath={workspacePath} />
    </div>
  </div>;
}

interface MetricProps {
  label: string;
  value: number | undefined;
  detail: string;
  to: string;
  icon: React.ComponentType<{ className?: string; "aria-hidden"?: boolean }>;
  tone: "brand" | "success" | "warning";
}

const metricTones: Record<MetricProps["tone"], string> = {
  brand: "bg-brand-50 text-brand-600 dark:bg-brand-500/15",
  success: "bg-success-50 text-success-600 dark:bg-success-500/15",
  warning: "bg-warning-50 text-warning-600 dark:bg-warning-500/15",
};

function MetricCard({ label, value, detail, to, icon: Icon, tone }: MetricProps) {
  return <Card><CardContent className="pt-5"><div className="flex items-start justify-between gap-3"><span className={`grid size-11 shrink-0 place-items-center rounded-xl ${metricTones[tone]}`}><Icon aria-hidden className="size-5" /></span><Button asChild variant="ghost" size="icon"><Link to={to} aria-label={`打开${label}`}><ArrowRight /></Link></Button></div><p className="mt-5 text-sm text-gray-500">{label}</p>{value === undefined ? <Skeleton className="mt-2 h-9 w-16" /> : <p className="mt-1 text-3xl font-semibold text-gray-900 dark:text-white">{value}</p>}<p className="mt-2 text-xs text-gray-500">{detail}</p></CardContent></Card>;
}

function NavigationHub({ workspacePath }: { workspacePath: string }) {
  const groups = [
    { label: "运行", items: [
      { label: "新建运行", detail: "从已发布策略启动执行", to: `${workspacePath}/runs/new`, icon: Rocket },
      { label: "运行记录", detail: "查看状态、任务和结果", to: `${workspacePath}/runs`, icon: Activity },
      { label: "待办中心", detail: "处理审批和外部输入", to: `${workspacePath}/actions`, icon: Inbox },
    ] },
    { label: "策略与配置", items: [
      { label: "策略管理", detail: "维护草稿和发布版本", to: `${workspacePath}/strategies`, icon: Workflow },
      { label: "编排画布", detail: "可视化设计执行流程", to: `${workspacePath}/canvas`, icon: Network },
      { label: "智能体配置", detail: "生成智能体节点声明", to: `${workspacePath}/agents`, icon: Bot },
      { label: "工具配置", detail: "选择受控工具并配置输入", to: `${workspacePath}/tools`, icon: Wrench },
      { label: "模型配置", detail: "设置策略默认逻辑模型", to: `${workspacePath}/models`, icon: Cpu },
      { label: "能力目录", detail: "查看当前注册表能力", to: `${workspacePath}/capabilities`, icon: Boxes },
    ] },
    { label: "治理", items: [
      { label: "审计日志", detail: "查询并导出项目活动记录", to: `${workspacePath}/audit-logs`, icon: ScrollText },
    ] },
  ];
  return <Card className="min-w-0"><CardHeader><div><CardTitle>功能导航</CardTitle><p className="mt-1 text-sm text-gray-500">按任务快速进入项目功能。</p></div></CardHeader><CardContent className="space-y-5">{groups.map((group) => <section key={group.label} aria-labelledby={`nav-${group.label}`}><h3 id={`nav-${group.label}`} className="mb-2 text-xs font-semibold text-gray-400">{group.label}</h3><div className="grid gap-2 sm:grid-cols-2">{group.items.map((item) => <NavigationCard key={item.label} {...item} />)}</div></section>)}</CardContent></Card>;
}

function NavigationCard({ label, detail, to, icon: Icon }: { label: string; detail: string; to: string; icon: MetricProps["icon"] }) {
  return <Link to={to} className="group flex min-w-0 items-center gap-3 rounded-xl border border-gray-200 p-3 transition hover:border-brand-300 hover:bg-brand-50/50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-500 dark:border-gray-800 dark:hover:border-brand-500/50 dark:hover:bg-brand-500/5"><span className="grid size-10 shrink-0 place-items-center rounded-lg bg-gray-100 text-gray-600 group-hover:bg-white group-hover:text-brand-600 dark:bg-gray-800 dark:text-gray-300 dark:group-hover:bg-gray-900"><Icon aria-hidden className="size-5" /></span><span className="min-w-0 flex-1"><span className="block text-sm font-medium text-gray-900 dark:text-white">{label}</span><span className="mt-0.5 block truncate text-xs text-gray-500">{detail}</span></span><ArrowRight aria-hidden className="size-4 shrink-0 text-gray-400 group-hover:text-brand-500" /></Link>;
}

function RecentRuns({ runs, loading, error, workspacePath }: { runs: RunSnapshot[] | undefined; loading: boolean; error: boolean; workspacePath: string }) {
  return <Card className="min-w-0"><CardHeader><div><CardTitle>最近运行</CardTitle><p className="mt-1 text-sm text-gray-500">快速查看最新执行状态。</p></div><Button asChild variant="ghost" size="sm"><Link to={`${workspacePath}/runs`}>查看全部 <ArrowRight /></Link></Button></CardHeader><CardContent>{loading ? <div className="space-y-3">{[1, 2, 3].map((item) => <Skeleton key={item} className="h-16" />)}</div> : null}{error ? <p className="rounded-xl bg-error-50 p-4 text-sm text-error-600 dark:bg-error-500/10">无法加载最近运行。</p> : null}{!loading && !error && !runs?.length ? <div className="flex min-h-48 flex-col items-center justify-center text-center"><span className="grid size-12 place-items-center rounded-xl bg-brand-50 text-brand-500 dark:bg-brand-500/15"><Rocket /></span><p className="mt-3 font-medium text-gray-900 dark:text-white">还没有运行记录</p><p className="mt-1 text-sm text-gray-500">发布策略后即可启动第一次运行。</p><Button asChild className="mt-4" size="sm"><Link to={`${workspacePath}/runs/new`}>新建运行</Link></Button></div> : null}{runs?.length ? <div className="divide-y divide-gray-100 dark:divide-gray-800">{runs.slice(0, 5).map((run) => <Link key={run.runId} to={`${workspacePath}/runs/${run.runId}`} className="flex min-w-0 items-center justify-between gap-3 py-3 first:pt-0 last:pb-0"><span className="min-w-0"><span className="block truncate font-mono text-xs text-gray-700 dark:text-gray-300">{run.runId}</span><span className="mt-1 block text-xs text-gray-500">{Object.values(run.taskCounts).reduce((total, count) => total + count, 0)} 个任务 · {run.snapshotSeq} 个事件</span></span><StatusBadge status={run.status} /></Link>)}</div> : null}</CardContent></Card>;
}
