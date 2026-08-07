import { useMemo, useRef, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import * as Dialog from "@radix-ui/react-dialog";
import {
  Activity, ArrowRight, BrainCircuit, BriefcaseBusiness, ChartNoAxesCombined, Check, ChevronDown,
  ChevronRight, CircleAlert, CircleCheck, Clock3, Copy, ExternalLink, FileCheck2, FileOutput, FilePlus2, FileScan, Files,
  FileText, Gauge, LoaderCircle, Network, Play, ReceiptText, Settings2, ShieldAlert, ShieldCheck,
  Sparkles, Workflow, X,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { Link, Navigate, useNavigate, useParams } from "react-router";
import { api } from "@/api/client";
import type { BusinessWorkSnapshot, DocumentSnapshot, RunSummarySnapshot } from "@/api/types";
import { DocumentUploadPanel } from "@/components/documents/document-intake";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  BUSINESS_WORK_QUERY_GC_TIME, BUSINESS_WORK_QUERY_STALE_TIME, BUSINESS_WORK_RUN_REFRESH_INTERVAL,
  DOCUMENT_CATEGORY_LABELS, getBusinessWork,
  type BusinessWorkDefinition,
} from "@/lib/business-works";
import { useWorkspaceScope } from "@/lib/demo-scope";
import { capabilityLabel } from "@/lib/capability-labels";

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

export function BusinessWorksPage() {
  const { workKey } = useParams();
  if (workKey) return <BusinessWorkDetail workKey={workKey} />;
  return <BusinessWorksIndexRedirect />;
}

function BusinessWorksIndexRedirect() {
  const { workspacePath } = useWorkspaceScope();
  return <Navigate to={`${workspacePath}/overview`} replace />;
}

function BusinessWorkDetail({ workKey }: { workKey: string }) {
  const { tenantId, projectId, workspacePath } = useWorkspaceScope();
  const local = getBusinessWork(workKey);
  const workQuery = useQuery({
    queryKey: ["business-work", tenantId, projectId, workKey],
    queryFn: () => api.getBusinessWork(tenantId, projectId, workKey),
    staleTime: BUSINESS_WORK_QUERY_STALE_TIME,
    gcTime: BUSINESS_WORK_QUERY_GC_TIME,
  });
  // Wait for API before falling back to local catalog, so configured works
  // are not briefly (or permanently on error) shown with empty requirements.
  if (workQuery.isPending) {
    return (
      <div className="min-w-0 space-y-6">
        {local ? <header className="rounded-2xl border border-gray-200/80 bg-white/90 p-5 shadow-theme-card dark:border-gray-800 dark:bg-white/[0.035]">
          <p className="text-sm text-gray-500">业务工作</p>
          <p className="mt-2 text-2xl font-semibold text-gray-900 dark:text-white">{local.shortName}</p>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-gray-500">{local.summary}</p>
        </header> : <Skeleton className="h-40" />}
        <Skeleton className="h-72" />
      </div>
    );
  }
  const work = workQuery.data ?? (local ? snapshotFromDefinition(local) : null);
  if (!work) return <Card><CardContent className="flex min-h-72 flex-col items-center justify-center gap-3 p-6 text-center"><BriefcaseBusiness className="size-9 text-gray-300" /><h1 className="text-lg font-semibold text-gray-900 dark:text-white">业务工作不存在</h1><p className="text-sm text-gray-500">该工作可能尚未登记或地址有误。</p><Button asChild variant="outline"><Link to={`${workspacePath}/overview`}>返回工作台</Link></Button></CardContent></Card>;
  return <BusinessWorkDetailContent
    work={work}
    workspacePath={workspacePath}
    tenantId={tenantId}
    projectId={projectId}
    catalogError={workQuery.isError && !workQuery.data ? workQuery.error.message : null}
  />;
}

type BusinessDetailStatus = "planned" | "unconfigured" | "preparing" | "ready" | "running" | "disabled" | "error";
type BusinessReadinessStatus = "completed" | "missing" | "processing" | "failed" | "unconfigured";
type BusinessReadinessDefinition = {
  id: string;
  name: string;
  type: "strategy" | "file";
  categories: string[];
  required: boolean;
  icon: LucideIcon;
  description?: string;
  requirement?: BusinessWorkSnapshot["documentRequirements"][number];
};
type BusinessReadinessItem = BusinessReadinessDefinition & {
  status: BusinessReadinessStatus;
  summary: string;
  helper: string;
  version?: string;
  updatedAt?: string;
  errorMessage?: string;
  errorMessages?: string[];
  documents: DocumentSnapshot[];
};

const PROCUREMENT_DESCRIPTION =
  "对招投标文件、投标结果及合同条款进行一致性比对，并结合供应商履约、舆情、司法等多源风险数据识别供应商风险。";

const PROCUREMENT_READINESS_DEFINITIONS: BusinessReadinessDefinition[] = [
  { id: "strategy", name: "执行策略", type: "strategy", categories: [], required: true, icon: Workflow },
  { id: "tender", name: "招标文件", type: "file", categories: ["TENDER_DOCUMENT"], required: true, icon: FileText },
  { id: "result", name: "投标结果", type: "file", categories: ["WINNING_BID", "AWARD_NOTICE"], required: true, icon: FileCheck2 },
  { id: "contract", name: "签章合同", type: "file", categories: ["MASTER_CONTRACT"], required: true, icon: FilePlus2 },
  { id: "supplier", name: "供应商资料", type: "file", categories: ["SUPPLIER_PERFORMANCE", "SUPPLIER", "SUPPLIER_MASTER"], required: false, icon: ShieldCheck },
];


function BusinessWorkDetailContent({
  work,
  workspacePath,
  tenantId,
  projectId,
  catalogError,
}: {
  work: BusinessWorkSnapshot;
  workspacePath: string;
  tenantId: string;
  projectId: string;
  catalogError: string | null;
}) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const readinessRef = useRef<HTMLElement | null>(null);
  const firstMissingRef = useRef<HTMLLIElement | null>(null);
  const [capabilitiesExpanded, setCapabilitiesExpanded] = useState(false);
  const [uploadCategory, setUploadCategory] = useState<string | null>(null);
  const [startDialogOpen, setStartDialogOpen] = useState(false);

  const bindingKeys = useMemo(
    () => [...work.documentBindingKeys].sort(),
    [work.documentBindingKeys],
  );
  const documentsQuery = useQuery({
    queryKey: ["business-work-documents", tenantId, projectId, bindingKeys],
    queryFn: () => api.listDocuments(tenantId, projectId, "", "", "", bindingKeys),
    enabled: work.status !== "planned",
    staleTime: BUSINESS_WORK_QUERY_STALE_TIME,
    gcTime: BUSINESS_WORK_QUERY_GC_TIME,
  });
  const runsQuery = useQuery({
    queryKey: ["business-work-run-summaries", tenantId, projectId, work.boundStrategyVersionId],
    queryFn: () => {
      if (!work.boundStrategyVersionId) throw new Error("当前业务工作尚未绑定执行策略。");
      return api.listRunSummaries(tenantId, projectId, work.boundStrategyVersionId);
    },
    enabled: work.status !== "planned" && Boolean(work.boundStrategyVersionId),
    staleTime: BUSINESS_WORK_QUERY_STALE_TIME,
    gcTime: BUSINESS_WORK_QUERY_GC_TIME,
    refetchInterval: (query) => (
      query.state.data?.items.some((run) => isActiveRun(run.status))
        ? BUSINESS_WORK_RUN_REFRESH_INTERVAL
        : false
    ),
  });

  const bindingKeySet = useMemo(() => new Set(bindingKeys), [bindingKeys]);
  const boundDocuments = useMemo(
    () => (documentsQuery.data?.items ?? []).filter((document) => document.businessWorkKeys.some((key) => bindingKeySet.has(key))),
    [bindingKeySet, documentsQuery.data?.items],
  );
  const readinessItems = useMemo(
    () => buildBusinessReadiness(work, boundDocuments),
    [boundDocuments, work],
  );
  const matchedRuns = useMemo(
    () => [...(runsQuery.data?.items ?? [])].sort((left, right) => runTimestamp(right) - runTimestamp(left)).slice(0, WORK_RUN_HISTORY_LIMIT),
    [runsQuery.data?.items],
  );
  const activeRun = matchedRuns.find((run) => isActiveRun(run.status));
  const readinessLoading = documentsQuery.isPending || runsQuery.isPending;
  const derivedState = useMemo(
    () => calculateBusinessDetailState(work, readinessItems, matchedRuns, readinessLoading),
    [matchedRuns, readinessItems, readinessLoading, work],
  );
  const missingItem = readinessItems.find((item) => item.required && item.status !== "completed");
  const latestRun = matchedRuns[0];
  const uploadRequirement = uploadCategory
    ? work.documentRequirements.find((item) => item.category === uploadCategory)
    : undefined;
  const strategyLabel = work.boundStrategyName && work.boundStrategyVersion != null
    ? `${work.boundStrategyName} · v${work.boundStrategyVersion}`
    : "未绑定";

  const focusReadiness = () => {
    const target = firstMissingRef.current;
    if (!target) return;
    target.scrollIntoView?.({ behavior: "smooth", block: "center" });
    target.focus?.({ preventScroll: true });
  };
  const handlePrimaryAction = () => {
    if (derivedState.status === "preparing" || derivedState.status === "error" || derivedState.status === "unconfigured") {
      focusReadiness();
      return;
    }
    if (derivedState.status === "running") {
      if (activeRun) void navigate(`${workspacePath}/runs/${activeRun.runId}`);
      else void navigate(`${workspacePath}/runs`);
      return;
    }
    if (derivedState.status === "ready") setStartDialogOpen(true);
  };
  const primaryLabel = {
    planned: "规划中",
    unconfigured: "配置运行条件",
    preparing: "补齐业务资料",
    ready: "开始处理",
    running: "查看运行进度",
    disabled: "已停用",
    error: "处理配置异常",
  }[derivedState.status];

  const Icon = WORK_ICONS[work.workKey] ?? BriefcaseBusiness;
  const hasImplementation = work.status !== "planned";
  const requiredCategories = [...new Set(readinessItems.filter((item) => item.type === "file" && item.required).flatMap((item) => item.categories))];
  const requiredDocsCompleted = requiredCategories.filter((category) => hasReadyDocument(boundDocuments, category)).length;
  const description = work.workKey === "procurement-supplier-risk" ? PROCUREMENT_DESCRIPTION : work.summary;

  return (
    <div className="min-w-0 space-y-6">
      <nav aria-label="面包屑" className="flex min-w-0 items-center gap-2 text-sm text-gray-500">
        <Link to={`${workspacePath}/overview`} className="shrink-0 hover:text-brand-600 dark:hover:text-brand-400">业务工作</Link>
        <ChevronRight className="size-4 shrink-0 text-gray-300" aria-hidden />
        <span className="min-w-0 truncate font-medium text-gray-800 dark:text-gray-200">{work.shortName}</span>
      </nav>

      <header data-testid="business-work-page-header" className="rounded-2xl border border-gray-200/80 bg-white/90 p-5 shadow-theme-card dark:border-gray-800 dark:bg-white/[0.035]">
        <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
          <div className="flex min-w-0 items-start gap-3">
            <span className="grid size-11 shrink-0 place-items-center rounded-2xl bg-brand-50 text-brand-600 dark:bg-brand-500/15 dark:text-brand-400">
              <Icon className="size-5" />
            </span>
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-sm font-medium text-brand-500">业务工作</span>
                <BusinessStatusTag status={derivedState.status} />
              </div>
              <h1 className="mt-1 text-xl font-semibold tracking-tight text-gray-900 dark:text-white">{work.name}</h1>
              <p className="mt-2 max-w-3xl text-sm leading-6 text-gray-600 dark:text-gray-300">{description}</p>
            </div>
          </div>
          <div className="flex shrink-0 flex-wrap items-center gap-2 lg:max-w-[18rem] lg:justify-end">
            <Button
              className="min-w-36 justify-center"
              disabled={derivedState.status === "disabled" || derivedState.status === "planned" || readinessLoading}
              onClick={handlePrimaryAction}
              loading={readinessLoading}
            >
              {primaryLabel}
            </Button>
            {work.workKey === "report-generation" ? <Button asChild variant="outline" size="sm"><Link to={`${workspacePath}/business-works/report-generation/demo`}><Sparkles />体验公开数据 Demo</Link></Button> : null}
            {hasImplementation ? <Button asChild variant="outline" size="sm"><Link to={`${workspacePath}/business-works/${work.workKey}/settings`}><Settings2 />运行配置</Link></Button> : null}
          </div>
        </div>
        <dl className="mt-5 grid gap-x-5 gap-y-4 border-t border-gray-100 pt-4 sm:grid-cols-2 xl:grid-cols-6 dark:border-gray-800">
          <OverviewMetric label="当前策略" value={strategyLabel} copyValue={work.boundStrategyVersionId ?? undefined} />
          <OverviewMetric label="策略状态" value={work.enabled && work.boundStrategyVersionId ? "已启用" : "待配置"} />
          <OverviewMetric label="必需资料" value={`${requiredDocsCompleted}/${requiredCategories.length}`} detail="按资料类型统计" />
          <OverviewMetric label="最近运行" value={latestRun ? formatDateTime(latestRun.startedAt ?? latestRun.completedAt) : "暂无"} />
          <OverviewMetric label="业务状态" value={businessStatusLabel(derivedState.status)} />
          <OverviewMetric label="生产准入" value={work.qualificationLabel} />
        </dl>
      </header>

      {catalogError ? <div role="alert" className="rounded-xl border border-warning-200 bg-warning-50 px-4 py-3 text-sm text-warning-800 dark:border-warning-500/20 dark:bg-warning-500/10 dark:text-warning-300">业务工作状态加载失败：{catalogError}。当前展示本地目录信息，资料状态可能不完整。</div> : null}

      <section ref={readinessRef} aria-labelledby="business-readiness-title">
        <Card>
          <CardContent className="space-y-4 p-5">
            <div className="flex flex-wrap items-end justify-between gap-3">
              <div>
                <h2 id="business-readiness-title" className="text-base font-semibold text-gray-900 dark:text-white">运行准备</h2>
                <p className="mt-1 text-sm text-gray-500">开始处理前，请确认策略与必需业务资料均已通过校验。</p>
              </div>
              <p className="text-sm font-semibold text-gray-700 dark:text-gray-200">运行准备 {derivedState.completedItemCount}/{readinessItems.length} 项完成</p>
            </div>
            <div className="h-1.5 overflow-hidden rounded-full bg-gray-100 dark:bg-gray-800" role="progressbar" aria-label="运行准备完成度" aria-valuemin={0} aria-valuemax={readinessItems.length} aria-valuenow={derivedState.completedItemCount}>
              <div className="h-full rounded-full bg-brand-500 transition-[width] duration-300" style={{ width: `${readinessItems.length ? (derivedState.completedItemCount / readinessItems.length) * 100 : 0}%` }} />
            </div>
            {documentsQuery.isError ? (
              <div role="alert" className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-error-200 bg-error-50 px-3 py-2.5 text-sm text-error-700 dark:border-error-500/20 dark:bg-error-500/10 dark:text-error-300">
                <span className="inline-flex items-center gap-2"><CircleAlert className="size-4 shrink-0" />业务资料加载失败：{documentsQuery.error.message}</span>
                <Button size="sm" variant="outline" onClick={() => void documentsQuery.refetch()} loading={documentsQuery.isFetching}>重试</Button>
              </div>
            ) : null}
            {documentsQuery.isPending ? <div className="space-y-2" aria-label="运行准备加载中">{[1, 2, 3, 4, 5].map((item) => <Skeleton key={item} className="h-[4.6rem]" />)}</div> : null}
            {!documentsQuery.isPending ? (
              <ol className="divide-y divide-gray-100 dark:divide-gray-800">
                {readinessItems.map((item, index) => (
                  <ReadinessItemRow
                    key={item.id}
                    item={item}
                    index={index}
                    firstMissingRef={item.id === missingItem?.id ? firstMissingRef : undefined}
                    workspacePath={workspacePath}
                    workKey={work.workKey}
                    onUpload={() => setUploadCategory(uploadCategoryForItem(item, boundDocuments))}
                  />
                ))}
              </ol>
            ) : null}
            {uploadCategory ? (
              <div className="rounded-xl border border-brand-200 bg-brand-50/50 p-4 dark:border-brand-500/30 dark:bg-brand-500/10">
                <div className="mb-3 flex items-start justify-between gap-3">
                  <div>
                    <p className="font-semibold text-gray-900 dark:text-white">上传{readinessItems.find((item) => item.categories.includes(uploadCategory))?.name ?? "业务资料"}</p>
                    <p className="mt-1 text-sm text-gray-600 dark:text-gray-300">上传完成后，运行准备会自动刷新并重新计算。</p>
                  </div>
                  <Button variant="ghost" size="icon" aria-label="关闭上传面板" onClick={() => setUploadCategory(null)}><X /></Button>
                </div>
                <DocumentUploadPanel
                  tenantId={tenantId}
                  projectId={projectId}
                  context={{
                    businessWorkKey: work.workKey,
                    businessWorkKeys: [work.workKey],
                    category: uploadCategory,
                    processingProfileRef: uploadRequirement?.processingProfile ?? undefined,
                    extractionSchemaRef: uploadRequirement?.extractionSchema ?? undefined,
                    classificationLabels: (uploadRequirement?.classificationLabels ?? []).map((label) => ({ label, displayName: uploadRequirement?.displayName })),
                  }}
                  onClose={() => setUploadCategory(null)}
                  onCompleted={async () => {
                    setUploadCategory(null);
                    await Promise.all([
                      queryClient.invalidateQueries({
                        queryKey: ["business-work-documents", tenantId, projectId, bindingKeys],
                      }),
                      queryClient.invalidateQueries({ queryKey: ["business-work", tenantId, projectId, work.workKey] }),
                    ]);
                  }}
                />
              </div>
            ) : null}
          </CardContent>
        </Card>
      </section>

      <section aria-labelledby="business-capabilities-title" aria-label="业务说明">
        <Card>
          <CardContent className="p-5">
            <button
              type="button"
              className="flex w-full items-center justify-between gap-4 text-left focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-brand-500/20"
              aria-expanded={capabilitiesExpanded}
              onClick={() => setCapabilitiesExpanded((value) => !value)}
            >
              <span className="min-w-0">
                <span id="business-capabilities-title" role="heading" aria-level={2} className="block text-base font-semibold text-gray-900 dark:text-white">业务能力</span>
                <span className="mt-1 block text-sm leading-6 text-gray-500">包含 {work.functions.length} 项业务能力，展开查看具体职责与说明。</span>
              </span>
              <span className="inline-flex shrink-0 items-center gap-1 text-sm font-medium text-brand-600 dark:text-brand-400">
                {capabilitiesExpanded ? "收起详情" : "展开详情"}
                {capabilitiesExpanded ? <ChevronDown className="size-4 rotate-180 transition-transform" /> : <ChevronDown className="size-4 transition-transform" />}
              </span>
            </button>
            <div className={`grid transition-[grid-template-rows,opacity] duration-300 ${capabilitiesExpanded ? "mt-5 grid-rows-[1fr] opacity-100" : "grid-rows-[0fr] opacity-0"}`}>
              <div className="min-h-0 overflow-hidden">
                <div className="grid gap-x-8 gap-y-5 border-t border-gray-100 pt-5 md:grid-cols-2 dark:border-gray-800">
                  {work.functions.map((item, index) => (
                    <div key={item.name} className="flex gap-3">
                      <span className="grid size-7 shrink-0 place-items-center rounded-lg bg-brand-50 text-xs font-semibold text-brand-600 dark:bg-brand-500/10 dark:text-brand-400">{String(index + 1).padStart(2, "0")}</span>
                      <div className="min-w-0">
                        <h3 className="text-sm font-semibold text-gray-900 dark:text-white">{item.name}</h3>
                        <p className="mt-1 text-sm leading-6 text-gray-600 dark:text-gray-300">{item.description}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </section>

      <BusinessRecentRuns
        workKey={work.workKey}
        boundStrategyLabel={work.boundStrategyName && work.boundStrategyVersion != null ? `${work.boundStrategyName} · v${work.boundStrategyVersion}` : null}
        runs={matchedRuns}
        loading={runsQuery.isPending}
        error={runsQuery.isError ? runsQuery.error.message : null}
        onRetry={() => void runsQuery.refetch()}
        workspacePath={workspacePath}
        onNavigate={(runId) => { void navigate(`${workspacePath}/runs/${runId}`); }}
      />

      <StartBusinessRunDialog
        open={startDialogOpen}
        onOpenChange={setStartDialogOpen}
        strategyLabel={strategyLabel}
        requiredDocuments={`${requiredDocsCompleted}/${requiredCategories.length}`}
        expectedObject={work.shortName}
        workspacePath={workspacePath}
        workKey={work.workKey}
      />
    </div>
  );
}

function buildBusinessReadiness(work: BusinessWorkSnapshot, documents: DocumentSnapshot[]): BusinessReadinessItem[] {
  const definitions = getBusinessReadinessDefinitions(work, documents);
  const strategyIssues = work.blockers.filter((blocker) => blocker.code !== "DOCUMENT_BINDING_MISSING");
  const strategyIssue = strategyIssues[0];
  return definitions.map((definition) => {
    if (definition.type === "strategy") {
      const bound = Boolean(work.boundStrategyName && work.boundStrategyVersion != null);
      const failed = Boolean(strategyIssue) || (bound && !work.enabled && work.status === "unavailable");
      return {
        ...definition,
        status: failed ? "failed" : bound ? "completed" : "unconfigured",
        summary: bound ? work.boundStrategyName ?? "执行策略" : "尚未绑定执行策略",
        helper: failed ? strategyIssue ? blockerDisplayName(strategyIssue) : "策略依赖未通过健康检查" : work.packVersion ? `能力包 ${work.packVersion}` : "绑定后生效",
        version: bound ? `v${work.boundStrategyVersion}` : undefined,
        errorMessage: failed ? strategyIssue ? blockerReason(strategyIssue) : "策略当前不可用" : undefined,
        errorMessages: failed ? strategyIssues.map((blocker) => blockerReason(blocker)) : undefined,
        documents: [],
      };
    }

    const matched = documents.filter((document) => definition.categories.includes(document.category));
    const states = definition.categories.map((category) => {
      const categoryDocuments = matched.filter((document) => document.category === category);
      const minCount = definition.requirement?.category === category
        ? definition.requirement.minCount ?? 1
        : definition.required ? 1 : 0;
      return {
        category,
        minCount,
        readyCount: categoryDocuments.filter((document) => isReadyDocumentStatus(document.status)).length,
        ready: categoryDocuments.some((document) => isReadyDocumentStatus(document.status)),
        processing: categoryDocuments.some((document) => document.status === "PROCESSING" || document.status === "UPLOADING"),
        failed: categoryDocuments.some((document) => document.status === "FAILED" || document.status === "REVIEW_REQUIRED"),
      };
    });
    const requiredReady = states.every((state) => state.readyCount >= state.minCount);
    const enoughReadyCategories = definition.required
      ? requiredReady
      : states.some((state) => state.ready) && states.every((state) => state.minCount === 0 || state.readyCount >= state.minCount);
    const status: BusinessReadinessStatus = states.some((state) => state.failed)
      ? "failed"
      : states.some((state) => state.processing)
        ? "processing"
        : enoughReadyCategories
          ? "completed"
          : definition.required
            ? "missing"
            : "unconfigured";
    const updatedAt = matched.map((document) => document.updatedAt).sort().at(-1);
    const requiredCount = states.reduce((total, state) => total + state.minCount, 0);
    const readyCount = states.reduce((total, state) => total + Math.min(state.readyCount, state.minCount), 0);
    const summary = matched.length
      ? definition.required && (definition.categories.length > 1 || requiredCount > 1) && readyCount < requiredCount
        ? `已提供 ${readyCount}/${requiredCount} 份资料`
        : matched.length === 1
          ? matched[0]?.name ?? "已关联资料"
          : `${matched.length} 个文件`
      : definition.required ? "尚未上传必需资料" : "可选资料，上传后增强风险判断";
    const helper = status === "failed"
      ? "文件校验失败，请重新上传"
      : status === "processing"
        ? "系统正在解析，请稍候"
        : updatedAt
          ? `最近更新 ${formatDateTime(updatedAt)}`
          : definition.required ? "运行前必须上传并校验" : "不影响本次运行资格";
    return {
      ...definition,
      status,
      summary,
      helper,
      updatedAt,
      errorMessage: status === "failed" ? matched.find((document) => document.status === "FAILED")?.name ? "文件解析异常，请重新上传" : "资料需要人工确认" : undefined,
      documents: matched,
    };
  });
}

function getBusinessReadinessDefinitions(work: BusinessWorkSnapshot, documents: DocumentSnapshot[]): BusinessReadinessDefinition[] {
  if (work.workKey === "procurement-supplier-risk") return PROCUREMENT_READINESS_DEFINITIONS;
  const requirements: BusinessReadinessDefinition[] = work.documentRequirements.map((requirement) => ({
    id: `file:${requirement.key ?? requirement.category}`,
    name: requirement.displayName ?? DOCUMENT_CATEGORY_LABELS[requirement.category] ?? requirement.category,
    type: "file" as const,
    categories: [requirement.category],
    required: requirement.required,
    icon: documentRequirementIcon(requirement.category),
    description: requirement.description,
    requirement,
  }));
  if (!requirements.length && documents.length) {
    const categories = [...new Set(documents.map((document) => document.category))];
    requirements.push({
      id: "linked-documents",
      name: "已关联资料",
      type: "file",
      categories,
      required: false,
      icon: Files,
    });
  }
  return [
    { id: "strategy", name: "执行策略", type: "strategy", categories: [], required: true, icon: Workflow },
    ...requirements,
  ];
}

function documentRequirementIcon(category: string): LucideIcon {
  if (/INVOICE|TAX|PAYMENT|COST/.test(category)) return ReceiptText;
  if (/SUPPLIER|RISK/.test(category)) return ShieldCheck;
  if (/CONTRACT|ORDER|SCOPE/.test(category)) return FilePlus2;
  if (/ACCEPTANCE|RECEIPT|DELIVERY/.test(category)) return FileCheck2;
  return FileText;
}

function calculateBusinessDetailState(
  work: BusinessWorkSnapshot,
  items: BusinessReadinessItem[],
  runs: RunSummarySnapshot[],
  loading: boolean,
): { status: BusinessDetailStatus; completedItemCount: number } {
  const completedItemCount = items.filter((item) => item.status === "completed").length;
  const hasRunningRun = runs.some((run) => isActiveRun(run.status));
  const strategy = items.find((item) => item.id === "strategy");
  const requiredDocumentsReady = items.filter((item) => item.type === "file" && item.required).every((item) => item.status === "completed");
  const hasTechnicalError = items.some((item) => item.status === "failed") || work.status === "unavailable";
  if (hasRunningRun) return { status: "running", completedItemCount };
  if (work.status === "planned") return { status: "planned", completedItemCount };
  if (strategy?.status === "unconfigured") return { status: "unconfigured", completedItemCount };
  if (strategy?.status === "failed" || hasTechnicalError) return { status: "error", completedItemCount };
  if (!work.enabled && strategy?.status === "completed") return { status: "disabled", completedItemCount };
  if (loading || !requiredDocumentsReady) return { status: "preparing", completedItemCount };
  return { status: "ready", completedItemCount };
}

function ReadinessItemRow({
  item,
  index,
  firstMissingRef,
  workspacePath,
  workKey,
  onUpload,
}: {
  item: BusinessReadinessItem;
  index: number;
  firstMissingRef?: React.RefObject<HTMLLIElement | null>;
  workspacePath: string;
  workKey: string;
  onUpload: () => void;
}) {
  const Icon = item.icon;
  const firstDocument = item.documents[0];
  return (
    <li ref={firstMissingRef} tabIndex={item.status === "completed" ? -1 : 0} className={`flex min-w-0 flex-col gap-3 py-4 first:pt-1 last:pb-1 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 sm:flex-row sm:items-center sm:gap-4 ${item.status === "missing" || item.status === "failed" ? "-mx-2 rounded-xl bg-warning-50/70 px-2 dark:bg-warning-500/10" : ""}`}>
      <div className="flex min-w-0 flex-1 items-start gap-3">
        <span className={`grid size-9 shrink-0 place-items-center rounded-xl ${readinessIconClass(item.status)}`} aria-hidden><Icon className="size-4" /></span>
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="text-sm font-semibold text-gray-900 dark:text-white">{index + 1}. {item.name}</h3>
            {item.required ? <span className="text-xs text-gray-400">必需</span> : <span className="text-xs text-gray-400">可选</span>}
          </div>
          <p className="mt-1 truncate text-sm text-gray-700 dark:text-gray-200" title={item.summary}>{item.summary}</p>
          {item.description ? <p className="mt-1 text-xs leading-5 text-gray-500 dark:text-gray-400">{item.description}</p> : null}
          <div className="mt-1 flex min-w-0 flex-wrap items-center gap-x-3 gap-y-1 text-xs text-gray-500">
            {item.version ? <span className="inline-flex items-center gap-1">版本 {item.version}<CopyButton label="复制策略版本" value={item.version} /></span> : null}
            <span className={item.status === "failed" ? "text-error-600 dark:text-error-400" : undefined}>{item.helper}</span>
            {item.errorMessage ? <span className="text-error-600 dark:text-error-400">{item.errorMessage}</span> : null}
            {item.errorMessages?.slice(1).map((message, messageIndex) => <span key={`${message}-${messageIndex}`} className="text-error-600 dark:text-error-400">{message}</span>)}
            {firstDocument ? <CopyButton label="复制文件 ID" value={firstDocument.documentId} /> : null}
          </div>
        </div>
      </div>
      <div className="flex shrink-0 items-center gap-2 sm:justify-end">
        <ReadinessStatusTag status={item.status} />
        {firstDocument ? <Button asChild variant="ghost" size="sm"><Link aria-label={firstDocument.name} to={`${workspacePath}/documents/${encodeURIComponent(firstDocument.documentId)}`}><ExternalLink />查看</Link></Button> : null}
        {item.type === "strategy" ? (
          <Button asChild variant="outline" size="sm"><Link to={`${workspacePath}/business-works/${workKey}/settings`}>更换策略</Link></Button>
        ) : (
          <Button size="sm" variant={item.status === "completed" ? "ghost" : "outline"} onClick={onUpload}>
            {item.status === "completed" ? "替换" : "上传文件"}
          </Button>
        )}
      </div>
    </li>
  );
}

function BusinessRecentRuns({
  workKey,
  boundStrategyLabel,
  runs,
  loading,
  error,
  onRetry,
  workspacePath,
  onNavigate,
}: {
  workKey: string;
  boundStrategyLabel: string | null;
  runs: RunSummarySnapshot[];
  loading: boolean;
  error: string | null;
  onRetry: () => void;
  workspacePath: string;
  onNavigate: (runId: string) => void;
}) {
  return (
    <section aria-labelledby="business-recent-runs-title">
      <Card>
        <CardContent className="space-y-4 p-5">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div className="flex items-start gap-3">
              <span className="grid size-9 shrink-0 place-items-center rounded-xl bg-brand-50 text-brand-600 dark:bg-brand-500/10"><Activity className="size-4" /></span>
              <div><h2 id="business-recent-runs-title" className="text-base font-semibold text-gray-900 dark:text-white">最近运行</h2><p className="mt-1 text-sm text-gray-500">{boundStrategyLabel ? `仅展示当前绑定策略「${boundStrategyLabel}」的最近运行。` : "按当前绑定执行策略展示最近运行。"}</p></div>
            </div>
            <Button asChild variant="ghost" size="sm"><Link to={`${workspacePath}/runs`}>查看全部 <ArrowRight /></Link></Button>
          </div>
          {loading ? <div className="space-y-2" aria-label="最近运行加载中">{[1, 2, 3].map((item) => <Skeleton key={item} className="h-14" />)}</div> : null}
          {error ? <div role="alert" className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-error-200 bg-error-50 px-3 py-2.5 text-sm text-error-700 dark:border-error-500/20 dark:bg-error-500/10 dark:text-error-300"><span className="inline-flex items-center gap-2"><CircleAlert className="size-4" />最近运行加载失败：{error}</span><Button size="sm" variant="outline" onClick={onRetry}>重试</Button></div> : null}
          {!loading && !error && !runs.length ? <div className="py-8 text-center"><Activity className="mx-auto size-7 text-gray-300" /><p className="mt-2 text-sm font-medium text-gray-700 dark:text-gray-200">暂无运行记录</p><p className="mt-1 text-sm text-gray-500">{boundStrategyLabel ? `当前绑定「${boundStrategyLabel}」尚无运行。` : "开始处理后，最近的运行结果会出现在这里。"}</p></div> : null}
          {!loading && !error && runs.length ? (
            <>
              <div className="hidden overflow-x-auto md:block">
                <table className="w-full min-w-[760px] text-left text-sm">
                  <thead className="border-b border-gray-100 text-xs text-gray-500 dark:border-gray-800"><tr><th className="px-3 py-2 font-medium">运行时间</th><th className="px-3 py-2 font-medium">发起人</th><th className="px-3 py-2 font-medium">耗时</th><th className="px-3 py-2 font-medium">处理情况</th><th className="px-3 py-2 font-medium">状态</th><th className="px-3 py-2 text-right font-medium">操作</th></tr></thead>
                  <tbody className="divide-y divide-gray-100 dark:divide-gray-800">{runs.map((run) => <RunTableRow key={run.runId} run={run} workspacePath={workspacePath} workKey={workKey} onNavigate={onNavigate} />)}</tbody>
                </table>
              </div>
              <div className="space-y-2 md:hidden">{runs.map((run) => <RunMobileCard key={run.runId} run={run} workspacePath={workspacePath} workKey={workKey} onNavigate={onNavigate} />)}</div>
            </>
          ) : null}
        </CardContent>
      </Card>
    </section>
  );
}

function RunTableRow({ run, workspacePath, workKey, onNavigate }: { run: RunSummarySnapshot; workspacePath: string; workKey: string; onNavigate: (runId: string) => void }) {
  return <tr tabIndex={0} className="cursor-pointer outline-none hover:bg-gray-50 focus-visible:bg-brand-50/60 dark:hover:bg-white/[0.03] dark:focus-visible:bg-brand-500/10" onClick={() => onNavigate(run.runId)} onKeyDown={(event) => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); onNavigate(run.runId); } }}>
    <td className="whitespace-nowrap px-3 py-3 text-gray-700 dark:text-gray-200">{formatDateTime(run.startedAt ?? run.completedAt)}</td>
    <td className="px-3 py-3 text-gray-700 dark:text-gray-200">{runOperatorName(run)}</td>
    <td className="whitespace-nowrap px-3 py-3 text-gray-600 dark:text-gray-300">{runDuration(run)}</td>
    <td className="px-3 py-3"><span className="block text-gray-700 dark:text-gray-200">{runTaskCount(run)} 个任务 / {run.eventCount ?? run.snapshotSeq} 个事件</span>{runFailureReason(run) ? <span className="mt-1 block max-w-52 truncate text-xs text-error-600" title={runFailureReason(run) ?? undefined}>{runFailureReason(run)}</span> : runCancelReason(run) ? <span className="mt-1 block max-w-52 truncate text-xs text-gray-500" title={runCancelReason(run) ?? undefined}>{runCancelReason(run)}</span> : null}</td>
    <td className="px-3 py-3"><RunStatusTag status={run.status} /></td>
    <td className="px-3 py-3 text-right"><RunActions run={run} workspacePath={workspacePath} workKey={workKey} /></td>
  </tr>;
}

function RunMobileCard({ run, workspacePath, workKey, onNavigate }: { run: RunSummarySnapshot; workspacePath: string; workKey: string; onNavigate: (runId: string) => void }) {
  return <article tabIndex={0} className="rounded-xl border border-gray-200 p-3 outline-none hover:border-brand-200 focus-visible:ring-2 focus-visible:ring-brand-500 dark:border-gray-800 dark:hover:border-brand-500/40" onClick={() => onNavigate(run.runId)} onKeyDown={(event) => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); onNavigate(run.runId); } }}>
    <div className="flex items-start justify-between gap-3"><div><p className="text-sm font-semibold text-gray-900 dark:text-white">{formatDateTime(run.startedAt ?? run.completedAt)}</p><p className="mt-1 text-xs text-gray-500">{runOperatorName(run)} · {runDuration(run)}</p></div><RunStatusTag status={run.status} /></div>
    <p className="mt-3 text-sm text-gray-700 dark:text-gray-200">{runTaskCount(run)} 个任务 / {run.eventCount ?? run.snapshotSeq} 个事件</p>
    {runFailureReason(run) ? <p className="mt-1 truncate text-xs text-error-600" title={runFailureReason(run) ?? undefined}>{runFailureReason(run)}</p> : null}
    <div className="mt-3"><RunActions run={run} workspacePath={workspacePath} workKey={workKey} /></div>
  </article>;
}

