import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Outlet, Route, Routes } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError, api } from "@/api/client";
import { sortStrategiesByUpdatedAtDesc, StrategiesPage } from "./strategies-page";
import { StrategyDetailPage } from "./strategy-detail-page";

vi.mock("@/api/client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/api/client")>();
  return {
    ...actual,
    api: {
      listStrategies: vi.fn(),
      getStrategyDeleteImpact: vi.fn(),
      deleteStrategy: vi.fn(),
      getDraft: vi.fn(),
      listVersions: vi.fn(),
      getCapabilities: vi.fn(),
      compileStrategy: vi.fn(),
      updateDraft: vi.fn(),
      publishStrategy: vi.fn(),
    },
  };
});

vi.mock("@/components/strategy/strategy-editor", () => ({
  StrategyEditor: () => <div>strategy-editor</div>,
}));

const draftOnly = {
  strategyId: "strategy-1",
  name: "draft-only",
  lifecycle: "ACTIVE",
  createdAt: "2026-07-23T00:00:00Z",
  updatedAt: "2026-07-23T00:00:00Z",
  draftId: "draft-1",
  draftRevision: 1,
  latestVersion: null,
};

const published = {
  ...draftOnly,
  strategyId: "strategy-2",
  name: "published-strategy",
  latestVersion: 1,
};

