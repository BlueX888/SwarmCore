import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { SchemaForm, validateSchemaValues } from "@/components/operations/schema-form";
import type { TaskSnapshot } from "@/api/types";
import { CommandStatus, EvaluationResult, evaluationIdFromInput, graph, refreshRunDetails } from "./run-detail-page";

const schema = {
  type: "object",
  required: ["reason"],
  properties: { reason: { type: "string", title: "Reason" } },
};

describe("human control forms", () => {
  it("validates required external input fields", () => {
    expect(validateSchemaValues(schema, {})).toBe("reason 为必填项。");
    expect(validateSchemaValues(schema, { reason: "approved" })).toBeNull();
  });

  it("does not submit an approval until its schema is satisfied", () => {
    const submit = vi.fn();
    render(<SchemaForm schema={schema} submitLabel="批准" busy={false} onSubmit={submit} />);
    fireEvent.click(screen.getByRole("button", { name: "批准" }));
    expect(screen.getByRole("alert")).toHaveTextContent("reason 为必填项");
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
  it("lays out dependencies left-to-right regardless of API task order", () => {
    const task = (nodeKey: string, dependencies: string[]): TaskSnapshot => ({ taskId: nodeKey, nodeKey, nodeType: "tool", status: "SUCCEEDED", dependencies, error: null, output: null, retryGeneration: 0, allowedActions: [] });
    const flow = graph([task("report", ["evaluate"]), task("analyze", ["read"]), task("read", []), task("evaluate", ["analyze"])]);
    const y = Object.fromEntries(flow.nodes.map((node) => [node.id, node.position.y]));

    expect(y).toEqual({ read: 0, analyze: 110, evaluate: 220, report: 330 });
    expect(flow.edges.every((edge) => edge.type === "smoothstep")).toBe(true);
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
