import {
  Background,
  Controls,
  Handle,
  MarkerType,
  MiniMap,
  Position,
  ReactFlow,
  ReactFlowProvider,
  useReactFlow,
  type Connection,
  type Edge,
  type Node,
  type NodeProps,
  type Viewport,
} from "@xyflow/react";
import { AlertTriangle, Braces, GitBranch, Play, Plus, Trash2 } from "lucide-react";
import * as React from "react";
import type { Diagnostic, SavedConfiguration } from "@/api/types";
import { Button } from "@/components/ui/button";
import { capabilityRefDisplayName } from "@/lib/capability-labels";
import { nodeTypeLabel } from "@/lib/display-text";
import {
  SUPPORTED_NODE_TYPES,
  addNode,
  assignAgentDeclaration,
  bindProjectAgentToNode,
  connectNodes,
  deleteNode,
  diagnosticNodeKey,
  disconnectNodes,
  isBindableAgentConfiguration,
  isSupportedNode,
  layoutStrategyGraph,
  listEdges,
  normalizeEditorState,
  setEntrypoint,
  unbindAgentFromNode,
  updateAgentDeclaration,
  updateNode,
  type AgentBindingState,
  type EditorState,
  type StrategyNode,
  type SupportedNodeType,
  type SwarmSpecDocument,
} from "./strategy-editor-model";

interface CanvasNodeData extends Record<string, unknown> {
  label: string;
  nodeType: string;
  entrypoint: boolean;
  readonly: boolean;
  diagnosticCount: number;
}

type CanvasNode = Node<CanvasNodeData, "strategy">;

export function StrategyCanvas(props: {
  spec: SwarmSpecDocument;
  editorState: EditorState;
  nodeTypes: string[];
  models?: string[];
  tools?: string[];
  agentConfigurations?: SavedConfiguration[];
  agentConfigurationsLoading?: boolean;
  agentConfigurationsError?: string;
  diagnostics: Diagnostic[];
  onSpecChange: (spec: SwarmSpecDocument) => void;
  onEditorStateChange: (state: EditorState) => void;
  onError: (message: string) => void;
}) {
  return <ReactFlowProvider><StrategyCanvasInner {...props} /></ReactFlowProvider>;
}

