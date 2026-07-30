import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Boxes, Check, Cpu, Files, Play, RefreshCw, Settings2, ShieldCheck, Workflow } from "lucide-react";
import { Link, useParams } from "react-router";
import { api } from "@/api/client";
import type { BusinessWorkSnapshot, DocumentSnapshot } from "@/api/types";
import { BusinessWorkPageHeader } from "@/components/business-works/business-work-page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useWorkspaceScope } from "@/lib/demo-scope";
import { DOCUMENT_CATEGORY_LABELS, documentBindingKeys } from "@/lib/business-works";
import {
  listPublishedStrategyOptions,
  type PublishedStrategyOption,
} from "@/lib/published-strategies";

const categoryLabels = DOCUMENT_CATEGORY_LABELS;

export function BusinessWorkSettingsPage() {
  const { workKey = "" } = useParams();
  const { tenantId, projectId, workspacePath } = useWorkspaceScope();
  const queryClient = useQueryClient();
  const [selectedStrategyVersionId, setSelectedStrategyVersionId] = useState("");
  const [bindSuccess, setBindSuccess] = useState(false);

  const work = useQuery({
    queryKey: ["business-work", tenantId, projectId, workKey],
    queryFn: () => api.getBusinessWork(tenantId, projectId, workKey),
  });
  const documents = useQuery({
    queryKey: ["documents", tenantId, projectId],
    queryFn: () => api.listDocuments(tenantId, projectId),
    enabled: Boolean(work.data && work.data.status !== "planned"),
  });
  const strategies = useQuery({
    queryKey: ["published-strategy-options", tenantId, projectId],
    enabled: Boolean(work.data && work.data.status !== "planned"),
    queryFn: () => listPublishedStrategyOptions(tenantId, projectId),
  });
  const decisionBindings = useQuery({
    queryKey: ["capability-pack-bindings", tenantId, projectId, work.data?.packVersionId],
    enabled: Boolean(work.data?.packVersionId && work.data.decisionSlots.length),
    queryFn: () => {
      if (!work.data?.packVersionId) throw new Error("能力包版本尚未载入。");
      return api.getPackBindings(tenantId, projectId, work.data.packVersionId);
    },
  });

  const bindingKeys = useMemo(
    () => new Set(documentBindingKeys(work.data?.workKey ?? workKey, work.data?.workItemType ?? null)),
    [work.data?.workItemType, work.data?.workKey, workKey],
  );
  const boundDocuments = useMemo(() => {
    const items = documents.data?.items ?? [];
    return items.filter((doc) => doc.businessWorkKeys.some((key) => bindingKeys.has(key)));
  }, [bindingKeys, documents.data?.items]);
  const availableCategoryCounts = useMemo(() => {
    const categories = new Map<string, number>();
    for (const doc of boundDocuments) {
      if (doc.status === "AVAILABLE" || doc.status === "REVIEW_REQUIRED") {
        categories.set(doc.category, (categories.get(doc.category) ?? 0) + 1);
      }
    }
    return categories;
  }, [boundDocuments]);

  useEffect(() => {
    const bound = work.data?.boundStrategyVersionId ?? "";
    if (bound) setSelectedStrategyVersionId(bound);
  }, [work.data?.boundStrategyVersionId]);

  useEffect(() => {
    if (!selectedStrategyVersionId && strategies.data?.[0]) {
      setSelectedStrategyVersionId(strategies.data[0].strategyVersionId);
    }
  }, [selectedStrategyVersionId, strategies.data]);

  const bindStrategy = useMutation({
    mutationFn: async () => {
      if (!selectedStrategyVersionId) throw new Error("请选择已发布的执行策略版本。");
      return api.bindBusinessWorkStrategy(tenantId, projectId, workKey, selectedStrategyVersionId);
    },
    onSuccess: async () => {
      setBindSuccess(true);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["business-work", tenantId, projectId, workKey] }),
        queryClient.invalidateQueries({ queryKey: ["business-works", tenantId, projectId] }),
        queryClient.invalidateQueries({ queryKey: ["capability-packs", tenantId, projectId] }),
      ]);
    },
    onMutate: () => setBindSuccess(false),
  });
  const configureChecklist = useMutation({
    mutationFn: async (slotName: string) => {
      const snapshot = work.data;
      if (!snapshot?.packVersionId) throw new Error("能力包版本尚未载入。");
      const slot = snapshot.decisionSlots.find((item) => item.slot === slotName);
      if (!slot?.inputSchema || !slot.outputSchema || !slot.allowedTypes?.includes("CHECKLIST")) {
        throw new Error("该决策槽位不支持自动创建检查清单。");
      }
      const created = await api.createDecisionAsset(tenantId, projectId, {
        name: `${snapshot.name}检查清单`,
        purpose: `用于${snapshot.name}的项目级资料完整性校验`,
        definition: buildChecklistDecision(snapshot, slot),
      });
      const published = await api.publishDecisionAsset(tenantId, projectId, created.decisionAssetId);
      await api.bindCapabilityPackDecision(
        tenantId,
        projectId,
        snapshot.packVersionId,
        slot.slot,
        published.decisionVersionId,
      );
    },
    onSuccess: async () => {
      await Promise.all([
        decisionBindings.refetch(),
        queryClient.invalidateQueries({ queryKey: ["business-work", tenantId, projectId, workKey] }),
        queryClient.invalidateQueries({ queryKey: ["business-works", tenantId, projectId] }),
        queryClient.invalidateQueries({ queryKey: ["capability-packs", tenantId, projectId] }),
      ]);
    },
  });

  if (work.isPending) {
    return <div className="space-y-4"><Skeleton className="h-24" /><Skeleton className="h-72" /></div>;
  }
  if (work.isError || !work.data) {
    return <LoadError message={work.error?.message ?? `未找到业务工作：${workKey}`} onRetry={() => void work.refetch()} />;
  }
  if (work.data.status === "planned") {
    return <Card><CardContent className="flex min-h-72 flex-col items-center justify-center gap-3 p-6 text-center">
      <Cpu className="size-8 text-gray-400" />
      <h1 className="text-lg font-semibold">该业务工作仍在规划中</h1>
      <p className="text-sm text-gray-500">尚无可配置的执行定义。</p>
      <Button asChild variant="outline"><Link to={`${workspacePath}/business-works/${workKey}`}>返回</Link></Button>
    </CardContent></Card>;
  }

  return <SettingsContent
    work={work.data}
    workspacePath={workspacePath}
    strategyOptions={strategies.data ?? []}
    strategiesPending={strategies.isLoading}
    strategiesError={strategies.isError ? strategies.error.message : null}
    selectedStrategyVersionId={selectedStrategyVersionId}
    onSelectStrategy={(value) => { setSelectedStrategyVersionId(value); setBindSuccess(false); }}
    documentsPending={documents.isLoading}
    documentsError={documents.isError ? documents.error.message : null}
    boundDocuments={boundDocuments}
    availableCategoryCounts={availableCategoryCounts}
    bindPending={bindStrategy.isPending}
    bindError={bindStrategy.isError ? bindStrategy.error.message : null}
    bindSuccess={bindSuccess}
    onBind={() => bindStrategy.mutate()}
    onRefresh={() => void Promise.all([work.refetch(), strategies.refetch(), documents.refetch()])}
    refreshing={work.isFetching || strategies.isFetching || documents.isFetching}
    decisionBindings={decisionBindings.data?.decisions ?? []}
    decisionBindingsPending={decisionBindings.isPending && decisionBindings.isEnabled}
    decisionBindingsError={decisionBindings.isError ? decisionBindings.error.message : null}
    configureChecklistPending={configureChecklist.isPending}
    configureChecklistError={configureChecklist.isError ? configureChecklist.error.message : null}
    onConfigureChecklist={(slot) => configureChecklist.mutate(slot)}
  />;
}

