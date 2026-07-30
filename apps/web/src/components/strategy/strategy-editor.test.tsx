import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import * as React from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { SavedConfiguration } from "@/api/types";
import { StrategyEditor } from "./strategy-editor";
import {
  EMPTY_EDITOR_STATE,
  createBlankSpec,
  normalizeEditorState,
  type EditorState,
  type SwarmSpecDocument,
} from "./strategy-editor-model";

afterEach(cleanup);

const MODEL_REFS = ["model://general@1", "model://reasoner@1"];
const TOOL_REFS = ["tool://search@1", "tool://document/read@1"];

const AGENT_CONFIG: SavedConfiguration = {
  configurationId: "cfg-reviewer",
  kind: "agent",
  name: "合同审查智能体",
  sourceRef: "inline/agno",
  revision: 1,
  createdBy: "test",
  updatedBy: "test",
  createdAt: "2026-01-01",
  updatedAt: "2026-01-01",
  configuration: {
    spec: {
      agents: {
        reviewer: {
          role: "审核员",
          instructions: "审核输入",
          model: "model://general@1",
        },
      },
      graph: {
        entrypoint: "reviewer",
        nodes: { reviewer: { type: "agent", agent: "reviewer", dependsOn: [] } },
      },
    },
  },
};

function agentSpec(): SwarmSpecDocument {
  const spec = createBlankSpec("agent-strategy");
  spec.spec.agents = {
    planner: {
      role: "Planner",
      instructions: "Plan the work.",
      model: "model://custom@9",
    },
  };
  spec.spec.graph.entrypoint = "planner";
  spec.spec.graph.nodes = {
    planner: { type: "agent", agent: "planner", dependsOn: [] },
  };
  return spec;
}

function toolSpec(): SwarmSpecDocument {
  const spec = createBlankSpec("tool-strategy");
  spec.spec.graph.entrypoint = "search";
  spec.spec.graph.nodes = {
    search: { type: "tool", tool: "tool://legacy@3", input: { query: "q" }, dependsOn: [] },
  };
  return spec;
}

function Harness({
  initial = createBlankSpec(),
  models = MODEL_REFS,
  tools = TOOL_REFS,
  agentConfigurations = [] as SavedConfiguration[],
  initialEditorState = EMPTY_EDITOR_STATE,
  nodeTypes = ["agent", "parallel", "join", "reducer", "approval", "input"],
}: {
  initial?: SwarmSpecDocument;
  models?: string[];
  tools?: string[];
  agentConfigurations?: SavedConfiguration[];
  initialEditorState?: EditorState;
  nodeTypes?: string[];
}) {
  const [spec, setSpec] = React.useState(initial);
  const [editorState, setEditorState] = React.useState(() => normalizeEditorState(initialEditorState));
  return <>
    <StrategyEditor
      spec={spec}
      editorState={editorState}
      nodeTypes={nodeTypes}
      models={models}
      tools={tools}
      agentConfigurations={agentConfigurations}
      diagnostics={[]}
      onSpecChange={setSpec}
      onEditorStateChange={setEditorState}
      onError={vi.fn()}
    />
    <output data-testid="active-spec">{JSON.stringify(spec)}</output>
    <output data-testid="active-editor-state">{JSON.stringify(editorState)}</output>
  </>;
}

