import type { Diagnostic, SavedConfiguration } from "@/api/types";

export const SUPPORTED_NODE_TYPES = [
  "agent",
  "tool",
  "parallel",
  "join",
  "reducer",
  "approval",
  "input",
] as const;

export type SupportedNodeType = (typeof SUPPORTED_NODE_TYPES)[number];
export type Position = { x: number; y: number };
export interface AgentBindingState {
  configurationId: string;
  revision: number;
  name: string;
  sourceRef: string;
}
export interface EditorState {
  positions: Record<string, Position>;
  viewport: { x: number; y: number; zoom: number };
  agentBindings: Record<string, AgentBindingState>;
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

export interface DirectedGraphEdge {
  source: string;
  target: string;
}

export interface ConnectResult {
  spec: SwarmSpecDocument;
  error?: string;
}

export const EMPTY_EDITOR_STATE: EditorState = {
  positions: {},
  viewport: { x: 0, y: 0, zoom: 1 },
  agentBindings: {},
};

export function normalizeEditorState(
  value?: Partial<EditorState> | null,
): EditorState {
  return {
    positions: value?.positions ? { ...value.positions } : {},
    viewport: value?.viewport
      ? { ...value.viewport }
      : { x: 0, y: 0, zoom: 1 },
    agentBindings: value?.agentBindings ? { ...value.agentBindings } : {},
  };
}

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

export function applySavedConfiguration(spec: SwarmSpecDocument, saved: SavedConfiguration): SwarmSpecDocument {
  const next = cloneSpec(spec);
  if (saved.kind === "model") {
    const savedSpec = objectValue(saved.configuration["spec"]);
    const defaults = objectValue(savedSpec["defaults"]);
    const model = defaults["model"];
    if (typeof model !== "string" || !model) throw new Error("模型配置缺少逻辑模型引用。");
    next.spec.defaults = { ...objectValue(next.spec.defaults), model };
    return next;
  }

  if (saved.kind === "agent") {
    const extracted = extractProjectAgentDeclaration(saved);
    const nodeKey = uniqueNodeKey(extracted.declarationKey, next.spec.graph.nodes);
    next.spec.agents = { ...next.spec.agents, [nodeKey]: extracted.declaration };
    next.spec.graph.nodes[nodeKey] = { type: "agent", agent: nodeKey, dependsOn: [] };
    if (!next.spec.graph.entrypoint) next.spec.graph.entrypoint = nodeKey;
    return next;
  }

  const entries = Object.entries(saved.configuration);
  const [sourceKey, node] = entries[0] ?? [];
  const toolNode = objectValue(node);
  if (!sourceKey || toolNode["type"] !== "tool") {
    throw new Error("工具配置缺少工具节点声明。");
  }
  const nodeKey = uniqueNodeKey(sourceKey, next.spec.graph.nodes);
  next.spec.graph.nodes[nodeKey] = { ...structuredClone(toolNode as StrategyNode), dependsOn: [] };
  if (!next.spec.graph.entrypoint) next.spec.graph.entrypoint = nodeKey;
  return next;
}

export function extractProjectAgentDeclaration(saved: SavedConfiguration): {
  declarationKey: string;
  declaration: Record<string, unknown>;
} {
  if (saved.kind !== "agent") {
    throw new Error("只能绑定智能体配置。");
  }
  const savedSpec = objectValue(saved.configuration["spec"]);
  const agents = objectValue(savedSpec["agents"]);
  const graph = objectValue(savedSpec["graph"]);
  const entrypoint = typeof graph["entrypoint"] === "string" ? graph["entrypoint"] : "";
  const nodes = objectValue(graph["nodes"]);
  const entryNode = entrypoint ? objectValue(nodes[entrypoint]) : {};
  let declarationKey = "";
  if (entryNode["type"] === "agent" && typeof entryNode["agent"] === "string" && agents[entryNode["agent"]]) {
    declarationKey = entryNode["agent"];
  } else if (entrypoint && agents[entrypoint]) {
    declarationKey = entrypoint;
  } else {
    declarationKey = Object.keys(agents)[0] ?? "";
  }
  const declaration = agents[declarationKey];
  if (!declarationKey || !declaration || typeof declaration !== "object" || Array.isArray(declaration)) {
    throw new Error("配置格式无效：缺少有效入口智能体声明。");
  }
  return {
    declarationKey,
    declaration: structuredClone(declaration as Record<string, unknown>),
  };
}

export function isBindableAgentConfiguration(saved: SavedConfiguration): boolean {
  try {
    extractProjectAgentDeclaration(saved);
    return true;
  } catch {
    return false;
  }
}

export function bindProjectAgentToNode(
  spec: SwarmSpecDocument,
  editorState: EditorState,
  nodeKey: string,
  saved: SavedConfiguration,
): { spec: SwarmSpecDocument; editorState: EditorState } {
  const node = spec.spec.graph.nodes[nodeKey];
  if (!node || node.type !== "agent") {
    throw new Error("只能绑定智能体节点。");
  }
  const extracted = extractProjectAgentDeclaration(saved);
  const next = cloneSpec(spec);
  next.spec.agents ??= {};
  const currentAgentKey = typeof node["agent"] === "string" ? node["agent"] : "";
  const referenceCount = currentAgentKey
    ? Object.values(next.spec.graph.nodes).filter(
      (candidate) => candidate.type === "agent" && candidate["agent"] === currentAgentKey,
    ).length
    : 0;
  const shared = referenceCount > 1;
  const targetKey = shared
    ? uniqueDeclarationKey(nodeKey, next.spec.agents)
    : (currentAgentKey || uniqueDeclarationKey(nodeKey, next.spec.agents));
  next.spec.agents[targetKey] = extracted.declaration;
  next.spec.graph.nodes[nodeKey] = { ...next.spec.graph.nodes[nodeKey], agent: targetKey };
  if (currentAgentKey && currentAgentKey !== targetKey) {
    const stillUsed = Object.values(next.spec.graph.nodes).some(
      (candidate) => candidate.type === "agent" && candidate["agent"] === currentAgentKey,
    );
    if (!stillUsed) {
      const { [currentAgentKey]: removedAgent, ...remainingAgents } = next.spec.agents;
      void removedAgent;
      next.spec.agents = remainingAgents;
    }
  }
  const normalized = normalizeEditorState(editorState);
  return {
    spec: next,
    editorState: {
      ...normalized,
      agentBindings: {
        ...normalized.agentBindings,
        [nodeKey]: {
          configurationId: saved.configurationId,
          revision: saved.revision,
          name: saved.name,
          sourceRef: saved.sourceRef,
        },
      },
    },
  };
}

export function unbindAgentFromNode(
  editorState: EditorState,
  nodeKey: string,
): EditorState {
  const normalized = normalizeEditorState(editorState);
  const { [nodeKey]: removedBinding, ...agentBindings } = normalized.agentBindings;
  void removedBinding;
  return { ...normalized, agentBindings };
}

function uniqueNodeKey(preferred: string, nodes: Record<string, StrategyNode>): string {
  if (!nodes[preferred]) return preferred;
  let suffix = 2;
  while (nodes[`${preferred}-${suffix}`]) suffix += 1;
  return `${preferred}-${suffix}`;
}

function uniqueDeclarationKey(
  preferred: string,
  agents: Record<string, Record<string, unknown>>,
): string {
  if (!agents[preferred]) return preferred;
  let suffix = 2;
  while (agents[`${preferred}-${suffix}`]) suffix += 1;
  return `${preferred}-${suffix}`;
}

function objectValue(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value) ? value as Record<string, unknown> : {};
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

export function layoutStrategyGraph(spec: SwarmSpecDocument): Record<string, Position> {
  const nodeKeys = Object.keys(spec.spec.graph.nodes);
  return layoutDirectedGraph(nodeKeys, listEdges(spec));
}

export function layoutDirectedGraph(
  nodeKeys: string[],
  edges: DirectedGraphEdge[],
): Record<string, Position> {
  const nodeOrder = new Map(nodeKeys.map((key, index) => [key, index]));
  const predecessors = new Map(nodeKeys.map((key) => [key, [] as string[]]));
  const successors = new Map(nodeKeys.map((key) => [key, [] as string[]]));
  for (const edge of edges) {
    predecessors.get(edge.target)?.push(edge.source);
    successors.get(edge.source)?.push(edge.target);
  }

  const depths = new Map<string, number>();
  const visiting = new Set<string>();
  const depthOf = (key: string): number => {
    const known = depths.get(key);
    if (known !== undefined) return known;
    if (visiting.has(key)) return 0;
    visiting.add(key);
    const dependencies = predecessors.get(key) ?? [];
    const depth = dependencies.length
      ? Math.max(...dependencies.map(depthOf)) + 1
      : 0;
    visiting.delete(key);
    depths.set(key, depth);
    return depth;
  };
  nodeKeys.forEach(depthOf);

  const layers = new Map<number, string[]>();
  for (const key of nodeKeys) {
    const depth = depths.get(key) ?? 0;
    layers.set(depth, [...(layers.get(depth) ?? []), key]);
  }

  const layerDepths = [...layers.keys()].sort((left, right) => left - right);
  const neighborPosition = (key: string): number => {
    const depth = depths.get(key) ?? 0;
    const layer = layers.get(depth) ?? [];
    return layer.indexOf(key) - (layer.length - 1) / 2;
  };
  const reorderLayer = (keys: string[], neighbors: Map<string, string[]>): void => {
    const previousOrder = new Map(keys.map((key, index) => [key, index]));
    const score = (key: string): number | null => {
      const connected = neighbors.get(key) ?? [];
      if (!connected.length) return null;
      return connected.reduce((total, neighbor) => total + neighborPosition(neighbor), 0) / connected.length;
    };
    keys.sort((left, right) => {
      const leftScore = score(left);
      const rightScore = score(right);
      if (leftScore !== null && rightScore !== null && leftScore !== rightScore) {
        return leftScore - rightScore;
      }
      if (leftScore !== null && rightScore === null) return -1;
      if (leftScore === null && rightScore !== null) return 1;
      return (previousOrder.get(left) ?? nodeOrder.get(left) ?? 0)
        - (previousOrder.get(right) ?? nodeOrder.get(right) ?? 0);
    });
  };
  for (let sweep = 0; sweep < 4; sweep += 1) {
    for (const depth of layerDepths.slice(1)) {
      reorderLayer(layers.get(depth) ?? [], predecessors);
    }
    for (const depth of layerDepths.slice(0, -1).reverse()) {
      reorderLayer(layers.get(depth) ?? [], successors);
    }
  }

  const horizontalGap = 240;
  const verticalGap = 140;
  const tallestLayer = Math.max(0, ...[...layers.values()].map((keys) => (keys.length - 1) * verticalGap));
  return Object.fromEntries(
    [...layers.entries()].flatMap(([depth, keys]) =>
      keys.map((key, index) => {
        const layerHeight = (keys.length - 1) * verticalGap;
        return [key, {
          x: 80 + depth * horizontalGap,
          y: 80 + (tallestLayer - layerHeight) / 2 + index * verticalGap,
        }];
      }),
    ),
  );
}

export function layoutStrategyEditorState(
  spec: SwarmSpecDocument,
  editorState: EditorState | Partial<EditorState> = EMPTY_EDITOR_STATE,
): EditorState {
  const normalized = normalizeEditorState(editorState);
  return {
    ...normalized,
    positions: layoutStrategyGraph(spec),
  };
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
  if (!sourceNode || !targetNode) return { spec, error: "连接的两个端点都必须存在。" };
  if (source === target) return { spec, error: "节点不能连接到自身。" };
  const dependencyExists = stringList(targetNode.dependsOn).includes(source);
  const branchExists = sourceNode.type === "parallel" && stringList(sourceNode.branches).includes(target);
  if (dependencyExists && (sourceNode.type !== "parallel" || branchExists)) {
    return { spec, error: "该连接已存在。" };
  }
  if (wouldCreateCycle(spec, source, target)) {
    return { spec, error: "该连接会形成循环。" };
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
      role: "执行者",
      instructions: "完成分配的任务。",
    };
  }
  const normalized = normalizeEditorState(editorState);
  return {
    spec: next,
    editorState: {
      ...normalized,
      positions: {
        ...normalized.positions,
        [nodeKey]: position ?? autoPosition(Object.keys(next.spec.graph.nodes).length - 1),
      },
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
  const normalized = normalizeEditorState(editorState);
  const { [nodeKey]: removedPosition, ...positions } = normalized.positions;
  void removedPosition;
  const { [nodeKey]: removedBinding, ...agentBindings } = normalized.agentBindings;
  void removedBinding;
  return { spec: next, editorState: { ...normalized, positions, agentBindings } };
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

const AGENT_KEY_RE = /^[a-z][a-z0-9_-]{0,62}$/;

export function isValidAgentDeclarationKey(key: string): boolean {
  return AGENT_KEY_RE.test(key);
}

/** Assign or rename the agent declaration referenced by a node. */
export function assignAgentDeclaration(
  spec: SwarmSpecDocument,
  nodeKey: string,
  nextAgentKey: string,
): SwarmSpecDocument {
  const node = spec.spec.graph.nodes[nodeKey];
  if (!node || node.type !== "agent") {
    throw new Error("只能为智能体节点设置声明名称。");
  }
  const trimmed = nextAgentKey.trim();
  const currentKey = typeof node["agent"] === "string" ? node["agent"] : "";
  if (!trimmed || trimmed === currentKey) return spec;
  if (!isValidAgentDeclarationKey(trimmed)) {
    throw new Error("智能体声明名称无效：须以小写字母开头，仅含小写字母、数字、下划线或连字符，最长 63 个字符。");
  }

  const next = cloneSpec(spec);
  next.spec.agents ??= {};
  const agents = next.spec.agents;

  if (agents[trimmed]) {
    next.spec.graph.nodes[nodeKey] = { ...next.spec.graph.nodes[nodeKey], agent: trimmed };
    if (currentKey && currentKey !== trimmed) {
      const stillUsed = Object.values(next.spec.graph.nodes).some(
        (candidate) => candidate.type === "agent" && candidate["agent"] === currentKey,
      );
      if (!stillUsed) {
        const { [currentKey]: removedAgent, ...remainingAgents } = next.spec.agents;
        void removedAgent;
        next.spec.agents = remainingAgents;
      }
    }
    return next;
  }

  const declaration = (currentKey ? agents[currentKey] : undefined) ?? {
    role: "执行者",
    instructions: "完成分配的任务。",
  };
  if (currentKey && agents[currentKey]) {
    const { [currentKey]: removedAgent, ...remainingAgents } = agents;
    void removedAgent;
    next.spec.agents = { ...remainingAgents, [trimmed]: declaration };
    for (const [key, candidate] of Object.entries(next.spec.graph.nodes)) {
      if (candidate.type === "agent" && candidate["agent"] === currentKey) {
        next.spec.graph.nodes[key] = { ...candidate, agent: trimmed };
      }
    }
    return next;
  }

  next.spec.agents = { ...agents, [trimmed]: declaration };
  next.spec.graph.nodes[nodeKey] = { ...next.spec.graph.nodes[nodeKey], agent: trimmed };
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
    case "tool": return { type, tool: "tool://search@1", input: {}, dependsOn: [] };
    case "parallel": return { type, branches: [], dependsOn: [] };
    case "join": return { type, strategy: "all", dependsOn: [] };
    case "reducer": return { type, reducer: "merge_object", dependsOn: [] };
    case "approval": return { type, prompt: "是否批准此步骤？", inputSchema: { type: "object" }, dependsOn: [] };
    case "input": return { type, prompt: "请提供输入", inputSchema: { type: "object" }, dependsOn: [] };
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
