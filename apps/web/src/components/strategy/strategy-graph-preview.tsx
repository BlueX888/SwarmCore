import { Background, Controls, Handle, Position, ReactFlow, ReactFlowProvider, type Edge, type Node, type NodeProps } from "@xyflow/react";
import { Braces, GitBranch, Play } from "lucide-react";
import { nodeTypeLabel } from "@/lib/display-text";
import { isSwarmSpecDocument, listEdges, type StrategyNode, type SwarmSpecDocument } from "./strategy-editor-model";

interface PreviewNodeData extends Record<string, unknown> {
  label: string;
  nodeType: string;
  entrypoint: boolean;
}

type PreviewNode = Node<PreviewNodeData, "preview">;

export function StrategyGraphPreview({ spec }: { spec: Record<string, unknown> }) {
  if (!isSwarmSpecDocument(spec)) {
    return <div className="grid h-64 place-items-center rounded-xl border border-dashed border-gray-300 text-sm text-gray-500 dark:border-gray-700">该策略版本没有可预览的图设计。</div>;
  }
  return <ReactFlowProvider><StrategyGraph spec={spec} /></ReactFlowProvider>;
}

function StrategyGraph({ spec }: { spec: SwarmSpecDocument }) {
  const positions = layoutGraph(spec.spec.graph.nodes);
  const nodes: PreviewNode[] = Object.entries(spec.spec.graph.nodes).map(([key, node]) => ({
    id: key,
    type: "preview",
    position: positions[key] ?? { x: 40, y: 40 },
    data: { label: key, nodeType: node.type, entrypoint: spec.spec.graph.entrypoint === key },
  }));
  const edges: Edge[] = listEdges(spec).map((edge) => ({
    ...edge,
    type: "smoothstep",
    animated: edge.branch,
    style: { stroke: edge.branch ? "var(--color-brand-500)" : "var(--color-gray-400)", strokeWidth: edge.branch ? 2 : 1.5 },
  }));
  return <div className="h-80 overflow-hidden rounded-xl border border-gray-200 bg-gray-50 dark:border-gray-800 dark:bg-gray-950" data-testid="strategy-graph-preview" aria-label="策略图设计预览">
    <ReactFlow<PreviewNode>
      nodes={nodes}
      edges={edges}
      nodeTypes={{ preview: PreviewGraphNode }}
      fitView
      fitViewOptions={{ padding: 0.2 }}
      minZoom={0.25}
      maxZoom={1.5}
      nodesDraggable={false}
      nodesConnectable={false}
      elementsSelectable={false}
      deleteKeyCode={null}
    >
      <Background />
      <Controls showInteractive={false} />
    </ReactFlow>
  </div>;
}

function PreviewGraphNode({ data }: NodeProps<PreviewNode>) {
  return <div className={`min-w-40 rounded-xl border-2 bg-white px-4 py-3 shadow-sm dark:bg-gray-900 ${data.entrypoint ? "border-brand-500" : "border-gray-300 dark:border-gray-700"}`}>
    <Handle type="target" position={Position.Left} isConnectable={false} />
    <div className="flex items-center gap-2">
      {data.nodeType === "parallel" ? <GitBranch className="size-4 text-brand-500" /> : <Braces className="size-4 text-gray-500" />}
      <strong className="text-sm text-gray-900 dark:text-white">{data.label}</strong>
    </div>
    <div className="mt-1 flex items-center gap-2 text-[11px] text-gray-500"><span>{nodeTypeLabel(data.nodeType)}</span>{data.entrypoint ? <span className="inline-flex items-center gap-1 text-success-600"><Play className="size-3" />入口</span> : null}</div>
    <Handle type="source" position={Position.Right} isConnectable={false} />
  </div>;
}

function layoutGraph(nodes: Record<string, StrategyNode>) {
  const depths = new Map<string, number>();
  const visiting = new Set<string>();
  const depthOf = (key: string): number => {
    const known = depths.get(key);
    if (known !== undefined) return known;
    if (visiting.has(key)) return 0;
    visiting.add(key);
    const dependencies = nodes[key]?.dependsOn?.filter((dependency) => nodes[dependency]) ?? [];
    const depth = dependencies.length ? Math.max(...dependencies.map(depthOf)) + 1 : 0;
    visiting.delete(key);
    depths.set(key, depth);
    return depth;
  };
  Object.keys(nodes).forEach(depthOf);
  const layers = new Map<number, string[]>();
  for (const key of Object.keys(nodes)) {
    const depth = depths.get(key) ?? 0;
    layers.set(depth, [...(layers.get(depth) ?? []), key]);
  }
  return Object.fromEntries([...layers.entries()].flatMap(([depth, keys]) => keys.map((key, index) => [key, { x: 50 + depth * 230, y: 35 + index * 110 }])));
}
