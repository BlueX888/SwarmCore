import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import * as Dialog from "@radix-ui/react-dialog";
import { Bot, CheckCircle2, Copy, Cpu, Eye, EyeOff, Network, Play, PlugZap, Plus, RefreshCw, Save, Search, Settings2, ShieldCheck, Trash2, Wrench, X } from "lucide-react";
import * as React from "react";
import { useNavigate, useSearchParams } from "react-router";
import { api } from "@/api/client";
import type { CapabilityKind, CapabilityPreset, CapabilitySummary, ReadinessReasonCode } from "@/api/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { PageHeader } from "@/components/ui/page-header";
import { Skeleton } from "@/components/ui/skeleton";
import { useWorkspaceScope } from "@/lib/demo-scope";
import { capabilityDisplayName, capabilitySearchHaystack, normalizeCapabilitySearch } from "@/lib/capability-labels";

const fieldClass = "h-10 w-full rounded-lg border border-gray-300 bg-transparent px-3 text-sm outline-none focus:border-brand-500 dark:border-gray-700";
const CONFIGURED_API_KEY_MASK = "••••••••";
const kindLabels: Record<CapabilityKind, string> = { agent: "智能体", tool: "工具", model: "模型", policy: "策略能力" };
const pageDescriptions: Record<CapabilityKind, string> = {
  agent: "选择已就绪智能体直接运行，或基于内置版本创建可编辑的项目配置。",
  tool: "选择已就绪工具直接运行，或保存参数为我的预设。",
  model: "管理当前项目可调用的模型型号；填写 API URL、ModelName 和 API Key 即可新建。",
  policy: "查看策略能力的就绪状态，或保存参数为我的预设。",
};
const reasonLabels: Record<ReadinessReasonCode, string> = {
  EXECUTOR_MISSING: "缺少执行器", ADAPTER_MISSING: "智能体适配器不可用", MODEL_ROUTE_MISSING: "缺少模型路由",
  SECRET_MISSING: "凭证不可用", DEPENDENCY_NOT_READY: "依赖能力未就绪", DEPENDENCY_CYCLE: "依赖形成循环",
  HEALTH_CHECK_FAILED: "健康检查失败", ENVIRONMENT_NOT_ALLOWED: "当前环境不允许", CAPABILITY_PACK_DISABLED: "业务能力包未启用",
  SCHEMA_INVALID: "参数结构无效", POLICY_DENIED: "策略不允许使用",
};
const riskFilterOptions = [
  { value: "", label: "全部" },
  { value: "LOW", label: "LOW" },
  { value: "MEDIUM", label: "MEDIUM" },
  { value: "HIGH", label: "HIGH" },
] as const;
type RiskFilter = (typeof riskFilterOptions)[number]["value"];

export function AgentCapabilitiesPage() { return <CapabilitiesPage kind="agent" />; }
export function ToolCapabilitiesPage() { return <CapabilitiesPage kind="tool" />; }
export function ModelCapabilitiesPage() { return <CapabilitiesPage kind="model" />; }
export function PolicyCapabilitiesPage() { return <CapabilitiesPage kind="policy" />; }

