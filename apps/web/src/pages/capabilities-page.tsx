import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Bot, Copy, Cpu, Network, Play, Plus, RefreshCw, Search, Settings2, ShieldCheck, Trash2, Wrench } from "lucide-react";
import * as React from "react";
import { useNavigate } from "react-router";
import { api } from "@/api/client";
import type { CapabilityKind, CapabilityPreset, CapabilitySummary, ReadinessReasonCode } from "@/api/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useWorkspaceScope } from "@/lib/demo-scope";

const fieldClass = "h-10 w-full rounded-lg border border-gray-300 bg-transparent px-3 text-sm outline-none focus:border-brand-500 dark:border-gray-700";
const kindLabels: Record<CapabilityKind, string> = { agent: "智能体", tool: "工具", model: "模型", policy: "策略" };
const pageDescriptions: Record<CapabilityKind, string> = {
  agent: "选择已就绪智能体直接运行，或基于内置版本创建可编辑的项目配置。",
  tool: "选择已就绪工具直接运行，或保存参数为我的预设。",
  model: "选择已就绪模型直接运行，或保存参数为我的预设。",
  policy: "查看策略的就绪状态，或保存参数为我的预设。",
};
const reasonLabels: Record<ReadinessReasonCode, string> = {
  EXECUTOR_MISSING: "缺少执行器", ADAPTER_MISSING: "智能体适配器不可用", MODEL_ROUTE_MISSING: "缺少模型路由",
  SECRET_MISSING: "凭证不可用", DEPENDENCY_NOT_READY: "依赖能力未就绪", DEPENDENCY_CYCLE: "依赖形成循环",
  HEALTH_CHECK_FAILED: "健康检查失败", ENVIRONMENT_NOT_ALLOWED: "当前环境不允许", CAPABILITY_PACK_DISABLED: "业务能力包未启用",
  SCHEMA_INVALID: "参数结构无效", POLICY_DENIED: "策略不允许使用",
};

export function AgentCapabilitiesPage() { return <CapabilitiesPage kind="agent" />; }
export function ToolCapabilitiesPage() { return <CapabilitiesPage kind="tool" />; }
export function ModelCapabilitiesPage() { return <CapabilitiesPage kind="model" />; }
export function PolicyCapabilitiesPage() { return <CapabilitiesPage kind="policy" />; }

