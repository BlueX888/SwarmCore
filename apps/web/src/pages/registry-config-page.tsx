import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Bot, Boxes, Check, Copy, Cpu, Network, Plus, RefreshCw, Save, Trash2, Wrench } from "lucide-react";
import * as React from "react";
import { Link, useNavigate, useSearchParams } from "react-router";
import { api } from "@/api/client";
import type { AgentCapability, CapabilityCatalog, ConfigurationKind, CreateSavedConfiguration, SavedConfiguration, ToolCapability } from "@/api/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useWorkspaceScope } from "@/lib/demo-scope";
import { filesystemToolInputError } from "@/lib/filesystem-tool-config";

const fieldClass = "mt-1 h-11 w-full rounded-lg border border-gray-300 bg-transparent px-3 text-sm outline-none focus:border-brand-500 dark:border-gray-700";
const textAreaClass = "mt-1 min-h-28 w-full rounded-lg border border-gray-300 bg-transparent p-3 text-sm outline-none focus:border-brand-500 dark:border-gray-700";

export function AgentConfigurationPage() {
  const [searchParams] = useSearchParams();
  const copyRef = searchParams.get("copy") ?? "";
  const configurationId = searchParams.get("configuration") ?? "";
  return <ConfigurationShell
    kind="agent"
    icon={<Bot />}
    title="智能体配置"
    description="编辑提示词、逻辑模型和可用工具，保存为当前项目可复用的版本化配置。"
    editorOnly
    initialSelectedId={configurationId}
  >
    {(catalog, selected, save, saving, saveNotice) => <AgentConfigurator key={(selected?.configurationId ?? copyRef) || "new"} catalog={catalog} initial={selected} copyFrom={selected ? undefined : catalog.agents.find((item) => item.id === copyRef)} onSave={save} saving={saving} submitLabel={selected ? "保存修改" : "创建智能体"} saveNotice={saveNotice} />}
  </ConfigurationShell>;
}

export function ToolConfigurationPage({ initialCreate = false }: { initialCreate?: boolean }) {
  return <ConfigurationShell
    kind="tool"
    icon={<Wrench />}
    title={initialCreate ? "新建工具" : "工具配置"}
    description="从平台受控工具中选择能力，填写当前项目的默认参数，保存为可复用工具。"
    initialCreate={initialCreate}
  >
    {(catalog, selected, save, saving, saveNotice) => <ToolConfigurator key={selected?.configurationId ?? "new"} catalog={catalog} initial={selected} onSave={save} saving={saving} submitLabel={selected ? "保存修改" : "创建工具配置"} saveNotice={saveNotice} />}
  </ConfigurationShell>;
}

export function ModelConfigurationPage() {
  return <ConfigurationShell
    kind="model"
    icon={<Cpu />}
    title="模型配置"
    description="选择可用逻辑模型，确认运行时和环境，并生成策略默认模型配置。"
  >
    {(catalog, selected, save, saving, saveNotice) => <ModelConfigurator key={selected?.configurationId ?? "new"} catalog={catalog} initial={selected} onSave={save} saving={saving} submitLabel={selected ? "保存修改" : "创建模型配置"} saveNotice={saveNotice} />}
  </ConfigurationShell>;
}