function StrategyCanvasInner({
  spec,
  editorState,
  nodeTypes: capabilityNodeTypes,
  models = [],
  tools = [],
  agentConfigurations = [],
  agentConfigurationsLoading = false,
  agentConfigurationsError,
  diagnostics,
  onSpecChange,
  onEditorStateChange,
  onError,
}: Parameters<typeof StrategyCanvas>[0]) {
  const flow = useReactFlow<CanvasNode>();
  const [selected, setSelected] = React.useState<string | null>(null);
  const graphNodes = spec.spec.graph.nodes;
  const availableTypes = SUPPORTED_NODE_TYPES.filter((type) => capabilityNodeTypes.includes(type));
  const diagnosticsByNode = React.useMemo(() => {
    const result = new Map<string, number>();
    for (const item of diagnostics) {
      const key = diagnosticNodeKey(item, spec);
      if (key) result.set(key, (result.get(key) ?? 0) + 1);
    }
    return result;
  }, [diagnostics, spec]);

  React.useEffect(() => {
    const missing = Object.keys(graphNodes).filter((key) => !editorState.positions[key]);
    if (!missing.length) return;
    const automaticPositions = layoutStrategyGraph(spec);
    const positions = { ...editorState.positions };
    missing.forEach((key) => {
      positions[key] = automaticPositions[key] ?? { x: 80, y: 80 };
    });
    onEditorStateChange(normalizeEditorState({ ...editorState, positions }));
  }, [editorState, graphNodes, onEditorStateChange, spec]);

  React.useEffect(() => {
    if (selected && !graphNodes[selected]) setSelected(null);
  }, [graphNodes, selected]);

  const automaticPositions = layoutStrategyGraph(spec);
  const nodes: CanvasNode[] = Object.entries(graphNodes).map(([key, node]) => ({
    id: key,
    type: "strategy",
    position: editorState.positions[key] ?? automaticPositions[key] ?? { x: 80, y: 80 },
    selected: selected === key,
    data: {
      label: key,
      nodeType: node.type,
      entrypoint: spec.spec.graph.entrypoint === key,
      readonly: !isSupportedNode(node),
      diagnosticCount: diagnosticsByNode.get(key) ?? 0,
    },
  }));
  const edges: Edge[] = listEdges(spec).map((edge) => {
    const color = edge.branch ? "var(--color-brand-500)" : "var(--color-gray-500)";
    return {
      ...edge,
      type: "smoothstep",
      label: edge.branch ? "分支" : undefined,
      animated: edge.branch,
      markerEnd: { type: MarkerType.ArrowClosed, color, width: 16, height: 16 },
      style: { stroke: color, strokeWidth: edge.branch ? 2 : 1.5 },
    };
  });

  const addAt = React.useCallback((type: SupportedNodeType, position?: { x: number; y: number }) => {
    const result = addNode(spec, type, position, editorState);
    onSpecChange(result.spec);
    onEditorStateChange(result.editorState);
    setSelected(result.nodeKey);
  }, [editorState, onEditorStateChange, onSpecChange, spec]);

  const removeMany = React.useCallback((nodeKeys: string[]) => {
    let nextSpec = spec;
    let nextEditorState = editorState;
    for (const nodeKey of nodeKeys) {
      const node = nextSpec.spec.graph.nodes[nodeKey];
      if (!node || !isSupportedNode(node)) continue;
      let removeAgent = false;
      if (node.type === "agent" && typeof node["agent"] === "string") {
        const agentKey = node["agent"];
        const references = Object.values(nextSpec.spec.graph.nodes).filter(
          (candidate) => candidate.type === "agent" && candidate["agent"] === agentKey,
        ).length;
        if (references === 1 && nextSpec.spec.agents?.[agentKey]) {
          removeAgent = window.confirm(`是否同时删除未使用的智能体声明“${agentKey}”？`);
        }
      }
      const result = deleteNode(nextSpec, nextEditorState, nodeKey, removeAgent);
      nextSpec = result.spec;
      nextEditorState = result.editorState;
    }
    onSpecChange(nextSpec);
    onEditorStateChange(nextEditorState);
    setSelected(null);
  }, [editorState, onEditorStateChange, onSpecChange, spec]);

  const remove = React.useCallback((nodeKey: string) => removeMany([nodeKey]), [removeMany]);

  const onConnect = React.useCallback((connection: Connection) => {
    if (!connection.source || !connection.target) return;
    const result = connectNodes(spec, connection.source, connection.target);
    if (result.error) onError(result.error);
    else onSpecChange(result.spec);
  }, [onError, onSpecChange, spec]);

  const onDrop = React.useCallback((event: React.DragEvent) => {
    event.preventDefault();
    const type = event.dataTransfer.getData("application/swarmcore-node") as SupportedNodeType;
    if (!availableTypes.includes(type)) return;
    addAt(type, flow.screenToFlowPosition({ x: event.clientX, y: event.clientY }));
  }, [addAt, availableTypes, flow]);

  const selectedNode = selected ? graphNodes[selected] : undefined;
  return <div className="grid min-w-0 gap-4 xl:grid-cols-[170px_minmax(0,1fr)_300px]">
    <aside className="rounded-xl border border-gray-200 p-3 dark:border-gray-800" aria-label="节点库">
      <p className="mb-3 text-sm font-semibold text-gray-800 dark:text-gray-200">节点库</p>
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 xl:grid-cols-1">
        {availableTypes.map((type) => <button
          key={type}
          type="button"
          draggable
          onDragStart={(event) => { event.dataTransfer.setData("application/swarmcore-node", type); event.dataTransfer.effectAllowed = "move"; }}
          onClick={() => addAt(type)}
          className="flex min-h-10 items-center gap-2 rounded-lg border border-gray-200 px-3 text-left text-sm capitalize hover:border-brand-400 hover:bg-brand-50 dark:border-gray-700 dark:hover:bg-brand-500/10"
        ><Plus className="size-4" />{nodeTypeLabel(type)}</button>)}
      </div>
      <p className="mt-3 text-xs text-gray-500">可拖放到画布，或单击添加。</p>
    </aside>
    <div
      className="h-[620px] min-h-[420px] overflow-hidden rounded-xl border border-gray-200 bg-gray-50 dark:border-gray-800 dark:bg-gray-950"
      onDragOver={(event) => { event.preventDefault(); event.dataTransfer.dropEffect = "move"; }}
      onDrop={onDrop}
      data-testid="strategy-canvas"
    >
      <ReactFlow<CanvasNode>
        nodes={nodes}
        edges={edges}
        nodeTypes={{ strategy: StrategyFlowNode }}
        defaultViewport={editorState.viewport}
        fitView
        fitViewOptions={{ padding: 0.15 }}
        minZoom={0.2}
        maxZoom={2}
        deleteKeyCode={["Backspace", "Delete"]}
        onConnect={onConnect}
        onNodeClick={(_, node) => setSelected(node.id)}
        onPaneClick={() => setSelected(null)}
        onNodeDragStop={(_, node) => onEditorStateChange(normalizeEditorState({
          ...editorState,
          positions: { ...editorState.positions, [node.id]: node.position },
        }))}
        onNodesDelete={(removed) => removeMany(removed.map((node) => node.id))}
        onEdgesDelete={(removed) => {
          const next = removed.reduce(
            (current, edge) => disconnectNodes(current, edge.source, edge.target),
            spec,
          );
          onSpecChange(next);
        }}
        onMoveEnd={(_, viewport: Viewport) => onEditorStateChange(normalizeEditorState({ ...editorState, viewport }))}
      >
        <Background />
        <MiniMap pannable zoomable />
        <Controls />
      </ReactFlow>
    </div>
    <PropertyPanel
      nodeKey={selected}
      node={selectedNode}
      spec={spec}
      editorState={editorState}
      models={models}
      tools={tools}
      agentConfigurations={agentConfigurations}
      agentConfigurationsLoading={agentConfigurationsLoading}
      agentConfigurationsError={agentConfigurationsError}
      readonly={selectedNode ? !isSupportedNode(selectedNode) : false}
      onSpecChange={onSpecChange}
      onEditorStateChange={onEditorStateChange}
      onDelete={remove}
      onError={onError}
    />
  </div>;
}

