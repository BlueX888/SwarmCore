import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { api } from "@/api/client";
import type { BusinessWorkSnapshot, CapabilityPackSnapshot, EvaluationSnapshot } from "@/api/types";
import { BusinessWorkWorkbenchPage } from "./business-work-workbench-page";

vi.mock("@/api/client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/api/client")>();
  return {
    ...actual,
    api: {
      ...actual.api,
      getBusinessWork: vi.fn(),
      listCapabilityPacks: vi.fn(),
      createWorkItem: vi.fn(),
      executeWorkItem: vi.fn(),
      createBusinessObject: vi.fn(),
      createCase: vi.fn(),
      assessCase: vi.fn(),
      createSupplierRiskMonitor: vi.fn(),
      refreshSupplierRiskMonitor: vi.fn(),
      getInvoiceAssuranceRuleTrends: vi.fn(),
      listWorkDocumentRequirements: vi.fn(),
      createUploadBatch: vi.fn(),
      initiateDocument: vi.fn(),
      uploadDocumentContent: vi.fn(),
      completeDocument: vi.fn(),
      getUploadBatch: vi.fn(),
    },
  };
});

const evaluation: EvaluationSnapshot = {
  evaluationId: "evaluation-1", workItemId: "item-1", workItemRevisionId: "revision-1", runId: "run-1",
  status: "RUNNING", result: null, capabilityPackVersionId: "version-1", planHash: "a".repeat(64), attachmentManifestHash: "b".repeat(64), createdAt: "2026-07-22T00:00:00Z",
};

function runnableWork(overrides: Partial<BusinessWorkSnapshot> = {}): BusinessWorkSnapshot {
  return {
    workKey: "document-integrity",
    name: "文件完整性校验智能体",
    shortName: "文件完整性校验",
    category: "business",
    summary: "完整性校验",
    status: "runnable",
    statusLabel: "可运行",
    packName: "contract-integrity",
    packVersionId: "version-1",
    packVersion: "1.2.0",
    enabled: true,
    bindingStatus: "ENABLED",
    blockers: [],
    agents: [],
    tools: [],
    models: [],
    documentRequirements: [],
    decisionSlots: [],
    functions: [],
    configuration: {},
    workItemType: "contract-case",
    caseBased: false,
    ...overrides,
    boundStrategyVersionId: overrides.boundStrategyVersionId ?? null,
    boundStrategyName: overrides.boundStrategyName ?? null,
    boundStrategyVersion: overrides.boundStrategyVersion ?? null,
  };
}

function v1Pack(): CapabilityPackSnapshot {
  return {
    packId: "pack-1", name: "contract-integrity", versionId: "version-1", version: "1.2.0", contentHash: "a".repeat(64),
    manifest: { spec: { workItemType: "contract-case" } }, enabled: true, bindingStatus: "ENABLED", configuration: {}, blockers: [],
  };
}

function renderPage(workKey = "document-integrity") {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}><MemoryRouter initialEntries={[`/business-works/${workKey}/workbench`]}><Routes>
    <Route path="/business-works/:workKey/workbench" element={<BusinessWorkWorkbenchPage />} />
    <Route path="/assessments/:assessmentId" element={<h1>评估结果</h1>} />
  </Routes></MemoryRouter></QueryClientProvider>);
}

