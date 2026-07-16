import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import * as React from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { StrategyEditor } from "./strategy-editor";
import { EMPTY_EDITOR_STATE, createBlankSpec } from "./strategy-editor-model";

afterEach(cleanup);

function Harness() {
  const [spec, setSpec] = React.useState(() => createBlankSpec());
  return <><StrategyEditor spec={spec} editorState={EMPTY_EDITOR_STATE} nodeTypes={["agent", "parallel", "join", "reducer", "approval", "input"]} diagnostics={[]} onSpecChange={setSpec} onEditorStateChange={vi.fn()} onError={vi.fn()} /><output data-testid="active-spec">{JSON.stringify(spec)}</output></>;
}

describe("StrategyEditor", () => {
  it("preserves the last valid Spec when text becomes invalid", () => {
    render(<Harness />);
    fireEvent.click(screen.getByRole("tab", { name: "JSON" }));
    const editor = screen.getByLabelText("JSON strategy spec");
    const valid = createBlankSpec("valid-name");
    fireEvent.change(editor, { target: { value: JSON.stringify(valid) } });
    expect(screen.getByTestId("active-spec")).toHaveTextContent("valid-name");
    fireEvent.change(editor, { target: { value: "{" } });
    expect(screen.getByRole("alert")).toHaveTextContent("last valid Spec");
    expect(screen.getByTestId("active-spec")).toHaveTextContent("valid-name");
    fireEvent.click(screen.getByRole("tab", { name: "CANVAS" }));
    expect(screen.getByTestId("strategy-canvas")).toBeInTheDocument();
  });

  it("renders the capability-driven node library", () => {
    render(<Harness />);
    expect(screen.getByRole("button", { name: /External Input/i })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Tool/i })).not.toBeInTheDocument();
  });
});
