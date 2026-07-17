import { describe, expect, it } from "vitest";
import type { Diagnostic } from "@/api/types";
import {
  EMPTY_EDITOR_STATE,
  addNode,
  connectNodes,
  createBlankSpec,
  deleteNode,
  diagnosticNodeKey,
  disconnectNodes,
  listEdges,
  wouldCreateCycle,
} from "./strategy-editor-model";

describe("Strategy Editor model", () => {
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
});
