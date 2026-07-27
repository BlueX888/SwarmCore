import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { api } from "@/api/client";
import type { AssessmentDetailSnapshot } from "@/api/types";
import { AssessmentPage } from "./assessment-page";

vi.mock("@/api/client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/api/client")>();
  return {
    ...actual,
    api: {
      ...actual.api,
      getAssessment: vi.fn(),
      getRun: vi.fn(),
      listCaseFindings: vi.fn(),
      listEvaluationReports: vi.fn(),
      listAssessmentDocumentSnapshots: vi.fn(),
    },
  };
});

function detail(overrides: Partial<AssessmentDetailSnapshot> = {}): AssessmentDetailSnapshot {
  return {
    assessmentId: "assessment-1",
    evaluationId: "assessment-1",
    caseId: "case-1",
    workItemId: "case-1",
    workItemRevisionId: "revision-1",
    runId: "run-1",
    status: "SUCCEEDED",
    result: {
      schemaVersion: "1",
      evaluationPeriod: { start: "2026-01-01", end: "2026-06-30" },
      contractId: "HT-1",
      overallScore: 88,
      grade: "A",
      riskLevel: "LOW",
      passed: true,
      reviewRequired: false,
      executiveSummary: "合同履约整体良好。",
      dimensions: [{ code: "quality", name: "质量", weight: 1, score: 90, status: "OK", summary: "达标", metrics: {}, evidenceRefs: [] }],
      findings: [],
    },
    capabilityPackVersionId: "version-1",
    planHash: "a".repeat(64),
    attachmentManifestHash: "b".repeat(64),
    registrySnapshot: {},
    createdAt: "2026-07-22T00:00:00Z",
    casePayload: { title: "合同后评价" },
    caseStatus: "EVALUATED",
    scenarioType: "contract-post-evaluation-case",
    owner: "采购部",
    ...overrides,
  };
}

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}><MemoryRouter initialEntries={["/assessments/assessment-1"]}><Routes>
    <Route path="/assessments/:assessmentId" element={<AssessmentPage />} />
    <Route path="/runs/:runId" element={<h1>运行详情</h1>} />
  </Routes></MemoryRouter></QueryClientProvider>);
}

