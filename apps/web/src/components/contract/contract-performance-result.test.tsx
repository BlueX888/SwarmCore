import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import {
  asContractPerformance,
  ContractPerformanceResultView,
} from "./contract-performance-result";

const result = {
  schemaVersion: "schema://contract-performance/result@1" as const,
  caseId: "case-1",
  planVersion: 2,
  asOf: "2026-07-27",
  status: "REVIEW_REQUIRED",
  collectionStatus: "PARTIAL",
  plan: {
    obligations: [{ id: "obl-1" }],
    milestones: [{ id: "ms-1" }, { id: "ms-2" }],
    paymentConditions: [{ id: "pay-1" }],
  },
  performance: {
    milestones: [
      { milestoneId: "ms-1", status: "ACCEPTED", evidenceIds: ["ev-1"] },
      { milestoneId: "ms-2", status: "OVERDUE", missingEvidenceTypes: ["ACCEPTANCE"] },
    ],
    paymentGates: [
      {
        paymentConditionId: "pay-1",
        gateStatus: "BLOCKED",
        paymentObserved: true,
        acceptanceSatisfied: false,
      },
    ],
    findings: [{ code: "PAYMENT_BEFORE_PREREQUISITES", severity: "HIGH", targetId: "pay-1" }],
  },
  gantt: {
    milestones: [
      {
        id: "ms-1",
        title: "首批验收",
        originalDueDate: "2026-06-01",
        currentDueDate: "2026-06-15",
        actualFinishDate: "2026-06-12",
        status: "ACCEPTED",
        evidenceStatus: "COMPLETE",
      },
    ],
    criticalPath: null,
    quality: { status: "MILESTONE_ONLY", reasons: ["INSUFFICIENT_DEPENDENCY_OR_DURATION_DATA"] },
  },
  evidenceLedger: {
    evidence: [
      {
        id: "ev-1",
        type: "PAYMENT",
        sourceRef: "ap",
        sourceRecordId: "PAY-001",
        businessDate: "2026-06-12",
        amount: 250000,
        currency: "CNY",
        contractKeys: { supplier: "示例供应商" },
        contentHash: "a".repeat(64),
      },
    ],
    links: [],
    unmatchedEvidenceIds: ["ev-public"],
    sourceResults: [
      {
        sourceRef: "erp://payments",
        status: "SUCCEEDED",
        recordCount: 1,
        attempts: 1,
        nextCursor: "cursor-2",
      },
    ],
    cursors: { "erp://payments": "cursor-2" },
  },
  changeHistory: {
    appliedChanges: [{ id: "chg-1" }],
    differences: [
      {
        changeId: "chg-1",
        path: "/milestones/0/dueDate",
        before: "2026-06-01",
        after: "2026-06-15",
      },
    ],
  },
  provenance: {
    planHash: "b".repeat(64),
    ruleSetRef: "rule://contract-performance@2",
    toolRefs: ["tool://contract-performance/evidence-match@1"],
  },
  approvals: [{ decision: "REQUEST_EVIDENCE" }],
  resultHash: "c".repeat(64),
};

describe("ContractPerformanceResultView", () => {
  it("recognizes only the contract-performance schema", () => {
    expect(asContractPerformance(result)).not.toBeNull();
    expect(asContractPerformance({ ...result, schemaVersion: "other" })).toBeNull();
  });

  it("shows baseline, evidence, payment gate, change, and traceability", () => {
    render(<ContractPerformanceResultView result={result} />);
    expect(screen.getByText("原始基准 / 当前基准 / 实际")).toBeInTheDocument();
    expect(screen.getByText("1 / 2")).toBeInTheDocument();
    expect(screen.getByText("存在 2 条未匹配证据、风险或缺口，系统未据此确认验收或付款。")).toBeInTheDocument();
    expect(screen.getByText("首批验收")).toBeInTheDocument();
    expect(screen.getByText("证据收件箱")).toBeInTheDocument();
    expect(screen.getByText("2026-06-12 · CNY 250,000 · 示例供应商")).toBeInTheDocument();
    expect(screen.getByText("PAY-001 · " + "a".repeat(64))).toBeInTheDocument();
    expect(screen.getByText("采集源、游标与重试")).toBeInTheDocument();
    expect(screen.getByText("erp://payments")).toBeInTheDocument();
    expect(screen.getByText("BLOCKED")).toBeInTheDocument();
    expect(screen.getByText("/milestones/0/dueDate")).toBeInTheDocument();
    expect(screen.getByText("冻结结果哈希")).toBeInTheDocument();
  });
});
