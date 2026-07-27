import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Activity, ArrowRight, BrainCircuit, BriefcaseBusiness, ChartNoAxesCombined, CheckCircle2, Files,
  FileCheck2, FileOutput, FileScan, Gauge, Network, Play, ReceiptText, Search, Settings2, ShieldCheck, Sparkles,
  Workflow,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { Link, useParams, useSearchParams } from "react-router";
import { api } from "@/api/client";
import type { BusinessWorkSnapshot, BusinessWorkStatus, DocumentSnapshot } from "@/api/types";
import { Badge } from "@/components/ui/badge";
import { BackLink } from "@/components/ui/back-link";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusBadge } from "@/components/ui/status-badge";
import {
  BUSINESS_WORK_CATEGORIES, BUSINESS_WORKS, DOCUMENT_CATEGORY_LABELS, documentBindingKeys, getBusinessWork,
  type BusinessWorkCategory, type BusinessWorkDefinition,
} from "@/lib/business-works";
import { useWorkspaceScope } from "@/lib/demo-scope";
import { cn } from "@/lib/utils";

const WORK_RUN_HISTORY_LIMIT = 5;

const WORK_ICONS: Record<string, LucideIcon> = {
  "ai-foundation-quality": BrainCircuit,
  "document-structuring": FileScan,
  "document-integrity": FileCheck2,
  "performance-plan-collection": BriefcaseBusiness,
  "invoice-assurance": ReceiptText,
  "deviation-analysis": Gauge,
  "report-generation": FileOutput,
  "contract-post-evaluation": ChartNoAxesCombined,
  "swarm-calibration": Network,
  "procurement-supplier-risk": ShieldCheck,
};

const CATEGORY_LABELS: Record<BusinessWorkCategory, string> = {
  foundation: "基础能力",
  business: "业务处理",
  governance: "调度治理",
};

const STATUS_BADGE: Record<BusinessWorkStatus, "neutral" | "primary" | "success" | "warning" | "error"> = {
  planned: "neutral",
  not_configured: "warning",
  incomplete: "warning",
  runnable: "success",
  unavailable: "error",
};

export function BusinessWorksPage() {
  const { workKey } = useParams();
  return workKey ? <BusinessWorkDetail workKey={workKey} /> : <BusinessWorkCatalog />;
}