function ConfigurationShell({ kind, icon, title, description, initialCreate = false, editorOnly = false, initialSelectedId = "", children }: { kind: ConfigurationKind; icon: React.ReactNode; title: string; description: string; initialCreate?: boolean; editorOnly?: boolean; initialSelectedId?: string; children: (catalog: CapabilityCatalog, selected: SavedConfiguration | undefined, save: (body: CreateSavedConfiguration) => void, saving: boolean, saveNotice: string) => React.ReactNode }) {
  const { tenantId, projectId, workspacePath } = useWorkspaceScope();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [notice, setNotice] = React.useState("");
  const [selectedId, setSelectedId] = React.useState(initialSelectedId || (initialCreate || editorOnly ? "new" : ""));
  const query = useQuery({ queryKey: ["capabilities", tenantId, projectId], queryFn: () => api.getCapabilities(tenantId, projectId) });
  const savedQuery = useQuery({ queryKey: ["saved-configurations", tenantId, projectId, kind], queryFn: () => api.listConfigurations(tenantId, projectId, kind) });
  const items = React.useMemo(() => savedQuery.data?.items ?? [], [savedQuery.data?.items]);
  const selected = items.find((item) => item.configurationId === selectedId);
  const itemLabel = { agent: "智能体", tool: "工具", model: "模型" }[kind];
  const editing = selectedId === "new" || Boolean(selected);
  const saveMutation = useMutation({
    mutationFn: (body: CreateSavedConfiguration) => selected
      ? api.updateConfiguration(tenantId, projectId, kind, selected.configurationId, body)
      : api.createConfiguration(tenantId, projectId, kind, body),
    onSuccess: async (saved) => {
      setNotice(selected ? `“${saved.name}”的修改已保存。` : `“${saved.name}”已创建。`);
      await queryClient.invalidateQueries({ queryKey: ["saved-configurations", tenantId, projectId, kind] });
      await queryClient.invalidateQueries({ queryKey: ["capability-center", tenantId, projectId] });
      if (kind === "agent" && !selected) {
        void navigate(`${workspacePath}/agents`);
        return;
      }
      setSelectedId(selected || editorOnly ? saved.configurationId : "");
    },
    onError: (error) => setNotice(`保存失败：${error.message}`),
  });
  const deleteMutation = useMutation({
    mutationFn: (configurationId: string) => api.deleteConfiguration(tenantId, projectId, kind, configurationId),
    onSuccess: async (_, configurationId) => {
      setNotice("配置已删除。");
      if (selectedId === configurationId) setSelectedId("");
      await queryClient.invalidateQueries({ queryKey: ["saved-configurations", tenantId, projectId, kind] });
    },
    onError: (error) => setNotice(`删除失败：${error.message}`),
  });
  const refresh = () => void Promise.all([query.refetch(), savedQuery.refetch()]);
  const startCreating = () => {
    setNotice("");
    setSelectedId("new");
  };
  return <div className="min-w-0 space-y-6">
    <div className="flex flex-wrap items-end justify-between gap-4">
      <div className="flex items-start gap-3"><span className="mt-1 grid size-11 shrink-0 place-items-center rounded-xl bg-brand-50 text-brand-500 dark:bg-brand-500/15">{icon}</span><div><p className="text-sm font-medium text-brand-500">构建</p><h1 className="mt-1 text-2xl font-semibold text-gray-900 dark:text-white">{title}</h1><p className="mt-1 max-w-3xl text-sm text-gray-500">{description}</p></div></div>
      {editorOnly ? <div className="flex flex-wrap gap-2"><Button variant="outline" onClick={refresh} loading={query.isFetching || savedQuery.isFetching}><RefreshCw />刷新</Button><Button asChild variant="outline"><Link to={`${workspacePath}/agents`}><ArrowLeft />返回智能体</Link></Button></div> : <div className="flex flex-wrap gap-2"><Button variant="outline" onClick={refresh} loading={query.isFetching || savedQuery.isFetching}><RefreshCw />刷新</Button><Button asChild variant="outline"><Link to={`${workspacePath}/${kind === "tool" ? "tools" : kind === "model" ? "models" : "agents"}`}><Boxes />能力目录</Link></Button><Button asChild variant="outline"><Link to={`${workspacePath}/canvas`}><Network />打开画布</Link></Button><Button onClick={startCreating}><Plus />新建{itemLabel}配置</Button></div>}
    </div>
    <p className="rounded-xl border border-warning-200 bg-warning-50 p-3 text-sm text-warning-700 dark:border-warning-500/30 dark:bg-warning-500/10">{kind === "agent" ? "系统内置智能体保持只读；创建后会生成当前项目的版本化智能体能力，并在执行时由 Agno Adapter 实例化。" : kind === "tool" ? "平台工具目录保持只读；新建工具会保存当前项目的名称和默认参数，不会修改工具执行器或系统注册表。" : "内置能力目录保持只读；你在这里保存的是当前项目可复用的配置，不会修改系统注册表。"}</p>
    {notice && !editing ? <p role="status" className="rounded-xl bg-brand-50 p-3 text-sm text-brand-700 dark:bg-brand-500/10 dark:text-brand-200">{notice}</p> : null}
    {editorOnly ? <div className="min-w-0 space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3 rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-800 dark:bg-gray-900"><div><h2 className="font-semibold text-gray-900 dark:text-white">{selected ? `编辑“${selected.name}”` : "新建智能体配置"}</h2><p className="mt-1 text-sm text-gray-500">直接编辑并保存；此页面不再重复展示能力目录。</p></div><label className="text-sm font-medium text-gray-700 dark:text-gray-300">打开已有配置<select aria-label="打开已有智能体配置" className={`${fieldClass} min-w-64`} value={selectedId} onChange={(event) => { setNotice(""); setSelectedId(event.target.value); }}><option value="new">新建智能体配置</option>{items.map((item) => <option key={item.configurationId} value={item.configurationId}>{item.name}</option>)}</select></label></div>
      {savedQuery.isError ? <p role="alert" className="rounded-xl bg-error-50 p-3 text-sm text-error-600">无法加载已有配置：{savedQuery.error.message}</p> : null}
      {query.isPending ? <Skeleton className="h-[520px]" /> : null}
      {query.isError ? <Card><CardContent className="flex min-h-60 flex-col items-center justify-center gap-3 pt-5 text-center"><p className="font-medium text-error-600">无法加载能力配置</p><p className="text-sm text-gray-500">{query.error.message}</p><Button onClick={() => void query.refetch()}>重试</Button></CardContent></Card> : null}
      {query.data && (selected || selectedId === "new") ? children(query.data, selected, (body) => saveMutation.mutate(body), saveMutation.isPending, notice) : null}
    </div> : !editing ? <div className="space-y-8"><RuntimeCapabilityLibrary kind={kind} catalog={query.data} loading={query.isPending} error={query.error?.message} /><ConfigurationLibrary itemLabel={itemLabel} itemIcon={icon} items={items} loading={savedQuery.isPending} error={savedQuery.error?.message} deleting={deleteMutation.isPending} onSelect={setSelectedId} onDelete={(configurationId) => deleteMutation.mutate(configurationId)} /></div> : <div className="min-w-0 space-y-5">
      <div className="flex flex-wrap items-center gap-3">
        <Button variant="outline" onClick={() => setSelectedId("")}><ArrowLeft />返回已配置{itemLabel}</Button>
        <div><h2 className="font-semibold text-gray-900 dark:text-white">{selected ? `编辑“${selected.name}”` : `新建${itemLabel}配置`}</h2><p className="mt-1 text-sm text-gray-500">{selected ? "修改参数后保存，将更新当前配置。" : "填写参数并保存后，配置会出现在列表中。"}</p></div>
      </div>
      <div className="min-w-0">
        {query.isPending ? <Skeleton className="h-[520px]" /> : null}
        {query.isError ? <Card><CardContent className="flex min-h-60 flex-col items-center justify-center gap-3 pt-5 text-center"><p className="font-medium text-error-600">无法加载能力配置</p><p className="text-sm text-gray-500">{query.error.message}</p><Button onClick={() => void query.refetch()}>重试</Button></CardContent></Card> : null}
        {query.data && (selected || selectedId === "new") ? children(query.data, selected, (body) => saveMutation.mutate(body), saveMutation.isPending, notice) : null}
      </div>
    </div>}
  </div>;
}