function RunActions({ run, workspacePath, workKey }: { run: RunSummarySnapshot; workspacePath: string; workKey: string }) {
  const stop = (event: React.MouseEvent) => event.stopPropagation();
  if (run.status === "SUCCEEDED") return <Link className="inline-flex items-center gap-1 text-sm font-semibold text-brand-600 hover:text-brand-700 dark:text-brand-400" to={`${workspacePath}/runs/${run.runId}`} onClick={stop}>查看报告 <ExternalLink className="size-3.5" /></Link>;
  if (run.status === "FAILED") return <span className="inline-flex flex-wrap justify-end gap-3"><Link className="text-sm font-semibold text-brand-600 hover:text-brand-700 dark:text-brand-400" to={`${workspacePath}/runs/${run.runId}`} onClick={stop}>查看原因</Link><Link className="text-sm font-semibold text-brand-600 hover:text-brand-700 dark:text-brand-400" to={`${workspacePath}/business-works/${workKey}/workbench`} onClick={stop}>重新运行</Link></span>;
  if (isActiveRun(run.status)) return <Link className="inline-flex items-center gap-1 text-sm font-semibold text-brand-600 hover:text-brand-700 dark:text-brand-400" to={`${workspacePath}/runs/${run.runId}`} onClick={stop}>查看进度 <ExternalLink className="size-3.5" /></Link>;
  return <Link className="text-sm font-semibold text-brand-600 hover:text-brand-700 dark:text-brand-400" to={`${workspacePath}/runs/${run.runId}`} onClick={stop}>查看详情</Link>;
}

