import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Boxes, Bot, Play, Plus, Power, RefreshCw, Settings2, Trash2, Wrench, X } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { api, ApiError } from "@/api/client";
import type { CreateCapabilityPackRequest } from "@/api/types";
import { CapabilityPackCreateForm, type CapabilityPackStrategyOption } from "@/components/capabilities/capability-pack-create-form";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { useWorkspaceScope } from "@/lib/demo-scope";
import { Link } from "react-router";

function packWorkItemType(manifest: Record<string, unknown>) {
  const spec = manifest.spec;
  if (!spec || typeof spec !== "object") return "-";
  const specValue = spec as Record<string, unknown>;
  const caseValue = specValue.case;
  const value = typeof caseValue === "object" && caseValue
    ? (caseValue as Record<string, unknown>).type
    : specValue.workItemType;
  return typeof value === "string" ? value : "-";
}

function packSlots(manifest: Record<string, unknown>, key: "decisions" | "documents") {
  const spec = manifest.spec;
  if (!spec || typeof spec !== "object") return [];
  const value = (spec as Record<string, unknown>)[key];
  return Array.isArray(value) ? value.filter((item): item is Record<string, unknown> => Boolean(item) && typeof item === "object") : [];
}

const PACK_TABS = ["概览", "编排策略", "决策资产", "资料要求", "业务案件", "评估结果", "报告与评测"] as const;

function packReferences(manifest: Record<string, unknown>, key: "agents" | "tools") {
  const spec = manifest.spec;
  if (!spec || typeof spec !== "object") return [];
  const value = (spec as Record<string, unknown>)[key];
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === "string") : [];
}

/** Strip scheme and @version, keep only the last path segment for compact card labels. */
export function capabilityRefLabel(ref: string) {
  const withoutScheme = ref.includes("://") ? ref.slice(ref.indexOf("://") + 3) : ref;
  const at = withoutScheme.lastIndexOf("@");
  const path = at >= 0 ? withoutScheme.slice(0, at) : withoutScheme;
  const slash = path.lastIndexOf("/");
  return slash >= 0 ? path.slice(slash + 1) : path;
}

const PACK_BLOCKER_LABELS: Record<string, string> = {
  DECISION_BINDING_MISSING: "缺少决策资产绑定",
  RESOURCE_BINDING_MISSING: "缺少业务资料（旧版本兼容项）",
  DEPENDENCY_NOT_READY: "运行依赖未就绪",
};