export function CapabilitiesPage({ kind }: { kind: CapabilityKind }) {
  const { tenantId, projectId, workspacePath } = useWorkspaceScope();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const queryClient = useQueryClient();
  const [search, setSearch] = React.useState(() => normalizeCapabilitySearch(searchParams.get("search") ?? ""));
  const [showNotReady, setShowNotReady] = React.useState(() => searchParams.get("showNotReady") === "1");
  const [riskFilter, setRiskFilter] = React.useState<RiskFilter>("");
  const [selected, setSelected] = React.useState<CapabilitySummary>();
  const [input, setInput] = React.useState<Record<string, unknown>>({});
  const [jsonInput, setJsonInput] = React.useState("{}");
  const [formError, setFormError] = React.useState("");
  const [presetName, setPresetName] = React.useState("");
  const [selectedPresetId, setSelectedPresetId] = React.useState("");
  const [creatingModel, setCreatingModel] = React.useState(false);
  const query = useQuery({ queryKey: ["capability-center", tenantId, projectId], queryFn: () => api.getCapabilityCenter(tenantId, projectId) });
  React.useEffect(() => {
    if (!selected || !query.data) return;
    const selectedLogical = selected.ref.replace(/@[^@]+$/, "");
    const refreshed = query.data.items.find((item) => item.ref === selected.ref)
      ?? query.data.items.find((item) => item.ref.replace(/@[^@]+$/, "") === selectedLogical);
    if (refreshed && refreshed !== selected) setSelected(refreshed);
  }, [query.data, selected]);
  const presets = useQuery({ queryKey: ["capability-presets", tenantId, projectId], queryFn: () => api.listPresets(tenantId, projectId) });
  const filtered = React.useMemo(() => (query.data?.items ?? []).filter((item) => {
    if (!showNotReady && item.readiness.status !== "READY") return false;
    if (item.kind !== kind) return false;
    // 模型广场只展示项目创建的具体型号，不罗列系统逻辑路由。
    if (kind === "model" && item.source !== "project") return false;
    if (kind === "tool" && riskFilter && item.risk !== riskFilter) return false;
    const needle = search.trim().toLowerCase();
    return !needle || capabilitySearchHaystack(item).includes(needle);
  }), [kind, query.data?.items, riskFilter, search, showNotReady]);
  const capabilityPresets = (presets.data?.items ?? []).filter((item) => item.capabilityRef === selected?.ref);
  const simpleProperties = selected ? simpleSchemaProperties(selected.inputSchema) : null;
  const choose = (item: CapabilitySummary) => {
    const defaults = schemaDefaults(item.inputSchema);
    setSelected(item); setInput(defaults); setJsonInput(JSON.stringify(defaults, null, 2)); setFormError(""); setPresetName(""); setSelectedPresetId("");
  };
  const resolvedInput = (): Record<string, unknown> | null => {
    if (simpleProperties) return input;
    try {
      const parsed: unknown = JSON.parse(jsonInput);
      if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) throw new Error("输入必须是 JSON 对象。");
      setFormError(""); return parsed as Record<string, unknown>;
    } catch (error) { setFormError(error instanceof Error ? error.message : "JSON 无效。"); return null; }
  };
  const run = useMutation({
    mutationFn: async () => {
      if (!selected) throw new Error("请选择能力。");
      const value = resolvedInput(); if (!value) throw new Error("请修正输入。");
      return api.runCapability(tenantId, projectId, selected.ref, value, selectedPresetId || undefined);
    },
    onSuccess: (handle) => void navigate(`${workspacePath}/runs/${handle.runId}`),
    onError: (error) => setFormError(error.message),
  });
  const savePreset = useMutation({
    mutationFn: async () => {
      if (!selected || !presetName.trim()) throw new Error("请填写预设名称。");
      const parameters = resolvedInput(); if (!parameters) throw new Error("请修正输入。");
      const body = { name: presetName.trim(), capabilityRef: selected.ref, parameters };
      return selectedPresetId ? api.updatePreset(tenantId, projectId, selectedPresetId, body) : api.createPreset(tenantId, projectId, body);
    },
    onSuccess: async (preset) => { setSelectedPresetId(preset.presetId); setPresetName(""); await queryClient.invalidateQueries({ queryKey: ["capability-presets", tenantId, projectId] }); },
    onError: (error) => setFormError(error.message),
  });
  const deletePreset = useMutation({
    mutationFn: (presetId: string) => api.deletePreset(tenantId, projectId, presetId),
    onSuccess: async (_, presetId) => { if (selectedPresetId === presetId) setSelectedPresetId(""); await queryClient.invalidateQueries({ queryKey: ["capability-presets", tenantId, projectId] }); },
  });
  const copyPreset = useMutation({
    mutationFn: (preset: CapabilityPreset) => api.copyPreset(tenantId, projectId, preset.presetId, `${preset.name} 副本`),
    onSuccess: async () => { await queryClient.invalidateQueries({ queryKey: ["capability-presets", tenantId, projectId] }); },
    onError: (error) => setFormError(error.message),
  });
  const loadPreset = (preset: CapabilityPreset) => {
    setSelectedPresetId(preset.presetId); setPresetName(preset.name); setInput(preset.parameters); setJsonInput(JSON.stringify(preset.parameters, null, 2)); setFormError("");
  };
  const addToCanvas = () => {
    if (!selected) return;
    const value = resolvedInput(); if (!value) return;
    void navigate(`${workspacePath}/canvas`, { state: { capability: selected, input: value } });
  };
  return <div className="min-w-0 space-y-6">
    <PageHeader
      eyebrow={kind === "model" ? "模型连接" : "能力中心"}
      title={kindLabels[kind]}
      description={pageDescriptions[kind]}
      actions={<>
        <Button variant="outline" onClick={() => void Promise.all([query.refetch(), presets.refetch()])} loading={query.isFetching || presets.isFetching}><RefreshCw />刷新</Button>
        {kind === "tool" ? <Button onClick={() => void navigate(`${workspacePath}/tools/new`)}><Plus />新建工具</Button> : null}
        {kind === "model" ? <Button onClick={() => setCreatingModel(true)}><Plus />新建模型</Button> : null}
        {kind === "agent" ? <Button onClick={() => void navigate(`${workspacePath}/agents/configure?new=1`)}><Plus />创建智能体</Button> : null}
        {kind === "policy" ? <Button onClick={() => void navigate(`${workspacePath}/policies/new`)}><Plus />新建策略</Button> : null}
      </>}
    />
    <Card><CardContent className="grid gap-3 pt-5 md:grid-cols-[minmax(0,1fr)_auto]"><label className="relative md:col-span-1"><Search className="absolute left-3 top-2.5 size-5 text-gray-400" /><input aria-label={`搜索${kindLabels[kind]}`} className={`${fieldClass} pl-10`} value={search} onChange={(event) => setSearch(event.target.value)} placeholder={kind === "model" ? "搜索模型名称或 API 连接" : `搜索${kindLabels[kind]}名称或用途`} /></label><div className="flex flex-wrap items-center gap-3 justify-self-end"><label className="flex items-center gap-2 whitespace-nowrap text-sm text-gray-600"><input type="checkbox" checked={showNotReady} onChange={(event) => setShowNotReady(event.target.checked)} />{kind === "model" ? "显示已配置但未就绪" : "显示未就绪"}</label>{kind === "tool" ? <div role="group" aria-label="按风险分类" className="flex rounded-lg bg-gray-100 p-1 dark:bg-gray-800">{riskFilterOptions.map((option) => <Button key={option.value || "all"} type="button" size="sm" variant={riskFilter === option.value ? "primary" : "ghost"} aria-pressed={riskFilter === option.value} onClick={() => setRiskFilter(option.value)} className="h-9 px-3">{option.label}</Button>)}</div> : null}</div></CardContent></Card>
    {query.isPending ? <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">{[1, 2, 3].map((item) => <Skeleton key={item} className="h-52" />)}</div> : null}
    {query.isError ? <Card><CardContent className="pt-5"><ErrorState title="无法加载能力中心" message={query.error.message} onRetry={() => void query.refetch()} /></CardContent></Card> : null}
    {!query.isPending && !query.isError && !filtered.length ? <Card><CardContent className="pt-5"><EmptyState
      title={kind === "model" ? (showNotReady ? "当前项目还没有模型 API 配置。" : "没有可调用的模型 API。") : "当前筛选条件下没有可显示的能力。"}
      description={kind === "model" ? "点击“新建模型”，只需填写 API URL、ModelName 和 API Key。" : undefined}
    /></CardContent></Card> : null}
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">{filtered.map((item) => <CapabilityCard key={item.ref} item={item} selected={selected?.ref === item.ref} onSelect={() => choose(item)} onConfigure={item.kind === "agent" ? () => void navigate(agentConfigurationPath(workspacePath, item)) : undefined} />)}</div>
    {kind === "model" && creatingModel ? <NewModelConfigurationDialog tenantId={tenantId} projectId={projectId} onClose={() => setCreatingModel(false)} onSaved={async () => { setCreatingModel(false); await query.refetch(); }} /> : null}
    {selected ? <Dialog.Root open onOpenChange={(open) => { if (!open) setSelected(undefined); }}><Dialog.Portal>
      <Dialog.Overlay className="fixed inset-0 z-40 bg-gray-950/50 backdrop-blur-[2px]" />
      <Dialog.Content className="fixed left-1/2 top-1/2 z-50 w-[calc(100vw-2rem)] max-w-3xl -translate-x-1/2 -translate-y-1/2 outline-none">
        <div className="flex max-h-[92vh] flex-col overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-theme-xl dark:border-gray-800 dark:bg-gray-900">
          <div className="flex shrink-0 items-start justify-between gap-4 border-b border-gray-100 p-5 dark:border-gray-800">
            <div className="min-w-0">
              <Dialog.Title asChild><h2 className="font-semibold text-gray-900 dark:text-white">{capabilityDisplayName(selected)}</h2></Dialog.Title>
              <Dialog.Description className="mt-1 text-sm text-gray-500">{kind === "model" ? (modelCardSubtitle(selected) ?? "编辑该型号的 API 连接。") : selected.description}</Dialog.Description>
            </div>
            <div className="flex shrink-0 items-center gap-2">
              <Badge color={selected.readiness.status === "READY" ? "success" : "warning"}>{selected.readiness.status === "READY" ? (kind === "model" ? "可调用" : "可用") : "未就绪"}</Badge>
              <Dialog.Close asChild><Button type="button" variant="ghost" size="icon" aria-label="关闭详情"><X /></Button></Dialog.Close>
            </div>
          </div>
          <div className="min-h-0 flex-1 space-y-5 overflow-y-auto p-5">
            {selected.readiness.reasons.length ? <ul className="rounded-xl bg-warning-50 p-4 text-sm text-warning-700 dark:bg-warning-500/10">{selected.readiness.reasons.map((reason) => <li key={`${reason.code}-${reason.dependencyRef ?? ""}`}>{reasonLabels[reason.code]}{reason.dependencyRef ? `：${capabilityDisplayName({ ref: reason.dependencyRef, name: reason.dependencyRef })}` : ""}</li>)}</ul> : null}
            {kind === "agent" ? <p className="rounded-xl bg-brand-50 p-3 text-sm text-brand-700 dark:bg-brand-500/10 dark:text-brand-200">{selected.source === "project" ? "这是当前项目的版本化智能体；运行时会由 Agno Adapter 创建真实实例。" : "系统内置版本保持只读。“编辑配置”会复制当前模型、工具和提示词，创建可独立修改的项目智能体。"}</p> : null}
            {kind === "model" ? <ModelProviderForm tenantId={tenantId} projectId={projectId} capabilityRef={selected.ref} onSaved={async () => { await queryClient.invalidateQueries({ queryKey: ["capability-center", tenantId, projectId] }); }} /> : null}
            {kind !== "model" ? <InputForm properties={simpleProperties} input={input} jsonInput={jsonInput} onInput={setInput} onJsonInput={setJsonInput} /> : null}
            {kind !== "model" ? <section className="space-y-3" aria-labelledby="preset-title"><div><h3 id="preset-title" className="font-semibold text-gray-900 dark:text-white">我的预设</h3><p className="text-sm text-gray-500">预设只保存可复用参数，不保存凭证。</p></div>{capabilityPresets.length ? <div className="flex flex-wrap gap-2">{capabilityPresets.map((preset) => <span key={preset.presetId} className="inline-flex items-center rounded-lg border border-gray-200 dark:border-gray-700"><button type="button" className="px-3 py-2 text-sm" onClick={() => loadPreset(preset)}>{preset.name}</button><button type="button" aria-label={`复制预设 ${preset.name}`} className="p-2 text-gray-400 hover:text-brand-500" onClick={() => copyPreset.mutate(preset)}><Copy className="size-4" /></button><button type="button" aria-label={`删除预设 ${preset.name}`} className="p-2 text-gray-400 hover:text-error-500" onClick={() => deletePreset.mutate(preset.presetId)}><Trash2 className="size-4" /></button></span>)}</div> : <p className="text-sm text-gray-500">尚未保存预设。</p>}<div className="flex flex-wrap gap-2"><input aria-label="预设名称" className={`${fieldClass} max-w-sm`} value={presetName} onChange={(event) => setPresetName(event.target.value)} placeholder="例如：日报检索" /><Button variant="outline" onClick={() => savePreset.mutate()} loading={savePreset.isPending} disabled={!presetName.trim()}>{selectedPresetId ? null : <Plus />}{selectedPresetId ? "更新预设" : "保存预设"}</Button>{selectedPresetId ? <Button variant="ghost" onClick={() => { setSelectedPresetId(""); setPresetName(""); }}>取消编辑</Button> : null}</div></section> : null}
            {formError ? <p role="alert" className="rounded-lg bg-error-50 p-3 text-sm text-error-600">{formError}</p> : null}
            <details className="rounded-xl border border-gray-200 p-4 text-sm dark:border-gray-800"><summary className="cursor-pointer font-medium">{kind === "model" ? "连接详情" : "高级详情"}</summary><pre className="mt-3 max-h-80 overflow-auto whitespace-pre-wrap text-xs text-gray-500">{JSON.stringify(kind === "model" ? { ref: selected.ref, source: selected.source } : { ref: selected.ref, source: selected.source, risk: selected.risk, inputSchema: selected.inputSchema, outputSchema: selected.outputSchema }, null, 2)}</pre></details>
          </div>
          {kind !== "model" ? <div className="flex shrink-0 flex-wrap justify-end gap-2 border-t border-gray-100 px-5 py-4 dark:border-gray-800">{kind === "agent" ? <Button aria-label="编辑当前智能体配置" variant="outline" onClick={() => void navigate(agentConfigurationPath(workspacePath, selected))}><Settings2 />编辑配置</Button> : null}<Button variant="outline" onClick={addToCanvas} disabled={selected.readiness.status !== "READY"}><Network />加入画布</Button><Button onClick={() => run.mutate()} loading={run.isPending} disabled={selected.readiness.status !== "READY"}><Play />立即运行</Button></div> : null}
        </div>
      </Dialog.Content>
    </Dialog.Portal></Dialog.Root> : null}
  </div>;
}

