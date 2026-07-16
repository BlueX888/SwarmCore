import type { Diagnostic } from "@/api/types";

export const SUPPORTED_NODE_TYPES = [
  "agent",
  "parallel",
  "join",
  "reducer",
  "approval",
  "input",
] as const;

export type SupportedNodeType = (typeof SUPPORTED_NODE_TYPES)[number];
export type Position = { x: number; y: number };
export interface EditorState {
  positions: Record<string, Position>;
  viewport: { x: number; y: number; zoom: number };
}

export type StrategyNode = Record<string, unknown> & {
  type: string;
  dependsOn?: string[];
  branches?: string[];
};

export interface SwarmSpecDocument extends Record<string, unknown> {
  apiVersion: string;
  kind: string;
  metadata: Record<string, unknown> & { name?: string };
  spec: Record<string, unknown> & {
    agents?: Record<string, Record<string, unknown>>;
    graph: Record<string, unknown> & {
      entrypoint: string;
      nodes: Record<string, StrategyNode>;
      output: Record<string, unknown>;
    };
  };
}

export interface StrategyEdge {
  id: string;
  source: string;
  target: string;
  branch: boolean;
}

export interface ConnectResult {
  spec: SwarmSpecDocument;
  error?: string;
}

export const EMPTY_EDITOR_STATE: EditorState = {
  positions: {},
  viewport: { x: 0, y: 0, zoom: 1 },
};

export function isSwarmSpecDocument(value: Record<string, unknown>): value is SwarmSpecDocument {
  const spec = value["spec"];
  if (!spec || typeof spec !== "object" || Array.isArray(spec)) return false;
  const graph = (spec as Record<string, unknown>)["graph"];
  if (!graph || typeof graph !== "object" || Array.isArray(graph)) return false;
  const nodes = (graph as Record<string, unknown>)["nodes"];
  return Boolean(nodes && typeof nodes === "object" && !Array.isArray(nodes));
}

export function createBlankSpec(name = "untitled-strategy"): SwarmSpecDocument {
  return {
    apiVersion: "swarmcore.io/v1",
    kind: "SwarmStrategy",
    metadata: { name },
    spec: {
      inputSchema: { type: "object" },
      outputSchema: { type: "object" },
      defaults: {},
      budget: {},
      agents: {},
      graph: { entrypoint: "", nodes: {}, output: {} },
      $defs: {},
    },
  };
}

export function cloneSpec(spec: SwarmSpecDocument): SwarmSpecDocument {
  return structuredClone(spec);
}

export function isSupportedNode(node: StrategyNode): node is StrategyNode & { type: SupportedNodeType } {
  return SUPPORTED_NODE_TYPES.includes(node.type as SupportedNodeType);
}

export function listEdges(spec: SwarmSpecDocument): StrategyEdge[] {
  const nodes = spec.spec.graph.nodes;
  const pairs = new Map<string, StrategyEdge>();
  for (const [target, node] of Object.entries(nodes)) {
    for (const source of stringList(node.dependsOn)) {
      if (!nodes[source]) continue;
      const id = edgeId(source, target);
      pairs.set(id, { id, source, target, branch: false });
    }
  }
  for (const [source, node] of Object.entries(nodes)) {
    if (node.type !== "parallel") continue;
    for (const target of stringList(node.branches)) {
      if (!nodes[target]) continue;
      const id = edgeId(source, target);
      pairs.set(id, { id, source, target, branch: true });
    }
  }
  return [...pairs.values()];
}

export function wouldCreateCycle(spec: SwarmSpecDocument, source: string, target: string): boolean {
  if (source === target) return true;
  const successors = new Map<string, Set<string>>();
  for (const key of Object.keys(spec.spec.graph.nodes)) successors.set(key, new Set());
  for (const edge of listEdges(spec)) successors.get(edge.source)?.add(edge.target);
  successors.get(source)?.add(target);
  const pending = [target];
  const visited = new Set<string>();
  while (pending.length) {
    const current = pending.pop();
    if (!current || visited.has(current)) continue;
    if (current === source) return true;
    visited.add(current);
    pending.push(...(successors.get(current) ?? []));
  }
  return false;
}

export function connectNodes(spec: SwarmSpecDocument, source: string, target: string): ConnectResult {
  const nodes = spec.spec.graph.nodes;
  const sourceNode = nodes[source];
  const targetNode = nodes[target];
  if (!sourceNode || !targetNode) return { spec, error: "Both connection endpoints must exist." };
  if (source === target) return { spec, error: "A node cannot connect to itself." };
  const dependencyExists = stringList(targetNode.dependsOn).includes(source);
  const branchExists = sourceNode.type === "parallel" && stringList(sourceNode.branches).includes(target);
  if (dependencyExists && (sourceNode.type !== "parallel" || branchExists)) {
    return { spec, error: "This connection already exists." };
  }
  if (wouldCreateCycle(spec, source, target)) {
    return { spec, error: "This connection would create a cycle." };
  }
  const next = cloneSpec(spec);
  const nextSource = next.spec.graph.nodes[source];
  const nextTarget = next.spec.graph.nodes[target];
  nextTarget.dependsOn = unique([...stringList(nextTarget.dependsOn), source]);
  if (nextSource.type === "parallel") {
    nextSource.branches = unique([...stringList(nextSource.branches), target]);
  }
  return { spec: next };
}

export function disconnectNodes(
  spec: SwarmSpecDocument,
  source: string,
  target: string,
): SwarmSpecDocument {
  const next = cloneSpec(spec);
  const sourceNode = next.spec.graph.nodes[source];
  const targetNode = next.spec.graph.nodes[target];
  if (targetNode) targetNode.dependsOn = stringList(targetNode.dependsOn).filter((item) => item !== source);
  if (sourceNode?.type === "parallel") {
    sourceNode.branches = stringList(sourceNode.branches).filter((item) => item !== target);
  }
  return next;
}