export function CapabilityPacksPage() {
  const { tenantId, projectId, workspacePath } = useWorkspaceScope();
  const queryClient = useQueryClient();
  const [createOpen, setCreateOpen] = useState(false);
  const [selectedTab, setSelectedTab] = useState<(typeof PACK_TABS)[number]>("概览");
  const [configurationEditor, setConfigurationEditor] = useState<{ versionId: string; source: string } | null>(null);
  const [configurationError, setConfigurationError] = useState<string | null>(null);
  const packs = useQuery({ queryKey: ["capability-packs", tenantId, projectId], queryFn: () => api.listCapabilityPacks(tenantId, projectId) });
  const strategyOptions = useQuery({
    queryKey: ["capability-pack-strategies", tenantId, projectId],
    enabled: createOpen,
    queryFn: async () => {
      const strategies = await api.listStrategies(tenantId, projectId, 100);
      const groups = await Promise.all(strategies.items.map(async (strategy) => {
        const versions = await api.listVersions(tenantId, projectId, strategy.strategyId);
        return Promise.all(versions.items.filter((version) => ["PUBLISHED", "TRUSTED"].includes(version.lifecycle)).map(async (version): Promise<CapabilityPackStrategyOption> => ({
          strategyName: strategy.name,
          version: await api.getVersion(tenantId, projectId, strategy.strategyId, version.strategyVersionId),
        })));
      }));
      return groups.flat();
    },
  });
  const create = useMutation({
    mutationFn: (body: CreateCapabilityPackRequest) => api.createCapabilityPack(tenantId, projectId, body),
    onSuccess: async () => {
      setCreateOpen(false);
      await queryClient.invalidateQueries({ queryKey: ["capability-packs", tenantId, projectId] });
    },
  });
  const enable = useMutation({
    mutationFn: ({ versionId, configuration }: { versionId: string; configuration: Record<string, unknown> }) => api.enableCapabilityPack(tenantId, projectId, versionId, configuration),
    onError: (error) => {
      if (error instanceof ApiError && error.code === "CAPABILITY_PACK_NOT_READY") {
        return queryClient.invalidateQueries({ queryKey: ["capability-packs", tenantId, projectId] });
      }
    },
    onSuccess: () => {
      setConfigurationEditor(null);
      setConfigurationError(null);
      return queryClient.invalidateQueries({ queryKey: ["capability-packs", tenantId, projectId] });
    },
  });
  const disable = useMutation({
    mutationFn: (versionId: string) => api.disableCapabilityPack(tenantId, projectId, versionId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["capability-packs", tenantId, projectId] }),
  });
  const remove = useMutation({
    mutationFn: (versionId: string) => api.deleteCapabilityPack(tenantId, projectId, versionId),
    onSuccess: async () => {
      setConfigurationEditor(null);
      setConfigurationError(null);
      await queryClient.invalidateQueries({ queryKey: ["capability-packs", tenantId, projectId] });
    },
  });

  function openConfiguration(versionId: string, configuration: Record<string, unknown>) {
    setConfigurationEditor({ versionId, source: JSON.stringify(configuration, null, 2) });
    setConfigurationError(null);
    enable.reset();
  }

  function saveConfiguration() {
    if (!configurationEditor) return;
    try {
      const parsed: unknown = JSON.parse(configurationEditor.source);
      if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) throw new Error("配置必须是 JSON 对象");
      setConfigurationError(null);
      enable.mutate({ versionId: configurationEditor.versionId, configuration: parsed as Record<string, unknown> });
    } catch (error) {
      setConfigurationError(error instanceof Error ? error.message : "配置 JSON 无效");
    }
  }

  function confirmDelete(pack: { name: string; version: string; versionId: string }) {
    remove.reset();
    if (!window.confirm(`确定删除能力包 ${pack.name} v${pack.version} 吗？此操作不可恢复。`)) return;
    remove.mutate(pack.versionId);
  }

  return <div className="min-w-0 space-y-6">
    <div className="flex flex-wrap items-end justify-between gap-4">
      <div>
        <p className="text-sm font-medium text-brand-500">业务工作</p>
        <h1 className="mt-1 text-2xl font-semibold text-gray-900 dark:text-white">业务能力包</h1>
        <p className="mt-1 text-sm text-gray-500">按项目启用不可变版本，历史评估继续绑定原版本。</p>
      </div>
      <div className="flex flex-wrap gap-2"><Button variant="outline" onClick={() => void packs.refetch()} loading={packs.isFetching}><RefreshCw />刷新</Button><Button onClick={() => { create.reset(); setCreateOpen(true); }}><Plus />新建能力包</Button></div>
    </div>

    <nav aria-label="能力包详情" className="flex gap-1 overflow-x-auto rounded-xl border border-gray-200 bg-white p-1 dark:border-gray-800 dark:bg-gray-900">{PACK_TABS.map((tab) => <button key={tab} type="button" aria-current={selectedTab === tab ? "page" : undefined} onClick={() => setSelectedTab(tab)} className={cn("shrink-0 rounded-lg px-3 py-2 text-sm font-medium", selectedTab === tab ? "bg-brand-50 text-brand-600 dark:bg-brand-500/10" : "text-gray-500 hover:text-gray-900 dark:hover:text-white")}>{tab}</button>)}</nav>

    {createOpen ? <CapabilityPackCreateForm packs={packs.data?.items ?? []} strategies={strategyOptions.data ?? []} loadingStrategies={strategyOptions.isPending} pending={create.isPending} error={create.error?.message ?? strategyOptions.error?.message} onCancel={() => setCreateOpen(false)} onSubmit={(body) => create.mutate(body)} /> : null}

    {packs.isPending ? <div className="grid gap-4 lg:grid-cols-2"><Skeleton className="h-40" /><Skeleton className="h-40" /></div> : null}
    {packs.isError ? <Card><CardContent className="flex min-h-60 flex-col items-center justify-center gap-3 pt-5 text-center"><p className="font-medium text-error-600">能力包加载失败</p><p className="text-sm text-gray-500">{packs.error.message}</p><Button onClick={() => void packs.refetch()}>重试</Button></CardContent></Card> : null}
    {packs.data?.items.length === 0 ? <Card><CardContent className="flex min-h-72 flex-col items-center justify-center gap-3 pt-5 text-center"><span className="grid size-14 place-items-center rounded-2xl bg-brand-50 text-brand-500 dark:bg-brand-500/15"><Boxes /></span><p className="font-medium text-gray-900 dark:text-white">暂无可信能力包</p><p className="text-sm text-gray-500">能力包由系统注册和发布。</p></CardContent></Card> : null}
    {packs.data?.items.length ? <div className="grid gap-4 lg:grid-cols-2">
      {packs.data.items.map((pack) => {
        const agents = packReferences(pack.manifest, "agents");
        const tools = packReferences(pack.manifest, "tools");
        const decisionSlots = packSlots(pack.manifest, "decisions");
        const documentRequirements = packSlots(pack.manifest, "documents");
        const deleteBlockedReason = pack.deleteBlockedReason ?? (pack.enabled ? "请先停用此版本，再执行删除" : null);
        return <Card key={pack.versionId} className="transition hover:border-brand-300 hover:shadow-theme-sm dark:hover:border-brand-500/50">
        <CardContent className="space-y-4 p-5">
          <div className="flex min-w-0 items-start gap-3">
            <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-brand-50 text-brand-600 dark:bg-brand-500/15"><Boxes className="size-5" /></span>
            <div className="min-w-0 flex-1">
              <div className="flex flex-wrap items-start justify-between gap-2">
                <h2 className="min-w-0 break-words text-base font-semibold leading-6 text-gray-900 dark:text-white">{pack.name}</h2>
                {pack.bindingStatus === "DEGRADED"
                  ? <PackBindingStatus tone="warning" label="已退化" />
                  : pack.enabled
                    ? <PackBindingStatus tone="success" label="已启用" />
                    : null}
              </div>
              <p className="mt-1.5 flex flex-wrap items-center gap-2 text-xs text-gray-500">
                <span>v{pack.version} · {pack.contentHash.slice(0, 12)}</span>
                <span className="max-w-full rounded-md bg-gray-50 px-2 py-1 text-gray-500 dark:bg-gray-800 dark:text-gray-400">{packWorkItemType(pack.manifest)}</span>
              </p>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-2 sm:justify-end" aria-label={`${pack.name} v${pack.version} 操作`}>
              {pack.enabled && pack.bindingStatus !== "DEGRADED" && !pack.blockers.length
                ? <Button asChild size="sm"><Link to={`${workspacePath}/capability-packs/${encodeURIComponent(pack.name)}/workbench`}><Play />进入工作台</Link></Button>
                : <Button size="sm" disabled title="请先启用能力包并处理运行阻塞项"><Play />进入工作台</Button>}
              <Button asChild variant="outline" size="sm"><Link to={`${workspacePath}/capability-packs/${encodeURIComponent(pack.name)}`}><Settings2 />配置能力包</Link></Button>
              {!pack.enabled && pack.bindingStatus !== "DEGRADED"
                ? pack.blockers.length
                  ? <Button asChild size="sm" variant="outline"><Link to={`${workspacePath}/capability-packs/${encodeURIComponent(pack.name)}`}>处理阻塞项</Link></Button>
                  : <Button size="sm" disabled={enable.isPending} onClick={() => enable.mutate({ versionId: pack.versionId, configuration: pack.configuration ?? {} })}>启用</Button>
                : null}
              <Button variant="outline" size="sm" aria-label={`配置 ${pack.name} v${pack.version}`} onClick={() => openConfiguration(pack.versionId, pack.configuration ?? {})}><Settings2 />配置</Button>
              {pack.enabled ? <Button variant="outline" size="sm" aria-label={`停用 ${pack.name} v${pack.version}`} disabled={disable.isPending} onClick={() => { remove.reset(); disable.mutate(pack.versionId); }}><Power />停用</Button> : null}
              <Button variant="outline" size="sm" aria-label={`删除 ${pack.name} v${pack.version}`} title={deleteBlockedReason ?? undefined} disabled={deleteBlockedReason !== null || remove.isPending} onClick={() => confirmDelete(pack)}><Trash2 />删除</Button>
          </div>
          {disable.isError && disable.variables === pack.versionId ? <p role="alert" className="text-xs text-error-600">停用失败：{disable.error.message}</p> : null}
          {remove.isError && remove.variables === pack.versionId ? <p role="alert" className="text-xs text-error-600">删除失败：{formatPackDeleteError(remove.error)}</p> : null}
          {selectedTab === "决策资产" ? <PackSlotList title="决策槽位" items={decisionSlots} empty="此版本使用兼容规则资产，未声明 v2 决策槽位。" /> : null}
          {selectedTab === "资料要求" ? <PackDocumentList items={documentRequirements} /> : null}
          {["业务案件", "评估结果", "报告与评测"].includes(selectedTab) ? <p className="rounded-xl bg-gray-50 p-4 text-sm text-gray-500 dark:bg-gray-800/60">{selectedTab}按当前能力包版本展示，历史记录继续保留原对象、决策和文件版本快照。</p> : null}
          <div className="grid gap-4 border-t border-gray-100 pt-4 sm:grid-cols-2 dark:border-gray-800">
            <PackReferenceList title={`Agent（${agents.length}）`} items={agents} emptyLabel="未声明 Agent" icon={Bot} />
            <PackReferenceList title={`工具（${tools.length}）`} items={tools} emptyLabel="未声明工具" icon={Wrench} />
          </div>
          {pack.blockers.length ? <div className="rounded-xl bg-warning-50 p-3 text-xs text-warning-700 dark:bg-warning-500/10"><p className="font-semibold">暂不可启用，请先通过“配置能力包”处理以下阻塞项</p><ul className="mt-1 space-y-1">{pack.blockers.map((blocker) => <li key={blocker.ref} className="break-all">{blocker.ref}：{blocker.reasons.map((reason) => PACK_BLOCKER_LABELS[reason] ?? reason).join("、")}</li>)}</ul></div> : null}
          {configurationEditor?.versionId === pack.versionId ? <section className="rounded-xl border border-brand-200 bg-brand-50/40 p-4 dark:border-brand-500/30 dark:bg-brand-500/5">
            <div className="flex items-start justify-between gap-3"><div><h3 className="text-sm font-semibold text-gray-900 dark:text-white">项目配置</h3><p className="mt-1 text-xs text-gray-500">可修改已发布能力包在当前项目的配置，不影响能力包版本内容。请勿填写密码、令牌等凭证。</p></div><Button variant="ghost" size="icon" aria-label="关闭配置" onClick={() => { setConfigurationEditor(null); setConfigurationError(null); }}><X /></Button></div>
            <label className="mt-3 block text-xs font-medium text-gray-700 dark:text-gray-300">配置 JSON
              <textarea aria-label={`${pack.name} v${pack.version} 项目配置 JSON`} spellCheck={false} value={configurationEditor.source} onChange={(event) => { setConfigurationEditor({ ...configurationEditor, source: event.target.value }); setConfigurationError(null); }} className="mt-2 min-h-32 w-full resize-y rounded-xl border border-gray-300 bg-white p-3 font-mono text-xs text-gray-800 outline-none focus:border-brand-500 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-200" />
            </label>
            {configurationError ? <p role="alert" className="mt-2 text-xs text-error-600">{configurationError}</p> : null}
            {enable.isError ? <p role="alert" className="mt-2 text-xs text-error-600">保存失败：{formatPackEnableError(enable.error)}</p> : null}
            <div className="mt-3 flex justify-end"><Button size="sm" loading={enable.isPending} disabled={pack.blockers.length > 0} onClick={saveConfiguration}>{pack.enabled ? "保存配置" : "保存并启用"}</Button></div>
          </section> : null}
        </CardContent>
      </Card>;
      })}
    </div> : null}
  </div>;
}