function BusinessWorkCatalog() {
  const { tenantId, projectId, workspacePath } = useWorkspaceScope();
  const [searchParams] = useSearchParams();
  const notice = searchParams.get("notice");
  const [category, setCategory] = useState<"all" | BusinessWorkCategory>("all");
  const [search, setSearch] = useState("");
  const works = useQuery({
    queryKey: ["business-works", tenantId, projectId],
    queryFn: () => api.listBusinessWorks(tenantId, projectId),
  });
  const items = works.data?.items ?? fallbackSnapshots();
  const visibleWorks = useMemo(() => {
    const keyword = search.trim().toLocaleLowerCase();
    return items.filter((work) => {
      if (category !== "all" && work.category !== category) return false;
      if (!keyword) return true;
      return [work.name, work.shortName, work.summary, ...work.functions.flatMap((item) => [item.name, item.description])]
        .some((value) => value.toLocaleLowerCase().includes(keyword));
    });
  }, [category, items, search]);

  return <div className="min-w-0 space-y-6">
    <header className="flex flex-wrap items-end justify-between gap-4">
      <div>
        <p className="text-sm font-medium text-brand-500">AI 智能体蜂群</p>
        <h1 className="mt-1 text-2xl font-semibold text-gray-900 dark:text-white">业务工作</h1>
        <p className="mt-1 max-w-3xl text-sm text-gray-500">按业务目标组织工作，每项工作独立组合 Agent、工具、模型、规则、业务资料和人工复核。</p>
      </div>
    </header>

    {notice ? <Card><CardContent className="border border-warning-200 bg-warning-50 p-4 text-sm text-warning-800 dark:border-warning-500/20 dark:bg-warning-500/10 dark:text-warning-300">{notice}</CardContent></Card> : null}
    {works.isError ? <Card><CardContent className="p-4 text-sm text-error-600">业务工作状态加载失败：{works.error.message}。当前显示本地目录。</CardContent></Card> : null}

    <section aria-label="业务工作概况" className="grid gap-3 sm:grid-cols-3">
      <SummaryCard label="业务工作" value={items.length} detail="独立工作入口" />
      <SummaryCard label="可运行" value={items.filter((item) => item.status === "runnable").length} detail="已满足运行资格" />
      <SummaryCard label="规划中" value={items.filter((item) => item.status === "planned").length} detail="尚未实现执行定义" />
    </section>

    <section className="space-y-4">
      <div className="flex flex-col gap-3 rounded-2xl border border-gray-200/80 bg-white/80 p-3 shadow-theme-xs backdrop-blur sm:flex-row sm:items-center sm:justify-between dark:border-gray-800 dark:bg-gray-900/70">
        <div className="flex gap-1 overflow-x-auto" role="group" aria-label="业务工作分类">
          {BUSINESS_WORK_CATEGORIES.map((item) => <button
            key={item.value}
            type="button"
            aria-pressed={category === item.value}
            onClick={() => setCategory(item.value)}
            className={cn("shrink-0 rounded-xl px-3 py-2 text-sm font-semibold transition", category === item.value ? "bg-brand-50 text-brand-600 dark:bg-brand-500/15 dark:text-brand-400" : "text-gray-500 hover:bg-gray-50 hover:text-gray-900 dark:hover:bg-gray-800 dark:hover:text-white")}
          >{item.label}</button>)}
        </div>
        <label className="relative block sm:w-72">
          <span className="sr-only">搜索业务工作或功能</span>
          <Search aria-hidden className="pointer-events-none absolute left-3.5 top-1/2 size-4 -translate-y-1/2 text-gray-400" />
          <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="搜索工作或功能" className="h-11 w-full rounded-xl border border-gray-200 bg-white pl-10 pr-3 text-sm text-gray-800 outline-none transition focus:border-brand-500 focus:ring-3 focus:ring-brand-500/10 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-200" />
        </label>
      </div>

      {works.isPending ? <div className="grid gap-4 lg:grid-cols-2 xl:grid-cols-3"><Skeleton className="h-64" /><Skeleton className="h-64" /><Skeleton className="h-64" /></div>
        : visibleWorks.length ? <div className="grid gap-4 lg:grid-cols-2 xl:grid-cols-3">
          {visibleWorks.map((work) => <BusinessWorkCard key={work.workKey} work={work} href={`${workspacePath}/business-works/${work.workKey}`} />)}
        </div> : <Card><CardContent className="flex min-h-56 flex-col items-center justify-center gap-2 p-6 text-center"><Search className="size-8 text-gray-300" /><p className="font-semibold text-gray-900 dark:text-white">没有匹配的业务工作</p><p className="text-sm text-gray-500">尝试更换分类或搜索词。</p></CardContent></Card>}
    </section>
  </div>;
}

function BusinessWorkCard({ work, href }: { work: BusinessWorkSnapshot; href: string }) {
  const Icon = WORK_ICONS[work.workKey] ?? BriefcaseBusiness;
  return <Card className="group transition hover:-translate-y-0.5 hover:border-brand-300 hover:shadow-theme-float dark:hover:border-brand-500/50">
    <CardContent className="flex h-full flex-col p-5">
      <div className="flex items-start justify-between gap-3">
        <span className="grid size-11 shrink-0 place-items-center rounded-2xl bg-brand-50 text-brand-600 dark:bg-brand-500/15 dark:text-brand-400"><Icon className="size-5" /></span>
        <div className="flex flex-wrap justify-end gap-1.5"><Badge color={STATUS_BADGE[work.status]}>{work.statusLabel}</Badge><Badge color={work.category === "business" ? "primary" : "neutral"}>{CATEGORY_LABELS[work.category as BusinessWorkCategory] ?? work.category}</Badge></div>
      </div>
      <h2 className="mt-4 text-base font-semibold text-gray-900 dark:text-white">{work.name}</h2>
      <p className="mt-2 flex-1 text-sm leading-6 text-gray-500">{work.summary}</p>
      <div className="mt-4 flex flex-wrap gap-1.5">{work.functions.slice(0, 3).map((item) => <span key={item.name} className="rounded-lg bg-gray-50 px-2 py-1 text-xs text-gray-600 dark:bg-gray-800 dark:text-gray-300">{item.name}</span>)}{work.functions.length > 3 ? <span className="rounded-lg bg-gray-50 px-2 py-1 text-xs text-gray-500 dark:bg-gray-800">+{work.functions.length - 3}</span> : null}</div>
      <Link to={href} aria-label={`查看${work.name}`} className="mt-5 inline-flex items-center gap-1.5 text-sm font-semibold text-brand-600 outline-none transition group-hover:gap-2.5 focus-visible:rounded-lg focus-visible:ring-3 focus-visible:ring-brand-500/20 dark:text-brand-400">进入业务工作<ArrowRight className="size-4" /></Link>
    </CardContent>
  </Card>;
}