function StartBusinessRunDialog({
  open,
  onOpenChange,
  strategyLabel,
  requiredDocuments,
  expectedObject,
  workspacePath,
  workKey,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  strategyLabel: string;
  requiredDocuments: string;
  expectedObject: string;
  workspacePath: string;
  workKey: string;
}) {
  return <Dialog.Root open={open} onOpenChange={onOpenChange}><Dialog.Portal><Dialog.Overlay className="fixed inset-0 z-40 bg-gray-950/50 backdrop-blur-[2px]" /><Dialog.Content className="fixed left-1/2 top-1/2 z-50 w-[calc(100vw-2rem)] max-w-lg -translate-x-1/2 -translate-y-1/2 rounded-2xl border border-gray-200 bg-white p-5 shadow-theme-float outline-none dark:border-gray-800 dark:bg-gray-900">
    <div className="flex items-start justify-between gap-4"><div><Dialog.Title className="text-base font-semibold text-gray-900 dark:text-white">确认开始处理</Dialog.Title><Dialog.Description className="mt-1 text-sm leading-6 text-gray-500">确认后进入办理页，补充本次业务输入并提交运行。</Dialog.Description></div><Dialog.Close asChild><Button variant="ghost" size="icon" aria-label="关闭确认弹窗"><X /></Button></Dialog.Close></div>
    <dl className="mt-5 divide-y divide-gray-100 rounded-xl border border-gray-200 dark:divide-gray-800 dark:border-gray-800"><div className="flex justify-between gap-4 px-3 py-2.5 text-sm"><dt className="text-gray-500">执行策略</dt><dd className="text-right font-medium text-gray-900 dark:text-white">{strategyLabel}</dd></div><div className="flex justify-between gap-4 px-3 py-2.5 text-sm"><dt className="text-gray-500">必需资料</dt><dd className="font-medium text-gray-900 dark:text-white">{requiredDocuments} 类已校验</dd></div><div className="flex justify-between gap-4 px-3 py-2.5 text-sm"><dt className="text-gray-500">预计处理对象</dt><dd className="font-medium text-gray-900 dark:text-white">{expectedObject}</dd></div></dl>
    <div className="mt-5 flex justify-end gap-2"><Dialog.Close asChild><Button variant="outline">取消</Button></Dialog.Close><Button asChild><Link to={`${workspacePath}/business-works/${workKey}/workbench`}><Play />进入办理</Link></Button></div>
  </Dialog.Content></Dialog.Portal></Dialog.Root>;
}

