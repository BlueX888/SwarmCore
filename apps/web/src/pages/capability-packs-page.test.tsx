import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError, api } from "@/api/client";
import { CapabilityPacksPage } from "./capability-packs-page";

vi.mock("@/api/client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/api/client")>();
  return {
    ...actual,
    api: {
      listCapabilityPacks: vi.fn(),
      listStrategies: vi.fn(),
      listVersions: vi.fn(),
      getVersion: vi.fn(),
      createCapabilityPack: vi.fn(),
      enableCapabilityPack: vi.fn(),
      deleteCapabilityPack: vi.fn(),
    },
  };
});

describe("capability packs page", () => {
  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
  });

  beforeEach(() => {
    vi.mocked(api.listCapabilityPacks).mockResolvedValue({ items: [{
      packId: "pack-1",
      name: "contract-integrity",
      versionId: "version-1",
      version: "1.1.0",
      contentHash: "a".repeat(64),
      manifest: { spec: {
        workItemType: "contract-case",
        agents: ["agent://contract/classifier@1", "agent://contract/extractor@1"],
        tools: ["tool://document/read@1", "tool://rules/evaluate@1"],
      } },
      enabled: true,
      bindingStatus: "ENABLED",
      configuration: { minimumConfidence: 0.8 },
      blockers: [],
    }] });
    vi.mocked(api.enableCapabilityPack).mockResolvedValue(undefined);
    vi.mocked(api.deleteCapabilityPack).mockResolvedValue(undefined);
    vi.mocked(api.listStrategies).mockResolvedValue({ items: [{ strategyId: "strategy-1", name: "contract-review", lifecycle: "ACTIVE", createdAt: "2026-01-01", updatedAt: "2026-01-01", draftId: null, draftRevision: null, latestVersion: 2 }], total: 1 });
    vi.mocked(api.listVersions).mockResolvedValue({ items: [{ strategyVersionId: "strategy-version-2", strategyId: "strategy-1", version: 2, lifecycle: "PUBLISHED", planHash: "c".repeat(64), schemaVersion: "swarmcore.io/v1", runtimeVersion: "1.1.0", createdAt: "2026-01-01" }], total: 1 });
    vi.mocked(api.getVersion).mockResolvedValue({
      strategyVersionId: "strategy-version-2", strategyId: "strategy-1", version: 2, lifecycle: "PUBLISHED", planHash: "c".repeat(64), schemaVersion: "swarmcore.io/v1", runtimeVersion: "1.1.0", createdAt: "2026-01-01",
      spec: { apiVersion: "swarmcore.io/v1", kind: "SwarmStrategy", metadata: { name: "contract-review" }, spec: { graph: { entrypoint: "review", nodes: { review: { type: "agent", agent: "reviewer", dependsOn: [] }, evaluate: { type: "tool", tool: "tool://rules/evaluate@1", dependsOn: ["review"] } }, output: {} } } }, normalizedSpec: {}, plan: {
        resolved_agents: { reviewer: { registryRef: "agent://contract/document-classifier@1" } },
        resolved_tools: { "tool://document/read@1": {}, "tool://rules/evaluate@1": {} },
        budget: { max_tokens: 250000, max_parallelism: 2 },
      },
    });
    vi.mocked(api.createCapabilityPack).mockResolvedValue({
      packId: "pack-2", name: "custom-capability", versionId: "version-2", version: "1.0.0", contentHash: "b".repeat(64),
      manifest: {}, enabled: false, bindingStatus: null, configuration: {}, blockers: [],
    });
  });

  it("shows the Agent and tool declarations for each immutable version", async () => {
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(<QueryClientProvider client={client}><MemoryRouter><CapabilityPacksPage /></MemoryRouter></QueryClientProvider>);

    expect(await screen.findByText("Agent（2）")).toBeVisible();
    expect(screen.getByText("classifier")).toBeVisible();
    expect(screen.getByText("extractor")).toBeVisible();
    expect(screen.getByTitle("agent://contract/classifier@1")).toBeVisible();
    expect(screen.getByTitle("agent://contract/extractor@1")).toBeVisible();
    expect(screen.getByText("工具（2）")).toBeVisible();
    expect(screen.getByText("read")).toBeVisible();
    expect(screen.getByText("evaluate")).toBeVisible();
    expect(screen.getByTitle("tool://document/read@1")).toBeVisible();
    expect(screen.getByTitle("tool://rules/evaluate@1")).toBeVisible();
    expect(screen.getByText("已启用")).toBeVisible();
  });

  it("edits project binding configuration without changing the immutable version", async () => {
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(<QueryClientProvider client={client}><MemoryRouter><CapabilityPacksPage /></MemoryRouter></QueryClientProvider>);

    fireEvent.click(await screen.findByRole("button", { name: "配置 contract-integrity v1.1.0" }));
    const editor = screen.getByLabelText("contract-integrity v1.1.0 项目配置 JSON");
    expect(editor).toHaveValue(JSON.stringify({ minimumConfidence: 0.8 }, null, 2));

    fireEvent.change(editor, { target: { value: JSON.stringify({ minimumConfidence: 0.9, reviewMode: "strict" }) } });
    fireEvent.click(screen.getByRole("button", { name: "保存配置" }));

    await waitFor(() => expect(api.enableCapabilityPack).toHaveBeenCalledWith(
      expect.any(String),
      expect.any(String),
      "version-1",
      { minimumConfidence: 0.9, reviewMode: "strict" },
    ));
  });

  it("rejects a project configuration that is not a JSON object", async () => {
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(<QueryClientProvider client={client}><MemoryRouter><CapabilityPacksPage /></MemoryRouter></QueryClientProvider>);

    fireEvent.click(await screen.findByRole("button", { name: "配置 contract-integrity v1.1.0" }));
    fireEvent.change(screen.getByLabelText("contract-integrity v1.1.0 项目配置 JSON"), { target: { value: "[]" } });
    fireEvent.click(screen.getByRole("button", { name: "保存配置" }));

    expect(screen.getByRole("alert")).toHaveTextContent("配置必须是 JSON 对象");
    expect(api.enableCapabilityPack).not.toHaveBeenCalled();
  });

  it("publishes a new immutable pack bound to a strategy-management version", async () => {
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(<QueryClientProvider client={client}><MemoryRouter><CapabilityPacksPage /></MemoryRouter></QueryClientProvider>);

    fireEvent.click(await screen.findByRole("button", { name: "新建能力包" }));
    expect(await screen.findByRole("dialog", { name: "新建业务能力包" })).toBeVisible();
    expect(await screen.findByText("contract-review · v2 · cccccccc")).toBeVisible();
    expect(screen.getByText("Agent 依赖")).toBeVisible();
    expect(screen.getByText("agent://contract/document-classifier@1")).toBeVisible();
    expect(screen.getByText("最大 Token：250000")).toBeVisible();
    expect(screen.getByTestId("strategy-graph-preview")).toBeVisible();
    expect(screen.getByText("review")).toBeInTheDocument();
    expect(screen.getAllByText("evaluate").length).toBeGreaterThan(0);
    fireEvent.click(screen.getByRole("button", { name: "发布能力包" }));

    await waitFor(() => expect(api.createCapabilityPack).toHaveBeenCalledTimes(1));
    const request = vi.mocked(api.createCapabilityPack).mock.calls[0]?.[2];
    expect(request?.manifest).toMatchObject({
      metadata: { name: "custom-capability", version: "1.0.0" },
      spec: {
        workItemType: "custom-work-item",
        agents: ["agent://contract/document-classifier@1"],
        tools: ["tool://document/read@1", "tool://rules/evaluate@1"],
        strategies: { execute: "strategy://project/strategy-1@2" },
      },
    });
    expect(request?.strategyVersionId).toBe("strategy-version-2");
    await waitFor(() => expect(screen.queryByRole("dialog", { name: "新建业务能力包" })).not.toBeInTheDocument());
  });

  it("deletes a capability pack version after confirmation", async () => {
    const confirm = vi.spyOn(window, "confirm").mockReturnValue(true);
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(<QueryClientProvider client={client}><MemoryRouter><CapabilityPacksPage /></MemoryRouter></QueryClientProvider>);

    fireEvent.click(await screen.findByRole("button", { name: "删除 contract-integrity v1.1.0" }));
    expect(confirm).toHaveBeenCalled();
    await waitFor(() => expect(api.deleteCapabilityPack).toHaveBeenCalledWith(
      expect.any(String),
      expect.any(String),
      "version-1",
    ));
    confirm.mockRestore();
  });

    it("shows delete errors from the API", async () => {
    const confirm = vi.spyOn(window, "confirm").mockReturnValue(true);
    vi.mocked(api.deleteCapabilityPack).mockRejectedValue(new ApiError(409, "能力包版本仍处于启用状态。请先停用后再删除。", "CAPABILITY_PACK_ENABLED"));
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(<QueryClientProvider client={client}><MemoryRouter><CapabilityPacksPage /></MemoryRouter></QueryClientProvider>);

    fireEvent.click(await screen.findByRole("button", { name: "删除 contract-integrity v1.1.0" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("删除失败：能力包版本仍处于启用状态。请先停用后再删除。");
    confirm.mockRestore();
  });

  it("maps not-found delete failures to Chinese copy", async () => {
    const confirm = vi.spyOn(window, "confirm").mockReturnValue(true);
    vi.mocked(api.deleteCapabilityPack).mockRejectedValue(new ApiError(404, "Not Found", "NOT_FOUND"));
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(<QueryClientProvider client={client}><MemoryRouter><CapabilityPacksPage /></MemoryRouter></QueryClientProvider>);

    fireEvent.click(await screen.findByRole("button", { name: "删除 contract-integrity v1.1.0" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("删除失败：能力包版本不存在或已被删除。");
    confirm.mockRestore();
  });
});