function BusinessWorkDetail({ workKey }: { workKey: string }) {
  const { tenantId, projectId, workspacePath } = useWorkspaceScope();
  const local = getBusinessWork(workKey);
  const workQuery = useQuery({
    queryKey: ["business-work", tenantId, projectId, workKey],
    queryFn: () => api.getBusinessWork(tenantId, projectId, workKey),
  });
  // Wait for API before falling back to local catalog, so configured works
  // are not briefly (or permanently on error) shown with empty requirements.
  if (workQuery.isPending) {
    return <div className="space-y-4"><Skeleton className="h-40" /><Skeleton className="h-72" /></div>;
  }
  const work = workQuery.data ?? (local ? snapshotFromDefinition(local) : null);
  if (!work) return <Card><CardContent className="flex min-h-72 flex-col items-center justify-center gap-3 p-6 text-center"><BriefcaseBusiness className="size-9 text-gray-300" /><h1 className="text-lg font-semibold text-gray-900 dark:text-white">业务工作不存在</h1><p className="text-sm text-gray-500">该工作可能尚未登记或地址有误。</p><Button asChild variant="outline"><Link to={`${workspacePath}/business-works`}>返回业务工作</Link></Button></CardContent></Card>;
  const Icon = WORK_ICONS[work.workKey] ?? BriefcaseBusiness;
  const canStart = work.status === "runnable";
  const hasImplementation = work.status !== "planned";
  const requiredDocCount = work.documentRequirements.filter((item) => item.required).length;
  const strategySummary = work.boundStrategyName && work.boundStrategyVersion != null
    ? `${work.boundStrategyName} · v${work.boundStrategyVersion}`
    : "尚未绑定";
  const startDisabledReason = work.status === "planned" ? "该业务工作仍在规划中" : "当前不满足运行资格";

  return <div className="min-w-0 space-y-5">
    <header>
      <BackLink to={`${workspacePath}/business-works`}>返回业务工作</BackLink>
      <div className="mt-4 rounded-[20px] border border-gray-200/80 bg-white/90 p-5 shadow-theme-card dark:border-gray-800 dark:bg-white/[0.035]">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div className="min-w-0 flex-1">
            <div className="flex min-w-0 items-start gap-3">
              <span className="grid size-11 shrink-0 place-items-center rounded-2xl bg-brand-50 text-brand-600 dark:bg-brand-500/15 dark:text-brand-400"><Icon className="size-5" /></span>
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge color={STATUS_BADGE[work.status]}>{work.statusLabel}</Badge>
                  <span className="text-xs text-gray-400">{CATEGORY_LABELS[work.category as BusinessWorkCategory] ?? work.category}</span>
                </div>
                <h1 className="mt-1 text-2xl font-semibold tracking-tight text-gray-900 dark:text-white">{work.name}</h1>
                <p className="mt-1 max-w-2xl text-sm leading-6 text-gray-500 line-clamp-2">{work.summary}</p>
              </div>
            </div>
            <dl className="mt-4 grid gap-3 border-t border-gray-100 pt-3 sm:grid-cols-2 dark:border-gray-800" aria-label="运行就绪摘要">
              <div>
                <dt className="text-[11px] font-medium uppercase tracking-wide text-gray-400">资料要求</dt>
                <dd className="mt-0.5 text-sm font-semibold text-gray-900 dark:text-white">{requiredDocCount ? `${requiredDocCount} 项必需` : "无强制要求"}</dd>
              </div>
              <div className="min-w-0">
                <dt className="text-[11px] font-medium uppercase tracking-wide text-gray-400">执行策略</dt>
                <dd className="mt-0.5 truncate text-sm font-semibold text-gray-900 dark:text-white" title={strategySummary}>{strategySummary}</dd>
              </div>
            </dl>
          </div>
          <div className="flex shrink-0 flex-col gap-2 sm:min-w-44 lg:items-stretch">
            {canStart
              ? <Button asChild className="w-full justify-center sm:w-auto lg:w-full"><Link to={`${workspacePath}/business-works/${work.workKey}/workbench`}><Play />开始办理</Link></Button>
              : <Button className="w-full justify-center sm:w-auto lg:w-full" disabled title={startDisabledReason}><Play />开始办理</Button>}
            <div className="flex flex-wrap gap-2 lg:flex-col lg:items-stretch">
              {work.workKey === "report-generation" ? <Button asChild variant="outline" size="sm" className="w-full justify-center sm:w-auto lg:w-full"><Link to={`${workspacePath}/business-works/report-generation/demo`}><Sparkles />体验公开数据 Demo</Link></Button> : null}
              {hasImplementation ? <Button asChild variant="outline" size="sm" className="w-full justify-center sm:w-auto lg:w-full"><Link to={`${workspacePath}/business-works/${work.workKey}/settings`}><Settings2 />项目配置</Link></Button> : null}
              <Button asChild variant="outline" size="sm" className="w-full justify-center sm:w-auto lg:w-full"><Link to={`${workspacePath}/documents`}><Files />准备业务资料</Link></Button>
            </div>
          </div>
        </div>
      </div>
    </header>

    {workQuery.isError && !workQuery.data ? (
      <p role="alert" className="rounded-xl border border-warning-200 bg-warning-50 px-4 py-3 text-sm text-warning-800 dark:border-warning-500/20 dark:bg-warning-500/10 dark:text-warning-300">
        业务工作状态加载失败：{workQuery.error.message}。当前显示本地目录信息，外部文件准备状态可能不完整。
      </p>
    ) : null}

    {work.blockers.length ? (
      <div className="rounded-xl border border-warning-200 bg-warning-50 px-4 py-3 dark:border-warning-500/20 dark:bg-warning-500/10" role="status">
        <p className="text-sm font-semibold text-warning-800 dark:text-warning-300">还需处理 {work.blockers.length} 项后才能办理</p>
        <ul className="mt-1.5 space-y-0.5 text-sm text-warning-700 dark:text-warning-400">
          {work.blockers.map((blocker) => <li key={`${blocker.code}-${blocker.ref ?? blocker.message}`}>{blocker.message}</li>)}
        </ul>
      </div>
    ) : null}

    <WorkFunctionsSection functions={work.functions} />

    <section className="grid items-stretch gap-4 xl:grid-cols-2" aria-label="项目配置摘要">
      <StrategyBindingCard work={work} workspacePath={workspacePath} hasImplementation={hasImplementation} compact />
      <div className="min-w-0 xl:h-0 xl:min-h-full">
        <ExternalFilesCard work={work} workspacePath={workspacePath} tenantId={tenantId} projectId={projectId} title="外部文件" compact />
      </div>
    </section>

    <WorkRunHistorySection
      workKey={work.workKey}
      boundStrategyVersionId={work.boundStrategyVersionId}
      boundStrategyName={work.boundStrategyName}
      boundStrategyVersion={work.boundStrategyVersion}
      hasImplementation={hasImplementation}
      workspacePath={workspacePath}
      tenantId={tenantId}
      projectId={projectId}
    />
  </div>;
}