export function CapabilitiesPage({ kind }: { kind: CapabilityKind }) {
  const { tenantId, projectId, workspacePath } = useWorkspaceScope();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [search, setSearch] = React.useState("");
  const [showNotReady, setShowNotReady] = React.useState(false);
  const [selected, setSelected] = React.useState<CapabilitySummary>();
  const [input, setInput] = React.useState<Record<string, unknown>>({});
  const [jsonInput, setJsonInput] = React.useState("{}");
  const [formError, setFormError] = React.useState("");
  const [presetName, setPresetName] = React.useState("");
  const [selectedPresetId, setSelectedPresetId] = React.useState("");
  const query = useQuery({ queryKey: ["capability-center", tenantId, projectId], queryFn: () => api.getCapabilityCenter(tenantId, projectId) });
  const presets = useQuery({ queryKey: ["capability-presets", tenantId, projectId], queryFn: () => api.listPresets(tenantId, projectId) });
  const filtered = React.useMemo(() => (query.data?.items ?? []).filter((item) => {
    if (!showNotReady && item.readiness.status !== "READY") return false;
    if (item.kind !== kind) return false;
    const needle = search.trim().toLowerCase();
    return !needle || `${item.name} ${item.description} ${item.ref}`.toLowerCase().includes(needle);
  }), [kind, query.data?.items, search, showNotReady]);
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
    <header className="flex flex-wrap items-end justify-between gap-4"><div><p className="text-sm font-medium text-brand-500">能力中心</p><h1 className="mt-1 text-2xl font-semibold text-gray-900 dark:text-white">{kindLabels[kind]}</h1><p className="mt-1 text-sm text-gray-500">{pageDescriptions[kind]}</p></div><div className="flex flex-wrap gap-2"><Button variant="outline" onClick={() => void Promise.all([query.refetch(), presets.refetch()])} loading={query.isFetching || presets.isFetching}><RefreshCw />刷新</Button>{kind === "agent" ? <Button onClick={() => void navigate(`${workspacePath}/agents/configure?new=1`)}><Plus />创建智能体</Button> : null}</div></header>
    <Card><CardContent className="grid gap-3 pt-5 md:grid-cols-[minmax(0,1fr)_auto]"><label className="relative"><Search className="absolute left-3 top-2.5 size-5 text-gray-400" /><input aria-label={`搜索${kindLabels[kind]}`} className={`${fieldClass} pl-10`} value={search} onChange={(event) => setSearch(event.target.value)} placeholder={`搜索${kindLabels[kind]}名称或用途`} /></label><label className="flex items-center gap-2 whitespace-nowrap text-sm text-gray-600"><input type="checkbox" checked={showNotReady} onChange={(event) => setShowNotReady(event.target.checked)} />显示未就绪</label></CardContent></Card>
    {query.isPending ? <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">{[1, 2, 3].map((item) => <Skeleton key={item} className="h-52" />)}</div> : null}
    {query.isError ? <Card><CardContent className="py-12 text-center text-error-600">无法加载能力中心：{query.error.message}</CardContent></Card> : null}
    {!query.isPending && !query.isError && !filtered.length ? <Card><CardContent className="py-12 text-center text-sm text-gray-500">当前筛选条件下没有可显示的能力。</CardContent></Card> : null}
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">{filtered.map((item) => <CapabilityCard key={item.ref} item={item} selected={selected?.ref === item.ref} onSelect={() => choose(item)} onConfigure={item.kind === "agent" ? () => void navigate(`${workspacePath}/agents/configure?copy=${encodeURIComponent(item.ref)}`) : undefined} />)}</div>
    {selected ? <Card><CardHeader><div><CardTitle>{selected.name}</CardTitle><p className="mt-1 text-sm text-gray-500">{selected.description}</p></div><Badge color={selected.readiness.status === "READY" ? "success" : "warning"}>{selected.readiness.status === "READY" ? "可用" : "未就绪"}</Badge></CardHeader><CardContent className="space-y-5">
      {selected.readiness.reasons.length ? <ul className="rounded-xl bg-warning-50 p-4 text-sm text-warning-700 dark:bg-warning-500/10">{selected.readiness.reasons.map((reason) => <li key={`${reason.code}-${reason.dependencyRef ?? ""}`}>{reasonLabels[reason.code]}{reason.dependencyRef ? `：${reason.dependencyRef}` : ""}</li>)}</ul> : null}
      {kind === "agent" ? <p className="rounded-xl bg-brand-50 p-3 text-sm text-brand-700 dark:bg-brand-500/10 dark:text-brand-200">系统内置版本保持只读。“编辑配置”会复制当前模型、工具和提示词，创建可独立修改的项目配置。</p> : null}
      <InputForm properties={simpleProperties} input={input} jsonInput={jsonInput} onInput={setInput} onJsonInput={setJsonInput} />
      <section className="space-y-3" aria-labelledby="preset-title"><div><h3 id="preset-title" className="font-semibold text-gray-900 dark:text-white">我的预设</h3><p className="text-sm text-gray-500">预设只保存可复用参数，不保存凭证。</p></div>{capabilityPresets.length ? <div className="flex flex-wrap gap-2">{capabilityPresets.map((preset) => <span key={preset.presetId} className="inline-flex items-center rounded-lg border border-gray-200 dark:border-gray-700"><button type="button" className="px-3 py-2 text-sm" onClick={() => loadPreset(preset)}>{preset.name}</button><button type="button" aria-label={`复制预设 ${preset.name}`} className="p-2 text-gray-400 hover:text-brand-500" onClick={() => copyPreset.mutate(preset)}><Copy className="size-4" /></button><button type="button" aria-label={`删除预设 ${preset.name}`} className="p-2 text-gray-400 hover:text-error-500" onClick={() => deletePreset.mutate(preset.presetId)}><Trash2 className="size-4" /></button></span>)}</div> : <p className="text-sm text-gray-500">尚未保存预设。</p>}<div className="flex flex-wrap gap-2"><input aria-label="预设名称" className={`${fieldClass} max-w-sm`} value={presetName} onChange={(event) => setPresetName(event.target.value)} placeholder="例如：日报检索" /><Button variant="outline" onClick={() => savePreset.mutate()} loading={savePreset.isPending} disabled={!presetName.trim()}>{selectedPresetId ? null : <Plus />}{selectedPresetId ? "更新预设" : "保存预设"}</Button>{selectedPresetId ? <Button variant="ghost" onClick={() => { setSelectedPresetId(""); setPresetName(""); }}>取消编辑</Button> : null}</div></section>
      {formError ? <p role="alert" className="rounded-lg bg-error-50 p-3 text-sm text-error-600">{formError}</p> : null}
      <div className="flex flex-wrap justify-end gap-2">{kind === "agent" ? <Button aria-label="编辑当前智能体配置" variant="outline" onClick={() => void navigate(`${workspacePath}/agents/configure?copy=${encodeURIComponent(selected.ref)}`)}><Settings2 />编辑配置</Button> : null}<Button variant="outline" onClick={addToCanvas} disabled={selected.readiness.status !== "READY"}><Network />加入画布</Button><Button onClick={() => run.mutate()} loading={run.isPending} disabled={selected.readiness.status !== "READY"}><Play />立即运行</Button></div>
      <details className="rounded-xl border border-gray-200 p-4 text-sm dark:border-gray-800"><summary className="cursor-pointer font-medium">高级详情</summary><pre className="mt-3 max-h-80 overflow-auto whitespace-pre-wrap text-xs text-gray-500">{JSON.stringify({ ref: selected.ref, source: selected.source, risk: selected.risk, inputSchema: selected.inputSchema, outputSchema: selected.outputSchema }, null, 2)}</pre></details>
    </CardContent></Card> : null}
  </div>;
}

function CapabilityCard({ item, selected, onSelect, onConfigure }: { item: CapabilitySummary; selected: boolean; onSelect: () => void; onConfigure?: () => void }) {
  const Icon = item.kind === "agent" ? Bot : item.kind === "model" ? Cpu : item.kind === "policy" ? ShieldCheck : Wrench;
  return <article className={`flex flex-col rounded-2xl border bg-white shadow-theme-xs transition dark:bg-gray-900 ${selected ? "border-brand-500 ring-3 ring-brand-500/10" : "border-gray-200 hover:border-brand-300 dark:border-gray-800"}`}><button type="button" onClick={onSelect} className="min-w-0 flex-1 p-5 text-left"><span className="flex items-start justify-between gap-3"><span className="grid size-11 place-items-center rounded-xl bg-brand-50 text-brand-500 dark:bg-brand-500/15"><Icon /></span><Badge color={item.readiness.status === "READY" ? "success" : "warning"}>{item.readiness.status === "READY" ? "可用" : "未就绪"}</Badge></span><span className="mt-4 block font-semibold text-gray-900 dark:text-white">{item.name}</span><span className="mt-1 line-clamp-2 block min-h-10 text-sm text-gray-500">{item.description}</span><span className="mt-4 flex items-center gap-2 text-xs text-gray-400"><span>{kindLabels[item.kind]}</span><span>·</span><span>{item.source === "system" ? "系统内置" : item.source}</span>{item.risk ? <><span>·</span><span>{item.risk} 风险</span></> : null}</span></button>{onConfigure ? <div className="border-t border-gray-100 px-5 py-2 dark:border-gray-800"><button type="button" aria-label={`编辑 ${item.name} 配置`} className="inline-flex items-center gap-2 py-1 text-sm font-medium text-brand-500 hover:text-brand-600" onClick={onConfigure}><Settings2 className="size-4" />编辑配置</button></div> : null}</article>;
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