describe("StrategyEditor", () => {
  it("hides JSON and YAML editing modes", () => {
    render(<Harness />);
    expect(screen.getByText("策略编辑器")).toBeInTheDocument();
    expect(screen.queryByRole("tablist", { name: "编辑模式" })).not.toBeInTheDocument();
    expect(screen.queryByRole("tab", { name: "JSON" })).not.toBeInTheDocument();
    expect(screen.queryByRole("tab", { name: "YAML" })).not.toBeInTheDocument();
    expect(screen.queryByRole("tab", { name: "画布" })).not.toBeInTheDocument();
    expect(screen.getByTestId("strategy-canvas")).toBeInTheDocument();
  });

  it("renders the capability-driven node library", () => {
    render(<Harness />);
    expect(screen.getByRole("button", { name: /外部输入/ })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /工具/ })).not.toBeInTheDocument();
  });

  it("lets agent nodes pick a configured model ref", () => {
    render(<Harness initial={agentSpec()} />);
    const node = document.querySelector('.react-flow__node[data-id="planner"]');
    expect(node).toBeTruthy();
    if (!node) return;
    fireEvent.click(node);
    const panel = screen.getByLabelText("节点属性");
    const model = within(panel).getByLabelText("模型");
    expect(model.tagName).toBe("SELECT");
    expect(model).toHaveDisplayValue("custom");
    expect(within(model).getByRole("option", { name: "使用策略默认模型" })).toBeInTheDocument();
    expect(within(model).getByRole("option", { name: "general" })).toBeInTheDocument();
    expect(within(model).getByRole("option", { name: "reasoner" })).toBeInTheDocument();
    expect(within(model).getByRole("option", { name: "custom" })).toBeInTheDocument();
    fireEvent.change(model, { target: { value: "model://general@1" } });
    const withModel = JSON.parse(screen.getByTestId("active-spec").textContent ?? "{}") as SwarmSpecDocument;
    expect(withModel.spec.agents?.planner?.model).toBe("model://general@1");
    fireEvent.change(model, { target: { value: "" } });
    const cleared = JSON.parse(screen.getByTestId("active-spec").textContent ?? "{}") as SwarmSpecDocument;
    expect(cleared.spec.agents?.planner?.model).toBeUndefined();
  });

  it("lets tool nodes pick a configured tool ref", () => {
    render(<Harness initial={toolSpec()} nodeTypes={["tool", "agent", "parallel", "join", "reducer", "approval", "input"]} />);
    const node = document.querySelector('.react-flow__node[data-id="search"]');
    expect(node).toBeTruthy();
    if (!node) return;
    fireEvent.click(node);
    const panel = screen.getByLabelText("节点属性");
    const tool = within(panel).getByLabelText("工具 Ref");
    expect(tool.tagName).toBe("SELECT");
    expect(tool).toHaveDisplayValue("legacy");
    expect(within(tool).getByRole("option", { name: "search" })).toBeInTheDocument();
    expect(within(tool).getByRole("option", { name: "document/read" })).toBeInTheDocument();
    expect(within(tool).getByRole("option", { name: "legacy" })).toBeInTheDocument();
    fireEvent.change(tool, { target: { value: "tool://document/read@1" } });
    const next = JSON.parse(screen.getByTestId("active-spec").textContent ?? "{}") as SwarmSpecDocument;
    expect(next.spec.graph.nodes.search).toMatchObject({ type: "tool", tool: "tool://document/read@1" });
  });

  it("lets users rename the agent declaration key", () => {
    render(<Harness initial={agentSpec()} />);
    const node = document.querySelector('.react-flow__node[data-id="planner"]');
    expect(node).toBeTruthy();
    if (!node) return;
    fireEvent.click(node);
    const panel = screen.getByLabelText("节点属性");
    const declaration = within(panel).getByLabelText("智能体声明");
    expect(declaration.tagName).toBe("INPUT");
    expect(declaration).toHaveValue("planner");
    fireEvent.change(declaration, { target: { value: "reviewer" } });
    fireEvent.blur(declaration);
    const nextSpec = JSON.parse(screen.getByTestId("active-spec").textContent ?? "{}") as SwarmSpecDocument;
    expect(nextSpec.spec.agents?.reviewer).toMatchObject({
      role: "Planner",
      instructions: "Plan the work.",
    });
    expect(nextSpec.spec.agents?.planner).toBeUndefined();
    expect(nextSpec.spec.graph.nodes.planner?.agent).toBe("reviewer");
    expect(declaration).toHaveValue("reviewer");
  });

  it("binds a project agent configuration from the property panel", () => {
    vi.spyOn(window, "confirm").mockReturnValue(true);
    render(<Harness initial={agentSpec()} agentConfigurations={[AGENT_CONFIG]} />);
    const node = document.querySelector('.react-flow__node[data-id="planner"]');
    expect(node).toBeTruthy();
    if (!node) return;
    fireEvent.click(node);
    const panel = screen.getByLabelText("节点属性");
    const binder = within(panel).getByRole("combobox", { name: "绑定已配置智能体" });
    fireEvent.change(binder, { target: { value: "cfg-reviewer" } });
    const nextSpec = JSON.parse(screen.getByTestId("active-spec").textContent ?? "{}") as SwarmSpecDocument;
    const nextState = JSON.parse(screen.getByTestId("active-editor-state").textContent ?? "{}") as EditorState;
    expect(nextSpec.spec.agents?.planner).toMatchObject({
      role: "审核员",
      instructions: "审核输入",
      model: "model://general@1",
    });
    expect(nextState.agentBindings.planner).toMatchObject({
      configurationId: "cfg-reviewer",
      revision: 1,
      name: "合同审查智能体",
    });
    expect(within(panel).getByLabelText("模型")).toBeDisabled();
    fireEvent.click(within(panel).getByRole("button", { name: "转为自定义" }));
    const unbound = JSON.parse(screen.getByTestId("active-editor-state").textContent ?? "{}") as EditorState;
    expect(unbound.agentBindings.planner).toBeUndefined();
    expect(within(panel).getByLabelText("模型")).not.toBeDisabled();
  });
});