function WorkFunctionsSection({
  functions,
}: {
  functions: BusinessWorkSnapshot["functions"];
}) {
  return (
    <section aria-labelledby="work-functions-title">
      <Card className="min-w-0">
        <CardContent className="space-y-3 p-4">
          <div className="flex flex-wrap items-end justify-between gap-2">
            <div>
              <h2 id="work-functions-title" className="text-sm font-semibold text-gray-900 dark:text-white">业务说明</h2>
              <p className="mt-0.5 text-xs text-gray-500">功能通过统一底座组合，后续可以继续添加和替换。</p>
            </div>
            <Badge color="primary">{functions.length} 项</Badge>
          </div>
          <div className="grid gap-2 md:grid-cols-2">
            {functions.map((item, index) => (
              <div key={item.name} className="flex gap-2.5 rounded-xl border border-gray-100 bg-gray-50/70 px-3 py-2.5 dark:border-gray-800 dark:bg-gray-900/40">
                <span className="mt-0.5 grid size-6 shrink-0 place-items-center rounded-lg bg-success-50 text-success-600 dark:bg-success-500/10 dark:text-success-500">
                  <CheckCircle2 className="size-3.5" />
                </span>
                <div className="min-w-0">
                  <h3 className="text-sm font-semibold text-gray-900 dark:text-white">
                    <span className="mr-1 text-gray-400">{String(index + 1).padStart(2, "0")}.</span>
                    {item.name}
                  </h3>
                  <p className="mt-0.5 text-xs leading-5 text-gray-500">{item.description}</p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </section>
  );
}

function WorkRunHistorySection({
  workKey,
  boundStrategyVersionId,
  boundStrategyName,
  boundStrategyVersion,
  hasImplementation,
  workspacePath,
  tenantId,
  projectId,
}: {
  workKey: string;
  boundStrategyVersionId: string | null;
  boundStrategyName: string | null;
  boundStrategyVersion: number | null;
  hasImplementation: boolean;
  workspacePath: string;
  tenantId: string;
  projectId: string;
}) {
  const settingsHref = `${workspacePath}/business-works/${workKey}/settings`;
  const strategyBound = Boolean(boundStrategyVersionId);
  const boundStrategyLabel = boundStrategyName && boundStrategyVersion != null
    ? `${boundStrategyName} · v${boundStrategyVersion}`
    : null;
  const runsQuery = useQuery({
    queryKey: ["runs", tenantId, projectId],
    queryFn: () => api.listRuns(tenantId, projectId),
    refetchInterval: 5000,
    enabled: strategyBound,
  });
  const runs = useMemo(() => {
    if (!boundStrategyVersionId) return [];
    const matched = (runsQuery.data?.items ?? []).filter(
      (run) => run.strategyVersionId === boundStrategyVersionId,
    );
    return matched.slice(0, WORK_RUN_HISTORY_LIMIT);
  }, [boundStrategyVersionId, runsQuery.data?.items]);

  return (
    <section aria-labelledby="work-run-history-title">
      <Card className="min-w-0">
        <CardContent className="space-y-3 p-4">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <span className="grid size-8 shrink-0 place-items-center rounded-xl bg-brand-50 text-brand-600 dark:bg-brand-500/10">
                  <Activity className="size-4" />
                </span>
                <div>
                  <h2 id="work-run-history-title" className="text-sm font-semibold text-gray-900 dark:text-white">运行记录</h2>
                  <p className="mt-0.5 text-xs text-gray-500">
                    {boundStrategyLabel
                      ? `仅展示当前绑定策略「${boundStrategyLabel}」的最近运行。`
                      : "按当前绑定执行策略展示最近运行。"}
                  </p>
                </div>
              </div>
            </div>
            <Button asChild variant="ghost" size="sm">
              <Link to={`${workspacePath}/runs`}>查看全部 <ArrowRight /></Link>
            </Button>
          </div>

          {!strategyBound ? (
            <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-gray-200 px-4 py-6 text-center dark:border-gray-700">
              <Workflow className="size-6 text-gray-300" />
              <p className="mt-2 text-sm font-medium text-gray-800 dark:text-gray-100">尚未绑定执行策略</p>
              <p className="mt-1 text-xs text-gray-500">绑定策略后，该策略版本产生的运行会出现在这里。</p>
              {hasImplementation ? (
                <Button asChild size="sm" variant="outline" className="mt-3">
                  <Link to={settingsHref}><Settings2 />前往项目配置绑定</Link>
                </Button>
              ) : null}
            </div>
          ) : null}

          {strategyBound && runsQuery.isPending ? (
            <div className="space-y-2">{[1, 2, 3].map((item) => <Skeleton key={item} className="h-12" />)}</div>
          ) : null}
          {strategyBound && runsQuery.isError ? (
            <p role="alert" className="rounded-xl bg-error-50 p-3 text-sm text-error-600 dark:bg-error-500/10">
              无法加载运行记录：{runsQuery.error.message}
            </p>
          ) : null}
          {strategyBound && !runsQuery.isPending && !runsQuery.isError && !runs.length ? (
            <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-gray-200 px-4 py-6 text-center dark:border-gray-700">
              <p className="text-sm font-medium text-gray-800 dark:text-gray-100">暂无运行记录</p>
              <p className="mt-1 text-xs text-gray-500">
                {boundStrategyLabel
                  ? `当前绑定「${boundStrategyLabel}」尚无运行。点击「开始办理」发起后，该策略版本的运行会出现在这里。`
                  : "使用当前绑定策略办理后，相关运行会出现在这里。"}
              </p>
              <Button asChild size="sm" variant="outline" className="mt-3">
                <Link to={`${workspacePath}/runs`}>打开运行记录</Link>
              </Button>
            </div>
          ) : null}
          {runs.length ? (
            <div className="divide-y divide-gray-100 dark:divide-gray-800">
              {runs.map((run) => (
                <Link
                  key={run.runId}
                  to={`${workspacePath}/runs/${run.runId}`}
                  className="flex min-w-0 items-center justify-between gap-3 py-2.5 first:pt-0 last:pb-0"
                >
                  <span className="min-w-0">
                    <span className="block truncate font-mono text-xs text-gray-700 dark:text-gray-300">{run.runId}</span>
                    <span className="mt-1 block text-xs text-gray-500">
                      {Object.values(run.taskCounts).reduce((total, count) => total + count, 0)} 个任务 · {run.snapshotSeq} 个事件
                    </span>
                  </span>
                  <StatusBadge status={run.status} />
                </Link>
              ))}
            </div>
          ) : null}
        </CardContent>
      </Card>
    </section>
  );
}

function StrategyBindingCard({
  work,
  workspacePath,
  hasImplementation,
  compact = false,
}: {
  work: BusinessWorkSnapshot;
  workspacePath: string;
  hasImplementation: boolean;
  compact?: boolean;
}) {
  const bound = Boolean(work.boundStrategyName && work.boundStrategyVersion != null);
  const settingsHref = `${workspacePath}/business-works/${work.workKey}/settings`;

  return (
    <Card className={cn("flex min-w-0 flex-col", !compact && "h-full")}>
      <CardContent className={cn("flex flex-col", compact ? "gap-3 p-4" : "h-full min-h-0 flex-1 gap-4 p-5")}>
        <div className="flex items-start justify-between gap-3">
          <div className="flex min-w-0 items-start gap-2.5">
            <span className="grid size-9 shrink-0 place-items-center rounded-xl bg-brand-50 text-brand-600 dark:bg-brand-500/10">
              <Workflow className="size-4" />
            </span>
            <div className="min-w-0">
              <h2 className="text-sm font-semibold text-gray-900 dark:text-white">策略绑定</h2>
              {!compact ? (
                <p className="mt-1 text-xs leading-5 text-gray-500">
                  绑定策略管理中已发布的执行策略版本；执行依赖由平台统一维护。
                </p>
              ) : null}
            </div>
          </div>
          <Badge color={bound ? "success" : "warning"}>{bound ? "已绑定" : "未绑定"}</Badge>
        </div>

        {bound ? (
          <div className={cn("rounded-xl border border-gray-200 bg-gray-50/80 px-3 py-3 dark:border-gray-800 dark:bg-gray-900/50", !compact && "flex min-h-0 flex-1 flex-col")}>
            <p className="text-xs font-medium text-gray-500">当前执行策略</p>
            <p className="mt-1 truncate text-sm font-semibold text-gray-900 dark:text-white" title={work.boundStrategyName ?? undefined}>
              {work.boundStrategyName}
            </p>
            <div className="mt-2 flex flex-wrap items-center gap-1.5">
              <Badge color="primary">v{work.boundStrategyVersion}</Badge>
              {work.enabled ? <Badge color="success">已启用</Badge> : <Badge color="warning">待启用</Badge>}
              {work.packVersion ? <span className="text-xs text-gray-400">能力包 {work.packVersion}</span> : null}
            </div>
          </div>
        ) : (
          <div className={cn("flex flex-col items-center justify-center rounded-xl border border-dashed border-gray-200 text-center dark:border-gray-700", compact ? "px-3 py-5" : "min-h-0 flex-1 px-4 py-8")}>
            <Workflow className="size-6 text-gray-300" />
            <p className="mt-2 text-sm font-medium text-gray-700 dark:text-gray-200">尚未绑定执行策略</p>
            <p className="mt-0.5 text-xs text-gray-500">绑定后即可按策略办理本业务工作。</p>
          </div>
        )}

        {hasImplementation ? (
          <div className={cn("flex justify-end", !compact && "mt-auto")}>
            <Button asChild size="sm" variant={bound ? "outline" : "primary"}>
              <Link to={settingsHref}>
                <Settings2 />
                {bound ? "管理策略绑定" : "绑定策略"}
              </Link>
            </Button>
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}

function ExternalFilesCard({
  work,
  workspacePath,
  tenantId,
  projectId,
  title,
  compact = false,
}: {
  work: BusinessWorkSnapshot;
  workspacePath: string;
  tenantId: string;
  projectId: string;
  title: string;
  compact?: boolean;
}) {
  const documentsQuery = useQuery({
    queryKey: ["documents", tenantId, projectId],
    queryFn: () => api.listDocuments(tenantId, projectId),
    enabled: work.status !== "planned",
  });
  const bindingKeys = useMemo(
    () => new Set(documentBindingKeys(work.workKey, work.workItemType)),
    [work.workKey, work.workItemType],
  );
  const boundDocuments = useMemo(() => {
    const items = documentsQuery.data?.items ?? [];
    return items.filter((doc) => doc.businessWorkKeys.some((key) => bindingKeys.has(key)));
  }, [bindingKeys, documentsQuery.data?.items]);
  const readyCategories = useMemo(() => {
    const categories = new Set<string>();
    for (const doc of boundDocuments) {
      if (doc.status === "AVAILABLE" || doc.status === "REVIEW_REQUIRED") {
        categories.add(doc.category);
      }
    }
    return categories;
  }, [boundDocuments]);
  const requirements = work.documentRequirements;
  const requiredReady = requirements.filter((item) => item.required).every((item) => readyCategories.has(item.category));
  const readinessLabel = requirements.some((item) => item.required)
    ? (requiredReady ? "已齐备" : "待补充")
    : (boundDocuments.length ? "已关联" : "无要求");

  return (
    <Card className="flex h-full min-h-0 min-w-0 flex-col">
      <CardContent className={cn("flex h-full min-h-0 flex-1 flex-col", compact ? "gap-2 p-4" : "gap-4 p-5")}>
        <div className="flex shrink-0 items-start justify-between gap-3">
          <div className="flex min-w-0 items-start gap-2.5">
            <span className="grid size-9 shrink-0 place-items-center rounded-xl bg-brand-50 text-brand-600 dark:bg-brand-500/10">
              <Files className="size-4" />
            </span>
            <div className="min-w-0">
              <h2 className="text-sm font-semibold text-gray-900 dark:text-white">{title}</h2>
              {!compact ? (
                <p className="mt-1 text-xs leading-5 text-gray-500">
                  按分类提供业务材料；办理时系统会自动匹配可用文件。
                </p>
              ) : null}
            </div>
          </div>
          <Badge color={readinessLabel === "待补充" ? "warning" : readinessLabel === "已齐备" || readinessLabel === "已关联" ? "success" : "neutral"}>
            {readinessLabel}
          </Badge>
        </div>
        {documentsQuery.isError ? (
          <p role="alert" className="text-sm text-error-600">文件加载失败：{documentsQuery.error.message}</p>
        ) : null}
        {documentsQuery.isPending && work.status !== "planned" ? <Skeleton className="h-20" /> : null}
        {!documentsQuery.isPending || work.status === "planned" ? (
          <div className="min-h-0 flex-1 overflow-y-auto pr-1">
            <ExternalFilesBody
              requirements={requirements}
              readyCategories={readyCategories}
              boundDocuments={boundDocuments}
              compact={compact}
            />
          </div>
        ) : null}
        <div className="mt-auto flex shrink-0 justify-end">
          <Button asChild size="sm" variant="outline">
            <Link to={`${workspacePath}/documents`}><Files />提供外部文件</Link>
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

function ExternalFilesBody({
  requirements,
  readyCategories,
  boundDocuments,
  compact = false,
}: {
  requirements: Array<{ category: string; required: boolean }>;
  readyCategories: Set<string>;
  boundDocuments: DocumentSnapshot[];
  compact?: boolean;
}) {
  if (requirements.length) {
    return (
      <ul className={cn("text-sm text-gray-600 dark:text-gray-300", compact ? "space-y-1.5" : "space-y-2")}>
        {requirements.map((item) => {
          const ready = readyCategories.has(item.category);
          const label = DOCUMENT_CATEGORY_LABELS[item.category] ?? item.category;
          const matching = boundDocuments.filter((doc) => doc.category === item.category);
          return (
            <li key={item.category} className={cn("rounded-lg bg-gray-50 dark:bg-gray-800/60", compact ? "px-2.5 py-1.5" : "rounded-xl px-3 py-2")}>
              <div className="flex justify-between gap-3">
                <span className="font-medium text-gray-800 dark:text-gray-100">{label}</span>
                <span className="shrink-0 text-xs">
                  {item.required ? "必需" : "可选"}
                  {" · "}
                  <span className={ready ? "text-success-700 dark:text-success-400" : "text-warning-700 dark:text-warning-400"}>
                    {ready ? "已准备" : "待提供"}
                  </span>
                  {compact && matching.length ? ` · ${matching.length} 个文件` : null}
                </span>
              </div>
              {!compact && matching.length ? (
                <ul className="mt-1 space-y-0.5 text-xs text-gray-500">
                  {matching.map((doc) => (
                    <li key={doc.documentId} className="truncate" title={doc.name}>{doc.name}</li>
                  ))}
                </ul>
              ) : null}
            </li>
          );
        })}
      </ul>
    );
  }

  if (boundDocuments.length) {
    if (compact) {
      return (
        <p className="text-sm text-gray-600 dark:text-gray-300">
          已关联 <span className="font-medium text-gray-900 dark:text-white">{boundDocuments.length}</span> 个外部文件
        </p>
      );
    }
    return (
      <div className="space-y-2">
        <p className="text-xs text-gray-500">当前策略未声明强制资料分类；以下文件已绑定到本业务工作。</p>
        <ul className="space-y-2 text-sm text-gray-600 dark:text-gray-300">
          {boundDocuments.map((doc) => (
            <li key={doc.documentId} className="flex justify-between gap-3 rounded-xl bg-gray-50 px-3 py-2 dark:bg-gray-800/60">
              <span className="min-w-0 truncate font-medium text-gray-800 dark:text-gray-100" title={doc.name}>{doc.name}</span>
              <span className="shrink-0 text-xs text-gray-500">{DOCUMENT_CATEGORY_LABELS[doc.category] ?? doc.category}</span>
            </li>
          ))}
        </ul>
      </div>
    );
  }

  return <p className="text-sm text-gray-500">当前无强制资料分类要求，也尚未绑定外部文件。</p>;
}

function SummaryCard({ label, value, detail, textValue }: { label: string; value: number; detail: string; textValue?: string }) {
  return <Card><CardContent className="p-4"><p className="text-xs font-semibold text-gray-500">{label}</p><div className="mt-2 flex items-end justify-between gap-2"><strong className="text-2xl font-semibold text-gray-900 dark:text-white">{textValue ?? value}</strong><span className="text-xs text-gray-400">{detail}</span></div></CardContent></Card>;
}

function snapshotFromDefinition(work: BusinessWorkDefinition): BusinessWorkSnapshot {
  return {
    workKey: work.key,
    name: work.name,
    shortName: work.shortName,
    category: work.category,
    summary: work.summary,
    status: "planned",
    statusLabel: "规划中",
    packName: null,
    packVersionId: null,
    packVersion: null,
    enabled: false,
    bindingStatus: null,
    blockers: [],
    agents: [],
    tools: [],
    models: [],
    documentRequirements: [],
    decisionSlots: [],
    functions: work.functions,
    configuration: {},
    workItemType: null,
    caseBased: false,
    boundStrategyVersionId: null,
    boundStrategyName: null,
    boundStrategyVersion: null,
  };
}

function fallbackSnapshots(): BusinessWorkSnapshot[] {
  return BUSINESS_WORKS.map(snapshotFromDefinition);
}