function AgentConfigurator({ catalog, initial, copyFrom, onSave, saving, submitLabel, saveNotice }: ConfiguratorProps & { copyFrom?: AgentCapability }) {
  const savedSpec = asObject(initial?.configuration["spec"]);
  const savedAgents = asObject(savedSpec["agents"]);
  const savedEntry = Object.entries(savedAgents)[0];
  const savedAgent = asObject(savedEntry?.[1]);
  const savedTools = stringArray(savedAgent["tools"]);
  const hasCopyDefinition = Boolean(copyFrom?.role && copyFrom.instructions && copyFrom.model);
  const [name, setName] = React.useState(initial?.name ?? (copyFrom?.role ? `${copyFrom.role} 项目配置` : "我的智能体"));
  const [source, setSource] = React.useState(initial ? (initial.sourceRef.startsWith("agent://") ? initial.sourceRef : "inline") : "inline");
  const [nodeKey, setNodeKey] = React.useState(savedEntry?.[0] ?? agentNodeKey(copyFrom?.role));
  const [role, setRole] = React.useState(stringValue(savedAgent["role"], copyFrom?.role ?? "执行助手"));
  const [instructions, setInstructions] = React.useState(stringValue(savedAgent["instructions"], copyFrom?.instructions ?? "完成分配的任务，并返回结构化结果。"));
  const [model, setModel] = React.useState(stringValue(savedAgent["model"], copyFrom?.model ?? (initial ? "" : catalog.models[0]?.ref ?? "")));
  const [tools, setTools] = React.useState<string[]>(savedTools.length ? savedTools : copyFrom?.tools ?? []);
  const selectedSource = source || "inline";
  const selectedModel = model || catalog.models[0]?.ref || "";
  const capability = catalog.agents.find((item) => item.id === selectedSource);
  const registered = selectedSource.startsWith("agent://");
  const validKey = /^[a-z][a-z0-9_-]*$/.test(nodeKey);
  const agentDeclaration = registered
    ? { ref: selectedSource }
    : { role, instructions, ...(selectedModel ? { model: selectedModel } : {}), ...(tools.length ? { tools } : {}) };
  const preview = {
    spec: {
      agents: { [nodeKey]: agentDeclaration },
      graph: { entrypoint: nodeKey, nodes: { [nodeKey]: { type: "agent", agent: nodeKey, dependsOn: [] } } },
    },
  };
  const toggleTool = (ref: string) => setTools((current) => current.includes(ref) ? current.filter((item) => item !== ref) : [...current, ref]);
  return <div className="grid min-w-0 gap-5 xl:grid-cols-[minmax(0,.9fr)_minmax(0,1.1fr)]">
    <Card><CardHeader><CardTitle>智能体定义</CardTitle><span className="text-xs text-gray-500">{catalog.registrySnapshot.slice(0, 18)}</span></CardHeader><CardContent className="space-y-5">
      {copyFrom && hasCopyDefinition ? <p className="rounded-xl bg-brand-50 p-3 text-sm text-brand-700 dark:bg-brand-500/10 dark:text-brand-200">已从“{copyFrom.role}”复制模型、工具和提示词；保存后会成为独立配置。</p> : null}
      {copyFrom && !hasCopyDefinition ? <p className="rounded-xl bg-warning-50 p-3 text-sm text-warning-700 dark:bg-warning-500/10">当前服务尚未返回该智能体的完整定义，已打开空白配置；刷新后可重试复制。</p> : null}
      <Field label="配置名称"><input aria-label="配置名称" className={fieldClass} value={name} onChange={(event) => setName(event.target.value)} /></Field>
      <Field label="智能体来源"><select aria-label="智能体来源" className={fieldClass} value={selectedSource} onChange={(event) => setSource(event.target.value)}><option value="inline">内联智能体声明</option>{catalog.agents.filter((item) => item.id.startsWith("agent://")).map((item) => <option key={item.id} value={item.id}>{item.id}</option>)}</select></Field>
      <Field label="节点标识" hint="小写字母开头，可使用数字、短横线和下划线"><input className={fieldClass} value={nodeKey} onChange={(event) => setNodeKey(event.target.value)} />{validKey ? null : <p role="alert" className="mt-1 text-xs text-error-600">节点标识格式无效。</p>}</Field>
      {registered ? <InfoGrid items={[["运行时", capability?.runtime ?? "—"], ["可用环境", capability?.environments.join("、") || "—"]]} /> : <>
        <section className="space-y-4 rounded-xl border border-gray-200 p-4 dark:border-gray-800"><div><h3 className="font-semibold text-gray-900 dark:text-white">提示词</h3><p className="mt-1 text-xs text-gray-500">这里定义稳定的系统指令；每次运行的任务输入仍在运行页填写。</p></div><Field label="角色与目标"><input aria-label="角色与目标" className={fieldClass} value={role} onChange={(event) => setRole(event.target.value)} /></Field><Field label="系统指令" hint="说明工作方式、边界和输出要求"><textarea aria-label="系统指令" className={`${textAreaClass} min-h-40`} value={instructions} onChange={(event) => setInstructions(event.target.value)} /></Field></section>
        <section className="space-y-3 rounded-xl border border-gray-200 p-4 dark:border-gray-800"><div><h3 className="font-semibold text-gray-900 dark:text-white">模型</h3><p className="mt-1 text-xs text-gray-500">选择逻辑模型（含项目创建的模型）；Provider 与凭证由模型配置统一管理。</p></div><Field label="首选逻辑模型"><select aria-label="首选逻辑模型" className={fieldClass} value={selectedModel} onChange={(event) => setModel(event.target.value)}><option value="">使用策略默认模型</option>{catalog.models.map((item) => <option key={item.ref} value={item.ref}>{item.ref}</option>)}</select></Field></section>
        <fieldset className="rounded-xl border border-gray-200 p-4 dark:border-gray-800"><legend className="px-1 font-semibold text-gray-900 dark:text-white">允许使用的工具</legend><p className="mb-3 text-xs text-gray-500">智能体只能调用这里明确授权的工具；高风险操作仍受审批策略控制。</p><div className="grid gap-2 sm:grid-cols-2">{catalog.tools.length ? catalog.tools.map((item) => <label key={item.ref} className="flex items-start gap-2 rounded-lg border border-gray-200 p-3 text-xs dark:border-gray-700"><input className="mt-0.5" type="checkbox" checked={tools.includes(item.ref)} onChange={() => toggleTool(item.ref)} /> <span className="min-w-0"><span className="block break-all font-mono">{item.ref}</span><span className="mt-1 block text-gray-400">{riskLabel(item.risk)}</span></span></label>) : <p className="text-sm text-gray-500">暂无可用工具。</p>}</div></fieldset>
      </>}
    </CardContent></Card>
    <PreviewCard title="智能体节点配置" value={preview} disabled={!name.trim() || !validKey || !selectedSource || (!registered && (!role.trim() || !instructions.trim()))} saving={saving} submitLabel={submitLabel} saveNotice={saveNotice} onSave={() => onSave({ name, sourceRef: registered ? selectedSource : "inline/agno", configuration: preview })} />
  </div>;
}

