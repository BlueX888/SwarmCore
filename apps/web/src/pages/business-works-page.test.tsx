import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { api } from "@/api/client";
import type { BusinessWorkSnapshot } from "@/api/types";
import { BUSINESS_WORKS } from "@/lib/business-works";
import { BusinessWorksPage } from "./business-works-page";

vi.mock("@/api/client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/api/client")>();
  return {
    ...actual,
    api: {
      ...actual.api,
      listBusinessWorks: vi.fn(),
      getBusinessWork: vi.fn(),
      listDocuments: vi.fn(),
    },
  };
});

function snapshot(overrides: Partial<BusinessWorkSnapshot> = {}): BusinessWorkSnapshot {
  const base = BUSINESS_WORKS.find((item) => item.key === (overrides.workKey ?? "document-integrity")) ?? BUSINESS_WORKS[2];
  return {
    workKey: base.key,
    name: base.name,
    shortName: base.shortName,
    category: base.category,
    summary: base.summary,
    status: "planned",
    statusLabel: "规划中",
    packName: null,
    packVersionId: null,
    packVersion: null,
    enabled: false,
    bindingStatus: null,
    blockers: [],
    agents: [],
    tools: [],
    models: [],
    documentRequirements: [],
    decisionSlots: [],
    functions: base.functions,
    configuration: {},
    workItemType: null,
    caseBased: false,
    ...overrides,
    boundStrategyVersionId: overrides.boundStrategyVersionId ?? null,
    boundStrategyName: overrides.boundStrategyName ?? null,
    boundStrategyVersion: overrides.boundStrategyVersion ?? null,
  };
}

function renderPage(path = "/business-works") {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}><MemoryRouter initialEntries={[path]}><Routes>
    <Route path="/business-works" element={<BusinessWorksPage />} />
    <Route path="/business-works/:workKey" element={<BusinessWorksPage />} />
    <Route path="/business-works/report-generation/demo" element={<h1>报告生成 Demo</h1>} />
    <Route path="/business-works/:workKey/workbench" element={<h1>业务工作台</h1>} />
    <Route path="/business-works/:workKey/settings" element={<h1>项目配置</h1>} />
  </Routes></MemoryRouter></QueryClientProvider>);
}

