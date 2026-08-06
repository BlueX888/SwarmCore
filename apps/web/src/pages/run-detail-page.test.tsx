import { fireEvent, render, screen } from "@testing-library/react";
import { Position } from "@xyflow/react";
import { describe, expect, it, vi } from "vitest";
import { SchemaForm, validateSchemaValues } from "@/components/operations/schema-form";
import type { TaskSnapshot } from "@/api/types";
import { layoutDirectedGraph } from "@/components/strategy/strategy-editor-model";
import { CommandStatus, EvaluationResult, evaluationIdFromInput, graph, refreshRunDetails } from "./run-detail-page";

const schema = {
  type: "object",
  required: ["reason"],
  properties: { reason: { type: "string", title: "Reason" } },
};

describe("human control forms", () => {
  it("validates required external input fields", () => {
    expect(validateSchemaValues(schema, {})).toBe("Reason 为必填项。");
    expect(validateSchemaValues(schema, { reason: "approved" })).toBeNull();
  });

  it("does not submit an approval until its schema is satisfied", () => {
    const submit = vi.fn();
    render(<SchemaForm schema={schema} submitLabel="批准" busy={false} onSubmit={submit} />);
    fireEvent.click(screen.getByRole("button", { name: "批准" }));
    expect(screen.getByRole("alert")).toHaveTextContent("Reason 为必填项");
    fireEvent.change(screen.getByLabelText(/Reason/), { target: { value: "safe" } });
    fireEvent.click(screen.getByRole("button", { name: "批准" }));
    expect(submit).toHaveBeenCalledWith({ reason: "safe" });
  });

  it("shows pending and rejected command outcomes without changing Run state", () => {
    const { rerender } = render(<CommandStatus command={{ commandId: "c", requestId: "r", commandSeq: 2, status: "ACCEPTED" }} loading={false} />);
    expect(screen.getByRole("status")).toHaveTextContent("已受理");
    rerender(<CommandStatus command={{ commandId: "c", requestId: "r", commandSeq: 2, status: "REJECTED", result: { code: "RUN_NOT_PAUSED" } }} loading={false} />);
    expect(screen.getByRole("status")).toHaveTextContent("RUN_NOT_PAUSED");
  });
});

describe("run graph layout", () => {
  const task = (nodeKey: string, dependencies: string[]): TaskSnapshot => ({ taskId: nodeKey, nodeKey, nodeType: "tool", status: "SUCCEEDED", dependencies, error: null, output: null, retryGeneration: 0, allowedActions: [] });

  it("uses the strategy layout and node order regardless of API task order", () => {
    const strategyNodeOrder = ["read", "analyze-b", "analyze-a", "report"];
    const tasks = [
      task("report", ["analyze-a", "analyze-b"]),
      task("analyze-a", ["read"]),
      task("read", []),
      task("analyze-b", ["read"]),
    ];
    const flow = graph(tasks, strategyNodeOrder);
    const positions = Object.fromEntries(flow.nodes.map((node) => [node.id, node.position]));
    const expected = layoutDirectedGraph(
      strategyNodeOrder,
      tasks.flatMap((item) => item.dependencies.map((source) => ({ source, target: item.nodeKey }))),
    );

    expect(positions).toEqual(expected);
    expect(positions["analyze-b"].y).toBeLessThan(positions["analyze-a"].y);
    expect(flow.nodes.every((node) => node.sourcePosition === Position.Right)).toBe(true);
    expect(flow.nodes.every((node) => node.targetPosition === Position.Left)).toBe(true);
    expect(flow.edges.every((edge) => edge.type === "smoothstep")).toBe(true);
  });

  it("falls back to task order when historical responses omit strategy order", () => {
    const flow = graph([
      task("report", ["evaluate"]),
      task("analyze", ["read"]),
      task("read", []),
      task("evaluate", ["analyze"]),
    ]);
    const x = Object.fromEntries(flow.nodes.map((node) => [node.id, node.position.x]));

    expect(x.read).toBeLessThan(x.analyze);
    expect(x.analyze).toBeLessThan(x.evaluate);
    expect(x.evaluate).toBeLessThan(x.report);
  });
});

describe("evaluation result", () => {
  it("extracts and presents the business result instead of the persistence receipt", () => {
    expect(evaluationIdFromInput({ evaluationId: "evaluation-1" })).toBe("evaluation-1");
    render(<EvaluationResult loading={false} evaluation={{ evaluationId: "evaluation-1", workItemId: "work-1", workItemRevisionId: "revision-1", runId: "run-1", status: "SUCCEEDED", capabilityPackVersionId: "pack-1", planHash: "a".repeat(64), attachmentManifestHash: "b".repeat(64), createdAt: "2026-07-22T00:00:00Z", result: { schemaVersion: "schema://contract/post-evaluation-result@1", evaluationPeriod: { start: "2026-01-01", end: "2026-06-30" }, contractId: "HT-2026-001", overallScore: 100, grade: "优秀", riskLevel: "LOW", passed: true, reviewRequired: false, executiveSummary: "七维后评价全部通过。", dimensions: [{ code: "DOCUMENT_COMPLETENESS", name: "文件完整性", weight: 10, score: 100, status: "EVALUATED", summary: "文件齐全", metrics: {}, evidenceRefs: [] }], findings: [] } }} />);

    expect(screen.getByText("最终评估结果")).toBeVisible();
    expect(screen.getByText("100.0 / 100")).toBeVisible();
    expect(screen.getByText("优秀")).toBeVisible();
    expect(screen.getByText("未发现需关注问题，无需人工复核。")).toBeVisible();
  });
});

describe("manual refresh", () => {
  it("refreshes every run-detail data source", async () => {
    const refreshers = [vi.fn().mockResolvedValue(undefined), vi.fn().mockResolvedValue(undefined), vi.fn().mockResolvedValue(undefined)];

    await refreshRunDetails(refreshers);

    refreshers.forEach((refresh) => expect(refresh).toHaveBeenCalledOnce());
  });
});