function ToolConfigurator({ catalog, initial, onSave, saving, submitLabel, saveNotice }: ConfiguratorProps) {
  const savedEntry = Object.entries(initial?.configuration ?? {})[0];
  const savedNode = asObject(savedEntry?.[1]);
  const [name, setName] = React.useState(initial?.name ?? "我的工具配置");
  const [selected, setSelected] = React.useState(initial?.sourceRef ?? "");
  const [nodeKey, setNodeKey] = React.useState(savedEntry?.[0] ?? "tool-1");
  const [inputSource, setInputSource] = React.useState(JSON.stringify(asObject(savedNode["input"]), null, 2));
  const tool = catalog.tools.find((item) => item.ref === (selected || catalog.tools[0]?.ref));
  const input = parseObject(inputSource);
  const filesystemError = tool && input.value ? filesystemToolInputError(tool.ref, input.value) : null;
  const validKey = /^[a-z][a-z0-9_-]*$/.test(nodeKey);
  const preview = { type: "tool", tool: tool?.ref ?? "", dependsOn: [], input: input.value ?? {} };
  const canSave = Boolean(name.trim() && tool && validKey && !input.error && !filesystemError);
  return <div className="grid min-w-0 gap-5 xl:grid-cols-[minmax(0,.9fr)_minmax(0,1.1fr)]">
    <div className="space-y-5"><Card><CardHeader><CardTitle>工具节点参数</CardTitle>{tool ? <RiskBadge risk={tool.risk} /> : null}</CardHeader><CardContent className="space-y-4">
      <Field label="配置名称"><input aria-label="配置名称" className={fieldClass} value={name} onChange={(event) => setName(event.target.value)} /></Field>
      <Field label="注册工具"><select aria-label="注册工具" className={fieldClass} value={tool?.ref ?? ""} onChange={(event) => setSelected(event.target.value)}>{catalog.tools.map((item) => <option key={item.ref} value={item.ref}>{item.ref}</option>)}</select></Field>
      <Field label="节点标识" hint="小写字母开头，可使用数字、短横线和下划线"><input className={fieldClass} value={nodeKey} onChange={(event) => setNodeKey(event.target.value)} />{validKey ? null : <p role="alert" className="mt-1 text-xs text-error-600">节点标识格式无效。</p>}</Field>
      <Field label="节点输入（JSON 对象）" hint={tool?.ref.startsWith("tool://filesystem/") ? "仅填写逻辑 mount 与相对路径；不能填写宿主机绝对路径或物理根目录。" : undefined}><textarea aria-label="节点输入（JSON 对象）" className={`${textAreaClass} font-mono text-xs`} value={inputSource} onChange={(event) => setInputSource(event.target.value)} />{input.error ? <p role="alert" className="mt-1 text-xs text-error-600">{input.error}</p> : null}{filesystemError ? <p role="alert" className="mt-1 text-xs text-error-600">{filesystemError}</p> : null}</Field>
    </CardContent></Card>{tool ? <ToolSchemas tool={tool} /> : <EmptyCatalog label="暂无已注册工具。" />}</div>
    <PreviewCard title="工具节点配置" value={{ [nodeKey]: preview }} disabled={!canSave} saving={saving} submitLabel={submitLabel} saveNotice={saveNotice} onSave={() => tool && onSave({ name, sourceRef: tool.ref, configuration: { [nodeKey]: preview } })} />
  </div>;
}