function StrategyFlowNode({ data, selected }: NodeProps<CanvasNode>) {
  return <div className={`min-w-40 rounded-xl border-2 bg-white px-4 py-3 shadow-sm dark:bg-gray-900 ${data.diagnosticCount ? "border-error-500" : selected ? "border-brand-500" : "border-gray-300 dark:border-gray-700"}`}>
    <Handle type="target" position={Position.Left} isConnectable={!data.readonly} />
    <div className="flex items-center gap-2">
      {data.nodeType === "parallel" ? <GitBranch className="size-4 text-brand-500" /> : <Braces className="size-4 text-gray-500" />}
      <strong className="text-sm text-gray-900 dark:text-white">{data.label}</strong>
    </div>
    <div className="mt-1 flex flex-wrap gap-1 text-[11px] text-gray-500">
      <span>{nodeTypeLabel(data.nodeType)}</span>
      {data.entrypoint ? <span className="inline-flex items-center gap-1 text-success-600"><Play className="size-3" />入口</span> : null}
      {data.readonly ? <span className="text-warning-600">只读</span> : null}
      {data.diagnosticCount ? <span className="inline-flex items-center gap-1 text-error-600"><AlertTriangle className="size-3" />{data.diagnosticCount}</span> : null}
    </div>
    <Handle type="source" position={Position.Right} isConnectable={!data.readonly} />
  </div>;
}