export function addNode(
  spec: SwarmSpecDocument,
  type: SupportedNodeType,
  position?: Position,
  editorState: EditorState = EMPTY_EDITOR_STATE,
): { spec: SwarmSpecDocument; editorState: EditorState; nodeKey: string } {
  const next = cloneSpec(spec);
  const nodeKey = nextNodeKey(next, type);
  next.spec.graph.nodes[nodeKey] = defaultNode(type, nodeKey);
  if (!next.spec.graph.entrypoint) next.spec.graph.entrypoint = nodeKey;
  if (type === "agent") {
    next.spec.agents ??= {};
    next.spec.agents[nodeKey] = {
      role: "Worker",
      instructions: "Complete the assigned task.",
    };
  }
  return {
    spec: next,
    editorState: {
      ...editorState,
      positions: { ...editorState.positions, [nodeKey]: position ?? autoPosition(Object.keys(next.spec.graph.nodes).length - 1) },
    },
    nodeKey,
  };
}

export function deleteNode(
  spec: SwarmSpecDocument,
  editorState: EditorState,
  nodeKey: string,
  removeUnusedAgent = false,
): { spec: SwarmSpecDocument; editorState: EditorState } {
  const next = cloneSpec(spec);
  const removed = next.spec.graph.nodes[nodeKey];
  const { [nodeKey]: removedNode, ...remainingNodes } = next.spec.graph.nodes;
  void removedNode;
  next.spec.graph.nodes = remainingNodes;
  for (const node of Object.values(next.spec.graph.nodes)) {
    node.dependsOn = stringList(node.dependsOn).filter((item) => item !== nodeKey);
    if (node.type === "parallel") {
      node.branches = stringList(node.branches).filter((item) => item !== nodeKey);
    }
  }
  if (next.spec.graph.entrypoint === nodeKey) {
    next.spec.graph.entrypoint = Object.keys(next.spec.graph.nodes)[0] ?? "";
  }
  if (removeUnusedAgent && removed?.type === "agent" && typeof removed["agent"] === "string") {
    const agentKey = removed["agent"];
    const stillUsed = Object.values(next.spec.graph.nodes).some(
      (node) => node.type === "agent" && node["agent"] === agentKey,
    );
    if (!stillUsed && next.spec.agents) {
      const { [agentKey]: removedAgent, ...remainingAgents } = next.spec.agents;
      void removedAgent;
      next.spec.agents = remainingAgents;
    }
  }
  const { [nodeKey]: removedPosition, ...positions } = editorState.positions;
  void removedPosition;
  return { spec: next, editorState: { ...editorState, positions } };
}

export function setEntrypoint(spec: SwarmSpecDocument, nodeKey: string): SwarmSpecDocument {
  if (!spec.spec.graph.nodes[nodeKey]) return spec;
  const next = cloneSpec(spec);
  next.spec.graph.entrypoint = nodeKey;
  return next;
}

export function updateNode(
  spec: SwarmSpecDocument,
  nodeKey: string,
  patch: Record<string, unknown>,
): SwarmSpecDocument {
  if (!spec.spec.graph.nodes[nodeKey]) return spec;
  const next = cloneSpec(spec);
  next.spec.graph.nodes[nodeKey] = { ...next.spec.graph.nodes[nodeKey], ...patch } as StrategyNode;
  return next;
}

export function updateAgentDeclaration(
  spec: SwarmSpecDocument,
  agentKey: string,
  patch: Record<string, unknown>,
): SwarmSpecDocument {
  const next = cloneSpec(spec);
  next.spec.agents ??= {};
  next.spec.agents[agentKey] = { ...(next.spec.agents[agentKey] ?? {}), ...patch };
  return next;
}

export function diagnosticNodeKey(diagnostic: Diagnostic, spec: SwarmSpecDocument): string | null {
  const nodeMatch = /^\$\.spec\.graph\.nodes\.([a-z][a-z0-9_-]*)/.exec(diagnostic.path);
  if (nodeMatch?.[1] && spec.spec.graph.nodes[nodeMatch[1]]) return nodeMatch[1];
  const agentMatch = /^\$\.spec\.agents\.([a-z][a-z0-9_-]*)/.exec(diagnostic.path);
  if (!agentMatch?.[1]) return null;
  return Object.entries(spec.spec.graph.nodes).find(
    ([, node]) => node.type === "agent" && node["agent"] === agentMatch[1],
  )?.[0] ?? null;
}

function defaultNode(type: SupportedNodeType, nodeKey: string): StrategyNode {
  switch (type) {
    case "agent": return { type, agent: nodeKey, dependsOn: [] };
    case "parallel": return { type, branches: [], dependsOn: [] };
    case "join": return { type, strategy: "all", dependsOn: [] };
    case "reducer": return { type, reducer: "merge_object", dependsOn: [] };
    case "approval": return { type, prompt: "Approve this step?", inputSchema: { type: "object" }, dependsOn: [] };
    case "input": return { type, prompt: "Provide input", inputSchema: { type: "object" }, dependsOn: [] };
  }
}

function nextNodeKey(spec: SwarmSpecDocument, type: SupportedNodeType): string {
  let index = 1;
  while (spec.spec.graph.nodes[`${type}-${index}`]) index += 1;
  return `${type}-${index}`;
}

function autoPosition(index: number): Position {
  return { x: 80 + (index % 3) * 240, y: 80 + Math.floor(index / 3) * 160 };
}

function stringList(value: unknown): string[] {
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === "string") : [];
}

function unique(values: string[]): string[] {
  return [...new Set(values)];
}

function edgeId(source: string, target: string): string {
  return `${source}--${target}`;
}