function agentConfigurationPath(workspacePath: string, item: CapabilitySummary): string {
  if (item.source === "project") {
    const match = /^agent:\/\/project\/([^@]+)@\d+$/.exec(item.ref);
    if (match?.[1]) return `${workspacePath}/agents/configure?configuration=${encodeURIComponent(match[1])}`;
  }
  return `${workspacePath}/agents/configure?copy=${encodeURIComponent(item.ref)}`;
}

function NewModelConfigurationDialog({ tenantId, projectId, onClose, onSaved }: { tenantId: string; projectId: string; onClose: () => void; onSaved: () => Promise<void> }) {
  const logicalModel = React.useMemo(() => `model://project/${crypto.randomUUID()}`, []);
  return <Dialog.Root open onOpenChange={(open) => { if (!open) onClose(); }}><Dialog.Portal><Dialog.Overlay className="fixed inset-0 z-40 bg-gray-950/50 backdrop-blur-[2px]" /><Dialog.Content className="fixed left-1/2 top-1/2 z-50 w-[calc(100vw-2rem)] max-w-2xl -translate-x-1/2 -translate-y-1/2 outline-none"><div className="rounded-2xl border border-gray-200 bg-white shadow-theme-xl dark:border-gray-800 dark:bg-gray-900"><div className="flex items-start justify-between border-b border-gray-100 p-5 dark:border-gray-800"><div><Dialog.Title className="font-semibold text-gray-900 dark:text-white">新建模型</Dialog.Title><Dialog.Description className="mt-1 text-sm text-gray-500">填写 API URL、ModelName 和 API Key。</Dialog.Description></div><Dialog.Close asChild><Button variant="ghost" size="icon" aria-label="关闭新建模型"><X /></Button></Dialog.Close></div><div className="space-y-4 p-5"><ModelProviderForm tenantId={tenantId} projectId={projectId} capabilityRef={logicalModel} createMode onSaved={onSaved} /></div></div></Dialog.Content></Dialog.Portal></Dialog.Root>;
}

