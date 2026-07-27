import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { api } from "@/api/client";
import type { RunSnapshot } from "@/api/types";
import { DEMO_PROJECT_ID, DEMO_TENANT_ID } from "@/lib/demo-scope";
import { RunsPage } from "./runs-page";

vi.mock("@/api/client", () => ({
  api: {
    listRuns: vi.fn(),
  },
}));

function runSnapshot(overrides: Partial<RunSnapshot> = {}): RunSnapshot {
  return {
    runId: "run-alpha",
    status: "SUCCEEDED",
    input: {},
    output: null,
    outputRef: null,
    snapshotSeq: 3,
    earliestAvailableSeq: 0,
    planHash: "a".repeat(64),
    usage: {},
    taskCounts: { SUCCEEDED: 2 },
    allowedActions: [],
    tasks: [],
    ...overrides,
  };
}

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <RunsPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("runs page filters", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.listRuns).mockResolvedValue({
      total: 2,
      items: [
        runSnapshot({ runId: "run-alpha", status: "SUCCEEDED", snapshotSeq: 3 }),
        runSnapshot({ runId: "run-beta", status: "RUNNING", snapshotSeq: 1, taskCounts: { RUNNING: 1 } }),
      ],
    });
  });

  afterEach(() => cleanup());

  it("lists runs and calls the list API for the workspace", async () => {
    renderPage();
    expect(await screen.findByRole("heading", { name: "最近运行" })).toBeVisible();
    expect(screen.getByText("共 2 条")).toBeVisible();
    expect(screen.getAllByText("run-alpha").length).toBeGreaterThan(0);
    expect(screen.getAllByText("run-beta").length).toBeGreaterThan(0);
    expect(api.listRuns).toHaveBeenCalledWith(DEMO_TENANT_ID, DEMO_PROJECT_ID);
  });

  it("filters by run id search and status", async () => {
    renderPage();
    await screen.findByRole("heading", { name: "最近运行" });

    fireEvent.change(screen.getByLabelText("搜索运行 ID"), { target: { value: "beta" } });
    expect(screen.getByText("匹配 1 / 共 2 条")).toBeVisible();
    expect(screen.queryAllByText("run-alpha")).toHaveLength(0);
    expect(screen.getAllByText("run-beta").length).toBeGreaterThan(0);

    fireEvent.click(screen.getByLabelText("按状态筛选"));
    fireEvent.click(screen.getByRole("option", { name: "成功" }));
    expect(screen.getByText("没有匹配的运行")).toBeVisible();
    expect(screen.getByText("匹配 0 / 共 2 条")).toBeVisible();
  });

  it("opens the status filter menu with current options", async () => {
    renderPage();
    await screen.findByRole("heading", { name: "最近运行" });

    const trigger = screen.getByLabelText("按状态筛选");
    expect(trigger).toHaveAttribute("aria-expanded", "false");
    fireEvent.click(trigger);
    expect(trigger).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByRole("option", { name: "全部状态" })).toBeVisible();
    expect(screen.getByRole("option", { name: "运行中" })).toBeVisible();
    expect(screen.getByRole("option", { name: "成功" })).toBeVisible();
  });
});
