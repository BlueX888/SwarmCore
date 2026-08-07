import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { api } from "@/api/client";
import type { BusinessWorkSnapshot } from "@/api/types";
import { BusinessWorkSettingsPage } from "./business-work-settings-page";

vi.mock("@/api/client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/api/client")>();
  return {
    ...actual,
    api: {
      ...actual.api,
      getBusinessWork: vi.fn(),
      listStrategies: vi.fn(),
      listVersions: vi.fn(),
      listPublishedStrategyVersions: vi.fn(),
      listDocuments: vi.fn(),
      bindBusinessWorkStrategy: vi.fn(),
      getPackBindings: vi.fn(),
      createDecisionAsset: vi.fn(),
      publishDecisionAsset: vi.fn(),
      bindCapabilityPackDecision: vi.fn(),
    },
  };
});

const workSnapshot: BusinessWorkSnapshot = {
  workKey: "contract-post-evaluation",
  name: "合同后评价",
  shortName: "合同后评价",
  category: "business",
  summary: "合同后评价业务",
  status: "incomplete",
  statusLabel: "配置不完整",
  qualificationStatus: "local_verified",
  qualificationLabel: "本地验证，待生产准入",
  packName: "contract-post-evaluation",
  packVersionId: "pack-version-1",
  packVersion: "2.0.5",
  enabled: true,
  bindingStatus: "ENABLED",
  blockers: [{ code: "DOCUMENT_BINDING_MISSING", message: "资料分类 CONTRACT 尚未绑定到本业务工作。", ref: "CONTRACT" }],
  agents: [
    "agent://contract/baseline-analyst@2",
    "agent://contract/performance-quality-analyst@2",
    "agent://contract/finance-invoice-analyst@2",
    "agent://contract/deviation-risk-analyst@2",
    "agent://contract/evidence-reviewer@1",
    "agent://contract/report-narrator@1",
  ],
  tools: [
    "tool://document/read-versions@1",
    "tool://evidence/search@1",
    "tool://document/coverage-check@1",
    "tool://contract/post-evaluation/merge-domains@1",
    "tool://contract/timeline-calculate@1",
    "tool://finance/amount-reconcile@1",
    "tool://invoice/assurance@1",
    "tool://deviation/aggregate@1",
    "tool://risk/aggregate@1",
    "tool://evidence/consistency-check@1",
    "tool://contract/post-evaluation@1",
    "tool://contract/post-evaluation/finalize@2",
    "tool://report/render-post-evaluation@3",
    "tool://workbench/record-post-evaluation@2",
  ],
  models: [],
  documentRequirements: [{ category: "CONTRACT", required: true }],
  documentBindingKeys: ["contract-post-evaluation", "contract-post-evaluation-case"],
  decisionSlots: [],
  functions: [],
  configuration: {},
  workItemType: "contract-post-evaluation-case",
  caseBased: true,
  boundStrategyVersionId: "strategy-version-1",
  boundStrategyName: "后评价执行策略",
  boundStrategyVersion: 7,
};

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={["/business-works/contract-post-evaluation/settings"]}>
        <Routes>
          <Route path="/business-works/:workKey/settings" element={<BusinessWorkSettingsPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("business work settings configuration", () => {
  beforeEach(() => {
    vi.mocked(api.getBusinessWork).mockResolvedValue(workSnapshot);
    vi.mocked(api.listStrategies).mockResolvedValue({
      items: [{ strategyId: "strategy-1", name: "后评价执行策略", lifecycle: "ACTIVE", createdAt: "2026-01-01", updatedAt: "2026-01-01", draftId: null, draftRevision: null, latestVersion: 7 }],
      total: 1,
    });
    vi.mocked(api.listVersions).mockResolvedValue({
      items: [{ strategyVersionId: "strategy-version-1", strategyId: "strategy-1", version: 7, lifecycle: "PUBLISHED", planHash: "a".repeat(64), schemaVersion: "swarmcore.io/v1", runtimeVersion: "1.1.0", createdAt: "2026-01-01" }],
      total: 1,
    });
    vi.mocked(api.listDocuments).mockResolvedValue({
      items: [{
        documentId: "document-1", name: "采购合同.pdf", category: "CONTRACT", tags: [], status: "AVAILABLE",
        currentVersion: 1, updatedAt: "2026-07-23T00:00:00Z", current: null,
        businessObjectIds: [], businessWorkKeys: ["contract-post-evaluation"], versions: [],
      }],
    });
    vi.mocked(api.bindBusinessWorkStrategy).mockResolvedValue({
      ...workSnapshot,
      status: "runnable",
      statusLabel: "可运行",
      blockers: [],
    });
    vi.mocked(api.listPublishedStrategyVersions).mockResolvedValue({
      items: [{ strategyVersionId: "strategy-version-1", strategyId: "strategy-1", strategyName: "后评价执行策略", version: 7, lifecycle: "PUBLISHED" }],
      total: 1,
    });
    vi.mocked(api.getPackBindings).mockResolvedValue({ decisions: [], resources: [] });
    vi.mocked(api.createDecisionAsset).mockResolvedValue({
      decisionAssetId: "decision-1",
      draftId: "draft-1",
      revision: 1,
      definition: {},
    });
    vi.mocked(api.publishDecisionAsset).mockResolvedValue({
      decisionAssetId: "decision-1",
      decisionVersionId: "decision-version-1",
      version: 1,
      contentHash: "a".repeat(64),
    });
    vi.mocked(api.bindCapabilityPackDecision).mockResolvedValue({
      bindingId: "binding-1",
      slot: "document-checklist",
      decisionVersionId: "decision-version-1",
      contentHash: "a".repeat(64),
    });
  });
  afterEach(() => { cleanup(); vi.clearAllMocks(); });

  it("shows only strategy binding and external file inputs", async () => {
    renderPage();

    expect(await screen.findByRole("heading", { name: "合同后评价" })).toBeVisible();
    expect(screen.getByTestId("business-work-page-header")).toBeVisible();
    expect(screen.getByRole("link", { name: "返回业务工作" })).toHaveAttribute(
      "href",
      "/business-works/contract-post-evaluation",
    );
    expect(screen.getByText("项目配置")).toBeVisible();
    expect(screen.getByText("选择已发布的执行策略，并提供合同后评价所需的外部文件。")).toBeVisible();
    expect(screen.getByText("策略绑定")).toBeVisible();
    expect(screen.getByText("外部文件")).toBeVisible();
    expect(screen.getByText("执行组成")).toBeVisible();
    expect(screen.getByText("Agent · 6")).toBeVisible();
    expect(screen.getByText("工具 · 14")).toBeVisible();
    expect(screen.getByText("agent://contract/evidence-reviewer@1")).toBeVisible();
    expect(screen.getByText("tool://evidence/search@1")).toBeVisible();
    expect(screen.getByLabelText("已发布策略版本")).toHaveValue("strategy-version-1");
    expect(screen.getByRole("link", { name: "打开策略管理" })).toHaveAttribute("href", "/strategies");
    expect(screen.getByRole("link", { name: "提供外部文件" })).toHaveAttribute("href", "/documents");
    expect(screen.getByText("已准备")).toBeVisible();
    expect(screen.getByText("采购合同.pdf")).toBeVisible();
    expect(screen.queryByText("配置 Agent")).not.toBeInTheDocument();
    expect(screen.queryByText("运行参数 JSON")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("项目运行配置 JSON")).not.toBeInTheDocument();
    expect(screen.queryByText("智能体 / 工具")).not.toBeInTheDocument();
  });

  it("binds the selected published strategy version", async () => {
    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: "重新绑定当前策略" }));
    await waitFor(() => expect(api.bindBusinessWorkStrategy).toHaveBeenCalledWith(
      expect.any(String),
      expect.any(String),
      "contract-post-evaluation",
      "strategy-version-1",
    ));
    expect(await screen.findByText("策略绑定已更新。")).toBeVisible();
  });

  it("stops showing the loading placeholder after strategies resolve", async () => {
    renderPage();
    expect(await screen.findByLabelText("已发布策略版本")).toBeVisible();
    await waitFor(() => {
      expect(screen.queryByText("正在加载策略…")).not.toBeInTheDocument();
    });
    expect(screen.getByRole("option", { name: /后评价执行策略 · v7/ })).toBeInTheDocument();
  });

  it("shows a failure message instead of infinite loading when strategies fail", async () => {
    vi.mocked(api.listPublishedStrategyVersions).mockRejectedValue(new Error("strategies unavailable"));
    renderPage();
    expect(await screen.findByRole("alert")).toHaveTextContent("策略加载失败：strategies unavailable");
    expect(screen.queryByText("正在加载策略…")).not.toBeInTheDocument();
  });

  it("creates, publishes, and binds a checklist for a missing decision slot", async () => {
    vi.mocked(api.getBusinessWork).mockResolvedValue({
      ...workSnapshot,
      workKey: "document-integrity",
      name: "文件完整性校验智能体",
      packName: "contract-integrity",
      documentRequirements: [{
        key: "contract",
        category: "CONTRACT",
        required: true,
        minCount: 1,
        acceptedMediaTypes: ["application/pdf"],
      }],
      decisionSlots: [{
        slot: "document-checklist",
        required: true,
        inputSchema: "schema://contract/validation-input@2",
        outputSchema: "schema://contract/validation-result@1",
        allowedTypes: ["CHECKLIST", "DECISION_TABLE"],
      }],
    });

    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: "创建并绑定检查清单" }));

    await waitFor(() => expect(api.createDecisionAsset).toHaveBeenCalledOnce());
    const createBody = vi.mocked(api.createDecisionAsset).mock.calls[0]?.[2];
    expect(createBody?.definition).toMatchObject({
      inputSchema: "schema://contract/validation-input@2",
      outputSchema: "schema://contract/validation-result@1",
    });
    expect(api.publishDecisionAsset).toHaveBeenCalledWith(
      expect.any(String),
      expect.any(String),
      "decision-1",
    );
    expect(api.bindCapabilityPackDecision).toHaveBeenCalledWith(
      expect.any(String),
      expect.any(String),
      "pack-version-1",
      "document-checklist",
      "decision-version-1",
    );
  });
});