function ModelProviderForm({ tenantId, projectId, capabilityRef, onSaved, createMode = false }: { tenantId: string; projectId: string; capabilityRef: string; onSaved: () => Promise<void>; createMode?: boolean }) {
  const queryClient = useQueryClient();
  const logicalModel = capabilityRef.replace(/@[^@]+$/, "");
  const configuration = useQuery({
    queryKey: ["model-provider", tenantId, projectId, logicalModel],
    queryFn: () => api.getModelProvider(tenantId, projectId, logicalModel),
    enabled: !createMode,
  });
  const [displayName, setDisplayName] = React.useState("");
  const [providerUrl, setProviderUrl] = React.useState("");
  const [modelName, setModelName] = React.useState("");
  const [apiKey, setApiKey] = React.useState("");
  const [editingKey, setEditingKey] = React.useState(false);
  const [showApiKey, setShowApiKey] = React.useState(false);
  const [notice, setNotice] = React.useState("");
  React.useEffect(() => {
    if (!configuration.data) return;
    setProviderUrl(configuration.data.providerUrl);
    setModelName(configuration.data.modelName);
    setDisplayName(configuration.data.displayName ?? "");
  }, [configuration.data]);
  const apiKeyConfigured = Boolean(!createMode && configuration.data?.apiKeyConfigured);
  const showingConfiguredMask = apiKeyConfigured && !apiKey && !editingKey;
  const body = () => ({
    logicalModel,
    providerUrl: providerUrl.trim(),
    modelName: modelName.trim(),
    displayName: (displayName.trim() || modelName.trim()),
    ...(apiKey ? { apiKey } : {}),
  });
  const canSubmit = Boolean(providerUrl.trim() && modelName.trim() && (apiKey || apiKeyConfigured));
  const test = useMutation({
    mutationFn: (requestBody: ReturnType<typeof body>) => api.testModelProvider(tenantId, projectId, requestBody),
    onSuccess: async (result) => {
      setNotice(
        result.readinessUpdated
          ? `连接成功：${result.modelName}，真实响应耗时 ${result.latencyMs} ms，模型已就绪。`
          : `连接成功：${result.modelName}，真实响应耗时 ${result.latencyMs} ms。请先保存当前配置，再重新检测以更新可用状态。`,
      );
      if (result.readinessUpdated) {
        await queryClient.invalidateQueries({ queryKey: ["capability-center", tenantId, projectId] });
      }
    },
    onError: (error) => setNotice(`连接失败：${error.message}`),
  });
  const reveal = useMutation({
    mutationFn: () => api.revealModelProviderApiKey(tenantId, projectId, logicalModel),
    onSuccess: ({ apiKey: savedApiKey }) => {
      setApiKey(savedApiKey);
      setEditingKey(true);
      setShowApiKey(true);
      setNotice("");
    },
    onError: (error) => setNotice(`读取失败：${error.message}`),
  });
  const save = useMutation({
    mutationFn: (requestBody: ReturnType<typeof body>) => api.saveModelProvider(tenantId, projectId, requestBody),
    onSuccess: async (saved, requestBody) => {
      queryClient.setQueryData(["model-provider", tenantId, projectId, logicalModel], saved);
      if (requestBody.apiKey) {
        setApiKey(requestBody.apiKey);
        setEditingKey(true);
        setShowApiKey(false);
      } else {
        setApiKey("");
        setEditingKey(false);
        setShowApiKey(false);
      }
      if (!createMode) await configuration.refetch();
      try {
        const result = await api.testModelProvider(tenantId, projectId, requestBody);
        setNotice(
          result.readinessUpdated
            ? `配置保存成功，连接检测成功：${result.modelName} 已就绪。`
            : "配置保存成功，但就绪状态尚未更新，请稍后重新检测。",
        );
      } catch (error) {
        setNotice(`配置保存成功，但自动连接检测失败：${error instanceof Error ? error.message : "未知错误"}`);
      }
      await onSaved();
    },
    onError: (error) => setNotice(`保存失败：${error.message}`),
  });
  return <section className="space-y-4 rounded-xl border border-gray-200 p-4 dark:border-gray-800" aria-labelledby="model-provider-title">
    <div><h3 id="model-provider-title" className="font-semibold text-gray-900 dark:text-white">模型 API 连接</h3><p className="mt-1 text-xs text-gray-500">保存后会自动调用模型检测连接；能正常响应即标记为可调用。再次打开时可点击眼睛查看 API Key。</p></div>
    <div className="grid gap-4 md:grid-cols-2">
      <label className="text-sm font-medium text-gray-700 dark:text-gray-300 md:col-span-2">显示名称<input aria-label="模型显示名称" className={`mt-2 ${fieldClass}`} value={displayName} onChange={(event) => { setDisplayName(event.target.value); setNotice(""); }} placeholder="可选，默认使用 ModelName" /></label>
      <label className="text-sm font-medium text-gray-700 dark:text-gray-300 md:col-span-2">API URL<input aria-label="模型 API URL" className={`mt-2 ${fieldClass}`} value={providerUrl} onChange={(event) => { setProviderUrl(event.target.value); setNotice(""); }} placeholder="https://api.example.com/v1" /></label>
      <label className="text-sm font-medium text-gray-700 dark:text-gray-300">ModelName<input aria-label="模型名称" className={`mt-2 ${fieldClass}`} value={modelName} onChange={(event) => { setModelName(event.target.value); setNotice(""); }} placeholder="gpt-4.1-mini" /></label>
      <div className="text-sm font-medium text-gray-700 dark:text-gray-300">
        <span>API Key</span>
        <div className="relative mt-2">
          <input
            aria-label="模型 API Key"
            type={showingConfiguredMask || !showApiKey ? "password" : "text"}
            autoComplete="new-password"
            className={`${fieldClass} pr-11`}
            value={showingConfiguredMask ? CONFIGURED_API_KEY_MASK : apiKey}
            onFocus={() => {
              if (showingConfiguredMask) {
                setEditingKey(true);
                setShowApiKey(false);
              }
            }}
            onBlur={() => {
              if (!apiKey) {
                setEditingKey(false);
                setShowApiKey(false);
              }
            }}
            onChange={(event) => {
              setEditingKey(true);
              setApiKey(event.target.value === CONFIGURED_API_KEY_MASK ? "" : event.target.value);
              setNotice("");
            }}
            placeholder={apiKeyConfigured ? "输入新密钥以覆盖" : "请输入 API Key"}
          />
          <button
            type="button"
            className="absolute right-1.5 top-1/2 grid size-7 -translate-y-1/2 place-items-center rounded-md text-gray-500 hover:bg-gray-100 hover:text-gray-700 disabled:pointer-events-none disabled:opacity-40 dark:hover:bg-gray-800 dark:hover:text-gray-200"
            aria-label={showingConfiguredMask ? "显示已保存 API Key" : showApiKey ? "隐藏 API Key" : "显示 API Key"}
            title={showingConfiguredMask ? "显示已保存 API Key" : showApiKey ? "隐藏 API Key" : "显示 API Key"}
            disabled={reveal.isPending || (!apiKey && !showingConfiguredMask)}
            onClick={() => {
              if (showingConfiguredMask) reveal.mutate();
              else setShowApiKey((value) => !value);
            }}
          >
            {showApiKey && !showingConfiguredMask ? <Eye className="size-4" aria-hidden="true" /> : <EyeOff className="size-4" aria-hidden="true" />}
          </button>
        </div>
        {apiKey ? (
          <p className="mt-1 text-xs font-normal text-gray-500">当前 API Key 已载入；可点击眼睛显示或隐藏。</p>
        ) : apiKeyConfigured ? (
          <p className="mt-1 text-xs font-normal text-gray-500">API Key 已保存；点击眼睛即可查看。</p>
        ) : null}
      </div>
    </div>
    {!createMode && configuration.isError ? <p role="alert" className="text-sm text-error-600">读取配置失败：{configuration.error.message}</p> : null}
    {notice ? <p role="status" className={`rounded-lg p-3 text-sm ${notice.startsWith("连接失败") || notice.startsWith("保存失败") || notice.startsWith("读取失败") || notice.includes("自动连接检测失败") ? "bg-error-50 text-error-600" : "bg-success-50 text-success-700"}`}>{notice}</p> : null}
    <div className="flex flex-wrap justify-end gap-2"><Button variant="outline" onClick={() => test.mutate(body())} loading={test.isPending} disabled={!canSubmit || save.isPending}><PlugZap />重新检测</Button><Button onClick={() => save.mutate(body())} loading={save.isPending} disabled={!canSubmit || test.isPending}><Save />{createMode ? "创建并保存" : "保存并检测"}</Button>{notice.includes("已就绪") ? <CheckCircle2 className="mt-2 size-5 text-success-500" aria-hidden="true" /> : null}</div>
  </section>;
}