function ModelConfigurator({ catalog, initial, onSave, saving, submitLabel, saveNotice }: ConfiguratorProps) {
  const [name, setName] = React.useState(initial?.name ?? "我的模型配置");
  const [selected, setSelected] = React.useState(initial?.sourceRef ?? "");
  const model = catalog.models.find((item) => item.ref === (selected || catalog.models[0]?.ref));
  const preview = { spec: { defaults: { model: model?.ref ?? "" } } };
  return <div className="grid min-w-0 gap-5 xl:grid-cols-[minmax(0,.9fr)_minmax(0,1.1fr)]">
    <Card><CardHeader><CardTitle>模型参数</CardTitle><span className="text-xs text-gray-500">逻辑引用</span></CardHeader><CardContent className="space-y-4">
      <Field label="配置名称"><input aria-label="配置名称" className={fieldClass} value={name} onChange={(event) => setName(event.target.value)} /></Field>
      <Field label="逻辑模型"><select aria-label="逻辑模型" className={fieldClass} value={model?.ref ?? ""} onChange={(event) => setSelected(event.target.value)}>{catalog.models.map((item) => <option key={item.ref} value={item.ref}>{item.ref}</option>)}</select></Field>
      {model ? <InfoGrid items={[["运行时", model.runtime], ["可用环境", model.environments.join("、") || "—"], ["模型引用", model.ref]]} /> : <EmptyCatalog label="暂无已注册模型。" />}
    </CardContent></Card>
    <PreviewCard title="策略默认模型配置" value={preview} disabled={!name.trim() || !model} saving={saving} submitLabel={submitLabel} saveNotice={saveNotice} onSave={() => model && onSave({ name, sourceRef: model.ref, configuration: preview })} />
  </div>;
}

