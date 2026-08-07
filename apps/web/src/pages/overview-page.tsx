import { useQuery } from "@tanstack/react-query";
import {
  Activity,
  ArrowRight,
  CheckCircle2,
  Clock3,
  FileWarning,
  FolderOpen,
  Inbox,
  Layers3,
  Play,
  RefreshCw,
  Settings2,
} from "lucide-react";
import type * as React from "react";
import { Link } from "react-router";
import { api } from "@/api/client";
import type { ProjectOverviewRunSnapshot, ProjectOverviewWorkSnapshot } from "@/api/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { PageHeader } from "@/components/ui/page-header";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusBadge } from "@/components/ui/status-badge";
import { useWorkspaceScope } from "@/lib/demo-scope";

const workStatusTone: Record<ProjectOverviewWorkSnapshot["status"], string> = {
  runnable: "bg-success-50 text-success-700 dark:bg-success-500/15 dark:text-success-300",
  incomplete: "bg-warning-50 text-warning-700 dark:bg-warning-500/15 dark:text-warning-300",
  not_configured: "bg-warning-50 text-warning-700 dark:bg-warning-500/15 dark:text-warning-300",
  planned: "bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-300",
  unavailable: "bg-error-50 text-error-700 dark:bg-error-500/15 dark:text-error-300",
};

export function OverviewPage() {
  const { tenantId, projectId, workspacePath } = useWorkspaceScope();
  const overview = useQuery({
    queryKey: ["overview", tenantId, projectId],
    queryFn: () => api.getProjectOverview(tenantId, projectId),
    refetchInterval: 10_000,
    staleTime: 5_000,
  });
  const refresh = () => void overview.refetch();
  const businessWorks = overview.data?.businessWorks.filter((work) => work.category === "business") ?? [];
  const secondaryWorks = overview.data?.businessWorks.filter((work) => work.category !== "business") ?? [];

  return (
    <div className="min-w-0 space-y-6">
      <PageHeader
        eyebrow="项目总览"
        title="项目工作台"
        description="聚焦当前未闭环事项、业务工作准备度和最新执行动态。"
        actions={(
          <>
            <Button variant="outline" onClick={refresh} loading={overview.isFetching}>
              <RefreshCw />刷新
            </Button>
            <Button asChild variant="outline"><Link to={`${workspacePath}/documents`}><FolderOpen />业务资料</Link></Button>
            <Button asChild><Link to={`${workspacePath}/actions`}><Inbox />待办中心</Link></Button>
          </>
        )}
      />

      {overview.isPending ? <OverviewSkeleton /> : null}
      {overview.isError && !overview.data ? (
        <Card>
          <CardContent className="pt-5">
            <ErrorState
              title="项目概览暂时无法加载"
              message="业务资料和待办中心仍可通过页面头部进入。"
              onRetry={refresh}
            />
          </CardContent>
        </Card>
      ) : null}
      {overview.data ? (
        <>
          <AttentionSection counts={overview.data.counts} workspacePath={workspacePath} />
          <section aria-labelledby="business-works-heading" className="space-y-3">
            <SectionHeading
              id="business-works-heading"
              title="业务工作"
              description="准备就绪后可直接开始处理；存在阻塞时先补齐资料或配置。"
            />
            {businessWorks.length ? (
              <div className="overview-business-grid grid gap-4">
                {businessWorks.map((work) => <BusinessWorkCard key={work.workKey} work={work} workspacePath={workspacePath} />)}
              </div>
            ) : (
              <Card><CardContent className="pt-5"><EmptyState icon={Layers3} title="暂无业务工作" description="业务工作配置完成后会在这里展示。" /></CardContent></Card>
            )}
          </section>
          <SecondaryWorks works={secondaryWorks} workspacePath={workspacePath} />
          <RecentRuns runs={overview.data.recentRuns} workspacePath={workspacePath} />
        </>
      ) : null}
    </div>
  );
}

function SectionHeading({ id, title, description }: { id: string; title: string; description: string }) {
  return (
    <div>
      <h2 id={id} className="text-lg font-semibold tracking-[-0.01em] text-gray-900 dark:text-white">{title}</h2>
      <p className="mt-1 text-sm text-gray-500">{description}</p>
    </div>
  );
}