describe("assessment page", () => {
  beforeEach(() => {
    vi.mocked(api.getAssessment).mockResolvedValue(detail());
    vi.mocked(api.getRun).mockResolvedValue({ runId: "run-1", status: "SUCCEEDED", completedAt: "2026-07-22T01:00:00Z" } as never);
    vi.mocked(api.listCaseFindings).mockResolvedValue({
      items: [{ findingId: "f-1", workItemId: "case-1", evaluationId: "assessment-1", ruleKey: "r1", code: "C1", category: "quality", severity: "MEDIUM", status: "OPEN", title: "需关注项", detail: "证据不足", evidence: {} }],
    });
    vi.mocked(api.listEvaluationReports).mockResolvedValue({
      items: [{ reportId: "report-1", evaluationId: "assessment-1", format: "PDF", templateVersion: "1", resultSchemaVersion: "1", content: null, contentHash: "c".repeat(64), createdAt: "2026-07-22T01:00:00Z" }],
    });
    vi.mocked(api.listAssessmentDocumentSnapshots).mockResolvedValue({
      items: [{ documentUsageSnapshotId: "snap-1", businessWorkKey: "report-generation", sha256: "d".repeat(64) }],
    });
  });
  afterEach(() => { cleanup(); vi.clearAllMocks(); });

  it("renders success assessment with findings, reports, snapshots and run drill-down", async () => {
    renderPage();
    expect(await screen.findByRole("heading", { name: "评估结果" })).toBeVisible();
    expect(screen.getByText("合同履约整体良好。")).toBeVisible();
    expect(screen.getByText("需关注项")).toBeVisible();
    expect(screen.getByText("PDF")).toBeVisible();
    expect(screen.getByText("report-generation")).toBeVisible();
    expect(screen.getByRole("link", { name: "查看技术运行详情" })).toHaveAttribute("href", "/runs/run-1");
  });

  it("shows progress while assessment is still running", async () => {
    vi.mocked(api.getAssessment).mockResolvedValue(detail({ status: "RUNNING", result: null }));
    vi.mocked(api.getRun).mockResolvedValue({ runId: "run-1", status: "RUNNING", completedAt: null } as never);
    renderPage();
    expect(await screen.findByText(/评估仍在进行中/)).toBeVisible();
  });

  it("shows formal report readability and quality gate status", async () => {
    const formal = detail().result as Record<string, unknown>;
    vi.mocked(api.getAssessment).mockResolvedValue(detail({
      result: {
        ...formal,
        schemaVersion: "schema://contract/post-evaluation-result@3",
        readabilityGate: {
          documentCount: 35,
          readableDocumentCount: 31,
          readabilityRate: 0.8857,
          formalThreshold: 0.8,
          formalEligible: true,
          reportMode: "FORMAL_REPORT",
          reasons: [],
        },
        reportQuality: {
          passed: true,
          blockingIssues: [],
          warnings: [],
          checks: { requiredSections: true, scoreConsistency: true },
        },
        reportDocument: {
          title: "采购合同履约后评价报告",
          reportNumber: "CPE-123456789ABC",
          reportMode: "FORMAL_REPORT",
          formalEligible: true,
        },
      } as never,
    }));

    renderPage();

    expect(await screen.findByText("报告质量状态")).toBeVisible();
    expect(screen.getByText("正式报告")).toBeVisible();
    expect(screen.getByText("质量门已通过")).toBeVisible();
    expect(screen.getByText("88.57%")).toBeVisible();
    expect(screen.getByText("CPE-123456789ABC")).toBeVisible();
  });

  it("renders deviation dimensions, trends and proposed responsibility", async () => {
    vi.mocked(api.getAssessment).mockResolvedValue(detail({
      scenarioType: "deviation-analysis-case",
      result: {
        schemaVersion: "schema://deviation-analysis/result@1",
        title: "项目偏差分析",
        subject: { subjectId: "P-1" },
        period: { start: "2026-01-01", end: "2026-06-30" },
        asOf: "2026-06-30",
        qualityStatus: "REVIEW_REQUIRED",
        reviewRequired: true,
        dimensions: {
          TIME: { status: "OK", metrics: { maximumDelayDays: 10, onTimeRate: 0.5, spi: 0.8 }, reasons: [], evidenceRefs: [] },
          CONTENT: { status: "OK", metrics: { actualCompletionRate: 0.8, contentVarianceRate: -0.2 }, reasons: [], evidenceRefs: [] },
          COST: { status: "OK", metrics: { currentBAC: 100, eac: 110, costVarianceRate: 0.1, currency: "CNY" }, reasons: [], evidenceRefs: [] },
        },
        rootCauses: [{ causeId: "c1", title: "设备到货延期", rationale: "到货记录晚于基线" }],
        trends: {
          status: "OK",
          summary: "已按同口径生成趋势。",
          points: [
            { asOf: "2026-05-31", timeVarianceDays: 5, contentVarianceRate: -0.1, costVarianceRate: 0.05 },
            { asOf: "2026-06-30", timeVarianceDays: 10, contentVarianceRate: -0.2, costVarianceRate: 0.1 },
          ],
        },
        responsibility: {
          status: "PENDING_CONFIRMATION",
          humanConfirmationRequired: true,
          proposals: [{ proposalId: "r1", party: "承包商", scope: "TIME", rationale: "设备到货延期", confidence: 0.8, evidenceRefs: [], status: "PROPOSED" }],
          decisions: [],
        },
        evidenceReview: { reviewRequired: true, reasons: ["责任建议待确认"] },
        narrative: { executiveSummary: "三类偏差均已计算。", recommendations: [] },
        provenance: {},
      } as never,
    }));
    renderPage();
    expect(await screen.findByText("项目偏差分析")).toBeVisible();
    expect(screen.getByText("时间偏差")).toBeVisible();
    expect(screen.getByRole("img", { name: "最大时间偏差（天）趋势图" })).toBeVisible();
    expect(screen.getAllByText("设备到货延期").length).toBeGreaterThan(0);
    expect(screen.getByText("承包商")).toBeVisible();
    expect(screen.getAllByText("PROPOSED").length).toBeGreaterThan(0);
  });

  it("shows load failure state", async () => {
    vi.mocked(api.getAssessment).mockRejectedValue(new Error("assessment missing"));
    renderPage();
    expect(await screen.findByRole("heading", { name: "Assessment 无法加载" })).toBeVisible();
    expect(screen.getByText("assessment missing")).toBeVisible();
  });
});
