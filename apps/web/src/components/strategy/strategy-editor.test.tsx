import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import * as React from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { StrategyEditor } from "./strategy-editor";
import { EMPTY_EDITOR_STATE, createBlankSpec, type SwarmSpecDocument } from "./strategy-editor-model";

afterEach(cleanup);

const MODEL_REFS = ["model://general@1", "model://reasoner@1"];

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

function Harness({
  initial = createBlankSpec(),
  models = MODEL_REFS,
}: {
  initial?: SwarmSpecDocument;
  models?: string[];
}) {
  const [spec, setSpec] = React.useState(initial);
  return <>
    <StrategyEditor
      spec={spec}
      editorState={EMPTY_EDITOR_STATE}
      nodeTypes={["agent", "parallel", "join", "reducer", "approval", "input"]}
      models={models}
      diagnostics={[]}
      onSpecChange={setSpec}
      onEditorStateChange={vi.fn()}
      onError={vi.fn()}
    />
    <output data-testid="active-spec">{JSON.stringify(spec)}</output>
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
    expect(model).toHaveDisplayValue("model://custom@9");
    expect(within(model).getByRole("option", { name: "使用策略默认模型" })).toBeInTheDocument();
    expect(within(model).getByRole("option", { name: "model://general@1" })).toBeInTheDocument();
    expect(within(model).getByRole("option", { name: "model://reasoner@1" })).toBeInTheDocument();
    expect(within(model).getByRole("option", { name: "model://custom@9" })).toBeInTheDocument();
    fireEvent.change(model, { target: { value: "model://general@1" } });
    const withModel = JSON.parse(screen.getByTestId("active-spec").textContent ?? "{}") as SwarmSpecDocument;
    expect(withModel.spec.agents?.planner?.model).toBe("model://general@1");
    fireEvent.change(model, { target: { value: "" } });
    const cleared = JSON.parse(screen.getByTestId("active-spec").textContent ?? "{}") as SwarmSpecDocument;
    expect(cleared.spec.agents?.planner?.model).toBeUndefined();
  });
});
