import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, Save } from "lucide-react";
import * as React from "react";
import { useLocation, useNavigate } from "react-router";
import { api } from "@/api/client";
import type { CanvasCapabilitySelection, ConfigurationKind, Diagnostic, SavedConfiguration } from "@/api/types";
import { StrategyEditor } from "@/components/strategy/strategy-editor";
import { EMPTY_EDITOR_STATE, applySavedConfiguration, cloneSpec, createBlankSpec, type EditorState } from "@/components/strategy/strategy-editor-model";
import { Button } from "@/components/ui/button";
import { BackLink } from "@/components/ui/back-link";
import { Card, CardContent } from "@/components/ui/card";
import { useWorkspaceScope } from "@/lib/demo-scope";
import { cn } from "@/lib/utils";

export function StrategyCreatePage({ standalone = false }: { standalone?: boolean }) {
  const { tenantId, projectId, workspacePath } = useWorkspaceScope();
  const navigate = useNavigate();
  const location = useLocation();
  const capabilitySelection = location.state as CanvasCapabilitySelection | null;
  const client = useQueryClient();
  const initial = React.useRef(capabilitySelection?.capability ? capabilitySpec(capabilitySelection) : null).current;
  const [name, setName] = React.useState(initial?.name ?? "untitled-strategy");
  const [spec, setSpec] = React.useState(() => initial?.spec ?? createBlankSpec("untitled-strategy"));
  const [editorState, setEditorState] = React.useState<EditorState>(() => initial?.editorState ?? structuredClone(EMPTY_EDITOR_STATE));
  const [diagnostics, setDiagnostics] = React.useState<Diagnostic[]>([]);
  const [message, setMessage] = React.useState("");
  const [selectedConfigurationId, setSelectedConfigurationId] = React.useState("");
  const capabilities = useQuery({ queryKey: ["capabilities", tenantId, projectId], queryFn: () => api.getCapabilities(tenantId, projectId) });
  const configurations = useQuery({
    queryKey: ["strategy-configurations", tenantId, projectId],
    queryFn: async () => (await Promise.all((["agent", "tool", "model"] as ConfigurationKind[]).map(async (kind) =>
      (await api.listConfigurations(tenantId, projectId, kind)).items,
    ))).flat(),
  });
  const compile = useMutation({
    mutationFn: () => api.compileStrategy(tenantId, projectId, spec),
    onSuccess: (result) => {
      setDiagnostics(result.diagnostics);
      const hash = result.plan?.["plan_hash"];
      setMessage(result.valid ? `计划校验通过 · ${typeof hash === "string" ? hash : ""}` : "编译发现错误。");
    },
    onError: (error) => setMessage(error.message),
  });
  const create = useMutation({
    mutationFn: async () => {
      const result = await api.compileStrategy(tenantId, projectId, spec);
      setDiagnostics(result.diagnostics);
      if (!result.valid) throw new Error("请先修复编译诊断，再创建草稿。");
      return api.createStrategy(tenantId, projectId, name.trim(), spec, editorState);
    },
    onSuccess: async (value) => {
      await client.invalidateQueries({ queryKey: ["strategies", tenantId, projectId] });
      void navigate(`${workspacePath}/strategies/${value.strategyId}`);
    },
    onError: (error) => setMessage(error.message),
  });
  const rename = (value: string) => {
    setName(value);
    const next = cloneSpec(spec);
    next.metadata.name = value.trim() || "untitled-strategy";
    setSpec(next);
  };
  const applyConfiguration = () => {
    const selected = configurations.data?.find((item) => item.configurationId === selectedConfigurationId);
    if (!selected) return;
    try {
      setSpec(applySavedConfiguration(spec, selected));
      setMessage(`已把“${selected.name}”加入策略草稿。`);
      setSelectedConfigurationId("");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "项目配置无法加入策略。");
    }
  };
  return <div className="min-w-0 space-y-6">
    <div>{standalone ? null : <BackLink to={`${workspacePath}/strategies`}>策略管理</BackLink>}<h1 className={cn(standalone ? "" : "mt-4", "text-2xl font-semibold text-gray-900 dark:text-white")}>{standalone ? "编排画布" : "创建策略"}</h1><p className="mt-1 text-sm text-gray-500">{standalone ? "直接在可视化画布上设计新的耐久工作流。" : "从空白画布开始，校验后创建耐久草稿。"}</p></div>
    <Card><CardContent className="space-y-5 pt-5">
      <div><label htmlFor="strategy-name" className="text-sm font-medium text-gray-700 dark:text-gray-300">名称</label><input id="strategy-name" value={name} onChange={(event) => rename(event.target.value)} className="mt-2 h-11 w-full rounded-xl border border-gray-300 bg-transparent px-4 outline-none focus:border-brand-500 dark:border-gray-700" /></div>
      <ProjectConfigurationPicker items={configurations.data ?? []} selected={selectedConfigurationId} loading={configurations.isPending} error={configurations.error?.message} onSelect={setSelectedConfigurationId} onApply={applyConfiguration} />
      <StrategyEditor spec={spec} editorState={editorState} nodeTypes={capabilities.data?.nodeTypes.map((item) => item.type) ?? []} models={capabilities.data?.models.map((item) => item.ref) ?? []} diagnostics={diagnostics} onSpecChange={(value) => { setSpec(value); setMessage(""); }} onEditorStateChange={setEditorState} onError={setMessage} />
      <div className="flex flex-wrap justify-end gap-2"><Button variant="outline" onClick={() => compile.mutate()} loading={compile.isPending}><CheckCircle2 />校验</Button><Button onClick={() => create.mutate()} loading={create.isPending} disabled={!name.trim()}><Save />创建草稿</Button></div>
      {message ? <p role="status" className="break-all rounded-xl bg-gray-50 p-3 text-sm text-gray-600 dark:bg-gray-800">{message}</p> : null}
      {diagnostics.length ? <DiagnosticList diagnostics={diagnostics} /> : null}
    </CardContent></Card>
  </div>;
}

