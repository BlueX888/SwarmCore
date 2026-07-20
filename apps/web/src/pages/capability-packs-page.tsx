import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Boxes, Bot, Plus, RefreshCw, Settings2, Trash2, Wrench, X } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { api, ApiError } from "@/api/client";
import type { CreateCapabilityPackRequest } from "@/api/types";
import { CapabilityPackCreateForm, type CapabilityPackStrategyOption } from "@/components/capabilities/capability-pack-create-form";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { useWorkspaceScope } from "@/lib/demo-scope";

function packWorkItemType(manifest: Record<string, unknown>) {
  const spec = manifest.spec;
  if (!spec || typeof spec !== "object") return "-";
  const value = (spec as Record<string, unknown>).workItemType;
  return typeof value === "string" ? value : "-";
}

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

export function CapabilityPacksPage() {
  const { tenantId, projectId } = useWorkspaceScope();
  const queryClient = useQueryClient();
  const [createOpen, setCreateOpen] = useState(false);
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
    onSuccess: () => {
      setConfigurationEditor(null);
      setConfigurationError(null);
      return queryClient.invalidateQueries({ queryKey: ["capability-packs", tenantId, projectId] });
    },
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

    {createOpen ? <CapabilityPackCreateForm packs={packs.data?.items ?? []} strategies={strategyOptions.data ?? []} loadingStrategies={strategyOptions.isPending} pending={create.isPending} error={create.error?.message ?? strategyOptions.error?.message} onCancel={() => setCreateOpen(false)} onSubmit={(body) => create.mutate(body)} /> : null}

    {packs.isPending ? <div className="grid gap-4 lg:grid-cols-2"><Skeleton className="h-40" /><Skeleton className="h-40" /></div> : null}
    {packs.isError ? <Card><CardContent className="flex min-h-60 flex-col items-center justify-center gap-3 pt-5 text-center"><p className="font-medium text-error-600">能力包加载失败</p><p className="text-sm text-gray-500">{packs.error.message}</p><Button onClick={() => void packs.refetch()}>重试</Button></CardContent></Card> : null}
    {packs.data?.items.length === 0 ? <Card><CardContent className="flex min-h-72 flex-col items-center justify-center gap-3 pt-5 text-center"><span className="grid size-14 place-items-center rounded-2xl bg-brand-50 text-brand-500 dark:bg-brand-500/15"><Boxes /></span><p className="font-medium text-gray-900 dark:text-white">暂无可信能力包</p><p className="text-sm text-gray-500">能力包由系统注册和发布。</p></CardContent></Card> : null}
    {packs.data?.items.length ? <div className="grid gap-4 lg:grid-cols-2">
      {packs.data.items.map((pack) => {
        const agents = packReferences(pack.manifest, "agents");
        const tools = packReferences(pack.manifest, "tools");
        return <Card key={pack.versionId} className="transition hover:border-brand-300 hover:shadow-theme-sm dark:hover:border-brand-500/50">
        <CardContent className="pt-5">
          <div className="flex items-start justify-between gap-4">
            <div className="flex min-w-0 gap-3">
              <span className="grid size-11 shrink-0 place-items-center rounded-xl bg-brand-50 text-brand-600 dark:bg-brand-500/15"><Boxes className="size-5" /></span>
              <div className="min-w-0">
                <h2 className="font-semibold text-gray-900 dark:text-white">{pack.name}</h2>
                <p className="mt-1 flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-gray-500">
                  <span>v{pack.version} · {pack.contentHash.slice(0, 12)}</span>
                  {pack.bindingStatus === "DEGRADED"
                    ? <PackBindingStatus tone="warning" label="已退化" />
                    : pack.enabled
                      ? <PackBindingStatus tone="success" label="已启用" />
                      : null}
                </p>
              </div>
            </div>
            <div className="flex shrink-0 flex-wrap items-center justify-end gap-2">
              {!pack.enabled && pack.bindingStatus !== "DEGRADED"
                ? <Button size="sm" disabled={enable.isPending || pack.blockers.length > 0} onClick={() => enable.mutate({ versionId: pack.versionId, configuration: pack.configuration ?? {} })}>启用</Button>
                : null}
              <Button variant="outline" size="sm" aria-label={`配置 ${pack.name} v${pack.version}`} onClick={() => openConfiguration(pack.versionId, pack.configuration ?? {})}><Settings2 />配置</Button>
              <Button variant="outline" size="sm" aria-label={`删除 ${pack.name} v${pack.version}`} disabled={remove.isPending} onClick={() => confirmDelete(pack)}><Trash2 />删除</Button>
            </div>
          </div>
          {remove.isError && remove.variables === pack.versionId ? <p role="alert" className="mt-3 text-xs text-error-600">删除失败：{formatPackDeleteError(remove.error)}</p> : null}
          <p className="mt-4 text-sm text-gray-500">工作项类型：<span className="font-medium text-gray-700 dark:text-gray-300">{packWorkItemType(pack.manifest)}</span></p>
          <div className="mt-4 grid gap-4 border-t border-gray-100 pt-4 sm:grid-cols-2 dark:border-gray-800">
            <PackReferenceList title={`Agent（${agents.length}）`} items={agents} emptyLabel="未声明 Agent" icon={Bot} />
            <PackReferenceList title={`工具（${tools.length}）`} items={tools} emptyLabel="未声明工具" icon={Wrench} />
          </div>
          {pack.blockers.length ? <div className="mt-4 rounded-xl bg-warning-50 p-3 text-xs text-warning-700 dark:bg-warning-500/10"><p className="font-semibold">暂不可完全启用</p><ul className="mt-1 space-y-1">{pack.blockers.map((blocker) => <li key={blocker.ref} className="break-all">{blocker.ref}：{blocker.reasons.join(", ")}</li>)}</ul></div> : null}
          {configurationEditor?.versionId === pack.versionId ? <section className="mt-4 rounded-xl border border-brand-200 bg-brand-50/40 p-4 dark:border-brand-500/30 dark:bg-brand-500/5">
            <div className="flex items-start justify-between gap-3"><div><h3 className="text-sm font-semibold text-gray-900 dark:text-white">项目配置</h3><p className="mt-1 text-xs text-gray-500">仅更新当前项目的绑定参数，不修改已发布的能力包版本。请勿填写密码、令牌等凭证。</p></div><Button variant="ghost" size="icon" aria-label="关闭配置" onClick={() => { setConfigurationEditor(null); setConfigurationError(null); }}><X /></Button></div>
            <label className="mt-3 block text-xs font-medium text-gray-700 dark:text-gray-300">配置 JSON
              <textarea aria-label={`${pack.name} v${pack.version} 项目配置 JSON`} spellCheck={false} value={configurationEditor.source} onChange={(event) => { setConfigurationEditor({ ...configurationEditor, source: event.target.value }); setConfigurationError(null); }} className="mt-2 min-h-36 w-full resize-y rounded-xl border border-gray-300 bg-white p-3 font-mono text-xs text-gray-800 outline-none focus:border-brand-500 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-200" />
            </label>
            {configurationError ? <p role="alert" className="mt-2 text-xs text-error-600">{configurationError}</p> : null}
            {enable.isError ? <p role="alert" className="mt-2 text-xs text-error-600">保存失败：{enable.error.message}</p> : null}
            <div className="mt-3 flex justify-end"><Button size="sm" loading={enable.isPending} disabled={pack.blockers.length > 0} onClick={saveConfiguration}>{pack.enabled ? "保存配置" : "保存并启用"}</Button></div>
          </section> : null}
        </CardContent>
      </Card>;
      })}
    </div> : null}
  </div>;
}