interface ConfiguratorProps { catalog: CapabilityCatalog; initial?: SavedConfiguration; onSave: (body: CreateSavedConfiguration) => void; saving: boolean; submitLabel: string; saveNotice: string; }

function PreviewCard({ title, value, disabled, saving, submitLabel, saveNotice, onSave }: { title: string; value: unknown; disabled?: boolean; saving?: boolean; submitLabel?: string; saveNotice?: string; onSave?: () => void }) {
  const [notice, setNotice] = React.useState("");
  const source = JSON.stringify(value, null, 2);
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(source);
      setNotice("配置已复制，可在画布的 JSON 编辑器中使用。");
    } catch {
      setNotice("无法访问剪贴板，请手动复制配置。");
    }
  };
  return <Card className="min-w-0"><CardHeader><CardTitle>{title}</CardTitle><div className="flex flex-wrap items-center justify-end gap-2">{saveNotice ? <span role="status" className={`text-sm ${saveNotice.startsWith("保存失败") ? "text-error-600" : "text-success-600"}`}>{saveNotice}</span> : null}<Button size="sm" variant="outline" onClick={() => void copy()} disabled={disabled}>{notice.startsWith("配置已复制") ? <Check /> : <Copy />}复制</Button>{onSave ? <Button size="sm" onClick={onSave} disabled={disabled} loading={saving}><Save />{submitLabel ?? "保存配置"}</Button> : null}</div></CardHeader><CardContent><pre aria-label={`${title}预览`} className="max-h-[520px] min-h-80 overflow-auto rounded-xl bg-gray-950 p-4 text-xs leading-6 text-gray-100">{source}</pre>{notice ? <p role="status" className="mt-3 text-sm text-gray-500">{notice}</p> : null}</CardContent></Card>;
}