function modelCardSubtitle(item: CapabilitySummary): string | null {
  const match = /^项目模型配置 · (.+)$/.exec(item.description.trim());
  const modelName = match?.[1]?.trim();
  if (!modelName) return null;
  const title = capabilityDisplayName(item);
  return modelName === title ? null : modelName;
}

function CapabilityCard({ item, selected, onSelect, onConfigure }: { item: CapabilitySummary; selected: boolean; onSelect: () => void; onConfigure?: () => void }) {
  const Icon = item.kind === "agent" ? Bot : item.kind === "model" ? Cpu : item.kind === "policy" ? ShieldCheck : Wrench;
  const riskColor = item.risk === "LOW" ? "success" : item.risk === "HIGH" || item.risk === "CRITICAL" ? "error" : "warning";
  const title = capabilityDisplayName(item);
  const modelSubtitle = item.kind === "model" ? modelCardSubtitle(item) : null;
  if (item.kind === "model") {
    return <article className={`flex flex-col rounded-2xl border bg-white shadow-theme-xs transition dark:bg-gray-900 ${selected ? "border-brand-500 ring-3 ring-brand-500/10" : "border-gray-200 hover:border-brand-300 dark:border-gray-800"}`}><button type="button" onClick={onSelect} className="min-w-0 flex-1 p-5 text-left"><span className="flex items-start justify-between gap-3"><span className="grid size-11 place-items-center rounded-xl bg-brand-50 text-brand-500 dark:bg-brand-500/15"><Icon /></span><Badge color={item.readiness.status === "READY" ? "success" : "warning"}>{item.readiness.status === "READY" ? "可调用" : "未就绪"}</Badge></span><span className="mt-4 block font-semibold text-gray-900 dark:text-white">{title}</span>{modelSubtitle ? <span className="mt-1 block text-sm text-gray-500">{modelSubtitle}</span> : null}</button></article>;
  }
  return <article className={`flex flex-col rounded-2xl border bg-white shadow-theme-xs transition dark:bg-gray-900 ${selected ? "border-brand-500 ring-3 ring-brand-500/10" : "border-gray-200 hover:border-brand-300 dark:border-gray-800"}`}><button type="button" onClick={onSelect} className="min-w-0 flex-1 p-5 text-left"><span className="flex items-start justify-between gap-3"><span className="grid size-11 place-items-center rounded-xl bg-brand-50 text-brand-500 dark:bg-brand-500/15"><Icon /></span><Badge color={item.readiness.status === "READY" ? "success" : "warning"}>{item.readiness.status === "READY" ? "可用" : "未就绪"}</Badge></span><span className="mt-4 block font-semibold text-gray-900 dark:text-white">{title}</span><span className="mt-1 line-clamp-2 block min-h-10 text-sm text-gray-500">{item.description}</span><span className="mt-4 flex items-center gap-2 text-xs"><Badge color="neutral">{item.source === "system" ? "系统内置" : item.source === "project" ? "项目创建" : item.source}</Badge>{item.risk ? <Badge color={riskColor}>{item.risk} 风险</Badge> : null}</span></button>{onConfigure ? <div className="border-t border-gray-100 px-5 py-2 dark:border-gray-800"><button type="button" aria-label={`编辑 ${title} 配置`} className="inline-flex items-center gap-2 py-1 text-sm font-medium text-brand-500 hover:text-brand-600" onClick={onConfigure}><Settings2 className="size-4" />编辑配置</button></div> : null}</article>;
}