function BusinessStatusTag({ status }: { status: BusinessDetailStatus }) {
  const color: Record<BusinessDetailStatus, "neutral" | "primary" | "success" | "warning" | "error"> = { planned: "neutral", unconfigured: "neutral", preparing: "warning", ready: "success", running: "primary", disabled: "neutral", error: "error" };
  return <Badge color={color[status]}>{businessStatusLabel(status)}</Badge>;
}

function ReadinessStatusTag({ status }: { status: BusinessReadinessStatus }) {
  const meta: Record<BusinessReadinessStatus, { label: string; color: "neutral" | "primary" | "success" | "warning" | "error"; icon: LucideIcon }> = {
    completed: { label: "已完成", color: "success", icon: Check },
    missing: { label: "缺失", color: "warning", icon: CircleAlert },
    processing: { label: "解析中", color: "primary", icon: LoaderCircle },
    failed: { label: "校验失败", color: "error", icon: ShieldAlert },
    unconfigured: { label: "未配置", color: "neutral", icon: CircleAlert },
  };
  const value = meta[status];
  const Icon = value.icon;
  return <Badge color={value.color}><Icon className={status === "processing" ? "size-3.5 animate-spin" : "size-3.5"} />{value.label}</Badge>;
}

function RunStatusTag({ status }: { status: string }) {
  const normalized = status.toUpperCase();
  const meta: Record<string, { label: string; color: "neutral" | "primary" | "success" | "warning" | "error"; icon: LucideIcon }> = {
    ACCEPTED: { label: "已接收", color: "neutral", icon: Clock3 },
    QUEUED: { label: "排队中", color: "neutral", icon: Clock3 },
    RUNNING: { label: "运行中", color: "primary", icon: LoaderCircle },
    SUCCEEDED: { label: "成功", color: "success", icon: CircleCheck },
    FAILED: { label: "失败", color: "error", icon: CircleAlert },
    CANCELLED: { label: "已取消", color: "neutral", icon: CircleAlert },
  };
  const value = meta[normalized] ?? { label: status, color: "neutral" as const, icon: CircleAlert };
  const Icon = value.icon;
  return <Badge color={value.color}><Icon className={normalized === "RUNNING" ? "size-3.5 animate-spin" : "size-3.5"} />{value.label}</Badge>;
}