function ConfigurationLibrary({ itemLabel, itemIcon, items, loading, error, deleting, onSelect, onDelete }: { itemLabel: string; itemIcon: React.ReactNode; items: SavedConfiguration[]; loading: boolean; error?: string; deleting: boolean; onSelect: (configurationId: string) => void; onDelete: (configurationId: string) => void }) {
  return <section aria-labelledby="configured-items-title" className="space-y-4"><div><h2 id="configured-items-title" className="text-lg font-semibold text-gray-900 dark:text-white">已配置{itemLabel}</h2><p className="mt-1 text-sm text-gray-500">当前项目共 {items.length} 项，点击卡片查看和修改参数。</p></div>
    {loading ? <div className="grid gap-4 md:grid-cols-2 2xl:grid-cols-3"><Skeleton className="h-44" /><Skeleton className="h-44" /></div> : null}
    {error ? <div className="rounded-xl border border-error-200 bg-error-50 p-4 text-sm text-error-700">无法加载已配置{itemLabel}：{error}</div> : null}
    {!loading && !error && items.length === 0 ? <div className="rounded-2xl border border-dashed border-gray-300 px-6 py-12 text-center dark:border-gray-700"><p className="text-sm text-gray-500">还没有已配置{itemLabel}，请点击页面上方的“新建{itemLabel}配置”。</p></div> : null}
    {!loading && !error && items.length > 0 ? <div className="grid gap-4 md:grid-cols-2 2xl:grid-cols-3">{items.map((item) => <Card key={item.configurationId} className="group flex min-h-44 flex-col transition hover:border-brand-300 hover:shadow-theme-sm dark:hover:border-brand-500/50"><button type="button" aria-label={`打开：${item.name}`} className="min-w-0 flex-1 p-5 text-left focus-visible:outline-hidden focus-visible:ring-3 focus-visible:ring-brand-500/20" onClick={() => onSelect(item.configurationId)}><span className="flex items-start justify-between gap-4"><span className="grid size-11 shrink-0 place-items-center rounded-xl bg-brand-50 text-brand-500 dark:bg-brand-500/15">{itemIcon}</span><span className="rounded-full bg-gray-100 px-2.5 py-1 text-xs text-gray-500 dark:bg-gray-800">版本 {item.revision}</span></span><span className="mt-4 block truncate font-semibold text-gray-900 dark:text-white">{item.name}</span><span className="mt-1 block break-all font-mono text-xs text-gray-500">{item.sourceRef}</span><span className="mt-3 block text-xs text-gray-400">更新于 {new Date(item.updatedAt).toLocaleString("zh-CN")}</span></button><div className="flex items-center justify-between border-t border-gray-100 px-5 py-2 dark:border-gray-800"><button type="button" className="text-sm font-medium text-brand-500 hover:text-brand-600" onClick={() => onSelect(item.configurationId)}>查看并编辑</button><Button variant="ghost" size="icon" aria-label={`删除${item.name}`} disabled={deleting} onClick={() => onDelete(item.configurationId)}><Trash2 /></Button></div></Card>)}</div> : null}
  </section>;
}

function RuntimeCapabilityLibrary({ kind, catalog, loading, error }: { kind: ConfigurationKind; catalog?: CapabilityCatalog; loading: boolean; error?: string }) {
  const itemLabel = { agent: "智能体", tool: "工具", model: "模型" }[kind];
  const entries = kind === "agent"
    ? (catalog?.agents ?? []).map((item) => ({ key: item.id, name: item.id, detail: `${item.runtime} · ${item.environments.join("、")}` }))
    : kind === "tool"
      ? (catalog?.tools ?? []).map((item) => ({ key: item.ref, name: item.ref, detail: `${riskLabel(item.risk)} · ${item.risk}` }))
      : (catalog?.models ?? []).map((item) => ({ key: item.ref, name: item.ref, detail: `${item.runtime} · ${item.environments.join("、")}` }));
  return <section aria-labelledby="runtime-capabilities-title" className="space-y-4"><div><h2 id="runtime-capabilities-title" className="text-lg font-semibold text-gray-900 dark:text-white">运行时可用{itemLabel}</h2><p className="mt-1 text-sm text-gray-500">系统注册表共 {entries.length} 项；点击“新建{itemLabel}配置”可保存当前项目参数。</p></div>
    {loading ? <div className="grid gap-3 md:grid-cols-2 2xl:grid-cols-3"><Skeleton className="h-24" /><Skeleton className="h-24" /></div> : null}
    {error ? <div className="rounded-xl border border-error-200 bg-error-50 p-4 text-sm text-error-700">无法加载运行时{itemLabel}：{error}</div> : null}
    {!loading && !error ? <div className="grid gap-3 md:grid-cols-2 2xl:grid-cols-3">{entries.map((item) => <Card key={item.key}><CardContent className="min-w-0 pt-5"><p className="break-all font-mono text-sm font-medium text-gray-800 dark:text-gray-200">{item.name}</p><p className="mt-2 text-xs text-gray-500">{item.detail}</p></CardContent></Card>)}</div> : null}
  </section>;
}