function OverviewSkeleton() {
  return (
    <div aria-label="正在加载项目工作台" className="space-y-6">
      <div className="grid gap-4 md:grid-cols-3">{[1, 2, 3].map((item) => <Skeleton key={item} className="h-32 rounded-[20px]" />)}</div>
      <div className="overview-business-grid grid gap-4">{[1, 2, 3, 4, 5, 6].map((item) => <Skeleton key={item} className="h-56 rounded-[20px]" />)}</div>
      <Skeleton className="h-64 rounded-[20px]" />
    </div>
  );
}

interface OverviewCounts {
  pendingApprovals: number;
  pendingInputs: number;
  documentsReviewRequired: number;
  documentsFailed: number;
  activeRuns: number;
  waitingRuns: number;
}

function AttentionSection({ counts, workspacePath }: { counts: OverviewCounts; workspacePath: string }) {
  const human = counts.pendingApprovals + counts.pendingInputs;
  const documents = counts.documentsReviewRequired + counts.documentsFailed;
  const clear = human === 0 && documents === 0 && counts.activeRuns === 0;
  return (
    <section aria-labelledby="attention-heading" className="space-y-3">
      <SectionHeading id="attention-heading" title="需要关注" description="只统计当前仍未闭环的事项。" />
      {clear ? (
        <Card className="border-success-200 bg-success-50/70 dark:border-success-500/30 dark:bg-success-500/10">
          <CardContent className="flex items-center gap-3 pt-5 text-success-700 dark:text-success-300">
            <CheckCircle2 aria-hidden className="size-6 shrink-0" />
            <div><p className="font-semibold">当前事项已闭环</p><p className="mt-0.5 text-sm">暂无待审批、待输入、异常资料或未结束运行。</p></div>
          </CardContent>
        </Card>
      ) : null}
      <div className="grid gap-4 md:grid-cols-3">
        <AttentionCard
          title="人工待办"
          value={human}
          detail={`${counts.pendingApprovals} 项审批 · ${counts.pendingInputs} 项外部输入`}
          to={`${workspacePath}/actions`}
          icon={Inbox}
          alert={human > 0}
        />
        <AttentionCard
          title="资料需处理"
          value={documents}
          detail={`${counts.documentsReviewRequired} 份待复核 · ${counts.documentsFailed} 份处理失败`}
          to={`${workspacePath}/documents?view=failed`}
          icon={FileWarning}
          alert={documents > 0}
        />
        <AttentionCard
          title="运行动态"
          value={counts.activeRuns}
          detail={`${counts.activeRuns} 个活跃运行 · ${counts.waitingRuns} 个等待人工处理`}
          to={`${workspacePath}/runs`}
          icon={Activity}
          alert={counts.waitingRuns > 0}
        />
      </div>
    </section>
  );
}

function AttentionCard({ title, value, detail, to, icon: Icon, alert }: {
  title: string;
  value: number;
  detail: string;
  to: string;
  icon: React.ComponentType<{ className?: string; "aria-hidden"?: boolean }>;
  alert: boolean;
}) {
  return (
    <Link
      to={to}
      aria-label={`${title}：${detail}`}
      className="group rounded-[20px] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-500"
    >
      <Card className="h-full transition group-hover:border-brand-300 group-hover:bg-brand-50/30 dark:group-hover:border-brand-500/50 dark:group-hover:bg-brand-500/5">
        <CardContent className="pt-5">
          <div className="flex items-start justify-between gap-4">
            <span className={`grid size-11 place-items-center rounded-xl ${alert ? "bg-warning-50 text-warning-600 dark:bg-warning-500/15 dark:text-warning-300" : "bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-300"}`}>
              <Icon aria-hidden className="size-5" />
            </span>
            <ArrowRight aria-hidden className="size-4 text-gray-400 transition group-hover:translate-x-0.5 group-hover:text-brand-500" />
          </div>
          <p className="mt-4 text-sm font-medium text-gray-600 dark:text-gray-300">{title}</p>
          <p className="mt-1 text-3xl font-semibold text-gray-900 dark:text-white">{value}</p>
          <p className="mt-2 text-xs text-gray-500">{detail}</p>
        </CardContent>
      </Card>
    </Link>
  );
}