describe("business works page", () => {
  beforeEach(() => {
    vi.mocked(api.listBusinessWorks).mockResolvedValue({
      items: BUSINESS_WORKS.map((work) => snapshot({
        workKey: work.key,
        name: work.name,
        shortName: work.shortName,
        category: work.category,
        summary: work.summary,
        functions: work.functions,
        status: work.key === "document-integrity" ? "runnable" : "planned",
        statusLabel: work.key === "document-integrity" ? "可运行" : "规划中",
        packName: work.key === "document-integrity" ? "contract-integrity" : null,
      })),
    });
    vi.mocked(api.getBusinessWork).mockImplementation((_tenant, _project, workKey) => {
      if (workKey === "document-integrity") {
        return Promise.resolve(snapshot({
          workKey: "document-integrity",
          status: "runnable",
          statusLabel: "可运行",
          packName: "contract-integrity",
          agents: ["agent://contract/document-classifier@1"],
          tools: ["tool://document/read@1"],
        }));
      }
      return Promise.resolve(snapshot({ workKey, status: "planned", statusLabel: "规划中" }));
    });
    vi.mocked(api.listDocuments).mockResolvedValue({ items: [] });
  });
  afterEach(() => { cleanup(); vi.clearAllMocks(); });

  it("lists works with real statuses instead of all planned", async () => {
    renderPage();
    expect(await screen.findByRole("heading", { name: "业务工作" })).toBeVisible();
    expect(screen.getAllByText("可运行").length).toBeGreaterThan(0);
    expect(screen.getAllByText("规划中").length).toBeGreaterThan(0);
  });

  it("lets runnable works enter the workbench and blocks planned works", async () => {
    renderPage("/business-works/document-integrity");
    expect(await screen.findByRole("heading", { name: "文件完整性校验智能体" })).toBeVisible();
    expect(screen.getByRole("link", { name: "开始办理" })).toHaveAttribute("href", "/business-works/document-integrity/workbench");
    expect(screen.getByRole("link", { name: "项目配置" })).toHaveAttribute("href", "/business-works/document-integrity/settings");
    const readiness = screen.getByLabelText("运行就绪摘要");
    expect(readiness).toBeVisible();
    expect(within(readiness).getByText("资料要求")).toBeVisible();
    expect(within(readiness).getByText("执行策略")).toBeVisible();
    expect(screen.getByText("可运行")).toBeVisible();

    renderPage("/business-works/invoice-assurance");
    expect(await screen.findByRole("heading", { name: "发票一致性校验智能体" })).toBeVisible();
    expect(screen.getByRole("button", { name: "开始办理" })).toBeDisabled();
  });

  it("offers the public-data demo from report generation", async () => {
    renderPage("/business-works/report-generation");

    expect(await screen.findByRole("heading", { name: "报告生成智能体" })).toBeVisible();
    expect(screen.getByRole("link", { name: "体验公开数据 Demo" })).toHaveAttribute(
      "href",
      "/business-works/report-generation/demo",
    );
  });

  it("filters by category and searches function descriptions", async () => {
    renderPage();
    await screen.findByRole("heading", { name: "业务工作" });
    fireEvent.click(screen.getByRole("button", { name: "调度治理" }));
    expect(screen.getByRole("heading", { name: "智能体调度校准智能体" })).toBeVisible();
    expect(screen.queryByRole("heading", { name: "发票一致性校验智能体" })).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "全部" }));
    fireEvent.change(screen.getByRole("textbox", { name: "搜索业务工作或功能" }), { target: { value: "甘特图" } });
    await waitFor(() => expect(screen.getByRole("heading", { name: "履约计划与执行采集智能体" })).toBeVisible());
    expect(screen.queryByRole("heading", { name: "文件完整性校验智能体" })).not.toBeInTheDocument();
  });

  it("shows shared configuration entries on detail", async () => {
    renderPage("/business-works/invoice-assurance");
    expect(await screen.findByRole("heading", { name: "发票一致性校验智能体" })).toBeVisible();
    const functions = screen.getByRole("region", { name: "业务说明" });
    expect(within(functions).getByRole("heading", { name: /发票信息识别/ })).toBeVisible();
    expect(screen.getAllByRole("link", { name: "准备业务资料" })[0]).toHaveAttribute("href", "/documents");
  });

  it("keeps contract post-evaluation detail focused on start readiness", async () => {
    vi.mocked(api.getBusinessWork).mockResolvedValue(snapshot({
      workKey: "contract-post-evaluation",
      name: "合同后评价",
      shortName: "合同后评价",
      status: "runnable",
      statusLabel: "可运行",
      packName: "contract-post-evaluation",
      packVersion: "1.6.1",
      enabled: true,
      workItemType: "contract-post-evaluation-case",
      documentRequirements: [{ category: "CONTRACT", required: true }],
      boundStrategyVersionId: "strategy-version-1",
      boundStrategyName: "后评价执行策略",
      boundStrategyVersion: 7,
    }));
    vi.mocked(api.listDocuments).mockResolvedValue({ items: [] });

    renderPage("/business-works/contract-post-evaluation");
    expect(await screen.findByRole("heading", { name: "合同后评价" })).toBeVisible();
    expect(screen.getByRole("link", { name: "开始办理" })).toHaveAttribute(
      "href",
      "/business-works/contract-post-evaluation/workbench",
    );
    expect(screen.getByLabelText("运行就绪摘要")).toBeVisible();
    expect(screen.queryByLabelText("当前运行资格")).not.toBeInTheDocument();
    expect(screen.getByText("业务说明").closest("details")).not.toHaveAttribute("open");
    expect(screen.queryByRole("heading", { name: "配置工作所需能力" })).not.toBeInTheDocument();
  });

  it("shows bound external files and readiness on contract post-evaluation detail", async () => {
    vi.mocked(api.getBusinessWork).mockResolvedValue(snapshot({
      workKey: "contract-post-evaluation",
      name: "合同后评价",
      shortName: "合同后评价",
      status: "incomplete",
      statusLabel: "配置不完整",
      packName: "contract-post-evaluation",
      packVersion: "1.6.1",
      enabled: true,
      workItemType: "contract-post-evaluation-case",
      documentRequirements: [{ category: "CONTRACT", required: true }],
      boundStrategyVersionId: "strategy-version-1",
      boundStrategyName: "后评价执行策略",
      boundStrategyVersion: 7,
    }));
    vi.mocked(api.listDocuments).mockResolvedValue({
      items: [{
        documentId: "document-1",
        name: "采购合同.pdf",
        category: "CONTRACT",
        tags: [],
        status: "AVAILABLE",
        currentVersion: 1,
        updatedAt: "2026-07-23T00:00:00Z",
        current: null,
        businessObjectIds: [],
        businessWorkKeys: ["contract-post-evaluation"],
        versions: [],
      }],
    });

    renderPage("/business-works/contract-post-evaluation");
    expect(await screen.findByRole("heading", { name: "合同后评价" })).toBeVisible();
    const summary = within(screen.getByRole("region", { name: "项目配置摘要" }));
    expect(summary.getByRole("heading", { name: "策略绑定" })).toBeVisible();
    expect(summary.getByText("已绑定")).toBeVisible();
    expect(summary.getByText("当前执行策略")).toBeVisible();
    expect(summary.getByText("后评价执行策略")).toBeVisible();
    expect(summary.getByText("v7")).toBeVisible();
    expect(summary.getByRole("link", { name: "管理策略绑定" })).toHaveAttribute(
      "href",
      "/business-works/contract-post-evaluation/settings",
    );
    expect(summary.getByRole("heading", { name: "外部文件" })).toBeVisible();
    expect(summary.getByText("合同文件")).toBeVisible();
    expect(summary.getByText(/已准备/)).toBeVisible();
    expect(summary.getByText("采购合同.pdf")).toBeVisible();
    expect(screen.queryByText("当前无强制资料分类要求。")).not.toBeInTheDocument();
    expect(summary.getByRole("link", { name: "提供外部文件" })).toHaveAttribute("href", "/documents");
    expect(screen.queryByRole("heading", { name: "业务配置入口" })).not.toBeInTheDocument();
  });

  it("prompts to bind a strategy when none is selected", async () => {
    vi.mocked(api.getBusinessWork).mockResolvedValue(snapshot({
      workKey: "contract-post-evaluation",
      name: "合同后评价",
      shortName: "合同后评价",
      status: "not_configured",
      statusLabel: "未配置",
      packName: "contract-post-evaluation",
      enabled: false,
      documentRequirements: [],
    }));

    renderPage("/business-works/contract-post-evaluation");
    expect(await screen.findByRole("heading", { name: "策略绑定" })).toBeVisible();
    expect(screen.getByText("尚未绑定执行策略")).toBeVisible();
    expect(screen.getByRole("link", { name: "绑定策略" })).toHaveAttribute(
      "href",
      "/business-works/contract-post-evaluation/settings",
    );
  });

  it("lists bound files even when strategy declares no document requirements", async () => {
    vi.mocked(api.getBusinessWork).mockResolvedValue(snapshot({
      workKey: "contract-post-evaluation",
      name: "合同后评价",
      shortName: "合同后评价",
      status: "runnable",
      statusLabel: "可运行",
      packName: "contract-post-evaluation",
      documentRequirements: [],
      boundStrategyVersionId: "strategy-version-1",
      boundStrategyName: "后评价执行策略",
      boundStrategyVersion: 7,
    }));
    vi.mocked(api.listDocuments).mockResolvedValue({
      items: [{
        documentId: "document-2",
        name: "验收资料.pdf",
        category: "PERFORMANCE",
        tags: [],
        status: "AVAILABLE",
        currentVersion: 1,
        updatedAt: "2026-07-23T00:00:00Z",
        current: null,
        businessObjectIds: [],
        businessWorkKeys: ["contract-post-evaluation"],
        versions: [],
      }],
    });

    renderPage("/business-works/contract-post-evaluation");
    expect(await screen.findByText("验收资料.pdf")).toBeVisible();
    expect(screen.getByText(/以下文件已绑定到本业务工作/)).toBeVisible();
  });
});