function ToolSchemas({ tool }: { tool: ToolCapability }) {
  return <Card><CardHeader><CardTitle>工具结构</CardTitle></CardHeader><CardContent className="grid gap-4 md:grid-cols-2"><SchemaPanel label="输入结构" value={tool.inputSchema} /><SchemaPanel label="输出结构" value={tool.outputSchema} /></CardContent></Card>;
}

function SchemaPanel({ label, value }: { label: string; value: Record<string, unknown> }) {
  return <div className="min-w-0"><p className="mb-2 text-xs font-semibold text-gray-500">{label}</p><pre className="max-h-64 overflow-auto rounded-lg bg-gray-50 p-3 text-xs text-gray-600 dark:bg-gray-800 dark:text-gray-300">{JSON.stringify(value, null, 2)}</pre></div>;
}

function RiskBadge({ risk }: { risk: string }) {
  const tone = risk === "LOW" ? "bg-success-50 text-success-700 dark:bg-success-500/15" : risk === "HIGH" || risk === "CRITICAL" ? "bg-error-50 text-error-700 dark:bg-error-500/15" : "bg-warning-50 text-warning-700 dark:bg-warning-500/15";
  return <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${tone}`}>{riskLabel(risk)}</span>;
}

function riskLabel(risk: string): string {
  const labels: Record<string, string> = { LOW: "低风险", MEDIUM: "中风险", HIGH: "高风险", CRITICAL: "严重风险" };
  return labels[risk] ?? risk;
}

function InfoGrid({ items }: { items: Array<[string, string]> }) {
  return <dl className="grid gap-3 rounded-xl bg-gray-50 p-4 text-sm sm:grid-cols-2 dark:bg-gray-800">{items.map(([label, value]) => <div key={label} className="min-w-0"><dt className="text-xs text-gray-500">{label}</dt><dd className="mt-1 break-all font-medium text-gray-800 dark:text-gray-200">{value}</dd></div>)}</dl>;
}

function EmptyCatalog({ label }: { label: string }) { return <p className="rounded-xl border border-dashed border-gray-300 p-8 text-center text-sm text-gray-500 dark:border-gray-700">{label}</p>; }

function Field({ label, hint, children }: { label: string; hint?: string; children: React.ReactNode }) {
  return <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">{label}{hint ? <span className="ml-2 text-xs font-normal text-gray-400">{hint}</span> : null}{children}</label>;
}

function parseObject(source: string): { value?: Record<string, unknown>; error?: string } {
  try {
    const value: unknown = JSON.parse(source);
    if (!value || typeof value !== "object" || Array.isArray(value)) return { error: "节点输入必须是 JSON 对象。" };
    return { value: value as Record<string, unknown> };
  } catch {
    return { error: "节点输入不是有效的 JSON。" };
  }
}

function asObject(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value) ? value as Record<string, unknown> : {};
}

function stringValue(value: unknown, fallback: string): string {
  return typeof value === "string" ? value : fallback;
}

function stringArray(value: unknown): string[] {
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === "string") : [];
}

function agentNodeKey(role: string | null | undefined): string {
  const normalized = (role ?? "").toLowerCase().replace(/[^a-z0-9_-]+/g, "-").replace(/^-+|-+$/g, "");
  return /^[a-z]/.test(normalized) ? normalized : "agent-1";
}