function OverviewMetric({ label, value, detail, copyValue }: { label: string; value: string; detail?: string; copyValue?: string }) {
  return <div className="min-w-0"><dt className="text-xs text-gray-500">{label}</dt><dd className="mt-1 flex min-w-0 items-center gap-1 text-sm font-semibold text-gray-900 dark:text-white"><span className="min-w-0 truncate" title={value}>{value}</span>{copyValue ? <CopyButton label={`复制${label}`} value={copyValue} /> : null}</dd>{detail ? <p className="mt-1 text-xs text-gray-500">{detail}</p> : null}</div>;
}

function CopyButton({ label, value }: { label: string; value: string }) {
  const [copied, setCopied] = useState(false);
  return <button type="button" className="inline-flex size-5 shrink-0 items-center justify-center rounded text-gray-400 hover:bg-gray-100 hover:text-brand-600 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 dark:hover:bg-white/10" aria-label={label} title={copied ? "已复制" : label} onClick={() => { if (!navigator.clipboard) return; void navigator.clipboard.writeText(value).then(() => setCopied(true)); }}><Copy className="size-3.5" /></button>;
}

function businessStatusLabel(status: BusinessDetailStatus): string {
  return { planned: "规划中", unconfigured: "未配置", preparing: "准备中", ready: "可运行", running: "运行中", disabled: "已停用", error: "配置异常" }[status];
}

