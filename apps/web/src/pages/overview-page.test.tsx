import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { api } from "@/api/client";
import type { ProjectOverviewSnapshot, ProjectOverviewWorkSnapshot } from "@/api/types";
import { OverviewPage } from "./overview-page";

vi.mock("@/api/client", () => ({ api: { getProjectOverview: vi.fn() } }));

const now = "2026-08-06T04:00:00Z";

function work(
  workKey: string,
  category: ProjectOverviewWorkSnapshot["category"],
  overrides: Partial<ProjectOverviewWorkSnapshot> = {},
): ProjectOverviewWorkSnapshot {
  return {
    workKey,
    name: `${workKey} 名称`,
    shortName: `${workKey} 简称`,
    category,
    status: "runnable",
    statusLabel: "可运行",
    qualificationStatus: "local_verified",
    qualificationLabel: "本地验证，待生产准入",
    blockers: [],
    readiness: { requiredDocuments: 2, satisfiedDocuments: 2, documentsReady: true, readyToStart: true },
    activeRunId: null,
    latestRun: null,
    ...overrides,
  };
}

function snapshot(overrides: Partial<ProjectOverviewSnapshot> = {}): ProjectOverviewSnapshot {
  return {
    generatedAt: now,
    counts: {
      pendingApprovals: 2,
      pendingInputs: 1,
      documentsAvailable: 8,
      documentsReviewRequired: 3,
      documentsFailed: 1,
      activeRuns: 2,
      waitingRuns: 1,
    },
    businessWorks: [
      work("business-active", "business", { activeRunId: "run-active" }),
      work("business-config", "business", { status: "not_configured", statusLabel: "未配置", readiness: { requiredDocuments: 0, satisfiedDocuments: 0, documentsReady: true, readyToStart: false } }),
      work("business-docs", "business", { readiness: { requiredDocuments: 3, satisfiedDocuments: 1, documentsReady: false, readyToStart: false } }),
      work("business-ready", "business"),
      work("business-five", "business"),
      work("business-six", "business"),
      work("business-seven", "business"),
      work("foundation-one", "foundation"),
      work("foundation-two", "foundation"),
      work("governance-one", "governance"),
    ],
    recentRuns: [{
      runId: "run-recent",
      businessWorkKey: "business-ready",
      businessWorkName: "合同后评价",
      status: "FAILED",
      strategyVersionId: "strategy-version",
      eventCount: 8,
      taskCount: 3,
      operatorName: "张三",
      createdAt: now,
      startedAt: "2026-08-06T03:59:00Z",
      completedAt: now,
      failureReason: "上游服务不可用",
      cancelReason: null,
    }],
    ...overrides,
  };
}

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter><OverviewPage /></MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("overview page", () => {
  beforeEach(() => {
    vi.mocked(api.getProjectOverview).mockReset();
    vi.mocked(api.getProjectOverview).mockResolvedValue(snapshot());
  });
  afterEach(() => cleanup());

  it("uses one overview query and renders the 7/2/1 business hierarchy", async () => {
    renderPage();

    expect(await screen.findByRole("heading", { name: "项目工作台" })).toBeVisible();
    expect(api.getProjectOverview).toHaveBeenCalledTimes(1);
    for (const key of ["business-active", "business-config", "business-docs", "business-ready", "business-five", "business-six", "business-seven"]) {
      expect(screen.getByText(`${key} 名称`)).toBeVisible();
    }
    expect(screen.getByText("foundation-one 名称")).toBeVisible();
    expect(screen.getByText("foundation-two 名称")).toBeVisible();
    expect(screen.getByText("governance-one 名称")).toBeVisible();
    expect(screen.queryByText("功能导航")).not.toBeInTheDocument();
  });

  it("links attention cards and all four business actions to professional pages", async () => {
    renderPage();
    await screen.findByRole("heading", { name: "需要关注" });

    expect(screen.getByRole("link", { name: /人工待办/ })).toHaveAttribute("href", "/actions");
    expect(screen.getByRole("link", { name: /资料需处理/ })).toHaveAttribute("href", "/documents?view=failed");
    expect(screen.getByRole("link", { name: /运行动态/ })).toHaveAttribute("href", "/runs");
    expect(screen.getByRole("link", { name: "business-active 名称：查看运行" })).toHaveAttribute("href", "/runs/run-active");
    expect(screen.getByRole("link", { name: "business-config 名称：完成配置" })).toHaveAttribute("href", "/business-works/business-config/settings");
    expect(screen.getByRole("link", { name: "business-docs 名称：查看缺失项" })).toHaveAttribute("href", "/business-works/business-docs");
    expect(screen.getByRole("link", { name: "business-ready 名称：开始处理" })).toHaveAttribute("href", "/business-works/business-ready/workbench");
  });

  it("shows a closed state and a lightweight recent run without a progress bar", async () => {
    vi.mocked(api.getProjectOverview).mockResolvedValue(snapshot({
      counts: { pendingApprovals: 0, pendingInputs: 0, documentsAvailable: 8, documentsReviewRequired: 0, documentsFailed: 0, activeRuns: 0, waitingRuns: 0 },
    }));
    renderPage();

    expect(await screen.findByText("当前事项已闭环")).toBeVisible();
    expect(screen.getByRole("link", { name: /合同后评价，运行 run-recent/ })).toHaveAttribute("href", "/runs/run-recent");
    expect(screen.getByText("3 个任务 · 8 个事件")).toBeVisible();
    expect(screen.getByText("上游服务不可用")).toBeVisible();
    expect(screen.queryByRole("img", { name: /任务进度/ })).not.toBeInTheDocument();
  });

  it("keeps header shortcuts available when the aggregate request fails", async () => {
    vi.mocked(api.getProjectOverview).mockRejectedValue(new Error("offline"));
    renderPage();

    expect(await screen.findByRole("alert")).toHaveTextContent("项目概览暂时无法加载");
    expect(screen.getByRole("link", { name: /业务资料/ })).toHaveAttribute("href", "/documents");
    expect(screen.getByRole("link", { name: /待办中心/ })).toHaveAttribute("href", "/actions");
    expect(screen.getByRole("button", { name: "重试" })).toBeVisible();
  });

  it("renders region skeletons while the overview is loading", () => {
    vi.mocked(api.getProjectOverview).mockImplementation(() => new Promise(() => undefined));
    renderPage();

    expect(screen.getByLabelText("正在加载项目工作台")).toBeVisible();
  });

  it("renders independent empty states for works and recent runs", async () => {
    vi.mocked(api.getProjectOverview).mockResolvedValue(snapshot({
      businessWorks: [],
      recentRuns: [],
    }));
    renderPage();

    expect(await screen.findByText("暂无业务工作")).toBeVisible();
    expect(screen.getByText("暂无基础与治理工作")).toBeVisible();
    expect(screen.getByText("暂无运行动态")).toBeVisible();
  });

  it("keeps existing data visible during a manual background refresh", async () => {
    let finishRefresh: ((value: ProjectOverviewSnapshot) => void) | undefined;
    vi.mocked(api.getProjectOverview)
      .mockResolvedValueOnce(snapshot())
      .mockImplementationOnce(() => new Promise((resolve) => { finishRefresh = resolve; }));
    renderPage();
    expect(await screen.findByText("business-ready 名称")).toBeVisible();

    fireEvent.click(screen.getByRole("button", { name: "刷新" }));
    await waitFor(() => expect(api.getProjectOverview).toHaveBeenCalledTimes(2));
    expect(screen.getByText("business-ready 名称")).toBeVisible();

    act(() => finishRefresh?.(snapshot()));
  });
});