function PropertyPanel({
  nodeKey,
  node,
  spec,
  editorState,
  models,
  tools,
  agentConfigurations,
  agentConfigurationsLoading,
  agentConfigurationsError,
  readonly,
  onSpecChange,
  onEditorStateChange,
  onDelete,
  onError,
}: {
  nodeKey: string | null;
  node?: StrategyNode;
  spec: SwarmSpecDocument;
  editorState: EditorState;
  models: string[];
  tools: string[];
  agentConfigurations: SavedConfiguration[];
  agentConfigurationsLoading: boolean;
  agentConfigurationsError?: string;
  readonly: boolean;
  onSpecChange: (spec: SwarmSpecDocument) => void;
  onEditorStateChange: (state: EditorState) => void;
  onDelete: (nodeKey: string) => void;
  onError: (message: string) => void;
}) {
  if (!nodeKey || !node) return <aside className="rounded-xl border border-gray-200 p-4 text-sm text-gray-500 dark:border-gray-800">请选择节点以编辑属性。</aside>;
  if (readonly) return <aside className="min-w-0 rounded-xl border border-warning-300 bg-warning-50/50 p-4 dark:border-warning-500/30 dark:bg-warning-500/10">
    <p className="font-semibold">{nodeKey}</p><p className="mt-1 text-sm text-warning-700 dark:text-warning-300">不支持的节点类型“{node.type}”将以只读方式保留。</p>
    <pre className="mt-3 max-h-96 overflow-auto whitespace-pre-wrap text-xs">{JSON.stringify(node, null, 2)}</pre>
  </aside>;
  const setNode = (patch: Record<string, unknown>) => onSpecChange(updateNode(spec, nodeKey, patch));
  const fieldClass = "mt-1 h-10 w-full rounded-lg border border-gray-300 bg-transparent px-3 text-sm dark:border-gray-700";
  const readonlyFieldClass = `${fieldClass} bg-gray-50 text-gray-600 dark:bg-gray-900 dark:text-gray-300`;
  const agentKey = node.type === "agent" && typeof node["agent"] === "string" ? node["agent"] : "";
  const agent = agentKey ? spec.spec.agents?.[agentKey] : undefined;
  const currentModel = stringValue(agent?.["model"]);
  const currentTool = stringValue(node["tool"]);
  const binding = editorState.agentBindings?.[nodeKey];
  const bound = Boolean(binding);
  return <aside className="min-w-0 space-y-4 rounded-xl border border-gray-200 p-4 dark:border-gray-800" aria-label="节点属性">
    <div className="flex items-center justify-between gap-2"><div><p className="font-semibold">{nodeKey}</p><p className="text-xs capitalize text-gray-500">{nodeTypeLabel(node.type)}</p></div><Button size="sm" variant="ghost" aria-label="删除节点" onClick={() => onDelete(nodeKey)}><Trash2 /></Button></div>
    <Button className="w-full" size="sm" variant={spec.spec.graph.entrypoint === nodeKey ? "primary" : "outline"} onClick={() => onSpecChange(setEntrypoint(spec, nodeKey))}><Play />{spec.spec.graph.entrypoint === nodeKey ? "当前入口" : "设为入口"}</Button>
    {node.type === "agent" ? <>
      <AgentBindingControls
        nodeKey={nodeKey}
        binding={binding}
        agentConfigurations={agentConfigurations}
        loading={agentConfigurationsLoading}
        error={agentConfigurationsError}
        fieldClass={fieldClass}
        onBind={(saved) => {
          try {
            const result = bindProjectAgentToNode(spec, editorState, nodeKey, saved);
            onSpecChange(result.spec);
            onEditorStateChange(result.editorState);
          } catch (error) {
            onError(error instanceof Error ? error.message : "绑定智能体配置失败。");
          }
        }}
        onUnbind={() => onEditorStateChange(unbindAgentFromNode(editorState, nodeKey))}
        onError={onError}
      />
      <AgentDeclarationField
        agentKey={agentKey}
        readonly={bound}
        fieldClass={bound ? readonlyFieldClass : fieldClass}
        onCommit={(nextKey) => {
          try {
            onSpecChange(assignAgentDeclaration(spec, nodeKey, nextKey));
            if (binding) onEditorStateChange(unbindAgentFromNode(editorState, nodeKey));
            return true;
          } catch (error) {
            onError(error instanceof Error ? error.message : "设置智能体声明失败。");
            return false;
          }
        }}
      />
      <Field label="角色"><input className={bound ? readonlyFieldClass : fieldClass} value={stringValue(agent?.["role"])} readOnly={bound} onChange={(event) => onSpecChange(updateAgentDeclaration(spec, agentKey, { role: event.target.value }))} /></Field>
      <Field label="指令"><textarea className={`mt-1 min-h-28 w-full rounded-lg border border-gray-300 p-3 text-sm dark:border-gray-700 ${bound ? "bg-gray-50 text-gray-600 dark:bg-gray-900 dark:text-gray-300" : "bg-transparent"}`} value={stringValue(agent?.["instructions"])} readOnly={bound} onChange={(event) => onSpecChange(updateAgentDeclaration(spec, agentKey, { instructions: event.target.value }))} /></Field>
      <Field label="模型"><select aria-label="模型" className={bound ? readonlyFieldClass : fieldClass} value={currentModel} disabled={bound} onChange={(event) => onSpecChange(updateAgentDeclaration(spec, agentKey, event.target.value ? { model: event.target.value } : { model: undefined }))}><option value="">使用策略默认模型</option>{models.map((ref) => <option key={ref} value={ref}>{capabilityRefDisplayName(ref)}</option>)}{currentModel && !models.includes(currentModel) ? <option value={currentModel}>{capabilityRefDisplayName(currentModel)}</option> : null}</select></Field>
    </> : null}
    {node.type === "tool" ? <><Field label="工具 Ref"><select aria-label="工具 Ref" className={fieldClass} value={currentTool} onChange={(event) => setNode({ tool: event.target.value })}>{tools.map((ref) => <option key={ref} value={ref}>{capabilityRefDisplayName(ref)}</option>)}{currentTool && !tools.includes(currentTool) ? <option value={currentTool}>{capabilityRefDisplayName(currentTool)}</option> : null}</select></Field><JsonField label="工具输入" value={recordValue(node["input"])} onCommit={(value) => setNode({ input: value })} onError={onError} /></> : null}
    {node.type === "join" ? <><Field label="汇合策略"><select className={fieldClass} value={stringValue(node["strategy"])} onChange={(event) => setNode({ strategy: event.target.value, quorum: event.target.value === "quorum" ? 1 : undefined })}>{["all", "any", "quorum", "first_success"].map((value) => <option key={value} value={value}>{joinStrategyLabel(value)}</option>)}</select></Field>{node["strategy"] === "quorum" ? <Field label="法定数量"><input type="number" min={1} className={fieldClass} value={numberValue(node["quorum"], 1)} onChange={(event) => setNode({ quorum: Number(event.target.value) })} /></Field> : null}</> : null}
    {node.type === "reducer" ? <Field label="归并方式"><select className={fieldClass} value={stringValue(node["reducer"])} onChange={(event) => setNode({ reducer: event.target.value })}>{["merge_object", "concat", "first_success", "vote"].map((value) => <option key={value} value={value}>{reducerLabel(value)}</option>)}</select></Field> : null}
    {node.type === "approval" || node.type === "input" ? <><Field label="提示语"><textarea className="mt-1 min-h-24 w-full rounded-lg border border-gray-300 bg-transparent p-3 text-sm dark:border-gray-700" value={stringValue(node["prompt"])} onChange={(event) => setNode({ prompt: event.target.value })} /></Field><JsonField label="输入结构" value={recordValue(node["inputSchema"])} onCommit={(value) => setNode({ inputSchema: value })} onError={onError} /></> : null}
    {node.type === "parallel" ? <p className="rounded-lg bg-gray-50 p-3 text-xs text-gray-500 dark:bg-gray-800">分支由出向连接维护：{stringArray(node.branches).join(", ") || "无"}</p> : null}
  </aside>;
}