function BusinessWorkCard({ work, workspacePath }: { work: ProjectOverviewWorkSnapshot; workspacePath: string }) {
  const action = businessWorkAction(work, workspacePath);
  const documentsText = work.readiness.requiredDocuments === 0
    ? "无需必需资料"
    : `${work.readiness.satisfiedDocuments}/${work.readiness.requiredDocuments} 份必需资料`;
  return (
    <Card className="flex min-h-56 flex-col">
      <CardHeader className="items-start">
        <div className="min-w-0">
          <CardTitle className="text-base">{work.name}</CardTitle>
          <p className="mt-1 text-xs text-gray-500">{work.shortName}</p>
        </div>
        <span className={`shrink-0 rounded-full px-2.5 py-1 text-xs font-medium ${workStatusTone[work.status]}`}>{work.statusLabel}</span>
      </CardHeader>
      <CardContent className="flex flex-1 flex-col">
        <dl className="space-y-2 text-sm">
          <div className="flex items-center justify-between gap-3"><dt className="text-gray-500">资料准备</dt><dd className={work.readiness.documentsReady ? "text-success-700 dark:text-success-300" : "text-warning-700 dark:text-warning-300"}>{documentsText}</dd></div>
          <div className="flex items-center justify-between gap-3"><dt className="text-gray-500">最近运行</dt><dd>{work.latestRun ? <StatusBadge status={work.latestRun.status} /> : <span className="text-gray-400">暂无运行</span>}</dd></div>
          <div className="flex items-center justify-between gap-3"><dt className="text-gray-500">生产准入</dt><dd className="text-right text-xs">{work.qualificationLabel}</dd></div>
        </dl>
        {!work.readiness.documentsReady ? <p className="mt-3 line-clamp-2 text-xs text-warning-700 dark:text-warning-300">必需资料未齐，请先查看缺失项。</p> : null}
        {work.status !== "runnable" && work.blockers[0] ? <p className="mt-3 line-clamp-2 text-xs text-error-600 dark:text-error-300">{work.blockers[0].message}</p> : null}
        <div className="mt-auto flex justify-end pt-5">
          <Button asChild size="sm" variant={action.variant}>
            <Link to={action.to} aria-label={`${work.name}：${action.label}`}>{action.icon}{action.label}</Link>
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

function businessWorkAction(work: ProjectOverviewWorkSnapshot, workspacePath: string) {
  if (work.activeRunId) {
    return { label: "查看运行", to: `${workspacePath}/runs/${work.activeRunId}`, icon: <Activity />, variant: "outline" as const };
  }
  if (work.status !== "runnable") {
    return { label: "完成配置", to: `${workspacePath}/business-works/${work.workKey}/settings`, icon: <Settings2 />, variant: "outline" as const };
  }
  if (!work.readiness.documentsReady) {
    return { label: "查看缺失项", to: `${workspacePath}/business-works/${work.workKey}`, icon: <FolderOpen />, variant: "outline" as const };
  }
  return { label: "开始处理", to: `${workspacePath}/business-works/${work.workKey}/workbench`, icon: <Play />, variant: "primary" as const };
}

function SecondaryWorks({ works, workspacePath }: { works: ProjectOverviewWorkSnapshot[]; workspacePath: string }) {
  return (
    <section aria-labelledby="secondary-works-heading" className="space-y-3">
      <SectionHeading id="secondary-works-heading" title="基础与治理" description="支撑业务处理的基础能力和调度治理状态。" />
      {works.length ? (
        <div className="grid gap-3 md:grid-cols-3">
          {works.map((work) => (
            <Card key={work.workKey}>
              <CardContent className="flex items-center gap-3 pt-5">
                <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-300"><Layers3 aria-hidden className="size-5" /></span>
                <div className="min-w-0 flex-1"><p className="truncate text-sm font-semibold text-gray-900 dark:text-white">{work.name}</p><p className="mt-1 flex items-center gap-2 text-xs text-gray-500"><span>{work.statusLabel}</span><span aria-hidden>·</span><span>{work.latestRun ? `最近 ${statusText(work.latestRun.status)}` : "暂无运行"}</span></p></div>
                <Button asChild variant="ghost" size="icon"><Link to={`${workspacePath}/business-works/${work.workKey}`} aria-label={`查看${work.name}详情`}><ArrowRight /></Link></Button>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : <Card><CardContent className="pt-5"><EmptyState icon={Layers3} title="暂无基础与治理工作" /></CardContent></Card>}
    </section>
  );
}

function RecentRuns({ runs, workspacePath }: { runs: ProjectOverviewRunSnapshot[]; workspacePath: string }) {
  return (
    <section aria-labelledby="recent-runs-heading">
      <Card>
        <CardHeader>
          <div><CardTitle id="recent-runs-heading">最近动态</CardTitle><p className="mt-1 text-sm text-gray-500">最近 5 条业务执行摘要。</p></div>
          <Button asChild variant="ghost" size="sm"><Link to={`${workspacePath}/runs`}>查看全部 <ArrowRight /></Link></Button>
        </CardHeader>
        <CardContent>
          {!runs.length ? <EmptyState icon={Activity} title="暂无运行动态" description="开始业务处理后，运行摘要会显示在这里。" /> : null}
          {runs.length ? <div className="divide-y divide-gray-100 dark:divide-gray-800">{runs.map((run) => <RunRow key={run.runId} run={run} workspacePath={workspacePath} />)}</div> : null}
        </CardContent>
      </Card>
    </section>
  );
}

function RunRow({ run, workspacePath }: { run: ProjectOverviewRunSnapshot; workspacePath: string }) {
  const reason = run.failureReason || run.cancelReason;
  return (
    <Link to={`${workspacePath}/runs/${run.runId}`} aria-label={`${run.businessWorkName}，运行 ${run.runId}`} className="group block py-4 first:pt-0 last:pb-0">
      <span className="flex min-w-0 items-start justify-between gap-4">
        <span className="min-w-0">
          <span className="block truncate text-sm font-semibold text-gray-900 group-hover:text-brand-600 dark:text-white">{run.businessWorkName}</span>
          <span className="mt-0.5 block truncate font-mono text-[11px] text-gray-400">{run.runId}</span>
          <span className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-gray-500">
            <span className="inline-flex items-center gap-1"><Clock3 aria-hidden className="size-3" />{formatShortTime(run.createdAt)}</span>
            {formatDuration(run.startedAt, run.completedAt) ? <span>耗时 {formatDuration(run.startedAt, run.completedAt)}</span> : null}
            <span>{run.taskCount} 个任务 · {run.eventCount} 个事件</span>
            <span>操作人 {run.operatorName}</span>
          </span>
          {reason ? <span className="mt-2 block line-clamp-1 text-xs text-error-600 dark:text-error-300">{reason}</span> : null}
        </span>
        <StatusBadge status={run.status} />
      </span>
    </Link>
  );
}

function statusText(status: string) {
  const labels: Record<string, string> = { SUCCEEDED: "已成功", FAILED: "失败", RUNNING: "运行中", WAITING_APPROVAL: "待审批", WAITING_INPUT: "待输入", CANCELLED: "已取消" };
  return labels[status] ?? status;
}

function formatShortTime(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "时间未知";
  const now = new Date();
  return date.toDateString() === now.toDateString()
    ? date.toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" })
    : date.toLocaleString("zh-CN", { month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" });
}

function formatDuration(start?: string | null, end?: string | null): string | null {
  if (!start) return null;
  const startMs = new Date(start).getTime();
  const endMs = end ? new Date(end).getTime() : Date.now();
  if (Number.isNaN(startMs) || Number.isNaN(endMs) || endMs < startMs) return null;
  const ms = endMs - startMs;
  if (ms < 1_000) return `${ms} 毫秒`;
  if (ms < 60_000) return `${(ms / 1_000).toFixed(1)} 秒`;
  if (ms < 3_600_000) return `${Math.floor(ms / 60_000)} 分 ${Math.round((ms % 60_000) / 1_000)} 秒`;
  return `${(ms / 3_600_000).toFixed(1)} 小时`;
}