function ProjectConfigurationPicker({ items, selected, loading, error, onSelect, onApply }: { items: SavedConfiguration[]; selected: string; loading: boolean; error?: string; onSelect: (value: string) => void; onApply: () => void }) {
  const labels: Record<ConfigurationKind, string> = { agent: "智能体", tool: "工具", model: "模型" };
  return <section className="rounded-xl border border-gray-200 p-4 dark:border-gray-800">
    <div><h2 className="font-semibold text-gray-900 dark:text-white">项目能力配置</h2><p className="mt-1 text-sm text-gray-500">把已保存的智能体、工具或默认模型配置加入当前 SwarmSpec；发布后会冻结到执行计划。</p></div>
    {error ? <p role="alert" className="mt-3 text-sm text-error-600">无法加载项目配置：{error}</p> : <div className="mt-3 flex flex-wrap gap-2"><select aria-label="项目能力配置" className="h-10 min-w-64 flex-1 rounded-lg border border-gray-300 bg-transparent px-3 text-sm dark:border-gray-700" value={selected} disabled={loading || !items.length} onChange={(event) => onSelect(event.target.value)}><option value="">{loading ? "正在加载…" : items.length ? "选择项目配置" : "暂无已保存配置"}</option>{items.map((item) => <option key={item.configurationId} value={item.configurationId}>{labels[item.kind]} · {item.name}</option>)}</select><Button type="button" variant="outline" disabled={!selected} onClick={onApply}>加入策略</Button></div>}
  </section>;
}

function capabilitySpec(selection: CanvasCapabilitySelection) {
  const { capability, input } = selection;
  const name = `capability-${capability.name.toLowerCase().replace(/[^a-z0-9_-]+/g, "-") || "draft"}`;
  const spec = createBlankSpec(name);
  spec.spec.inputSchema = capability.inputSchema ?? { type: "object" };
  spec.spec.outputSchema = { type: "object" };
  spec.spec.graph.entrypoint = "capability";
  spec.spec.graph.output = { result: "{{ tasks.capability.output }}" };
  if (capability.kind === "tool") {
    spec.spec.graph.nodes["capability"] = { type: "tool", tool: capability.ref, input, dependsOn: [] };
  } else {
    spec.spec.graph.nodes["capability"] = { type: "agent", agent: "capability", dependsOn: [] };
    spec.spec.agents = { capability: capability.kind === "agent" ? { ref: capability.ref } : { role: "能力执行者", instructions: "处理输入并返回最终结果。", model: capability.ref } };
  }
  return { name, spec, editorState: { ...structuredClone(EMPTY_EDITOR_STATE), positions: { capability: { x: 80, y: 80 } } } };
}

function DiagnosticList({ diagnostics }: { diagnostics: Diagnostic[] }) {
  return <ul className="space-y-2" aria-label="编译诊断">{diagnostics.map((item, index) => <li key={`${item.code}-${index}`} className="rounded-lg border border-error-200 p-3 text-sm dark:border-error-500/30"><strong className="text-error-600">{item.code}</strong> <code className="break-all text-xs text-gray-500">{item.path}</code><p className="mt-1 text-gray-600 dark:text-gray-300">{item.message}</p></li>)}</ul>;
}