function SettingsContent({
  work, workspacePath, strategyOptions, strategiesPending, strategiesError, selectedStrategyVersionId,
  onSelectStrategy, documentsPending, documentsError, boundDocuments, availableCategoryCounts, bindPending,
  bindError, bindSuccess, onBind, onRefresh, refreshing,
  decisionBindings, decisionBindingsPending, decisionBindingsError, configureChecklistPending,
  configureChecklistError, onConfigureChecklist,
}: {
  work: BusinessWorkSnapshot;
  workspacePath: string;
  strategyOptions: PublishedStrategyOption[];
  strategiesPending: boolean;
  strategiesError: string | null;
  selectedStrategyVersionId: string;
  onSelectStrategy: (value: string) => void;
  documentsPending: boolean;
  documentsError: string | null;
  boundDocuments: DocumentSnapshot[];
  availableCategoryCounts: Map<string, number>;
  bindPending: boolean;
  bindError: string | null;
  bindSuccess: boolean;
  onBind: () => void;
  onRefresh: () => void;
  refreshing: boolean;
  decisionBindings: Array<{ slot: string; decisionVersionId: string; contentHash: string }>;
  decisionBindingsPending: boolean;
  decisionBindingsError: string | null;
  configureChecklistPending: boolean;
  configureChecklistError: string | null;
  onConfigureChecklist: (slot: string) => void;
}) {
  const requiredDocuments = work.documentRequirements.filter((item) => item.required);
  const preparedRequired = requiredDocuments.filter(
    (item) => (availableCategoryCounts.get(item.category) ?? 0) >= (item.minCount ?? 1),
  ).length;
  const boundLabel = work.boundStrategyName && work.boundStrategyVersion != null
    ? `${work.boundStrategyName} · v${work.boundStrategyVersion}`
    : "尚未绑定";
  const selectedIsBound = Boolean(work.boundStrategyVersionId) && selectedStrategyVersionId === work.boundStrategyVersionId;
  const pageDescription = work.workKey === "contract-post-evaluation"
    ? "选择已发布的执行策略，并提供合同后评价所需的外部文件。"
    : "选择已发布的执行策略，并提供该业务工作所需的外部文件。";

  const missingRequired = useMemo(
    () => requiredDocuments.filter(
      (item) => (availableCategoryCounts.get(item.category) ?? 0) < (item.minCount ?? 1),
    ),
    [availableCategoryCounts, requiredDocuments],
  );

  return <div className="min-w-0 space-y-5">
    <BusinessWorkPageHeader
      backTo={`${workspacePath}/business-works/${work.workKey}`}
      icon={Settings2}
      meta={<>
        <p className="text-sm font-medium text-brand-500">项目配置</p>
        <Badge color={work.status === "runnable" ? "success" : "warning"}>{work.statusLabel}</Badge>
        {work.packVersion ? <Badge color="primary">v{work.packVersion}</Badge> : null}
      </>}
      title={work.name}
      description={pageDescription}
      actions={<>
        {work.status === "runnable" ? (
          <Button asChild className="w-full justify-center"><Link to={`${workspacePath}/business-works/${work.workKey}/workbench`}><Play />进入工作台</Link></Button>
        ) : null}
        <Button className="w-full justify-center" variant="outline" onClick={onRefresh} loading={refreshing}><RefreshCw />刷新</Button>
      </>}
    />

    <section className="grid gap-3 md:grid-cols-3" aria-label="业务配置进度">
      <SummaryCard label="可用状态" value={work.statusLabel} detail={work.enabled ? "已启用执行策略" : "尚未启用"} icon={Boxes} />
      <SummaryCard label="当前绑定策略" value={boundLabel} detail={work.enabled ? "项目当前绑定版本" : "绑定后生效"} icon={Workflow} />
      <SummaryCard label="必需外部文件" value={`${preparedRequired} / ${requiredDocuments.length}`} detail={preparedRequired === requiredDocuments.length ? "文件已准备" : "仍有文件待提供"} icon={Files} />
    </section>

    <Card><CardContent className="space-y-5 p-5">
      <SectionTitle
        icon={Cpu}
        title="执行组成"
        description="能力包冻结的 Agent 与工具清单。执行时由绑定策略编排，评分仍由确定性工具完成。"
      />
      <div className="grid gap-4 lg:grid-cols-2">
        <RuntimeReferences
          title={`Agent · ${work.agents.length}`}
          empty="当前能力包未声明 Agent。"
          values={work.agents}
        />
        <RuntimeReferences
          title={`工具 · ${work.tools.length}`}
          empty="当前能力包未声明工具。"
          values={work.tools}
        />
      </div>
    </CardContent></Card>

    {work.decisionSlots.length ? <Card><CardContent className="space-y-5 p-5">
      <SectionTitle
        icon={ShieldCheck}
        title="决策规则"
        description="按能力包声明的输入、输出契约创建并绑定项目级不可变规则版本。"
      />
      {decisionBindingsError ? <p role="alert" className="text-sm text-error-600">决策绑定加载失败：{decisionBindingsError}</p> : null}
      {configureChecklistError ? <p role="alert" className="text-sm text-error-600">{configureChecklistError}</p> : null}
      <div className="grid gap-3">
        {work.decisionSlots.map((slot) => {
          const binding = decisionBindings.find((item) => item.slot === slot.slot);
          const supportsChecklist = Boolean(slot.inputSchema && slot.outputSchema && slot.allowedTypes?.includes("CHECKLIST"));
          return <article key={slot.slot} className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-gray-200 p-4 dark:border-gray-800">
            <div className="min-w-0">
              <h3 className="font-medium text-gray-900 dark:text-white">{slot.slot}</h3>
              <p className="mt-1 text-xs text-gray-500">{slot.required ? "必需决策槽位" : "可选决策槽位"} · {binding ? "已绑定已发布版本" : "尚未绑定"}</p>
            </div>
            {binding ? (
              <span className="inline-flex items-center gap-1 rounded-full bg-success-50 px-2 py-1 text-xs text-success-700 dark:bg-success-500/10"><Check className="size-3.5" />已绑定</span>
            ) : supportsChecklist ? (
              <Button size="sm" loading={configureChecklistPending || decisionBindingsPending} onClick={() => onConfigureChecklist(slot.slot)}>
                <ShieldCheck />创建并绑定检查清单
              </Button>
            ) : (
              <span className="text-xs text-warning-700">需要在决策资产接口中绑定兼容版本</span>
            )}
          </article>;
        })}
      </div>
    </CardContent></Card> : null}

    <Card><CardContent className="space-y-5 p-5">
      <SectionTitle
        icon={Workflow}
        title="策略绑定"
        description="选择策略管理中已发布的执行策略版本。策略内部的执行依赖由平台统一维护，此处不可编辑。"
        action={<Button asChild variant="outline" size="sm"><Link to={`${workspacePath}/strategies`}>打开策略管理</Link></Button>}
      />
      {strategiesError ? <p role="alert" className="text-sm text-error-600">策略加载失败：{strategiesError}</p> : null}
      {!strategiesPending && !strategiesError && !strategyOptions.length ? (
        <div className="rounded-xl border border-dashed border-gray-200 px-4 py-8 text-center dark:border-gray-700">
          <p className="text-sm text-gray-500">当前项目暂无已发布的执行策略。</p>
          <Button asChild variant="outline" size="sm" className="mt-3"><Link to={`${workspacePath}/strategies`}>前往策略管理发布</Link></Button>
        </div>
      ) : (
        <label className="block text-xs font-medium text-gray-700 dark:text-gray-300">
          已发布策略版本
          <select
            aria-label="已发布策略版本"
            value={selectedStrategyVersionId}
            disabled={strategiesPending || !strategyOptions.length}
            onChange={(event) => onSelectStrategy(event.target.value)}
            className="mt-2 h-11 w-full rounded-xl border border-gray-300 bg-white px-3 text-sm outline-none focus:border-brand-500 disabled:opacity-60 dark:border-gray-700 dark:bg-gray-900"
          >
            <option value="">{strategiesPending ? "正在加载策略…" : "请选择已发布策略版本"}</option>
            {strategyOptions.map((option) => (
              <option key={option.strategyVersionId} value={option.strategyVersionId}>
                {option.strategyName} · v{option.version}
                {option.strategyVersionId === work.boundStrategyVersionId ? " · 当前已绑定" : ""}
              </option>
            ))}
          </select>
        </label>
      )}
      {work.boundStrategyVersionId ? (
        <p className="text-xs text-gray-500">当前绑定版本：{boundLabel}</p>
      ) : null}
      {bindError ? <p role="alert" className="text-sm text-error-600">{bindError}</p> : null}
      {bindSuccess ? <p role="status" className="text-sm text-success-700">策略绑定已更新。</p> : null}
      <div className="flex justify-end">
        <Button
          loading={bindPending}
          disabled={!selectedStrategyVersionId || strategiesPending || !strategyOptions.length}
          onClick={onBind}
        >
          <Workflow />
          {work.enabled && selectedIsBound ? "重新绑定当前策略" : work.enabled ? "更新策略绑定" : "绑定策略并启用"}
        </Button>
      </div>
    </CardContent></Card>

    <Card><CardContent className="space-y-5 p-5">
      <SectionTitle
        icon={Files}
        title="外部文件"
        description="按文件分类提供业务材料。执行时系统会自动匹配可用文件，无需在此配置文件处理工具。"
        action={<Button asChild variant="outline" size="sm"><Link to={`${workspacePath}/documents`}>提供外部文件</Link></Button>}
      />
      {documentsError ? <p role="alert" className="text-sm text-error-600">文件加载失败：{documentsError}</p> : null}
      {documentsPending ? <Skeleton className="h-24" /> : null}
      {!documentsPending && !work.documentRequirements.length ? (
        boundDocuments.length ? (
          <div className="space-y-2">
            <p className="text-sm text-gray-500">当前执行策略未声明外部文件要求；以下文件已绑定到本业务工作。</p>
            <ul className="space-y-2 text-sm text-gray-600 dark:text-gray-300">
              {boundDocuments.map((doc) => (
                <li key={doc.documentId} className="flex justify-between gap-3 rounded-xl border border-gray-200 px-3 py-2 dark:border-gray-800">
                  <span className="min-w-0 truncate font-medium text-gray-800 dark:text-gray-100" title={doc.name}>{doc.name}</span>
                  <span className="shrink-0 text-xs text-gray-500">{categoryLabels[doc.category] ?? doc.category}</span>
                </li>
              ))}
            </ul>
          </div>
        ) : (
          <p className="text-sm text-gray-500">当前执行策略未声明外部文件要求，也尚未绑定外部文件。</p>
        )
      ) : null}
      <div className="grid gap-3 lg:grid-cols-2">
        {work.documentRequirements.map((requirement) => {
          const availableCount = availableCategoryCounts.get(requirement.category) ?? 0;
          const available = requirement.required
            ? availableCount >= (requirement.minCount ?? 1)
            : availableCount > 0;
          const matching = boundDocuments.filter((doc) => doc.category === requirement.category);
          return (
            <article key={requirement.category} className="min-w-0 rounded-xl border border-gray-200 p-4 dark:border-gray-800">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h3 className="font-medium text-gray-900 dark:text-white">{requirement.displayName ?? categoryLabels[requirement.category] ?? requirement.category}</h3>
                  <p className="mt-1 text-xs text-gray-500">
                    {requirement.required ? "执行前需要" : "可选文件"} · 已准备 {availableCount}
                    {requirement.maxCount ? ` / 最多 ${requirement.maxCount}` : ""}
                  </p>
                  {requirement.description ? <p className="mt-1 text-xs leading-5 text-gray-400">{requirement.description}</p> : null}
                </div>
                {available
                  ? <span className="inline-flex items-center gap-1 rounded-full bg-success-50 px-2 py-1 text-xs text-success-700 dark:bg-success-500/10"><Check className="size-3.5" />已准备</span>
                  : <span className="rounded-full bg-warning-50 px-2 py-1 text-xs text-warning-700 dark:bg-warning-500/10">待提供</span>}
              </div>
              {matching.length ? (
                <ul className="mt-3 space-y-1 text-xs text-gray-500">
                  {matching.map((doc) => (
                    <li key={doc.documentId} className="truncate" title={doc.name}>{doc.name}</li>
                  ))}
                </ul>
              ) : null}
            </article>
          );
        })}
      </div>
      {missingRequired.length ? (
        <div className="rounded-xl bg-warning-50 p-3 text-xs text-warning-700 dark:bg-warning-500/10">
          <p className="font-semibold">缺少必需外部文件</p>
          <ul className="mt-2 space-y-1">
            {missingRequired.map((item) => (
              <li key={item.category}>{categoryLabels[item.category] ?? item.category}</li>
            ))}
          </ul>
        </div>
      ) : null}
    </CardContent></Card>
  </div>;
}

