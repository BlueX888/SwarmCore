import { describe, expect, it } from "vitest";
import type { Diagnostic, SavedConfiguration } from "@/api/types";
import {
  EMPTY_EDITOR_STATE,
  addNode,
  applySavedConfiguration,
  assignAgentDeclaration,
  bindProjectAgentToNode,
  connectNodes,
  createBlankSpec,
  deleteNode,
  diagnosticNodeKey,
  disconnectNodes,
  extractProjectAgentDeclaration,
  isBindableAgentConfiguration,
  layoutStrategyEditorState,
  layoutStrategyGraph,
  listEdges,
  normalizeEditorState,
  unbindAgentFromNode,
  wouldCreateCycle,
} from "./strategy-editor-model";

const CONFIG_META = {
  createdBy: "test",
  updatedBy: "test",
  createdAt: "2026-01-01",
  updatedAt: "2026-01-01",
};

function agentConfiguration(overrides?: Partial<SavedConfiguration>): SavedConfiguration {
  return {
    configurationId: "cfg-reviewer",
    kind: "agent",
    name: "合同审查智能体",
    sourceRef: "inline/agno",
    revision: 1,
    configuration: {
      spec: {
        agents: {
          reviewer: {
            role: "审核员",
            instructions: "审核输入",
            model: "model://general@1",
            tools: ["tool://search@1"],
          },
        },
        graph: {
          entrypoint: "reviewer",
          nodes: { reviewer: { type: "agent", agent: "reviewer", dependsOn: [] } },
        },
      },
    },
    ...CONFIG_META,
    ...overrides,
  };
}

