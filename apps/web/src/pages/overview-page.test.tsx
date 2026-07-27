import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { api } from "@/api/client";
import { OverviewPage } from "./overview-page";

vi.mock("@/api/client", () => ({ api: {
  listRuns: vi.fn(),
  listStrategies: vi.fn(),
  listApprovals: vi.fn(),
  listInputs: vi.fn(),
  getCapabilities: vi.fn(),
} }));

describe("overview page", () => {
  beforeEach(() => {
    vi.mocked(api.listRuns).mockResolvedValue({ total: 2, items: [
      { runId: "run-active", status: "RUNNING", input: {}, output: null, outputRef: null, snapshotSeq: 4, earliestAvailableSeq: 1, strategyVersionId: "strategy-version-1", planHash: "a".repeat(64), usage: {}, taskCounts: { RUNNING: 2 }, allowedActions: [], tasks: [] },
      { runId: "run-complete", status: "SUCCEEDED", input: {}, output: {}, outputRef: null, snapshotSeq: 8, earliestAvailableSeq: 1, strategyVersionId: "strategy-version-2", planHash: "b".repeat(64), usage: {}, taskCounts: { SUCCEEDED: 3 }, allowedActions: [], tasks: [] },
    ] });
    vi.mocked(api.listStrategies).mockResolvedValue({ total: 2, items: [
      { strategyId: "strategy-1", name: "one", lifecycle: "ACTIVE", createdAt: new Date(0).toISOString(), updatedAt: new Date(0).toISOString(), draftId: "draft-1", draftRevision: 1, latestVersion: 1 },
      { strategyId: "strategy-2", name: "two", lifecycle: "DRAFT", createdAt: new Date(0).toISOString(), updatedAt: new Date(0).toISOString(), draftId: "draft-2", draftRevision: 1, latestVersion: null },
    ] });
    vi.mocked(api.listApprovals).mockResolvedValue({ total: 2, items: [] });
    vi.mocked(api.listInputs).mockResolvedValue({ total: 1, items: [] });
    vi.mocked(api.getCapabilities).mockResolvedValue({ schemaVersion: "swarmcore.io/capabilities/v1", registrySnapshot: "registry:test", nodeTypes: [], agents: [{ id: "inline/agno", runtime: "agno", environments: ["development"], declarationSchema: {} }], tools: [{ ref: "tool://search@1", risk: "LOW", inputSchema: {}, outputSchema: {} }], models: [{ ref: "model://general@1", runtime: "agno", environments: ["development"] }], limits: {}, swarmSpecSchema: {} });
  });

  it("shows project metrics, recent runs and global navigation", async () => {
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(<QueryClientProvider client={client}><MemoryRouter><OverviewPage /></MemoryRouter></QueryClientProvider>);

    expect(await screen.findByRole("heading", { name: "工作台" })).toBeVisible();
    expect(screen.getByText("1 个正在执行")).toBeVisible();
    expect(screen.getByText("2 项审批 · 1 项输入")).toBeVisible();
    expect(screen.getByText("1 个智能体 · 1 个工具 · 1 个模型")).toBeVisible();
    expect(screen.getByRole("link", { name: /run-active/ })).toHaveAttribute("href", "/runs/run-active");
    expect(screen.getByRole("link", { name: /查看并运行已注册智能体/ })).toHaveAttribute("href", "/agents");
    expect(screen.getByRole("link", { name: /查看能力治理策略/ })).toHaveAttribute("href", "/policies");
    expect(screen.getByRole("link", { name: /审计日志/ })).toHaveAttribute("href", "/audit-logs");
  });
});