export function buildChecklistDecision(
  work: BusinessWorkSnapshot,
  slot: BusinessWorkSnapshot["decisionSlots"][number],
): Record<string, unknown> {
  return {
    apiVersion: "swarmcore.io/decision/v1",
    kind: "DecisionAsset",
    type: "CHECKLIST",
    engine: "swarmcore.rules.v1",
    inputSchema: slot.inputSchema,
    outputSchema: slot.outputSchema,
    definition: {
      schemaVersion: "schema://contract/checklist-rule@1",
      match: {},
      requirements: work.documentRequirements.map((item) => ({
        key: item.key ?? item.category.toLowerCase(),
        documentType: item.category.toLowerCase(),
        required: item.required,
        minCount: item.minCount ?? (item.required ? 1 : 0),
        ...(item.maxCount ? { maxCount: item.maxCount } : {}),
        mediaTypes: item.acceptedMediaTypes ?? [],
        severity: item.required ? "CRITICAL" : "MEDIUM",
      })),
    },
    tests: [],
  };
}

function SummaryCard({ label, value, detail, icon: Icon }: { label: string; value: string; detail: string; icon: typeof Boxes }) {
  return <Card className="min-w-0"><CardContent className="flex min-w-0 items-start gap-3 p-4"><span className="grid size-10 shrink-0 place-items-center rounded-xl bg-brand-50 text-brand-600 dark:bg-brand-500/10"><Icon className="size-5" /></span><div className="min-w-0"><p className="text-xs text-gray-500">{label}</p><p className="mt-1 truncate font-semibold text-gray-900 dark:text-white" title={value}>{value}</p><p className="mt-1 truncate text-xs text-gray-400" title={detail}>{detail}</p></div></CardContent></Card>;
}