function PackSlotList({ title, items, empty }: { title: string; items: Record<string, unknown>[]; empty: string }) {
  return <section className="rounded-xl border border-gray-100 p-4 dark:border-gray-800"><h3 className="text-sm font-semibold text-gray-900 dark:text-white">{title}</h3>{items.length ? <ul className="mt-3 space-y-2">{items.map((item) => <li key={String(item.slot)} className="flex flex-wrap items-center justify-between gap-2 rounded-lg bg-gray-50 px-3 py-2 text-sm dark:bg-gray-800"><span className="font-medium">{String(item.slot)}</span><span className="text-xs text-gray-500">{item.required ? "必需绑定" : "可选绑定"}</span></li>)}</ul> : <p className="mt-2 text-sm text-gray-500">{empty}</p>}</section>;
}

function PackDocumentList({ items }: { items: Record<string, unknown>[] }) {
  return <section className="rounded-xl border border-gray-100 p-4 dark:border-gray-800"><h3 className="text-sm font-semibold text-gray-900 dark:text-white">业务资料要求</h3>{items.length ? <ul className="mt-3 space-y-2">{items.map((item) => <li key={String(item.category)} className="flex flex-wrap items-center justify-between gap-2 rounded-lg bg-gray-50 px-3 py-2 text-sm dark:bg-gray-800"><span className="font-medium">{String(item.category)}</span><span className="text-xs text-gray-500">{item.required ? "执行前需要" : "可选资料"}</span></li>)}</ul> : <p className="mt-2 text-sm text-gray-500">此版本未声明额外资料要求。</p>}</section>;
}