describe("Strategy Editor model", () => {
  it("applies saved agent, tool, and model configurations to an executable spec", () => {
    let spec = createBlankSpec();
    const common = { revision: 1, createdBy: "test", updatedBy: "test", createdAt: "2026-01-01", updatedAt: "2026-01-01" };
    spec = applySavedConfiguration(spec, {
      ...common, configurationId: "agent", kind: "agent", name: "审核员", sourceRef: "inline/agno",
      configuration: { spec: { agents: { reviewer: { role: "审核员", instructions: "审核输入", model: "model://general@1", tools: ["tool://search@1"] } } } },
    });
    spec = applySavedConfiguration(spec, {
      ...common, configurationId: "tool", kind: "tool", name: "搜索", sourceRef: "tool://search@1",
      configuration: { search: { type: "tool", tool: "tool://search@1", input: { query: "{{ input.query }}" } } },
    });
    spec = applySavedConfiguration(spec, {
      ...common, configurationId: "model", kind: "model", name: "默认模型", sourceRef: "model://general@1",
      configuration: { spec: { defaults: { model: "model://general@1" } } },
    });

    expect(spec.spec.agents?.reviewer).toMatchObject({ role: "审核员", model: "model://general@1" });
    expect(spec.spec.graph.nodes.reviewer).toMatchObject({ type: "agent", agent: "reviewer" });
    expect(spec.spec.graph.nodes.search).toMatchObject({ type: "tool", tool: "tool://search@1" });
    expect(spec.spec.defaults).toEqual({ model: "model://general@1" });
    expect(spec.spec.graph.entrypoint).toBe("reviewer");
  });

  it("maps normal and parallel connections without creating a second strategy format", () => {
    let spec = createBlankSpec();
    let state = structuredClone(EMPTY_EDITOR_STATE);
    const parallel = addNode(spec, "parallel", undefined, state);
    spec = parallel.spec; state = parallel.editorState;
    const agent = addNode(spec, "agent", undefined, state);
    spec = agent.spec;

    const connected = connectNodes(spec, parallel.nodeKey, agent.nodeKey);
    expect(connected.error).toBeUndefined();
    expect(connected.spec.spec.graph.nodes[agent.nodeKey]?.dependsOn).toEqual([parallel.nodeKey]);
    expect(connected.spec.spec.graph.nodes[parallel.nodeKey]?.branches).toEqual([agent.nodeKey]);
    expect(listEdges(connected.spec)).toEqual([expect.objectContaining({ source: parallel.nodeKey, target: agent.nodeKey, branch: true })]);

    const disconnected = disconnectNodes(connected.spec, parallel.nodeKey, agent.nodeKey);
    expect(disconnected.spec.graph.nodes[agent.nodeKey]?.dependsOn).toEqual([]);
    expect(disconnected.spec.graph.nodes[parallel.nodeKey]?.branches).toEqual([]);
  });

  it("rejects self, duplicate and cyclic connections", () => {
    let spec = createBlankSpec();
    let state = structuredClone(EMPTY_EDITOR_STATE);
    const first = addNode(spec, "agent", undefined, state); spec = first.spec; state = first.editorState;
    const second = addNode(spec, "approval", undefined, state); spec = second.spec;
    expect(connectNodes(spec, first.nodeKey, first.nodeKey).error).toContain("自身");
    spec = connectNodes(spec, first.nodeKey, second.nodeKey).spec;
    expect(connectNodes(spec, first.nodeKey, second.nodeKey).error).toContain("已存在");
    expect(wouldCreateCycle(spec, second.nodeKey, first.nodeKey)).toBe(true);
    expect(connectNodes(spec, second.nodeKey, first.nodeKey).error).toContain("循环");
  });

  it("lays out dependency stages from left to right and centers parallel branches", () => {
    const spec = createBlankSpec();
    spec.spec.graph.entrypoint = "read-contract";
    spec.spec.graph.nodes = {
      "read-contract": { type: "tool", tool: "tool://contract", dependsOn: [] },
      "read-performance": { type: "tool", tool: "tool://performance", dependsOn: ["read-contract"] },
      "read-risk": { type: "tool", tool: "tool://risk", dependsOn: ["read-performance"] },
      "read-invoice": { type: "tool", tool: "tool://invoice", dependsOn: ["read-performance"] },
      "read-deviation": { type: "tool", tool: "tool://deviation", dependsOn: ["read-performance"] },
      analyze: { type: "agent", agent: "analyst", dependsOn: ["read-risk", "read-invoice", "read-deviation"] },
    };

    const positions = layoutStrategyGraph(spec);

    expect(positions["read-contract"].x).toBeLessThan(positions["read-performance"].x);
    expect(positions["read-performance"].x).toBeLessThan(positions["read-risk"].x);
    expect(positions["read-risk"].x).toBe(positions["read-invoice"].x);
    expect(positions["read-invoice"].x).toBe(positions["read-deviation"].x);
    expect(positions["read-deviation"].x).toBeLessThan(positions.analyze.x);
    expect(positions["read-risk"].y).toBeLessThan(positions["read-invoice"].y);
    expect(positions["read-invoice"].y).toBeLessThan(positions["read-deviation"].y);
    expect(positions["read-contract"].y).toBe(positions["read-invoice"].y);
    expect(positions["read-performance"].y).toBe(positions["read-invoice"].y);
    expect(positions.analyze.y).toBe(positions["read-invoice"].y);
  });

  it("replaces saved positions when a strategy editor is opened", () => {
    const spec = createBlankSpec();
    spec.spec.graph.nodes = {
      first: { type: "tool", tool: "tool://first", dependsOn: [] },
      second: { type: "tool", tool: "tool://second", dependsOn: ["first"] },
    };
    const saved = {
      positions: {
        first: { x: 900, y: 900 },
        second: { x: 10, y: 10 },
      },
      viewport: { x: 12, y: 34, zoom: 0.7 },
      agentBindings: {
        first: {
          configurationId: "cfg-1",
          revision: 1,
          name: "保留绑定",
          sourceRef: "inline/agno",
        },
      },
    };

    const state = layoutStrategyEditorState(spec, saved);

    expect(state.positions.first.x).toBeLessThan(state.positions.second.x);
    expect(state.positions).not.toEqual(saved.positions);
    expect(state.viewport).toEqual(saved.viewport);
    expect(state.agentBindings).toEqual(saved.agentBindings);
  });

  it("removes dependencies and layout while preserving declarations by default", () => {
    let spec = createBlankSpec();
    let state = structuredClone(EMPTY_EDITOR_STATE);
    const agent = addNode(spec, "agent", { x: 12, y: 34 }, state); spec = agent.spec; state = agent.editorState;
    const approval = addNode(spec, "approval", undefined, state); spec = approval.spec; state = approval.editorState;
    spec = connectNodes(spec, agent.nodeKey, approval.nodeKey).spec;
    const result = deleteNode(spec, state, agent.nodeKey);
    expect(result.spec.spec.graph.nodes[agent.nodeKey]).toBeUndefined();
    expect(result.spec.spec.graph.nodes[approval.nodeKey]?.dependsOn).toEqual([]);
    expect(result.spec.spec.agents?.[agent.nodeKey]).toBeDefined();
    expect(result.editorState.positions[agent.nodeKey]).toBeUndefined();
  });

  it("does not mutate or drop unsupported nodes on import", () => {
    const spec = createBlankSpec();
    spec.spec.graph.nodes["legacy-tool"] = { type: "tool", tool: "tool://legacy", custom: { untouched: true } };
    spec.spec.graph.entrypoint = "legacy-tool";
    const before = JSON.stringify(spec);
    expect(listEdges(spec)).toEqual([]);
    expect(JSON.stringify(spec)).toBe(before);
    expect(spec.spec.graph.nodes["legacy-tool"]?.["custom"]).toEqual({ untouched: true });
  });

  it("keeps layout outside the Spec and locates compiler diagnostics", () => {
    const spec = createBlankSpec();
    const before = JSON.stringify(spec);
    const result = addNode(spec, "agent", { x: 999, y: 888 }, EMPTY_EDITOR_STATE);
    const semanticSpec = result.spec;
    const semanticBeforeMove = JSON.stringify(semanticSpec);
    const moved = { ...result.editorState, positions: { [result.nodeKey]: { x: 1, y: 2 } } };
    expect(JSON.stringify(semanticSpec)).toBe(semanticBeforeMove);
    expect(JSON.stringify(spec)).toBe(before);
    expect(moved.positions[result.nodeKey]).toEqual({ x: 1, y: 2 });
    const diagnostic: Diagnostic = { severity: "error", code: "TEST", path: `$.spec.graph.nodes.${result.nodeKey}.agent`, message: "bad" };
    expect(diagnosticNodeKey(diagnostic, semanticSpec)).toBe(result.nodeKey);
  });

  it("defaults missing agentBindings when normalizing editor state", () => {
    expect(normalizeEditorState({ positions: {}, viewport: { x: 0, y: 0, zoom: 1 } })).toEqual(EMPTY_EDITOR_STATE);
    expect(normalizeEditorState(undefined).agentBindings).toEqual({});
  });

  it("binds a project agent snapshot into the selected node declaration", () => {
    const agent = addNode(createBlankSpec(), "agent", undefined, structuredClone(EMPTY_EDITOR_STATE));
    const saved = agentConfiguration();

    const bound = bindProjectAgentToNode(agent.spec, agent.editorState, agent.nodeKey, saved);

    expect(bound.spec.spec.agents?.[agent.nodeKey]).toMatchObject({
      role: "审核员",
      instructions: "审核输入",
      model: "model://general@1",
    });
    expect(bound.spec.spec.graph.nodes[agent.nodeKey]?.agent).toBe(agent.nodeKey);
    expect(bound.editorState.agentBindings[agent.nodeKey]).toEqual({
      configurationId: "cfg-reviewer",
      revision: 1,
      name: "合同审查智能体",
      sourceRef: "inline/agno",
    });
  });

  it("splits shared agent declarations when binding one node", () => {
    let spec = createBlankSpec();
    let state = structuredClone(EMPTY_EDITOR_STATE);
    const first = addNode(spec, "agent", undefined, state);
    spec = first.spec;
    state = first.editorState;
    const second = addNode(spec, "agent", undefined, state);
    spec = second.spec;
    state = second.editorState;
    spec.spec.agents = {
      shared: { role: "共享", instructions: "共享指令", model: "model://general@1" },
    };
    spec.spec.graph.nodes[first.nodeKey] = { type: "agent", agent: "shared", dependsOn: [] };
    spec.spec.graph.nodes[second.nodeKey] = { type: "agent", agent: "shared", dependsOn: [] };

    const bound = bindProjectAgentToNode(spec, state, first.nodeKey, agentConfiguration({ revision: 2 }));

    expect(bound.spec.spec.graph.nodes[first.nodeKey]?.agent).toBe(first.nodeKey);
    expect(bound.spec.spec.agents?.[first.nodeKey]).toMatchObject({ role: "审核员", instructions: "审核输入" });
    expect(bound.spec.spec.graph.nodes[second.nodeKey]?.agent).toBe("shared");
    expect(bound.spec.spec.agents?.shared).toMatchObject({ role: "共享", instructions: "共享指令" });
  });

  it("keeps the declaration snapshot when unbinding and clears binding metadata", () => {
    const agent = addNode(createBlankSpec(), "agent", undefined, structuredClone(EMPTY_EDITOR_STATE));
    const bound = bindProjectAgentToNode(agent.spec, agent.editorState, agent.nodeKey, agentConfiguration());
    const unbound = unbindAgentFromNode(bound.editorState, agent.nodeKey);
    expect(unbound.agentBindings[agent.nodeKey]).toBeUndefined();
    expect(bound.spec.spec.agents?.[agent.nodeKey]).toMatchObject({ role: "审核员" });
  });

  it("removes agentBindings when deleting a node and preserves bindings on layout", () => {
    const agent = addNode(createBlankSpec(), "agent", { x: 1, y: 2 }, structuredClone(EMPTY_EDITOR_STATE));
    const bound = bindProjectAgentToNode(agent.spec, agent.editorState, agent.nodeKey, agentConfiguration());
    const laidOut = layoutStrategyEditorState(bound.spec, bound.editorState);
    expect(laidOut.agentBindings[agent.nodeKey]?.revision).toBe(1);
    const deleted = deleteNode(bound.spec, bound.editorState, agent.nodeKey);
    expect(deleted.editorState.agentBindings[agent.nodeKey]).toBeUndefined();
  });

  it("rejects invalid agent configurations for binding", () => {
    const invalid = agentConfiguration({
      configuration: { spec: { agents: {}, graph: { entrypoint: "missing", nodes: {} } } },
    });
    expect(isBindableAgentConfiguration(invalid)).toBe(false);
    expect(() => extractProjectAgentDeclaration(invalid)).toThrow(/配置格式无效/);
    expect(() => extractProjectAgentDeclaration(agentConfiguration({ kind: "tool" }))).toThrow(/只能绑定智能体/);
  });

  it("renames agent declarations and updates node references", () => {
    const agent = addNode(createBlankSpec(), "agent");
    const renamed = assignAgentDeclaration(agent.spec, agent.nodeKey, "planner");
    expect(renamed.spec.agents?.planner).toMatchObject({ role: "执行者", instructions: "完成分配的任务。" });
    expect(renamed.spec.agents?.[agent.nodeKey]).toBeUndefined();
    expect(renamed.spec.graph.nodes[agent.nodeKey]?.agent).toBe("planner");
  });

  it("rebinds a node to an existing declaration and drops unused keys", () => {
    let spec = createBlankSpec();
    const first = addNode(spec, "agent");
    spec = first.spec;
    const second = addNode(spec, "agent");
    spec = second.spec;
    const rebound = assignAgentDeclaration(spec, second.nodeKey, first.nodeKey);
    expect(rebound.spec.graph.nodes[second.nodeKey]?.agent).toBe(first.nodeKey);
    expect(rebound.spec.agents?.[second.nodeKey]).toBeUndefined();
    expect(rebound.spec.agents?.[first.nodeKey]).toBeDefined();
  });

  it("rejects invalid custom agent declaration names", () => {
    const agent = addNode(createBlankSpec(), "agent");
    expect(() => assignAgentDeclaration(agent.spec, agent.nodeKey, "Planner")).toThrow(/智能体声明名称无效/);
    expect(() => assignAgentDeclaration(agent.spec, agent.nodeKey, "1agent")).toThrow(/智能体声明名称无效/);
  });
});
