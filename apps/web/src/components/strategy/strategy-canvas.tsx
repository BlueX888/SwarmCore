import {
  Background,
  Controls,
  Handle,
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
import type { Diagnostic } from "@/api/types";
import { Button } from "@/components/ui/button";
import {
  SUPPORTED_NODE_TYPES,
  addNode,
  connectNodes,
  deleteNode,
  diagnosticNodeKey,
  disconnectNodes,
  isSupportedNode,
  listEdges,
  setEntrypoint,
  updateAgentDeclaration,
  updateNode,
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
    const positions = { ...editorState.positions };
    missing.forEach((key, index) => {
      const ordinal = Object.keys(graphNodes).indexOf(key);
      positions[key] = { x: 80 + (ordinal % 3) * 240, y: 80 + Math.floor(ordinal / 3) * 160 + index * 4 };
    });
    onEditorStateChange({ ...editorState, positions });
  }, [editorState, graphNodes, onEditorStateChange]);

  React.useEffect(() => {
    if (selected && !graphNodes[selected]) setSelected(null);
  }, [graphNodes, selected]);

  const nodes: CanvasNode[] = Object.entries(graphNodes).map(([key, node], index) => ({
    id: key,
    type: "strategy",
    position: editorState.positions[key] ?? { x: 80 + (index % 3) * 240, y: 80 + Math.floor(index / 3) * 160 },
    selected: selected === key,
    data: {
      label: key,
      nodeType: node.type,
      entrypoint: spec.spec.graph.entrypoint === key,
      readonly: !isSupportedNode(node),
      diagnosticCount: diagnosticsByNode.get(key) ?? 0,
    },
  }));
  const edges: Edge[] = listEdges(spec).map((edge) => ({
    ...edge,
    type: "smoothstep",
    label: edge.branch ? "branch" : undefined,
    animated: edge.branch,
    style: edge.branch ? { stroke: "var(--color-brand-500)", strokeWidth: 2 } : undefined,
  }));

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
          removeAgent = window.confirm(`Also remove the unused agent declaration "${agentKey}"?`);
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
    <aside className="rounded-xl border border-gray-200 p-3 dark:border-gray-800" aria-label="Node library">
      <p className="mb-3 text-sm font-semibold text-gray-800 dark:text-gray-200">Node library</p>
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 xl:grid-cols-1">
        {availableTypes.map((type) => <button
          key={type}
          type="button"
          draggable
          onDragStart={(event) => { event.dataTransfer.setData("application/swarmcore-node", type); event.dataTransfer.effectAllowed = "move"; }}
          onClick={() => addAt(type)}
          className="flex min-h-10 items-center gap-2 rounded-lg border border-gray-200 px-3 text-left text-sm capitalize hover:border-brand-400 hover:bg-brand-50 dark:border-gray-700 dark:hover:bg-brand-500/10"
        ><Plus className="size-4" />{nodeLabel(type)}</button>)}
      </div>
      <p className="mt-3 text-xs text-gray-500">Drag to place, or click to add.</p>
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
        fitView={Object.keys(editorState.positions).length === 0}
        minZoom={0.2}
        maxZoom={2}
        deleteKeyCode={["Backspace", "Delete"]}
        onConnect={onConnect}
        onNodeClick={(_, node) => setSelected(node.id)}
        onPaneClick={() => setSelected(null)}
        onNodeDragStop={(_, node) => onEditorStateChange({
          ...editorState,
          positions: { ...editorState.positions, [node.id]: node.position },
        })}
        onNodesDelete={(removed) => removeMany(removed.map((node) => node.id))}
        onEdgesDelete={(removed) => {
          const next = removed.reduce(
            (current, edge) => disconnectNodes(current, edge.source, edge.target),
            spec,
          );
          onSpecChange(next);
        }}
        onMoveEnd={(_, viewport: Viewport) => onEditorStateChange({ ...editorState, viewport })}
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
      readonly={selectedNode ? !isSupportedNode(selectedNode) : false}
      onSpecChange={onSpecChange}
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
      <span>{nodeLabel(data.nodeType)}</span>
      {data.entrypoint ? <span className="inline-flex items-center gap-1 text-success-600"><Play className="size-3" />entry</span> : null}
      {data.readonly ? <span className="text-warning-600">read-only</span> : null}
      {data.diagnosticCount ? <span className="inline-flex items-center gap-1 text-error-600"><AlertTriangle className="size-3" />{data.diagnosticCount}</span> : null}
    </div>
    <Handle type="source" position={Position.Right} isConnectable={!data.readonly} />
  </div>;
}

