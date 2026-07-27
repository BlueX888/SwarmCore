import { Background, Controls, Handle, MarkerType, Position, ReactFlow, ReactFlowProvider, type Edge, type Node, type NodeProps } from "@xyflow/react";
import { Braces, GitBranch, Play } from "lucide-react";
import { nodeTypeLabel } from "@/lib/display-text";
import { isSwarmSpecDocument, layoutStrategyGraph, listEdges, type SwarmSpecDocument } from "./strategy-editor-model";

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
  const positions = layoutStrategyGraph(spec);
  const nodes: PreviewNode[] = Object.entries(spec.spec.graph.nodes).map(([key, node]) => ({
    id: key,
    type: "preview",
    position: positions[key] ?? { x: 40, y: 40 },
    data: { label: key, nodeType: node.type, entrypoint: spec.spec.graph.entrypoint === key },
  }));
  const edges: Edge[] = listEdges(spec).map((edge) => {
    const color = edge.branch ? "var(--color-brand-500)" : "var(--color-gray-500)";
    return {
      ...edge,
      type: "smoothstep",
      animated: edge.branch,
      markerEnd: { type: MarkerType.ArrowClosed, color, width: 16, height: 16 },
      style: { stroke: color, strokeWidth: edge.branch ? 2 : 1.5 },
    };
  });
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