function renderList() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <StrategiesPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("strategy delete ui", () => {
  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
  });

  beforeEach(() => {
    vi.mocked(api.listStrategies).mockResolvedValue({ items: [draftOnly, published], total: 2 });
    vi.mocked(api.getStrategyDeleteImpact).mockResolvedValue({
      strategyId: draftOnly.strategyId,
      deletable: true,
      blockers: [],
    });
    vi.mocked(api.deleteStrategy).mockResolvedValue(undefined);
    vi.mocked(api.getDraft).mockResolvedValue({
      draftId: "draft-1",
      strategyId: draftOnly.strategyId,
      revision: 1,
      spec: {
        apiVersion: "swarmcore.io/v1",
        kind: "SwarmStrategy",
        metadata: { name: "draft-only" },
        spec: {
          agents: { one: { role: "worker", instructions: "work" } },
          graph: { entrypoint: "one", nodes: { one: { type: "agent" } }, output: {} },
        },
      },
      editorState: { positions: {}, viewport: { x: 0, y: 0, zoom: 1 } },
      diagnostics: [],
      updatedBy: "tester",
      updatedAt: "2026-07-23T00:00:00Z",
    });
    vi.mocked(api.listVersions).mockResolvedValue({ items: [], total: 0 });
    vi.mocked(api.getCapabilities).mockResolvedValue({ nodeTypes: [], agents: [], tools: [], models: [] } as never);
  });

  it("shows delete entry on the strategies list", async () => {
    renderList();
    expect(await screen.findByRole("button", { name: "删除 draft-only" })).toBeVisible();
    expect(screen.getByRole("button", { name: "删除 published-strategy" })).toBeVisible();
  });

  it("shows a short description for every strategy", async () => {
    renderList();
    const descriptions = await screen.findAllByText("项目自定义执行策略，用于编排智能体、工具与业务流程。");
    expect(descriptions).toHaveLength(2);
  });

  it("sorts strategies by updatedAt descending even when API order differs", async () => {
    const older = { ...draftOnly, strategyId: "strategy-old", name: "older-strategy", updatedAt: "2026-07-20T00:00:00Z" };
    const newer = { ...published, strategyId: "strategy-new", name: "newer-strategy", updatedAt: "2026-07-25T12:00:00Z" };
    vi.mocked(api.listStrategies).mockResolvedValue({ items: [older, newer], total: 2 });
    renderList();
    expect(await screen.findByText("newer-strategy")).toBeVisible();
    const names = screen.getAllByRole("link").map((node) => node.textContent ?? "");
    const newerIndex = names.findIndex((text) => text.includes("newer-strategy"));
    const olderIndex = names.findIndex((text) => text.includes("older-strategy"));
    expect(newerIndex).toBeGreaterThanOrEqual(0);
    expect(olderIndex).toBeGreaterThan(newerIndex);
  });

  it("sortStrategiesByUpdatedAtDesc puts newest first", () => {
    const sorted = sortStrategiesByUpdatedAtDesc([
      { ...draftOnly, strategyId: "a", updatedAt: "2026-07-21T00:00:00Z" },
      { ...draftOnly, strategyId: "b", updatedAt: "2026-07-23T00:00:00Z" },
      { ...draftOnly, strategyId: "c", updatedAt: "2026-07-22T00:00:00Z" },
    ]);
    expect(sorted.map((item) => item.strategyId)).toEqual(["b", "c", "a"]);
  });

  it("does not navigate when clicking delete on a card", async () => {
    renderList();
    fireEvent.click(await screen.findByRole("button", { name: "删除 draft-only" }));
    await waitFor(() => expect(api.getStrategyDeleteImpact).toHaveBeenCalled());
    expect(screen.getByRole("dialog", { name: "删除策略" })).toBeVisible();
    expect(api.deleteStrategy).not.toHaveBeenCalled();
  });

  it("shows confirmation dialog for deletable strategy and deletes after name confirm", async () => {
    renderList();
    fireEvent.click(await screen.findByRole("button", { name: "删除 draft-only" }));
    expect(await screen.findByText("将同时删除尚未发布的草稿")).toBeVisible();
    expect(screen.getByText("此操作不可恢复")).toBeVisible();
    const confirm = screen.getByRole("button", { name: "确认删除" });
    expect(confirm).toBeDisabled();
    fireEvent.change(screen.getByLabelText("确认策略名称"), { target: { value: "draft-only" } });
    expect(confirm).toBeEnabled();
    fireEvent.click(confirm);
    await waitFor(() => expect(api.deleteStrategy).toHaveBeenCalledWith(
      expect.any(String),
      expect.any(String),
      "strategy-1",
    ));
    await waitFor(() => expect(api.listStrategies).toHaveBeenCalledTimes(2));
  });

  it("cancels without sending DELETE", async () => {
    renderList();
    fireEvent.click(await screen.findByRole("button", { name: "删除 draft-only" }));
    fireEvent.click(await screen.findByRole("button", { name: "取消" }));
    await waitFor(() => expect(screen.queryByRole("dialog", { name: "删除策略" })).not.toBeInTheDocument());
    expect(api.deleteStrategy).not.toHaveBeenCalled();
  });

  it("shows blockers when published versions exist", async () => {
    vi.mocked(api.getStrategyDeleteImpact).mockResolvedValue({
      strategyId: published.strategyId,
      deletable: false,
      blockers: [{ code: "STRATEGY_HAS_PUBLISHED_VERSIONS", count: 1, message: "策略存在 1 个已发布版本" }],
    });
    renderList();
    fireEvent.click(await screen.findByRole("button", { name: "删除 published-strategy" }));
    expect(await screen.findByText("策略存在 1 个已发布版本")).toBeVisible();
    expect(screen.queryByRole("button", { name: "确认删除" })).not.toBeInTheDocument();
  });

  it("renders readable 409 errors", async () => {
    vi.mocked(api.deleteStrategy).mockRejectedValue(
      new ApiError(409, "策略已有发布版本或历史使用记录，不能删除。", "STRATEGY_DELETE_BLOCKED", [
        { code: "STRATEGY_HAS_PUBLISHED_VERSIONS", count: 2, message: "策略存在 2 个已发布版本" },
      ]),
    );
    renderList();
    fireEvent.click(await screen.findByRole("button", { name: "删除 draft-only" }));
    fireEvent.change(await screen.findByLabelText("确认策略名称"), { target: { value: "draft-only" } });
    fireEvent.click(screen.getByRole("button", { name: "确认删除" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("策略存在 2 个已发布版本");
  });

  it("prevents duplicate delete submissions while pending", async () => {
    let resolveDelete: (() => void) | undefined;
    vi.mocked(api.deleteStrategy).mockImplementation(
      () => new Promise((resolve) => {
        resolveDelete = () => resolve(undefined);
      }),
    );
    renderList();
    fireEvent.click(await screen.findByRole("button", { name: "删除 draft-only" }));
    fireEvent.change(await screen.findByLabelText("确认策略名称"), { target: { value: "draft-only" } });
    const confirm = screen.getByRole("button", { name: "确认删除" });
    fireEvent.click(confirm);
    await waitFor(() => expect(confirm).toBeDisabled());
    fireEvent.click(confirm);
    expect(api.deleteStrategy).toHaveBeenCalledTimes(1);
    resolveDelete?.();
    await waitFor(() => expect(screen.queryByRole("dialog", { name: "删除策略" })).not.toBeInTheDocument());
  });

  it("returns to strategies list after detail-page delete", async () => {
    vi.mocked(api.listStrategies).mockResolvedValue({ items: [draftOnly], total: 1 });
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={client}>
        <MemoryRouter initialEntries={["/strategies/strategy-1"]}>
          <Routes>
            <Route path="/strategies" element={<Outlet />}>
              <Route index element={<div>strategies-list</div>} />
              <Route path=":strategyId" element={<StrategyDetailPage />} />
            </Route>
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>,
    );

    fireEvent.click(await screen.findByRole("button", { name: "删除策略" }));
    fireEvent.change(await screen.findByLabelText("确认策略名称"), { target: { value: "draft-only" } });
    fireEvent.click(screen.getByRole("button", { name: "确认删除" }));
    await waitFor(() => expect(api.deleteStrategy).toHaveBeenCalled());
    expect(await screen.findByText("strategies-list")).toBeVisible();
  });

  it("loads trusted strategies without draft instead of staying on skeleton", async () => {
    const trusted = {
      strategyId: "trusted-1",
      name: "trusted-deviation-analysis-execute",
      lifecycle: "TRUSTED",
      createdAt: "2026-07-23T00:00:00Z",
      updatedAt: "2026-07-26T00:00:00Z",
      draftId: null,
      draftRevision: null,
      latestVersion: 1,
    };
    vi.mocked(api.listStrategies).mockResolvedValue({ items: [trusted], total: 1 });
    vi.mocked(api.listVersions).mockResolvedValue({
      items: [{
        strategyVersionId: "version-1",
        strategyId: trusted.strategyId,
        version: 1,
        lifecycle: "PUBLISHED",
        planHash: "a".repeat(64),
        schemaVersion: "swarmcore.io/v1",
        runtimeVersion: "1.1.0",
        createdAt: "2026-07-23T00:00:00Z",
      }],
      total: 1,
    });
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={client}>
        <MemoryRouter initialEntries={["/strategies/trusted-1"]}>
          <Routes>
            <Route path="/strategies/:strategyId" element={<StrategyDetailPage />} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>,
    );

    expect(await screen.findByText("该策略没有可编辑草稿")).toBeVisible();
    expect(screen.getByRole("heading", { name: trusted.name })).toBeVisible();
    expect(screen.getByText("版本 1")).toBeVisible();
    expect(api.getDraft).not.toHaveBeenCalled();
    expect(document.querySelector(".animate-pulse")).toBeNull();
  });
});