describe("business work workbench", () => {
  beforeEach(() => {
    vi.mocked(api.getBusinessWork).mockResolvedValue(runnableWork());
    vi.mocked(api.listCapabilityPacks).mockResolvedValue({ items: [v1Pack()] });
    vi.mocked(api.createWorkItem).mockResolvedValue({ workItemId: "item-1", workItemType: "contract-case", status: "DRAFT", revisionId: "revision-1", revision: 1 } as never);
    vi.mocked(api.executeWorkItem).mockResolvedValue(evaluation);
    vi.mocked(api.createBusinessObject).mockResolvedValue({ businessObjectId: "object-1", versionId: "object-version-1", objectType: "contract", canonicalKey: "HT-2026-001", currentVersion: 1, schemaRef: "schema://contract/facts@1", data: {} });
    vi.mocked(api.createCase).mockResolvedValue({ caseId: "case-1", scenarioType: "contract-post-evaluation-case", caseRevisionId: "case-revision-1", revision: 1, payload: {}, status: "DRAFT", owner: null, subjects: [], createdAt: "2026-07-22T00:00:00Z", updatedAt: "2026-07-22T00:00:00Z" });
    vi.mocked(api.assessCase).mockResolvedValue(evaluation);
    vi.mocked(api.createSupplierRiskMonitor).mockResolvedValue({
      monitorId: "monitor-1",
      caseId: "case-1",
      supplierName: "上海龙田数码科技有限公司",
      supplierCreditCode: "91310116740594799B",
      status: "ACTIVE",
      cadence: "DAILY",
      sources: [],
      nextCheckAt: null,
      lastCheckedAt: null,
      lastSnapshotId: null,
      createdAt: "2026-07-28T00:00:00Z",
      updatedAt: "2026-07-28T00:00:00Z",
    });
    vi.mocked(api.refreshSupplierRiskMonitor).mockResolvedValue(evaluation);
    vi.mocked(api.getInvoiceAssuranceRuleTrends).mockResolvedValue({
      bucket: "day",
      totalAssessments: 2,
      outcomes: { PAYMENT_BLOCKED: 1, REVIEW_REQUIRED: 1 },
      buckets: [],
      topRules: [{ ruleId: "PARTY_ENTERPRISE_PUBLIC_STATUS", status: "WARN", count: 2 }],
    });
    vi.mocked(api.listWorkDocumentRequirements).mockResolvedValue({
      processingProfileRef: null,
      items: [],
    });
    vi.mocked(api.createUploadBatch).mockRejectedValue(new Error("batch tracking unavailable"));
  });
  afterEach(() => { cleanup(); vi.clearAllMocks(); });

  it("renders a workbench hero with status and actions", async () => {
    renderPage();
    expect(await screen.findByRole("heading", { name: "文件完整性校验智能体" })).toBeVisible();
    expect(screen.getByTestId("business-work-page-header")).toBeVisible();
    expect(screen.getByText("工作台")).toBeVisible();
    expect(screen.getByRole("link", { name: "返回业务工作" })).toHaveAttribute("href", "/business-works/document-integrity");
    expect(screen.getByRole("link", { name: "业务资料" })).toHaveAttribute("href", "/documents");
    expect(screen.getByRole("link", { name: "项目配置" })).toHaveAttribute("href", "/business-works/document-integrity/settings");
    expect(screen.getByText("运行资格")).toBeVisible();
    expect(screen.getByText("执行策略")).toBeVisible();
  });

  it("runs the v1 work item flow and opens the assessment page", async () => {
    renderPage();
    expect(await screen.findByRole("heading", { name: "文件完整性校验智能体" })).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "开始办理" }));
    await waitFor(() => expect(api.createWorkItem).toHaveBeenCalled());
    expect(api.executeWorkItem).toHaveBeenCalledWith(expect.any(String), expect.any(String), "item-1");
    expect(await screen.findByRole("heading", { name: "评估结果" })).toBeVisible();
  });

  it("runs the v2 case assessment flow", async () => {
    vi.mocked(api.getBusinessWork).mockResolvedValue(runnableWork({
      workKey: "contract-post-evaluation",
      name: "合同后评价",
      packName: "contract-post-evaluation",
      workItemType: "contract-post-evaluation-case",
      caseBased: true,
    }));
    vi.mocked(api.listCapabilityPacks).mockResolvedValue({
      items: [{
        ...v1Pack(),
        name: "contract-post-evaluation",
        manifest: { spec: { case: { type: "contract-post-evaluation-case", subjectRoles: [{ key: "contract", objectType: "contract", role: "PRIMARY", min: 1, max: 1 }] } } },
      }],
    });
    renderPage("contract-post-evaluation");
    expect(await screen.findByRole("heading", { name: "合同后评价" })).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "开始办理" }));
    await waitFor(() => expect(api.assessCase).toHaveBeenCalledWith(expect.any(String), expect.any(String), "case-1"));
    expect(await screen.findByRole("heading", { name: "评估结果" })).toBeVisible();
  });

  it("submits the contract-performance collect operation with sources and a published plan", async () => {
    vi.mocked(api.getBusinessWork).mockResolvedValue(runnableWork({
      workKey: "performance-plan-collection",
      name: "履约计划与执行采集智能体",
      packName: "contract-performance",
      workItemType: "contract-performance-case",
      caseBased: true,
    }));
    vi.mocked(api.listCapabilityPacks).mockResolvedValue({
      items: [{
        ...v1Pack(),
        name: "contract-performance",
        version: "1.0.9",
        manifest: {
          spec: {
            case: {
              type: "contract-performance-case",
              subjectRoles: [
                {
                  key: "contract",
                  objectType: "contract",
                  role: "PRIMARY",
                  min: 1,
                  max: 1,
                },
              ],
            },
          },
        },
      }],
    });
    renderPage("performance-plan-collection");

    expect(await screen.findByLabelText("办理类型")).toHaveValue("INITIALIZE");
    fireEvent.change(screen.getByLabelText("办理类型"), {
      target: { value: "COLLECT" },
    });
    fireEvent.change(screen.getByLabelText("履约采集源"), {
      target: {
        value: JSON.stringify([
          {
            kind: "PUBLIC_DFE_SPEND_CSV",
            sourceRef: "public://dfe/spend/2024-09",
            url: "https://assets.publishing.service.gov.uk/example.csv",
          },
        ]),
      },
    });
    fireEvent.change(screen.getByLabelText("已发布履约计划"), {
      target: {
        value: JSON.stringify({
          schemaVersion: "schema://contract-performance/plan@1",
          contract: { contractId: "ESFA-25001" },
          obligations: [],
          milestones: [],
        }),
      },
    });
    fireEvent.click(screen.getByRole("button", { name: "开始办理" }));

    await waitFor(() => expect(api.createCase).toHaveBeenCalled());
    const request = vi.mocked(api.createCase).mock.calls[0]?.[2];
    const payload = request?.payload;
    expect(payload).toMatchObject({
      operation: "COLLECT",
      currency: "CNY",
      timezone: "Asia/Shanghai",
      contractObjectId: "object-1",
    });
    const sources = Array.isArray(payload?.sources) ? payload.sources : [];
    expect(sources[0]).toMatchObject({
      kind: "PUBLIC_DFE_SPEND_CSV",
      sourceRef: "public://dfe/spend/2024-09",
    });
    const plan = payload?.plan;
    expect(plan && typeof plan === "object" ? plan : {}).toMatchObject({
      schemaVersion: "schema://contract-performance/plan@1",
    });
    expect(api.assessCase).toHaveBeenCalledWith(
      expect.any(String),
      expect.any(String),
      "case-1",
    );
  });

  it("creates a supplier monitor and refreshes it through the shared case flow", async () => {
    vi.mocked(api.getBusinessWork).mockResolvedValue(runnableWork({
      workKey: "procurement-supplier-risk",
      name: "招采一致性与供应商风控",
      packName: "procurement-supplier-risk",
      workItemType: "procurement-supplier-risk-case",
      caseBased: true,
    }));
    vi.mocked(api.listCapabilityPacks).mockResolvedValue({
      items: [{
        ...v1Pack(),
        name: "procurement-supplier-risk",
        manifest: {
          spec: {
            case: {
              type: "procurement-supplier-risk-case",
              subjectRoles: [
                {
                  key: "procurement",
                  objectType: "procurement",
                  role: "PRIMARY",
                  min: 1,
                  max: 1,
                },
                {
                  key: "supplier",
                  objectType: "supplier",
                  role: "RELATED",
                  min: 1,
                  max: 20,
                },
              ],
            },
          },
        },
      }],
    });
    renderPage("procurement-supplier-risk");

    fireEvent.change(await screen.findByLabelText("供应商名称"), {
      target: { value: "上海龙田数码科技有限公司" },
    });
    fireEvent.change(screen.getByLabelText("统一社会信用代码"), {
      target: { value: "91310116740594799b" },
    });
    fireEvent.click(screen.getByRole("button", { name: "开始办理" }));

    await waitFor(() =>
      expect(api.createSupplierRiskMonitor).toHaveBeenCalledWith(
        expect.any(String),
        expect.any(String),
        expect.objectContaining({
          caseId: "case-1",
          supplierName: "上海龙田数码科技有限公司",
          supplierCreditCode: "91310116740594799B",
          cadence: "DAILY",
        }),
      ),
    );
    expect(api.refreshSupplierRiskMonitor).toHaveBeenCalledWith(
      expect.any(String),
      expect.any(String),
      "monitor-1",
    );
    expect(api.assessCase).not.toHaveBeenCalled();
    expect(await screen.findByRole("heading", { name: "评估结果" })).toBeVisible();
  });

  it("blocks planned works from starting", async () => {
    vi.mocked(api.getBusinessWork).mockResolvedValue(runnableWork({ status: "planned", statusLabel: "规划中", packName: null }));
    renderPage("invoice-assurance");
    expect(await screen.findByRole("heading", { name: "该业务工作仍在规划中" })).toBeVisible();
    expect(screen.queryByRole("button", { name: "开始办理" })).not.toBeInTheDocument();
  });

  it("submits scheduling-calibration evidence and sandbox inputs", async () => {
    vi.mocked(api.getBusinessWork).mockResolvedValue(runnableWork({
      workKey: "swarm-calibration",
      name: "智能体调度校准智能体",
      packName: "swarm-calibration",
      workItemType: "swarm-calibration-case",
      caseBased: true,
    }));
    vi.mocked(api.listCapabilityPacks).mockResolvedValue({
      items: [{
        ...v1Pack(),
        name: "swarm-calibration",
        manifest: {
          spec: {
            case: {
              type: "swarm-calibration-case",
              subjectsRequired: false,
              subjectRoles: [],
            },
          },
        },
      }],
    });

    renderPage("swarm-calibration");

    expect(await screen.findByLabelText("真实 GitHub Issue URL")).toHaveValue(
      "https://github.com/temporalio/sdk-python/issues/782",
    );
    expect(screen.getByLabelText("本次校准目标")).toHaveValue(
      "基于真实 Issue、讨论和合并代码，校验任务调度、主备切换与结论质量。",
    );
    fireEvent.click(screen.getByRole("button", { name: "开始办理" }));
    await waitFor(() => expect(api.createWorkItem).toHaveBeenCalled());
    const request = vi.mocked(api.createWorkItem).mock.calls[0]?.[2];
    expect(request?.workItemType).toBe("swarm-calibration-case");
    expect(request?.payload.issueUrl).toBe(
      "https://github.com/temporalio/sdk-python/issues/782",
    );
    expect(request?.payload.acceptanceCriteria).toContain(
      "所有关键结论都引用冻结证据",
    );
    expect(request?.payload.sandbox).toEqual({
      enabled: true,
      testCommand: ["python", "-m", "pytest", "-q"],
    });
  });

  it("shows historical invoice rule trends", async () => {
    vi.mocked(api.getBusinessWork).mockResolvedValue(runnableWork({
      workKey: "invoice-assurance",
      name: "发票一致性校验智能体",
      packName: "invoice-assurance",
      workItemType: "invoice-assurance-case",
      caseBased: true,
    }));
    vi.mocked(api.listCapabilityPacks).mockResolvedValue({
      items: [{
        ...v1Pack(),
        name: "invoice-assurance",
        manifest: { spec: { case: { type: "invoice-assurance-case", subjectRoles: [] } } },
      }],
    });

    renderPage("invoice-assurance");

    expect(await screen.findByRole("heading", { name: "规则命中趋势" })).toBeVisible();
    expect(await screen.findByText("PARTY_ENTERPRISE_PUBLIC_STATUS")).toBeVisible();
    expect(screen.getByText("2 次")).toBeVisible();
  });

  it("disables start when readiness blockers exist", async () => {
    vi.mocked(api.getBusinessWork).mockResolvedValue(runnableWork({
      status: "incomplete",
      statusLabel: "配置不完整",
      blockers: [{ code: "DOCUMENT_BINDING_MISSING", message: "资料分类 CONTRACT 尚未绑定到本业务工作。", ref: "CONTRACT" }],
    }));
    renderPage();
    expect(await screen.findByText("运行前还需准备资料或配置")).toBeVisible();
    expect(screen.getByRole("button", { name: "开始办理" })).toBeDisabled();
  });

  it("uses the selected document profile and refreshes readiness after upload", async () => {
    const apiRequirement = {
      key: "source-document",
      displayName: "待结构化原始文档",
      description: "待结构化原始文档",
      required: true,
      minCount: 1,
      maxCount: null,
      acceptedMediaTypes: ["application/vnd.oasis.opendocument.text"],
      classificationLabels: ["CONTRACT"],
      processingProfileRef: "document-profile://business-structuring@1",
      extractionSchemaRef: "schema://document/contract-structure@1",
      category: "SOURCE_DOCUMENT",
      satisfiedCount: 0,
      satisfied: false,
    };
    const incomplete = runnableWork({
      workKey: "document-structuring",
      name: "文档结构化",
      status: "incomplete",
      statusLabel: "资料待补充",
      blockers: [{ code: "DOCUMENT_BINDING_MISSING", message: "SOURCE_DOCUMENT 0 / 1", ref: "SOURCE_DOCUMENT" }],
      documentRequirements: [{
        key: "source-document",
        displayName: "待结构化原始文档",
        required: true,
        minCount: 1,
        maxCount: null,
        acceptedMediaTypes: ["application/vnd.oasis.opendocument.text"],
        classificationLabels: ["CONTRACT"],
        processingProfile: "document-profile://business-structuring@1",
        extractionSchema: "schema://document/contract-structure@1",
        category: "SOURCE_DOCUMENT",
      }],
    });
    vi.mocked(api.getBusinessWork)
      .mockResolvedValueOnce(incomplete)
      .mockResolvedValue(runnableWork({
        workKey: "document-structuring",
        name: "文档结构化",
        statusLabel: "可运行",
      }));
    vi.mocked(api.listWorkDocumentRequirements).mockResolvedValue({
      processingProfileRef: "document-profile://business-default@1",
      items: [apiRequirement],
    });
    vi.mocked(api.initiateDocument).mockResolvedValue({
      documentId: "document-1",
      uploadId: "upload-1",
      version: 1,
      blobId: "blob-1",
      uploadRef: "/internal/v1/blobs/blob-1",
      capabilityToken: "token",
      status: "UPLOADING",
    });
    vi.mocked(api.uploadDocumentContent).mockResolvedValue(undefined);
    vi.mocked(api.completeDocument).mockResolvedValue({
      documentId: "document-1",
      name: "contract.odt",
      category: "SOURCE_DOCUMENT",
      tags: [],
      status: "AVAILABLE",
      currentVersion: 1,
      updatedAt: "2026-07-30T00:00:00Z",
      current: null,
      businessObjectIds: [],
      businessWorkKeys: ["document-structuring"],
      versions: [],
    });

    renderPage("document-structuring");
    expect(await screen.findByText("SOURCE_DOCUMENT 0 / 1")).toBeVisible();
    expect(screen.getByRole("button", { name: "开始办理" })).toBeDisabled();
    fireEvent.click(screen.getByRole("button", { name: "上下文上传" }));

    const input = screen.getByLabelText<HTMLInputElement>("选择业务资料文件");
    const file = new File([Uint8Array.from([111, 100, 116])], "contract.odt", {
      type: "application/vnd.oasis.opendocument.text",
    });
    Object.defineProperty(file, "arrayBuffer", {
      configurable: true,
      value: () => Promise.resolve(Uint8Array.from([111, 100, 116]).buffer),
    });
    Object.defineProperty(input, "files", {
      configurable: true,
      value: {
        0: file,
        length: 1,
        item: (index: number) => (index === 0 ? file : null),
        [Symbol.iterator]: function* () {
          yield file;
        },
      },
    });
    fireEvent.change(input);
    fireEvent.click(screen.getByRole("button", { name: /开始上传/ }));

    await waitFor(() => expect(api.completeDocument).toHaveBeenCalledWith(
      expect.any(String),
      expect.any(String),
      "upload-1",
      expect.any(String),
      expect.objectContaining({
        profileRef: "document-profile://business-structuring@1",
        extractionSchemaRef: "schema://document/contract-structure@1",
      }),
    ));
    await waitFor(() => expect(api.getBusinessWork).toHaveBeenCalledTimes(2));
    expect(screen.getByRole("button", { name: "开始办理" })).toBeEnabled();
  });

  it("shows a clear message when document selection is required", async () => {
    const { ApiError } = await import("@/api/client");
    vi.mocked(api.assessCase).mockRejectedValue(
      new ApiError(422, "请先提供并绑定所需业务资料后再开始办理。", "DOCUMENT_SELECTION_REQUIRED"),
    );
    vi.mocked(api.getBusinessWork).mockResolvedValue(runnableWork({
      workKey: "contract-post-evaluation",
      name: "合同后评价",
      packName: "contract-post-evaluation",
      workItemType: "contract-post-evaluation-case",
      caseBased: true,
    }));
    vi.mocked(api.listCapabilityPacks).mockResolvedValue({
      items: [{
        ...v1Pack(),
        name: "contract-post-evaluation",
        manifest: { spec: { case: { type: "contract-post-evaluation-case", subjectRoles: [{ key: "contract", objectType: "contract", role: "PRIMARY", min: 1, max: 1 }] } } },
      }],
    });
    renderPage("contract-post-evaluation");
    expect(await screen.findByRole("heading", { name: "合同后评价" })).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "开始办理" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "提交失败：请先在「业务资料」中提供并绑定所需文件，再开始办理。",
    );
  });

  it("surfaces schema validation details instead of a generic incomplete message", async () => {
    const { ApiError } = await import("@/api/client");
    vi.mocked(api.createWorkItem).mockRejectedValue(
      new ApiError(422, "supplier.creditCode: '' does not match '^[0-9A-Z]{18}$'", "INPUT_SCHEMA_INVALID"),
    );
    renderPage();
    expect(await screen.findByRole("heading", { name: "文件完整性校验智能体" })).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "开始办理" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "提交失败：统一社会信用代码须为 18 位数字或大写字母。",
    );
  });

  it("keeps form supplier values when advanced JSON is open with stale empty supplier", async () => {
    vi.mocked(api.getBusinessWork).mockResolvedValue(runnableWork({
      workKey: "procurement-supplier-risk",
      name: "招采一致性与供应商风控",
      packName: "procurement-supplier-risk",
      workItemType: "procurement-supplier-risk-case",
      caseBased: true,
    }));
    vi.mocked(api.listCapabilityPacks).mockResolvedValue({
      items: [{
        ...v1Pack(),
        name: "procurement-supplier-risk",
        manifest: {
          spec: {
            case: {
              type: "procurement-supplier-risk-case",
              subjectRoles: [
                { key: "procurement", objectType: "procurement", role: "PRIMARY", min: 1, max: 1 },
                { key: "supplier", objectType: "supplier", role: "RELATED", min: 1, max: 20 },
              ],
            },
          },
        },
      }],
    });
    renderPage("procurement-supplier-risk");

    fireEvent.change(await screen.findByLabelText("供应商名称"), {
      target: { value: "上海龙田数码科技有限公司" },
    });
    fireEvent.change(screen.getByLabelText("统一社会信用代码"), {
      target: { value: "91310116740594799B" },
    });
    fireEvent.click(screen.getByRole("button", { name: "展开高级 JSON 输入" }));
    const advanced = await screen.findByLabelText("业务输入 JSON");
    fireEvent.change(advanced, {
      target: {
        value: JSON.stringify({
          title: "招采一致性与供应商风控评估",
          projectNo: "ZC-2026-001",
          lotNo: "LOT-01",
          procurementType: "ENTERPRISE",
          asOf: "2026-07-28",
          supplier: { name: "", creditCode: "", aliases: [] },
          riskSources: [{ kind: "CCGP_SERIOUS_ILLEGAL", sourceRef: "official://ccgp/serious-illegal" }],
        }, null, 2),
      },
    });
    fireEvent.click(screen.getByRole("button", { name: "开始办理" }));

    await waitFor(() => expect(api.createCase).toHaveBeenCalled());
    const request = vi.mocked(api.createCase).mock.calls[0]?.[2];
    expect(request?.payload.supplier).toMatchObject({
      name: "上海龙田数码科技有限公司",
      creditCode: "91310116740594799B",
    });
    expect(request?.payload.riskSources).toEqual([
      { kind: "CCGP_SERIOUS_ILLEGAL", sourceRef: "official://ccgp/serious-illegal" },
    ]);
  });

  it("rejects empty supplier fields before calling the API", async () => {
    vi.mocked(api.getBusinessWork).mockResolvedValue(runnableWork({
      workKey: "procurement-supplier-risk",
      name: "招采一致性与供应商风控",
      packName: "procurement-supplier-risk",
      workItemType: "procurement-supplier-risk-case",
      caseBased: true,
    }));
    vi.mocked(api.listCapabilityPacks).mockResolvedValue({
      items: [{
        ...v1Pack(),
        name: "procurement-supplier-risk",
        manifest: {
          spec: {
            case: {
              type: "procurement-supplier-risk-case",
              subjectRoles: [
                { key: "supplier", objectType: "supplier", role: "RELATED", min: 1, max: 20 },
              ],
            },
          },
        },
      }],
    });
    renderPage("procurement-supplier-risk");
    expect(await screen.findByLabelText("供应商名称")).toHaveValue("");
    fireEvent.click(screen.getByRole("button", { name: "开始办理" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("提交失败：请填写供应商名称。");
    expect(api.createCase).not.toHaveBeenCalled();
  });

  it("injects contractObjectId for contract-performance cases", async () => {
    vi.mocked(api.getBusinessWork).mockResolvedValue(runnableWork({
      workKey: "performance-plan-collection",
      name: "履约计划与执行采集智能体",
      packName: "contract-performance",
      workItemType: "contract-performance-case",
      caseBased: true,
    }));
    vi.mocked(api.listCapabilityPacks).mockResolvedValue({
      items: [{
        ...v1Pack(),
        name: "contract-performance",
        version: "1.0.9",
        manifest: {
          spec: {
            case: {
              type: "contract-performance-case",
              subjectRoles: [
                { key: "contract", objectType: "contract", role: "PRIMARY", min: 1, max: 1 },
              ],
            },
          },
        },
      }],
    });
    renderPage("performance-plan-collection");
    expect(await screen.findByLabelText("办理类型")).toHaveValue("INITIALIZE");
    fireEvent.click(screen.getByRole("button", { name: "开始办理" }));
    await waitFor(() => expect(api.createCase).toHaveBeenCalled());
    const request = vi.mocked(api.createCase).mock.calls[0]?.[2];
    expect(request?.payload).toMatchObject({
      contractObjectId: "object-1",
      currency: "CNY",
      timezone: "Asia/Shanghai",
      operation: "INITIALIZE",
    });
  });
});
