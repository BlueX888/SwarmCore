import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import {
  asProcurementSupplierRisk,
  ProcurementSupplierRiskResultView,
} from "./procurement-supplier-risk-result";

const result = {
  schemaVersion: "schema://procurement-supplier-risk/result@1" as const,
  caseId: "case-1",
  monitorId: "monitor-1",
  assessmentId: "assessment-1",
  asOf: "2026-07-28",
  supplier: { name: "华东设备", creditCode: "91310000TEST00001" },
  decision: "BLOCK" as const,
  riskLevel: "D",
  consistency: {
    clauseLineages: [
      {
        matchKey: "PAYMENT:1",
        category: "PAYMENT",
        changeType: "CHANGED",
        clauses: {
          TENDER: { text: "验收后30日付款", evidenceRefs: [{ page: 1 }] },
          BID: { text: "验收后30日付款", evidenceRefs: [{ page: 2 }] },
          AWARD: { text: "验收后30日付款", evidenceRefs: [{ page: 3 }] },
          CONTRACT: { text: "验收后60日付款", evidenceRefs: [{ page: 4 }] },
        },
      },
    ],
    findings: [
      {
        findingId: "finding-1",
        category: "PAYMENT",
        severity: "BLOCKER",
        changeType: "CHANGED",
        title: "付款条款改变",
        summary: "付款账期由30日改为60日",
        evidenceRefs: [{ page: 1 }, { page: 4 }],
      },
    ],
  },
  risk: {
    overallRiskScore: 75,
    externalRiskScore: 80,
    dataCoverage: 1,
    sourceStatuses: [
      {
        sourceRef: "internal://blacklist",
        status: "SUCCEEDED",
        fetchedAt: "2026-07-28T08:00:00+08:00",
      },
    ],
    hardGates: [
      {
        code: "INTERNAL_BLACKLIST",
        sourceRef: "internal://blacklist",
        sourceRecordId: "blacklist-1",
        evidenceRefs: [{ recordId: "blacklist-1" }],
      },
    ],
  },
  performance: {
    score: 92,
    coverage: 100,
    sampleSize: 5,
    status: "SCORED",
    metrics: [{ key: "ON_TIME_DELIVERY", value: 90, weight: 25, available: true }],
  },
  history: {
    hasMaterialChange: true,
    riskLevelChange: { from: "B", to: "D" },
    decisionChange: { from: "PASS", to: "BLOCK" },
    added: [{ id: "risk-1" }],
  },
  provenance: {
    ruleVersions: ["rule://supplier-risk@1"],
    documentContentHash: "a".repeat(64),
  },
  snapshotHash: "b".repeat(64),
  resultHash: "c".repeat(64),
};

describe("ProcurementSupplierRiskResultView", () => {
  it("recognizes only the procurement supplier risk schema", () => {
    expect(asProcurementSupplierRisk(result)).not.toBeNull();
    expect(asProcurementSupplierRisk({ ...result, schemaVersion: "other" })).toBeNull();
  });

  it("shows four-way clauses, hard gates, real sources, performance and history", () => {
    render(<ProcurementSupplierRiskResultView result={result} />);
    expect(screen.getByText("招标 / 投标 / 中标 / 合同四方条款链")).toBeInTheDocument();
    expect(screen.getByText("验收后60日付款")).toBeInTheDocument();
    expect(screen.getAllByText("INTERNAL_BLACKLIST").length).toBeGreaterThan(0);
    expect(screen.getByText("internal://blacklist")).toBeInTheDocument();
    expect(screen.getByText("ON_TIME_DELIVERY")).toBeInTheDocument();
    expect(screen.getByText("历史变化与可追溯依据")).toBeInTheDocument();
  });
});