function formatPackDeleteError(error: Error) {
  if (error instanceof ApiError) {
    if (
      error.code === "CAPABILITY_PACK_ENABLED"
      || error.code === "CAPABILITY_PACK_HAS_EVALUATIONS"
      || error.code === "CAPABILITY_PACK_TRUSTED"
    ) {
      return error.message;
    }
    if (error.status === 404 || /not found/i.test(error.message) || error.message.includes("能力包版本不存在")) {
      return "能力包版本不存在或已被删除。";
    }
  }
  return error.message;
}

function formatPackEnableError(error: Error) {
  if (error instanceof ApiError && error.code === "CAPABILITY_PACK_NOT_READY") {
    const blockers = (error.blockers ?? []).filter(
      (blocker): blocker is { ref: string; reasons: string[] } =>
        typeof blocker.ref === "string" && Array.isArray(blocker.reasons),
    );
    if (blockers.length) {
      const details = blockers.map((blocker) => `${blocker.ref}：${blocker.reasons.map((reason) => PACK_BLOCKER_LABELS[reason] ?? reason).join("、")}`).join("；");
      return `能力包尚未就绪：${details}。请通过“配置能力包”处理。`;
    }
    return "能力包尚未就绪，请刷新后通过“配置能力包”处理阻塞项。";
  }
  return error.message;
}