function AgentBindingControls({
  nodeKey,
  binding,
  agentConfigurations,
  loading,
  error,
  fieldClass,
  onBind,
  onUnbind,
  onError,
}: {
  nodeKey: string;
  binding?: AgentBindingState;
  agentConfigurations: SavedConfiguration[];
  loading: boolean;
  error?: string;
  fieldClass: string;
  onBind: (saved: SavedConfiguration) => void;
  onUnbind: () => void;
  onError: (message: string) => void;
}) {
  const bindable = agentConfigurations.filter(isBindableAgentConfiguration);
  const selectedId = binding?.configurationId ?? "";
  const current = agentConfigurations.find((item) => item.configurationId === selectedId);
  const sourceMissing = Boolean(binding && !loading && !error && !current);
  const hasUpdate = Boolean(binding && current && current.revision > binding.revision);

  const choose = (configurationId: string) => {
    if (!configurationId) return;
    const saved = agentConfigurations.find((item) => item.configurationId === configurationId);
    if (!saved) return;
    if (!isBindableAgentConfiguration(saved)) {
      onError("配置格式无效：缺少有效入口智能体声明。");
      return;
    }
    const replacing = Boolean(binding) || configurationId !== selectedId;
    if (replacing && !window.confirm("将用所选智能体配置替换当前节点声明；其他节点不受影响。")) {
      return;
    }
    onBind(saved);
  };

  return <section className="space-y-2 rounded-lg border border-gray-200 p-3 dark:border-gray-800">
    <div className="flex items-center justify-between gap-2">
      <p className="text-xs font-medium text-gray-600 dark:text-gray-300">绑定已配置智能体</p>
      {binding ? <Button type="button" size="sm" variant="ghost" onClick={onUnbind}>转为自定义</Button> : null}
    </div>
    {error ? <p role="alert" className="text-xs text-error-600">无法加载已配置智能体，可重试</p> : null}
    <select
      aria-label="绑定已配置智能体"
      className={fieldClass}
      value={selectedId}
      disabled={Boolean(error) || loading || !bindable.length}
      onChange={(event) => choose(event.target.value)}
    >
      <option value="">{loading ? "正在加载…" : bindable.length ? "选择项目智能体配置" : "暂无可用智能体配置"}</option>
      {bindable.map((item) => <option key={item.configurationId} value={item.configurationId}>{item.name} · r{item.revision}</option>)}
      {binding && !bindable.some((item) => item.configurationId === binding.configurationId) ? (
        <option value={binding.configurationId}>{binding.name} · r{binding.revision}</option>
      ) : null}
    </select>
    {binding ? <p className="text-xs text-gray-500">已绑定 {binding.name} · r{binding.revision}</p> : null}
    {hasUpdate && current ? <div className="flex flex-wrap items-center gap-2">
      <p role="status" className="text-xs text-warning-700 dark:text-warning-300">已有新版本 r{current.revision}，可重新绑定</p>
      <Button type="button" size="sm" variant="outline" onClick={() => {
        if (!window.confirm("将用所选智能体配置替换当前节点声明；其他节点不受影响。")) return;
        onBind(current);
      }}>重新绑定</Button>
    </div> : null}
    {sourceMissing ? <p role="status" className="text-xs text-warning-700 dark:text-warning-300">源配置已删除，当前节点仍可运行</p> : null}
    <p className="sr-only">{nodeKey}</p>
  </section>;
}