function readinessIconClass(status: BusinessReadinessStatus): string {
  return { completed: "bg-success-50 text-success-600 dark:bg-success-500/10", missing: "bg-warning-50 text-warning-600 dark:bg-warning-500/10", processing: "bg-brand-50 text-brand-600 dark:bg-brand-500/10", failed: "bg-error-50 text-error-600 dark:bg-error-500/10", unconfigured: "bg-gray-100 text-gray-500 dark:bg-gray-800" }[status];
}

function hasReadyDocument(documents: DocumentSnapshot[], category: string): boolean {
  return documents.some((document) => document.category === category && isReadyDocumentStatus(document.status));
}

function uploadCategoryForItem(item: BusinessReadinessItem, documents: DocumentSnapshot[]): string | null {
  if (item.status === "completed") return item.categories[0] ?? null;
  return item.categories.find((category) => !hasReadyDocument(documents, category)) ?? item.categories[0] ?? null;
}

function isReadyDocumentStatus(status: DocumentSnapshot["status"]): boolean {
  return status === "AVAILABLE";
}

function isActiveRun(status: string): boolean {
  return ["ACCEPTED", "QUEUED", "RUNNING", "PENDING", "WAITING_INPUT", "WAITING_APPROVAL", "PAUSING", "CANCELLING"].includes(status);
}

