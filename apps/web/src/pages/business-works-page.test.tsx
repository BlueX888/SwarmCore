import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { api } from "@/api/client";
import type { BusinessWorkSnapshot, DocumentSnapshot, RunSummarySnapshot } from "@/api/types";
import { BUSINESS_WORKS } from "@/lib/business-works";
import { BusinessWorksPage } from "./business-works-page";

vi.mock("@/api/client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/api/client")>();
  return {
    ...actual,
    api: {
      ...actual.api,
      getBusinessWork: vi.fn(),
      listDocuments: vi.fn(),
      listRunSummaries: vi.fn(),
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
    <Route path="/agents" element={<h1>智能体能力中心</h1>} />
    <Route path="/overview" element={<h1>工作台</h1>} />
    <Route path="/t/:tenantId/p/:projectId/business-works" element={<BusinessWorksPage />} />
    <Route path="/t/:tenantId/p/:projectId/overview" element={<h1>项目工作台</h1>} />
  </Routes></MemoryRouter></QueryClientProvider>);
}

function procurementSnapshot(overrides: Partial<BusinessWorkSnapshot> = {}): BusinessWorkSnapshot {
  return snapshot({
    workKey: "procurement-supplier-risk",
    name: "招采一致性与供应商风控智能体",
    shortName: "招采与供应商风控",
    status: "runnable",
    statusLabel: "可运行",
    packName: "procurement-supplier-risk",
    packVersion: "1.0.4",
    enabled: true,
    workItemType: "procurement-supplier-risk-case",
    documentRequirements: [
      { category: "TENDER_DOCUMENT", required: true },
      { category: "WINNING_BID", required: true },
      { category: "AWARD_NOTICE", required: true },
      { category: "MASTER_CONTRACT", required: true },
      { category: "SUPPLIER_PERFORMANCE", required: false },
    ],
    boundStrategyVersionId: "strategy-version-1",
    boundStrategyName: "供应商风险评估策略",
    boundStrategyVersion: 5,
    ...overrides,
  });
}

function procurementDocument(category: string, name = `${category}.pdf`, status: "AVAILABLE" | "PROCESSING" | "FAILED" = "AVAILABLE"): DocumentSnapshot {
  return {
    documentId: `${category.toLowerCase()}-1`,
    name,
    category,
    tags: [],
    status,
    currentVersion: 1,
    updatedAt: "2026-07-30T10:21:00Z",
    current: null,
    businessObjectIds: [],
    businessWorkKeys: ["procurement-supplier-risk"],
    versions: [],
  };
}

function runnableSnapshot(workKey: string, overrides: Partial<BusinessWorkSnapshot> = {}): BusinessWorkSnapshot {
  return snapshot({
    workKey,
    status: "runnable",
    statusLabel: "可运行",
    packName: `${workKey}-pack`,
    enabled: true,
    boundStrategyVersionId: "strategy-version-1",
    boundStrategyName: `${workKey} 执行策略`,
    boundStrategyVersion: 1,
    ...overrides,
  });
}

function businessDocument(workKey: string, category: string, name = `${category}.pdf`, status: DocumentSnapshot["status"] = "AVAILABLE"): DocumentSnapshot {
  return {
    documentId: `${workKey}-${category.toLowerCase()}-1`,
    name,
    category,
    tags: [],
    status,
    currentVersion: 1,
    updatedAt: "2026-07-30T10:21:00Z",
    current: null,
    businessObjectIds: [],
    businessWorkKeys: [workKey],
    versions: [],
  };
}