function RuntimeReferences({ title, values, empty }: { title: string; values: string[]; empty: string }) {
  return <div className="min-w-0 rounded-xl border border-gray-200 p-4 dark:border-gray-800">
    <h3 className="text-sm font-semibold text-gray-900 dark:text-white">{title}</h3>
    {values.length ? (
      <ul className="mt-3 grid gap-2 text-xs text-gray-600 dark:text-gray-300">
        {values.map((value) => (
          <li key={value} className="min-w-0 rounded-lg bg-gray-50 px-3 py-2 font-mono dark:bg-white/[0.04]" title={value}>
            <span className="block truncate">{value}</span>
          </li>
        ))}
      </ul>
    ) : <p className="mt-3 text-xs text-gray-500">{empty}</p>}
  </div>;
}

function SectionTitle({ icon: Icon, title, description, action }: { icon: typeof Files; title: string; description: string; action?: React.ReactNode }) {
  return <div className="flex flex-wrap items-start justify-between gap-3"><div className="flex items-start gap-3"><span className="grid size-10 shrink-0 place-items-center rounded-xl bg-brand-50 text-brand-600 dark:bg-brand-500/10"><Icon className="size-5" /></span><div><h2 className="font-semibold text-gray-900 dark:text-white">{title}</h2><p className="mt-1 text-xs leading-5 text-gray-500">{description}</p></div></div>{action}</div>;
}

function LoadError({ message, onRetry }: { message: string; onRetry: () => void }) {
  return <Card><CardContent className="flex min-h-60 flex-col items-center justify-center gap-3 p-5 text-center"><Cpu className="size-8 text-gray-400" /><p className="font-medium text-gray-900 dark:text-white">项目配置无法加载</p><p className="text-sm text-gray-500">{message}</p><Button onClick={onRetry}>重试</Button></CardContent></Card>;
}
