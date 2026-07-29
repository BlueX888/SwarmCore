import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { api } from "@/api/client";
import { SupplierRiskOperations } from "./supplier-risk-operations";

vi.mock("@/api/client", () => ({
  api: {
    listSupplierRiskAlerts: vi.fn(),
    listSupplierRiskHistory: vi.fn(),
    listSupplierRiskWorkOrders: vi.fn(),
    refreshSupplierRiskMonitor: vi.fn(),
    createSupplierRiskWorkOrder: vi.fn(),
    updateSupplierRiskWorkOrder: vi.fn(),
  },
}));

function renderOperations() {
  const client = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
  return render(
    <QueryClientProvider client={client}>
      <SupplierRiskOperations
        tenantId="tenant-1"
        projectId="project-1"
        monitorId="monitor-1"
      />
    </QueryClientProvider>,
  );
}

describe("SupplierRiskOperations", () => {
  beforeEach(() => {
    vi.mocked(api.listSupplierRiskAlerts).mockResolvedValue({
      items: [
        {
          alertId: "alert-1",
          monitorId: "monitor-1",
          snapshotId: "snapshot-1",
          alertType: "HARD_GATE",
          severity: "CRITICAL",
          status: "OPEN",
          title: "命中政府采购禁入",
          details: {},
          evidence: [{ recordId: "ccgp-1" }],
          createdAt: "2026-07-28T08:00:00Z",
          updatedAt: "2026-07-28T08:00:00Z",
        },
      ],
    });
    vi.mocked(api.listSupplierRiskHistory).mockResolvedValue({
      items: [
        {
          snapshotId: "snapshot-1",
          evaluationId: "evaluation-1",
          asOf: "2026-07-28T08:00:00Z",
          decision: "BLOCK",
          riskLevel: "D",
          riskScore: 100,
          sourceCoverage: {},
          changeSummary: { hasMaterialChange: true },
          resultHash: "a".repeat(64),
          result: {},
        },
      ],
    });
    vi.mocked(api.listSupplierRiskWorkOrders).mockResolvedValue({ items: [] });
    vi.mocked(api.createSupplierRiskWorkOrder).mockResolvedValue({
      workOrderId: "work-order-1",
      alertId: "alert-1",
      status: "OPEN",
      priority: "HIGH",
      assignee: null,
      dueAt: null,
      resolution: null,
      createdBy: "tester",
      createdAt: "2026-07-28T08:00:00Z",
      updatedAt: "2026-07-28T08:00:00Z",
      actions: [{ action: "CREATE" }],
    });
    vi.mocked(api.refreshSupplierRiskMonitor).mockResolvedValue({
      evaluationId: "evaluation-2",
      workItemId: "case-1",
      workItemRevisionId: "revision-1",
      runId: "run-2",
      status: "ACCEPTED",
      result: null,
      capabilityPackVersionId: "pack-1",
      planHash: "b".repeat(64),
      attachmentManifestHash: "c".repeat(64),
      createdAt: "2026-07-28T09:00:00Z",
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("shows alerts and history, creates work orders, and refreshes the monitor", async () => {
    renderOperations();

    expect(await screen.findByText("命中政府采购禁入")).toBeVisible();
    expect(screen.getByText("D · BLOCK")).toBeVisible();
    expect(screen.getByText("有变化")).toBeVisible();

    fireEvent.click(screen.getByRole("button", { name: "创建工单" }));
    await waitFor(() =>
      expect(api.createSupplierRiskWorkOrder).toHaveBeenCalledWith(
        "tenant-1",
        "project-1",
        "alert-1",
        { priority: "HIGH" },
      ),
    );

    fireEvent.click(screen.getByRole("button", { name: "立即刷新" }));
    await waitFor(() =>
      expect(api.refreshSupplierRiskMonitor).toHaveBeenCalledWith(
        "tenant-1",
        "project-1",
        "monitor-1",
      ),
    );
    expect(await screen.findByText(/evaluation-2/)).toBeVisible();
  });
});