function PackBindingStatus({ tone, label }: { tone: "success" | "warning"; label: string }) {
  return <span className={cn(
    "inline-flex shrink-0 items-center gap-1.5 rounded-full px-2 py-1 text-xs font-medium",
    tone === "success" ? "bg-success-50 text-success-700 dark:bg-success-500/10 dark:text-success-400" : "bg-warning-50 text-warning-700 dark:bg-warning-500/10 dark:text-warning-400",
  )}>
    <span className={cn("size-1.5 shrink-0 rounded-full", tone === "success" ? "bg-success-500" : "bg-warning-500")} aria-hidden />
    {label}
  </span>;
}

function PackReferenceList({ title, items, emptyLabel, icon: Icon }: { title: string; items: string[]; emptyLabel: string; icon: LucideIcon }) {
  return <div className="min-w-0 space-y-2">
    <p className="text-xs font-semibold text-gray-500">{title}</p>
    {items.length ? <div className="flex flex-wrap gap-2">{items.map((item) => {
      const label = capabilityRefLabel(item);
      return <span key={item} title={item} className="inline-flex max-w-full items-center gap-1.5 rounded-lg bg-gray-50 px-2.5 py-1.5 text-xs text-gray-700 dark:bg-gray-800 dark:text-gray-300">
        <Icon className="size-3.5 shrink-0 text-brand-500" aria-hidden />
        <span className="truncate font-medium">{label}</span>
        <span className="sr-only">{item}</span>
      </span>;
    })}</div> : <p className="text-xs text-gray-400">{emptyLabel}</p>}
  </div>;
}