describe("business works page", () => {
  beforeEach(() => {
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
    vi.mocked(api.listRunSummaries).mockResolvedValue({ total: 0, items: [] });
  });
  afterEach(() => { cleanup(); vi.clearAllMocks(); });

  it.each(BUSINESS_WORKS.filter((definition) => definition.key !== "procurement-supplier-risk"))(
    "renders the shared reference layout for $key",
    async (definition) => {
      const requirements = definition.key === "swarm-calibration"
        ? []
        : [{ category: "WORK_INPUT", displayName: "业务输入资料", description: "用于本次业务处理的输入资料。", required: true, minCount: 1 }];
      vi.mocked(api.getBusinessWork).mockResolvedValue(runnableSnapshot(definition.key, { documentRequirements: requirements }));
      vi.mocked(api.listDocuments).mockResolvedValue({
        items: requirements.length ? [businessDocument(definition.key, "WORK_INPUT", "业务输入资料.pdf")] : [],
      });

      renderPage(`/business-works/${definition.key}`);

      expect(await screen.findByRole("heading", { name: definition.name })).toBeVisible();
      expect(screen.getByTestId("business-work-page-header")).toBeVisible();
      expect(screen.getByLabelText("运行准备完成度")).toHaveAttribute("aria-valuenow", requirements.length ? "2" : "1");
      expect(screen.getByRole("region", { name: "运行准备" })).toBeVisible();
      expect(screen.getByRole("region", { name: "业务能力" })).toBeVisible();
      expect(screen.getByRole("heading", { name: "最近运行" })).toBeVisible();
      expect(screen.getByRole("button", { name: "开始处理" })).toBeVisible();
      expect(screen.getByRole("link", { name: "运行配置" })).toHaveAttribute(
        "href",
        `/business-works/${definition.key}/settings`,
      );
      if (requirements.length) {
        expect(screen.getByRole("heading", { name: /业务输入资料/ })).toBeVisible();
        expect(screen.getByText("用于本次业务处理的输入资料。")).toBeVisible();
      }
    },
  );

  it("keeps the report-generation demo beside the shared actions", async () => {
    vi.mocked(api.getBusinessWork).mockResolvedValue(runnableSnapshot("report-generation", { documentRequirements: [] }));

    renderPage("/business-works/report-generation");

    expect(await screen.findByRole("button", { name: "开始处理" })).toBeVisible();
    expect(screen.getByRole("link", { name: "体验公开数据 Demo" })).toHaveAttribute(
      "href",
      "/business-works/report-generation/demo",
    );
  });

  it("shows generic document counts and blocks until minCount is met", async () => {
    vi.mocked(api.getBusinessWork).mockResolvedValue(runnableSnapshot("document-integrity", {
      documentRequirements: [{ category: "MASTER_CONTRACT", displayName: "主合同", description: "需要两份主合同资料。", required: true, minCount: 2 }],
    }));
    vi.mocked(api.listDocuments).mockResolvedValue({
      items: [businessDocument("document-integrity", "MASTER_CONTRACT", "主合同-1.pdf")],
    });

    renderPage("/business-works/document-integrity");

    expect(await screen.findByRole("button", { name: "补齐业务资料" })).toBeVisible();
    expect(screen.getByText("已提供 1/2 份资料")).toBeVisible();
    expect(screen.getByText("需要两份主合同资料。")).toBeVisible();
    expect(screen.getByRole("heading", { name: /主合同/ })).toBeVisible();
  });

  it("shows the planned and unconfigured states in the same header", async () => {
    vi.mocked(api.getBusinessWork).mockResolvedValue(snapshot({
      workKey: "document-structuring",
      status: "planned",
      statusLabel: "规划中",
      enabled: false,
    }));
    renderPage("/business-works/document-structuring");
    expect(await screen.findByRole("button", { name: "规划中" })).toBeDisabled();
    expect(screen.queryByRole("link", { name: "运行配置" })).not.toBeInTheDocument();

    vi.mocked(api.getBusinessWork).mockResolvedValue(snapshot({
      workKey: "invoice-assurance",
      status: "not_configured",
      statusLabel: "未配置",
      packName: "invoice-assurance",
      enabled: false,
    }));
    renderPage("/business-works/invoice-assurance");
    expect(await screen.findByRole("button", { name: "配置运行条件" })).toBeVisible();
    expect(screen.getAllByText("尚未绑定执行策略").length).toBeGreaterThan(0);
    expect(screen.getByRole("link", { name: "运行配置" })).toHaveAttribute(
      "href",
      "/business-works/invoice-assurance/settings",
    );
  });

  it("keeps dependency blockers inside the strategy readiness row", async () => {
    vi.mocked(api.getBusinessWork).mockResolvedValue(runnableSnapshot("ai-foundation-quality", {
      status: "unavailable",
      statusLabel: "暂不可用",
      blockers: [{ code: "DEPENDENCY_NOT_READY", message: "依赖未就绪", ref: "agent://contract/report-quality-reviewer@1" }],
    }));

    renderPage("/business-works/ai-foundation-quality");

    expect(await screen.findByRole("button", { name: "处理配置异常" })).toBeVisible();
    expect(screen.getByText("报告质量复核智能体")).toBeVisible();
    expect(screen.getByRole("region", { name: "运行准备" })).toBeVisible();
  });

  it("filters recent runs by the current strategy and uses the current work key for reruns", async () => {
    vi.mocked(api.getBusinessWork).mockResolvedValue(runnableSnapshot("document-integrity", { documentRequirements: [] }));
    vi.mocked(api.listRunSummaries).mockResolvedValue({
      total: 2,
      items: [
        {
          runId: "run-matched",
          status: "SUCCEEDED",
          strategyVersionId: "strategy-version-1",
          snapshotSeq: 3,
          taskCount: 2,
          operatorName: "当前用户",
          createdAt: "2026-07-30T10:00:00Z",
          startedAt: "2026-07-30T10:00:01Z",
          completedAt: "2026-07-30T10:01:00Z",
          failureReason: null,
          cancelReason: null,
        },
        {
          runId: "run-failed",
          status: "FAILED",
          strategyVersionId: "strategy-version-1",
          snapshotSeq: 2,
          taskCount: 1,
          operatorName: "当前用户",
          createdAt: "2026-07-29T10:00:00Z",
          startedAt: "2026-07-29T10:00:01Z",
          completedAt: "2026-07-29T10:01:00Z",
          failureReason: "运行失败",
          cancelReason: null,
        },
      ],
    });

    renderPage("/business-works/document-integrity");

    expect(await screen.findByRole("heading", { name: "最近运行" })).toBeVisible();
    expect(screen.getByText("仅展示当前绑定策略「document-integrity 执行策略 · v1」的最近运行。")).toBeVisible();
    expect(screen.getAllByRole("link", { name: "查看报告" })[0]).toHaveAttribute("href", "/runs/run-matched");
    expect(screen.getAllByRole("link", { name: "重新运行" })[0]).toHaveAttribute(
      "href",
      "/business-works/document-integrity/workbench",
    );
  });

  it("keeps the shared sections visible when documents fail to load", async () => {
    vi.mocked(api.getBusinessWork).mockResolvedValue(runnableSnapshot("document-integrity", { documentRequirements: [] }));
    vi.mocked(api.listDocuments).mockRejectedValue(new Error("资料服务不可用"));

    renderPage("/business-works/document-integrity");

    expect(await screen.findByRole("alert")).toHaveTextContent("资料服务不可用");
    expect(screen.getByRole("region", { name: "业务能力" })).toBeVisible();
    expect(screen.getByRole("heading", { name: "最近运行" })).toBeVisible();
  });

  it("uses business-readable names for procurement readiness blockers", async () => {
    vi.mocked(api.getBusinessWork).mockResolvedValue(snapshot({
      workKey: "procurement-supplier-risk",
      name: "招采一致性与供应商风控智能体",
      status: "unavailable",
      statusLabel: "暂不可用",
      packName: "procurement-supplier-risk",
      enabled: true,
      blockers: [
        {
          code: "DEPENDENCY_NOT_READY",
          message: "agent://procurement/clause-evidence-analyst@3 尚未就绪",
          ref: "agent://procurement/clause-evidence-analyst@3",
        },
        {
          code: "DEPENDENCY_NOT_READY",
          message: "agent://supplier/risk-analyst@1 尚未就绪",
          ref: "agent://supplier/risk-analyst@1",
        },
        {
          code: "DEPENDENCY_NOT_READY",
          message: "agent://procurement/evidence-quality-reviewer@1 尚未就绪",
          ref: "agent://procurement/evidence-quality-reviewer@1",
        },
      ],
    }));

    renderPage("/business-works/procurement-supplier-risk");

    expect(await screen.findByText("招采条款证据分析智能体")).toBeVisible();
    expect(screen.getAllByText("该智能体当前未就绪")).toHaveLength(3);
    expect(screen.queryByText("agent://procurement/clause-evidence-analyst@3 尚未就绪"))
      .not.toBeInTheDocument();
  });

  it("labels tool and model dependency blockers distinctly", async () => {
    vi.mocked(api.getBusinessWork).mockResolvedValue(snapshot({
      workKey: "procurement-supplier-risk",
      name: "招采一致性与供应商风控智能体",
      status: "incomplete",
      statusLabel: "配置不完整",
      packName: "procurement-supplier-risk",
      enabled: true,
      blockers: [
        {
          code: "DEPENDENCY_NOT_READY",
          message: "tool://evidence/search@1 尚未就绪",
          ref: "tool://evidence/search@1",
        },
        {
          code: "HEALTH_CHECK_FAILED",
          message: "model://general@1：HEALTH_CHECK_FAILED",
          ref: "model://general@1",
        },
      ],
    }));

    renderPage("/business-works/procurement-supplier-risk");

    expect(await screen.findByText("该工具当前未就绪")).toBeVisible();
    expect(screen.getByText("依赖健康检查未通过")).toBeVisible();
  });

  it("shows Chinese category labels for procurement tender documents", async () => {
    vi.mocked(api.getBusinessWork).mockResolvedValue(snapshot({
      workKey: "procurement-supplier-risk",
      name: "招采一致性与供应商风险",
      shortName: "招采风险",
      status: "runnable",
      statusLabel: "可运行",
      packName: "procurement-supplier-risk",
      packVersion: "1.0.4",
      enabled: true,
      workItemType: "procurement-supplier-risk-case",
      documentRequirements: [{ category: "TENDER_DOCUMENT", required: true }],
      boundStrategyVersionId: "strategy-version-1",
      boundStrategyName: "招采风险策略",
      boundStrategyVersion: 1,
    }));
    vi.mocked(api.listDocuments).mockResolvedValue({
      items: [{
        documentId: "tender-1",
        name: "招案2026-1952公开招标文件文本提取",
        category: "TENDER_DOCUMENT",
        tags: [],
        status: "AVAILABLE",
        currentVersion: 1,
        updatedAt: "2026-07-23T00:00:00Z",
        current: null,
        businessObjectIds: [],
        businessWorkKeys: ["procurement-supplier-risk"],
        versions: [],
      }],
    });

    renderPage("/business-works/procurement-supplier-risk");
    const summary = within(await screen.findByRole("region", { name: "运行准备" }));
    expect(summary.getByRole("heading", { name: /招标文件/ })).toBeVisible();
    expect(summary.queryByText("TENDER_DOCUMENT")).not.toBeInTheDocument();
    expect(summary.getByRole("link", { name: "招案2026-1952公开招标文件文本提取" })).toHaveAttribute("href", "/documents/tender-1");
  });

  it("shows preparing state and focuses the first missing procurement item", async () => {
    vi.mocked(api.getBusinessWork).mockResolvedValue(procurementSnapshot());
    vi.mocked(api.listDocuments).mockResolvedValue({
      items: [
        procurementDocument("TENDER_DOCUMENT", "招采2026-1952项目招标公告"),
        procurementDocument("WINNING_BID", "招采2026-1952中标结果公告"),
        procurementDocument("AWARD_NOTICE", "招采2026-1952成交通知书"),
        procurementDocument("SUPPLIER_PERFORMANCE", "供应商履约资料.zip"),
      ],
    });

    renderPage("/business-works/procurement-supplier-risk");

    expect(await screen.findByRole("button", { name: "补齐业务资料" })).toBeVisible();
    expect(screen.getByText((_, node) => node?.tagName === "P" && /运行准备 4\/5 项完成/.test(node.textContent ?? ""))).toBeVisible();
    expect(screen.getByRole("heading", { name: /4\. 签章合同/ })).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "补齐业务资料" }));
    await waitFor(() => expect(document.activeElement).toHaveTextContent("签章合同"));
  });

  it("shows ready state and confirms before entering procurement processing", async () => {
    vi.mocked(api.getBusinessWork).mockResolvedValue(procurementSnapshot());
    vi.mocked(api.listDocuments).mockResolvedValue({
      items: [
        procurementDocument("TENDER_DOCUMENT"),
        procurementDocument("WINNING_BID"),
        procurementDocument("AWARD_NOTICE"),
        procurementDocument("MASTER_CONTRACT", "招采2026-1952签章合同.pdf"),
      ],
    });

    renderPage("/business-works/procurement-supplier-risk");

    const start = await screen.findByRole("button", { name: "开始处理" });
    expect(screen.getAllByText("可运行").length).toBeGreaterThan(0);
    fireEvent.click(start);
    expect(await screen.findByRole("heading", { name: "确认开始处理" })).toBeVisible();
    expect(screen.getAllByText("供应商风险评估策略 · v5").length).toBeGreaterThan(0);
    expect(screen.getByRole("link", { name: "进入办理" })).toHaveAttribute(
      "href",
      "/business-works/procurement-supplier-risk/workbench",
    );
  });

  it("shows running state and prevents duplicate processing", async () => {
    vi.mocked(api.getBusinessWork).mockResolvedValue(procurementSnapshot());
    vi.mocked(api.listDocuments).mockResolvedValue({
      items: [
        procurementDocument("TENDER_DOCUMENT"),
        procurementDocument("WINNING_BID"),
        procurementDocument("AWARD_NOTICE"),
        procurementDocument("MASTER_CONTRACT"),
      ],
    });
    const runningRun: RunSummarySnapshot = {
      runId: "procurement-running",
      status: "RUNNING",
      snapshotSeq: 8,
      strategyVersionId: "strategy-version-1",
      taskCount: 1,
      operatorName: "当前用户",
      createdAt: "2026-07-30T14:32:00Z",
      startedAt: "2026-07-30T14:32:00Z",
      completedAt: null,
      failureReason: null,
      cancelReason: null,
    };
    vi.mocked(api.listRunSummaries).mockResolvedValue({ total: 1, items: [runningRun] });

    renderPage("/business-works/procurement-supplier-risk");

    expect(await screen.findByRole("button", { name: "查看运行进度" })).toBeVisible();
    expect(screen.queryByRole("button", { name: "开始处理" })).not.toBeInTheDocument();
    expect(screen.getAllByRole("link", { name: "查看进度" })[0]).toHaveAttribute("href", "/runs/procurement-running");
  });

  it("shows configuration error when a procurement file fails validation", async () => {
    vi.mocked(api.getBusinessWork).mockResolvedValue(procurementSnapshot());
    vi.mocked(api.listDocuments).mockResolvedValue({
      items: [
        procurementDocument("TENDER_DOCUMENT"),
        procurementDocument("WINNING_BID"),
        procurementDocument("AWARD_NOTICE"),
        procurementDocument("MASTER_CONTRACT", "签章合同.pdf", "FAILED"),
      ],
    });

    renderPage("/business-works/procurement-supplier-risk");

    expect(await screen.findByRole("button", { name: "处理配置异常" })).toBeVisible();
    expect(screen.getByText("文件解析异常，请重新上传")).toBeVisible();
    expect(screen.getByText("校验失败")).toBeVisible();
  });

  it("keeps the empty recent runs state lightweight", async () => {
    vi.mocked(api.getBusinessWork).mockResolvedValue(procurementSnapshot());
    vi.mocked(api.listDocuments).mockResolvedValue({
      items: [
        procurementDocument("TENDER_DOCUMENT"),
        procurementDocument("WINNING_BID"),
        procurementDocument("AWARD_NOTICE"),
        procurementDocument("MASTER_CONTRACT"),
      ],
    });
    vi.mocked(api.listRunSummaries).mockResolvedValue({ total: 0, items: [] });

    renderPage("/business-works/procurement-supplier-risk");

    expect(await screen.findByRole("heading", { name: "最近运行" })).toBeVisible();
    expect(screen.getByText("暂无运行记录")).toBeVisible();
    expect(screen.queryByRole("columnheader")).not.toBeInTheDocument();
  });

  it("keeps other sections available when business documents fail to load", async () => {
    vi.mocked(api.getBusinessWork).mockResolvedValue(procurementSnapshot());
    vi.mocked(api.listDocuments).mockRejectedValue(new Error("资料服务不可用"));

    renderPage("/business-works/procurement-supplier-risk");

    expect(await screen.findByRole("alert")).toHaveTextContent("资料服务不可用");
    expect(screen.getByRole("heading", { name: "业务能力" })).toBeVisible();
    expect(screen.getByRole("heading", { name: "最近运行" })).toBeVisible();
  });

  it("shows linked files in the shared readiness card when no requirements are declared", async () => {
    vi.mocked(api.getBusinessWork).mockResolvedValue(runnableSnapshot("contract-post-evaluation", { documentRequirements: [] }));
    vi.mocked(api.listDocuments).mockResolvedValue({
      items: [businessDocument("contract-post-evaluation", "PERFORMANCE", "验收资料.pdf")],
    });

    renderPage("/business-works/contract-post-evaluation");

    expect(await screen.findByRole("heading", { name: /已关联资料/ })).toBeVisible();
    expect(screen.getByRole("link", { name: "验收资料.pdf" })).toHaveAttribute(
      "href",
      "/documents/contract-post-evaluation-performance-1",
    );
    expect(screen.getByRole("button", { name: "开始处理" })).toBeVisible();
  });

  it("keeps empty run history scoped to the current strategy", async () => {
    vi.mocked(api.getBusinessWork).mockResolvedValue(runnableSnapshot("document-integrity", { documentRequirements: [] }));
    vi.mocked(api.listRunSummaries).mockResolvedValue({
      total: 0,
      items: [],
    });

    renderPage("/business-works/document-integrity");

    expect(await screen.findByText("暂无运行记录")).toBeVisible();
    expect(screen.getByText(/当前绑定「document-integrity 执行策略 · v1」尚无运行/)).toBeVisible();
    expect(screen.getByRole("link", { name: "查看全部" })).toHaveAttribute("href", "/runs");
  });

  it("does not show runs when the work is only a local planned fallback", async () => {
    vi.mocked(api.getBusinessWork).mockResolvedValue(snapshot({
      workKey: "document-integrity",
      status: "planned",
      statusLabel: "规划中",
      enabled: false,
    }));

    renderPage("/business-works/document-integrity");

    expect(await screen.findByRole("button", { name: "规划中" })).toBeDisabled();
    expect(api.listRunSummaries).not.toHaveBeenCalled();
  });

});