function AgentDeclarationField({
  agentKey,
  readonly,
  fieldClass,
  onCommit,
}: {
  agentKey: string;
  readonly: boolean;
  fieldClass: string;
  onCommit: (nextKey: string) => boolean;
}) {
  const [draft, setDraft] = React.useState(agentKey);
  React.useEffect(() => setDraft(agentKey), [agentKey]);
  const commit = () => {
    const trimmed = draft.trim();
    if (!trimmed || trimmed === agentKey) {
      setDraft(agentKey);
      return;
    }
    if (!onCommit(trimmed)) setDraft(agentKey);
  };
  return <Field label="智能体声明"><input
    aria-label="智能体声明"
    className={fieldClass}
    value={draft}
    readOnly={readonly}
    placeholder="例如 planner"
    spellCheck={false}
    onChange={(event) => setDraft(event.target.value)}
    onBlur={commit}
    onKeyDown={(event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        (event.target as HTMLInputElement).blur();
      }
    }}
  /></Field>;
}

function JsonField({ label, value, onCommit, onError }: { label: string; value: Record<string, unknown>; onCommit: (value: Record<string, unknown>) => void; onError: (message: string) => void }) {
  const source = JSON.stringify(value, null, 2);
  const [text, setText] = React.useState(source);
  React.useEffect(() => setText(source), [source]);
  return <Field label={label}><textarea className="mt-1 min-h-28 w-full rounded-lg border border-gray-300 bg-transparent p-3 font-mono text-xs dark:border-gray-700" value={text} onChange={(event) => setText(event.target.value)} onBlur={() => { try { const parsed: unknown = JSON.parse(text); if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) throw new Error("必须是对象"); onCommit(parsed as Record<string, unknown>); } catch (error) { onError(`${label}无效：${error instanceof Error ? error.message : "JSON 无效"}`); } }} /></Field>;
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return <label className="block text-xs font-medium text-gray-600 dark:text-gray-300">{label}{children}</label>;
}

function joinStrategyLabel(value: string): string { return ({ all: "全部完成", any: "任意完成", quorum: "达到法定数量", first_success: "首个成功" } as Record<string, string>)[value] ?? value; }
function reducerLabel(value: string): string { return ({ merge_object: "合并对象", concat: "拼接", first_success: "首个成功", vote: "投票" } as Record<string, string>)[value] ?? value; }

function stringValue(value: unknown): string { return typeof value === "string" ? value : ""; }
function numberValue(value: unknown, fallback: number): number { return typeof value === "number" ? value : fallback; }
function recordValue(value: unknown): Record<string, unknown> { return value && typeof value === "object" && !Array.isArray(value) ? value as Record<string, unknown> : {}; }
function stringArray(value: unknown): string[] { return Array.isArray(value) ? value.filter((item): item is string => typeof item === "string") : []; }