function InputForm({ properties, input, jsonInput, onInput, onJsonInput }: { properties: Array<[string, Record<string, unknown>]> | null; input: Record<string, unknown>; jsonInput: string; onInput: (value: Record<string, unknown>) => void; onJsonInput: (value: string) => void }) {
  if (!properties) return <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">运行输入（JSON）<textarea aria-label="运行输入 JSON" className="mt-2 min-h-44 w-full rounded-xl border border-gray-300 bg-transparent p-3 font-mono text-xs dark:border-gray-700" value={jsonInput} onChange={(event) => onJsonInput(event.target.value)} /></label>;
  if (!properties.length) return <p className="rounded-lg bg-gray-50 p-3 text-sm text-gray-500 dark:bg-gray-800">此能力无需输入参数。</p>;
  return <div className="grid gap-4 md:grid-cols-2">{properties.map(([name, schema]) => <label key={name} className="text-sm font-medium text-gray-700 dark:text-gray-300">{textValue(schema["title"], name)}{schema["type"] === "boolean" ? <select className={`mt-2 ${fieldClass}`} value={input[name] === true ? "true" : "false"} onChange={(event) => onInput({ ...input, [name]: event.target.value === "true" })}><option value="false">否</option><option value="true">是</option></select> : <input className={`mt-2 ${fieldClass}`} type={schema["type"] === "number" || schema["type"] === "integer" ? "number" : "text"} value={textValue(input[name])} onChange={(event) => onInput({ ...input, [name]: schema["type"] === "number" || schema["type"] === "integer" ? Number(event.target.value) : event.target.value })} />}</label>)}</div>;
}

function simpleSchemaProperties(schema: Record<string, unknown> | null | undefined): Array<[string, Record<string, unknown>]> | null {
  if (!schema || schema["type"] !== "object") return null;
  const properties = schema["properties"];
  if (!properties || typeof properties !== "object" || Array.isArray(properties)) return [];
  const entries = Object.entries(properties as Record<string, unknown>);
  return entries.every(([, value]) => value && typeof value === "object" && !Array.isArray(value) && ["string", "number", "integer", "boolean"].includes(String((value as Record<string, unknown>)["type"]))) ? entries as Array<[string, Record<string, unknown>]> : null;
}

function schemaDefaults(schema: Record<string, unknown> | null | undefined): Record<string, unknown> {
  const properties = schema?.["properties"];
  if (!properties || typeof properties !== "object" || Array.isArray(properties)) return {};
  return Object.fromEntries(Object.entries(properties as Record<string, unknown>).flatMap(([name, value]) => {
    if (!value || typeof value !== "object" || Array.isArray(value) || !("default" in value)) return [];
    return [[name, (value as Record<string, unknown>)["default"]]];
  }));
}

function textValue(value: unknown, fallback = ""): string {
  return typeof value === "string" || typeof value === "number" ? String(value) : fallback;
}
