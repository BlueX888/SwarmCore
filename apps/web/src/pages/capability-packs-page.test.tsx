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
      disableCapabilityPack: vi.fn(),
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
      manifest: { apiVersion: "swarmcore.io/v2", spec: {
        case: { type: "contract-case", schema: "schema://contract/case@1" },
        agents: ["agent://contract/classifier@1", "agent://contract/extractor@1"],
        tools: ["tool://document/read@1", "tool://rules/evaluate@1"],
      } },
      enabled: true,
      bindingStatus: "ENABLED",
      configuration: { minimumConfidence: 0.8 },
      blockers: [],
    }] });
    vi.mocked(api.enableCapabilityPack).mockResolvedValue(undefined);
    vi.mocked(api.disableCapabilityPack).mockResolvedValue({
      packId: "pack-1", name: "contract-integrity", versionId: "version-1", version: "1.1.0", contentHash: "a".repeat(64),
      manifest: {}, enabled: false, bindingStatus: "DISABLED", configuration: {}, blockers: [],
    });
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
    expect(screen.getByRole("link", { name: "进入工作台" })).toHaveAttribute("href", "/capability-packs/contract-integrity/workbench");
    expect(screen.getByRole("button", { name: "决策资产" })).toBeVisible();
    expect(screen.getByRole("button", { name: "资料要求" })).toBeVisible();
  });

  it("keeps long capability names separate from their action group", async () => {
    vi.mocked(api.listCapabilityPacks).mockResolvedValue({ items: [{
      packId: "pack-post-evaluation",
      name: "contract-post-evaluation",
      versionId: "version-post-evaluation",
      version: "1.5.0",
      contentHash: "b".repeat(64),
      manifest: { spec: { case: { type: "contract-post-evaluation-case" }, agents: [], tools: [] } },
      enabled: false,
      bindingStatus: null,
      configuration: {},
      blockers: [],
    }] });
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(<QueryClientProvider client={client}><MemoryRouter><CapabilityPacksPage /></MemoryRouter></QueryClientProvider>);

    expect(await screen.findByRole("heading", { name: "contract-post-evaluation" })).toBeVisible();
    const actions = screen.getByLabelText("contract-post-evaluation v1.5.0 操作");
    expect(actions).toContainElement(screen.getByRole("link", { name: "配置能力包" }));
    expect(screen.getByRole("link", { name: "配置能力包" })).toHaveAttribute("href", "/capability-packs/contract-post-evaluation");
    expect(actions).toContainElement(screen.getByRole("button", { name: "进入工作台" }));
    expect(screen.getByRole("button", { name: "进入工作台" })).toBeDisabled();
    expect(actions).toContainElement(screen.getByRole("button", { name: "启用" }));
  });

  it("edits project binding configuration without changing the immutable version", async () => {
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(<QueryClientProvider client={client}><MemoryRouter><CapabilityPacksPage /></MemoryRouter></QueryClientProvider>);

    fireEvent.click(await screen.findByRole("button", { name: "配置 contract-integrity v1.1.0" }));
    expect(screen.getByText("可修改已发布能力包在当前项目的配置，不影响能力包版本内容。请勿填写密码、令牌等凭证。")).toBeVisible();
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

  it("shows missing v2 bindings before the user attempts to enable the pack", async () => {
    vi.mocked(api.listCapabilityPacks).mockResolvedValue({ items: [{
      packId: "pack-1", name: "contract-integrity", versionId: "version-1", version: "2.0.0", contentHash: "a".repeat(64),
      manifest: { apiVersion: "swarmcore.io/v2", spec: { case: { type: "contract-case" }, agents: [], tools: [] } },
      enabled: false, bindingStatus: "DISABLED", configuration: {},
      blockers: [{ ref: "contract-files", reasons: ["RESOURCE_BINDING_MISSING"] }],
    }] });
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(<QueryClientProvider client={client}><MemoryRouter><CapabilityPacksPage /></MemoryRouter></QueryClientProvider>);

    expect(await screen.findByText("contract-files：缺少业务资料（旧版本兼容项）")).toBeVisible();
    expect(screen.getByRole("link", { name: "处理阻塞项" })).toHaveAttribute("href", "/capability-packs/contract-integrity");
    fireEvent.click(screen.getByRole("button", { name: "配置 contract-integrity v2.0.0" }));
    expect(screen.getByRole("button", { name: "保存并启用" })).toBeDisabled();
    expect(api.enableCapabilityPack).not.toHaveBeenCalled();
  });

  it("shows readiness blocker details returned while saving configuration", async () => {
    vi.mocked(api.enableCapabilityPack).mockRejectedValue(new ApiError(
      409,
      "CAPABILITY_PACK_NOT_READY",
      "CAPABILITY_PACK_NOT_READY",
      [{ ref: "contract-files", reasons: ["RESOURCE_BINDING_MISSING"] }],
    ));
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(<QueryClientProvider client={client}><MemoryRouter><CapabilityPacksPage /></MemoryRouter></QueryClientProvider>);

    fireEvent.click(await screen.findByRole("button", { name: "配置 contract-integrity v1.1.0" }));
    fireEvent.click(screen.getByRole("button", { name: "保存配置" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("保存失败：能力包尚未就绪：contract-files：缺少业务资料（旧版本兼容项）。请通过“配置能力包”处理。");
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
      apiVersion: "swarmcore.io/v2",
      metadata: { name: "custom-capability", version: "1.0.0" },
      spec: {
        case: { type: "custom-work-item", schema: "schema://contract/case@1" },
        agents: ["agent://contract/document-classifier@1"],
        tools: ["tool://document/read@1", "tool://rules/evaluate@1"],
        strategies: { execute: "strategy://project/strategy-1@2" },
      },
    });
    expect(request?.manifest.spec).not.toHaveProperty("workItemType");
    expect(request?.strategyVersionId).toBe("strategy-version-2");
    await waitFor(() => expect(screen.queryByRole("dialog", { name: "新建业务能力包" })).not.toBeInTheDocument());
  });

  it("deletes a capability pack version after confirmation", async () => {
    vi.mocked(api.listCapabilityPacks).mockResolvedValue({ items: [{
      packId: "pack-1", name: "contract-integrity", versionId: "version-1", version: "1.1.0", contentHash: "a".repeat(64),
      manifest: {}, enabled: false, bindingStatus: "DISABLED", configuration: {}, blockers: [],
    }] });
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

  it("keeps deletion visible but disabled until an enabled pack is stopped", async () => {
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(<QueryClientProvider client={client}><MemoryRouter><CapabilityPacksPage /></MemoryRouter></QueryClientProvider>);

    expect(await screen.findByRole("button", { name: "停用 contract-integrity v1.1.0" })).toBeVisible();
    expect(screen.getByRole("button", { name: "删除 contract-integrity v1.1.0" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "删除 contract-integrity v1.1.0" })).toHaveAttribute("title", "请先停用此版本，再执行删除");
    fireEvent.click(screen.getByRole("button", { name: "停用 contract-integrity v1.1.0" }));

    await waitFor(() => expect(api.disableCapabilityPack).toHaveBeenCalledWith(
      expect.any(String),
      expect.any(String),
      "version-1",
    ));
    expect(api.deleteCapabilityPack).not.toHaveBeenCalled();
  });

  it("keeps evaluation-referenced versions visible but prevents an invalid delete request", async () => {
    vi.mocked(api.listCapabilityPacks).mockResolvedValue({ items: [{
      packId: "pack-1", name: "contract-post-evaluation", versionId: "version-1", version: "1.1.0", contentHash: "a".repeat(64),
      manifest: {}, enabled: false, bindingStatus: "DISABLED", configuration: {}, blockers: [],
      deleteBlockedReason: "能力包版本仍有历史评估引用。无法删除。",
    }] });
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(<QueryClientProvider client={client}><MemoryRouter><CapabilityPacksPage /></MemoryRouter></QueryClientProvider>);

    const deleteButton = await screen.findByRole("button", { name: "删除 contract-post-evaluation v1.1.0" });
    expect(deleteButton).toBeVisible();
    expect(deleteButton).toBeDisabled();
    expect(deleteButton).toHaveAttribute("title", "能力包版本仍有历史评估引用。无法删除。");
    fireEvent.click(deleteButton);
    expect(api.deleteCapabilityPack).not.toHaveBeenCalled();
  });

  it("shows delete errors from the API", async () => {
    vi.mocked(api.listCapabilityPacks).mockResolvedValue({ items: [{
      packId: "pack-1", name: "contract-integrity", versionId: "version-1", version: "1.1.0", contentHash: "a".repeat(64),
      manifest: {}, enabled: false, bindingStatus: "DISABLED", configuration: {}, blockers: [],
    }] });
    const confirm = vi.spyOn(window, "confirm").mockReturnValue(true);
    vi.mocked(api.deleteCapabilityPack).mockRejectedValue(new ApiError(409, "能力包版本仍处于启用状态。请先停用后再删除。", "CAPABILITY_PACK_ENABLED"));
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(<QueryClientProvider client={client}><MemoryRouter><CapabilityPacksPage /></MemoryRouter></QueryClientProvider>);

    fireEvent.click(await screen.findByRole("button", { name: "删除 contract-integrity v1.1.0" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("删除失败：能力包版本仍处于启用状态。请先停用后再删除。");
    confirm.mockRestore();
  });

  it("maps not-found delete failures to Chinese copy", async () => {
    vi.mocked(api.listCapabilityPacks).mockResolvedValue({ items: [{
      packId: "pack-1", name: "contract-integrity", versionId: "version-1", version: "1.1.0", contentHash: "a".repeat(64),
      manifest: {}, enabled: false, bindingStatus: "DISABLED", configuration: {}, blockers: [],
    }] });
    const confirm = vi.spyOn(window, "confirm").mockReturnValue(true);
    vi.mocked(api.deleteCapabilityPack).mockRejectedValue(new ApiError(404, "Not Found", "NOT_FOUND"));
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(<QueryClientProvider client={client}><MemoryRouter><CapabilityPacksPage /></MemoryRouter></QueryClientProvider>);

    fireEvent.click(await screen.findByRole("button", { name: "删除 contract-integrity v1.1.0" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("删除失败：能力包版本不存在或已被删除。");
    confirm.mockRestore();
  });
});