function runTimestamp(run: RunSummarySnapshot): number {
  const value = run.startedAt ?? run.completedAt ?? run.createdAt;
  if (!value) return 0;
  const timestamp = Date.parse(value);
  return Number.isNaN(timestamp) ? 0 : timestamp;
}

function runOperatorName(run: RunSummarySnapshot): string {
  return run.operatorName || "当前用户";
}

function runFailureReason(run: RunSummarySnapshot): string | null {
  return run.failureReason ?? null;
}

function runCancelReason(run: RunSummarySnapshot): string | null {
  return run.cancelReason ?? null;
}

function runTaskCount(run: RunSummarySnapshot): number {
  return run.taskCount;
}

function runDuration(run: RunSummarySnapshot): string {
  if (!run.startedAt || !run.completedAt) return "—";
  const seconds = Math.max(0, Math.round((Date.parse(run.completedAt) - Date.parse(run.startedAt)) / 1000));
  if (!Number.isFinite(seconds)) return "—";
  const minutes = Math.floor(seconds / 60);
  return minutes ? `${minutes}分${String(seconds % 60).padStart(2, "0")}秒` : `${seconds}秒`;
}

function formatDateTime(value?: string | null): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  const parts = new Intl.DateTimeFormat("zh-CN", { timeZone: "Asia/Shanghai", year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", hour12: false }).formatToParts(date);
  const get = (type: Intl.DateTimeFormatPartTypes) => parts.find((part) => part.type === type)?.value ?? "";
  return `${get("year")}-${get("month")}-${get("day")} ${get("hour")}:${get("minute")}`;
}

function blockerDisplayName(blocker: BusinessWorkSnapshot["blockers"][number]): string {
  if (!blocker.ref) return blocker.message;
  return capabilityLabel(blocker.ref) ?? blocker.message;
}

function blockerReason(blocker: BusinessWorkSnapshot["blockers"][number]): string {
  if (blocker.code === "DEPENDENCY_NOT_READY") {
    if (blocker.ref?.startsWith("tool://")) return "该工具当前未就绪";
    if (blocker.ref?.startsWith("model://")) return "该模型当前未就绪";
    if (blocker.ref?.startsWith("agent://")) return "该智能体当前未就绪";
    return "依赖能力当前未就绪";
  }
  if (blocker.code === "DECISION_BINDING_MISSING") return "尚未完成决策规则绑定";
  if (blocker.code === "RESOURCE_BINDING_MISSING") return "尚未完成资源绑定";
  if (blocker.code === "ADAPTER_MISSING") return "智能体运行时适配器不可用";
  if (blocker.code === "MODEL_ROUTE_MISSING") return "尚未配置模型路由";
  if (blocker.code === "SECRET_MISSING") return "模型凭证不可用";
  if (blocker.code === "HEALTH_CHECK_FAILED") return "依赖健康检查未通过";
  if (blocker.code === "EXECUTOR_MISSING") return "工具执行器未注册";
  return blocker.ref ? "当前配置尚未满足运行要求" : blocker.message;
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
    qualificationStatus: "planned",
    qualificationLabel: "尚未实现",
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
    documentBindingKeys: [],
    decisionSlots: [],
    functions: work.functions,
    configuration: {},
    workItemType: null,
    caseBased: false,
    caseDefinition: null,
    boundStrategyVersionId: null,
    boundStrategyName: null,
    boundStrategyVersion: null,
  };
}