function formatPackDeleteError(error: Error) {
  if (error instanceof ApiError) {
    if (error.code === "CAPABILITY_PACK_ENABLED" || error.code === "CAPABILITY_PACK_HAS_EVALUATIONS") {
      return error.message;
    }
    if (error.status === 404 || /not found/i.test(error.message)) {
      return "能力包版本不存在或已被删除。";
    }
  }
  return error.message;
}

function PackBindingStatus({ tone, label }: { tone: "success" | "warning"; label: string }) {
  return <span className={cn(
    "inline-flex items-center gap-1.5 font-medium",
    tone === "success" ? "text-success-600 dark:text-success-500" : "text-warning-600 dark:text-warning-500",
  )}>
    <span className="text-gray-300 dark:text-gray-600" aria-hidden>·</span>
    <span className={cn("size-1.5 shrink-0 rounded-full", tone === "success" ? "bg-success-500" : "bg-warning-500")} aria-hidden />
    {label}
  </span>;
}

function PackReferenceList({ title, items, emptyLabel, icon: Icon }: { title: string; items: string[]; emptyLabel: string; icon: LucideIcon }) {
  return <div className="min-w-0">
    <p className="text-xs font-semibold text-gray-500">{title}</p>
    {items.length ? <ul className="mt-2 space-y-1.5">{items.map((item) => {
      const label = capabilityRefLabel(item);
      return <li key={item} title={item} className="flex items-center gap-2 rounded-lg bg-gray-50 px-2.5 py-2 text-xs text-gray-700 dark:bg-gray-800 dark:text-gray-300">
        <Icon className="size-3.5 shrink-0 text-brand-500" aria-hidden />
        <span className="min-w-0 truncate font-medium">{label}</span>
        <span className="sr-only">{item}</span>
      </li>;
    })}</ul> : <p className="mt-2 text-xs text-gray-400">{emptyLabel}</p>}
  </div>;
}