function PropertyPanel({ nodeKey, node, spec, readonly, onSpecChange, onDelete, onError }: {
  nodeKey: string | null;
  node?: StrategyNode;
  spec: SwarmSpecDocument;
  readonly: boolean;
  onSpecChange: (spec: SwarmSpecDocument) => void;
  onDelete: (nodeKey: string) => void;
  onError: (message: string) => void;
}) {
  if (!nodeKey || !node) return <aside className="rounded-xl border border-gray-200 p-4 text-sm text-gray-500 dark:border-gray-800">Select a node to edit its properties.</aside>;
  if (readonly) return <aside className="min-w-0 rounded-xl border border-warning-300 bg-warning-50/50 p-4 dark:border-warning-500/30 dark:bg-warning-500/10">
    <p className="font-semibold">{nodeKey}</p><p className="mt-1 text-sm text-warning-700 dark:text-warning-300">Unsupported node type “{node.type}” is preserved read-only.</p>
    <pre className="mt-3 max-h-96 overflow-auto whitespace-pre-wrap text-xs">{JSON.stringify(node, null, 2)}</pre>
  </aside>;
  const setNode = (patch: Record<string, unknown>) => onSpecChange(updateNode(spec, nodeKey, patch));
  const fieldClass = "mt-1 h-10 w-full rounded-lg border border-gray-300 bg-transparent px-3 text-sm dark:border-gray-700";
  const agentKey = node.type === "agent" && typeof node["agent"] === "string" ? node["agent"] : "";
  const agent = agentKey ? spec.spec.agents?.[agentKey] : undefined;
  return <aside className="min-w-0 space-y-4 rounded-xl border border-gray-200 p-4 dark:border-gray-800" aria-label="Node properties">
    <div className="flex items-center justify-between gap-2"><div><p className="font-semibold">{nodeKey}</p><p className="text-xs capitalize text-gray-500">{nodeLabel(node.type)}</p></div><Button size="sm" variant="ghost" aria-label="Delete node" onClick={() => onDelete(nodeKey)}><Trash2 /></Button></div>
    <Button className="w-full" size="sm" variant={spec.spec.graph.entrypoint === nodeKey ? "primary" : "outline"} onClick={() => onSpecChange(setEntrypoint(spec, nodeKey))}><Play />{spec.spec.graph.entrypoint === nodeKey ? "Entrypoint" : "Set as entrypoint"}</Button>
    {node.type === "agent" ? <>
      <Field label="Agent declaration"><select className={fieldClass} value={agentKey} onChange={(event) => setNode({ agent: event.target.value })}>{Object.keys(spec.spec.agents ?? {}).map((key) => <option key={key}>{key}</option>)}</select></Field>
      <Field label="Role"><input className={fieldClass} value={stringValue(agent?.["role"])} onChange={(event) => onSpecChange(updateAgentDeclaration(spec, agentKey, { role: event.target.value }))} /></Field>
      <Field label="Instructions"><textarea className="mt-1 min-h-28 w-full rounded-lg border border-gray-300 bg-transparent p-3 text-sm dark:border-gray-700" value={stringValue(agent?.["instructions"])} onChange={(event) => onSpecChange(updateAgentDeclaration(spec, agentKey, { instructions: event.target.value }))} /></Field>
      <Field label="Model"><input className={fieldClass} placeholder="model://general" value={stringValue(agent?.["model"])} onChange={(event) => onSpecChange(updateAgentDeclaration(spec, agentKey, event.target.value ? { model: event.target.value } : { model: undefined }))} /></Field>
    </> : null}
    {node.type === "join" ? <><Field label="Join strategy"><select className={fieldClass} value={stringValue(node["strategy"])} onChange={(event) => setNode({ strategy: event.target.value, quorum: event.target.value === "quorum" ? 1 : undefined })}>{["all", "any", "quorum", "first_success"].map((value) => <option key={value}>{value}</option>)}</select></Field>{node["strategy"] === "quorum" ? <Field label="Quorum"><input type="number" min={1} className={fieldClass} value={numberValue(node["quorum"], 1)} onChange={(event) => setNode({ quorum: Number(event.target.value) })} /></Field> : null}</> : null}
    {node.type === "reducer" ? <Field label="Reducer"><select className={fieldClass} value={stringValue(node["reducer"])} onChange={(event) => setNode({ reducer: event.target.value })}>{["merge_object", "concat", "first_success", "vote"].map((value) => <option key={value}>{value}</option>)}</select></Field> : null}
    {node.type === "approval" || node.type === "input" ? <><Field label="Prompt"><textarea className="mt-1 min-h-24 w-full rounded-lg border border-gray-300 bg-transparent p-3 text-sm dark:border-gray-700" value={stringValue(node["prompt"])} onChange={(event) => setNode({ prompt: event.target.value })} /></Field><JsonField label="Input schema" value={recordValue(node["inputSchema"])} onCommit={(value) => setNode({ inputSchema: value })} onError={onError} /></> : null}
    {node.type === "parallel" ? <p className="rounded-lg bg-gray-50 p-3 text-xs text-gray-500 dark:bg-gray-800">Branches are maintained by outgoing connections: {stringArray(node.branches).join(", ") || "none"}</p> : null}
  </aside>;
}

function JsonField({ label, value, onCommit, onError }: { label: string; value: Record<string, unknown>; onCommit: (value: Record<string, unknown>) => void; onError: (message: string) => void }) {
  const source = JSON.stringify(value, null, 2);
  const [text, setText] = React.useState(source);
  React.useEffect(() => setText(source), [source]);
  return <Field label={label}><textarea className="mt-1 min-h-28 w-full rounded-lg border border-gray-300 bg-transparent p-3 font-mono text-xs dark:border-gray-700" value={text} onChange={(event) => setText(event.target.value)} onBlur={() => { try { const parsed: unknown = JSON.parse(text); if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) throw new Error("must be an object"); onCommit(parsed as Record<string, unknown>); } catch (error) { onError(`Invalid ${label}: ${error instanceof Error ? error.message : "invalid JSON"}`); } }} /></Field>;
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return <label className="block text-xs font-medium text-gray-600 dark:text-gray-300">{label}{children}</label>;
}

function nodeLabel(type: string): string {
  return type === "input" ? "External Input" : type.replaceAll("_", " ");
}

function stringValue(value: unknown): string { return typeof value === "string" ? value : ""; }
function numberValue(value: unknown, fallback: number): number { return typeof value === "number" ? value : fallback; }
function recordValue(value: unknown): Record<string, unknown> { return value && typeof value === "object" && !Array.isArray(value) ? value as Record<string, unknown> : {}; }
function stringArray(value: unknown): string[] { return Array.isArray(value) ? value.filter((item): item is string => typeof item === "string") : []; }
