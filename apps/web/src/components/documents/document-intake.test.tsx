import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError, api } from "@/api/client";
import {
  DocumentBindingEditor,
  DocumentClassificationReview,
  DocumentExtractionReviewForm,
  DocumentProcessingStatus,
  DocumentRequirementChecklist,
  DocumentUploadPanel,
} from "@/components/documents/document-intake";
import type { DocumentProcessingResultSnapshot, DocumentSnapshot } from "@/api/types";

vi.mock("@/api/client", async () => {
  const actual = await vi.importActual<typeof import("@/api/client")>("@/api/client");
  return {
    ...actual,
    api: {
      createUploadBatch: vi.fn(),
      initiateDocument: vi.fn(),
      uploadDocumentContent: vi.fn(),
      completeDocument: vi.fn(),
      getUploadBatch: vi.fn(),
      getDocumentProcessingResult: vi.fn(),
      confirmDocumentClassification: vi.fn(),
      confirmDocumentFields: vi.fn(),
      updateDocumentBindings: vi.fn(),
      getDocumentProcessing: vi.fn(),
      getDocumentProcessingEvents: vi.fn(),
      getDocumentStructuredPackage: vi.fn(),
      cancelDocumentProcessing: vi.fn(),
      downloadArtifact: vi.fn(),
    },
  };
});

function wrap(node: ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{node}</QueryClientProvider>);
}

describe("document intake components", () => {
  afterEach(() => {
    cleanup();
  });

  beforeEach(() => {
    vi.mocked(api.createUploadBatch).mockReset();
    vi.mocked(api.initiateDocument).mockReset();
    vi.mocked(api.uploadDocumentContent).mockReset();
    vi.mocked(api.completeDocument).mockReset();
    vi.mocked(api.getUploadBatch).mockReset();
    vi.mocked(api.getDocumentProcessingResult).mockReset();
    vi.mocked(api.confirmDocumentClassification).mockReset();
    vi.mocked(api.confirmDocumentFields).mockReset();
    vi.mocked(api.updateDocumentBindings).mockReset();
    vi.mocked(api.getDocumentProcessing).mockReset();
    vi.mocked(api.getDocumentProcessingEvents).mockReset();
    vi.mocked(api.getDocumentStructuredPackage).mockReset();
    vi.mocked(api.cancelDocumentProcessing).mockReset();
    vi.mocked(api.downloadArtifact).mockReset();
  });

  it("renders requirement checklist without JSON editor", () => {
    wrap(
      <DocumentRequirementChecklist
        items={[
          {
            key: "primary",
            displayName: "主要业务文件",
            description: "必需",
            required: true,
            minCount: 1,
            maxCount: 3,
            acceptedMediaTypes: ["text/plain"],
            classificationLabels: ["PRIMARY"],
            processingProfileRef: "document-profile://business-default@1",
            extractionSchemaRef: "schema://document/generic-text@1",
            category: "CONTRACT",
            satisfiedCount: 0,
            satisfied: false,
          },
        ]}
      />,
    );
    expect(screen.getByText("主要业务文件")).toBeInTheDocument();
    expect(screen.queryByText(/JSON/i)).not.toBeInTheDocument();
    expect(screen.getByText(/未满足/)).toBeInTheDocument();
  });

  it("exposes multi-file upload without business-work hardcoding", () => {
    wrap(
      <DocumentUploadPanel
        tenantId="t1"
        projectId="p1"
        context={{ businessWorkKey: "any-work", category: "OTHER" }}
      />,
    );
    expect(screen.getByLabelText("选择业务资料文件")).toBeInTheDocument();
    expect(screen.getByText(/支持多文件/)).toBeInTheDocument();
    expect(screen.queryByText("contract-post-evaluation")).not.toBeInTheDocument();
    expect(screen.queryByText("document-integrity")).not.toBeInTheDocument();
  });

  it("continues uploading when createUploadBatch returns Not Found", async () => {
    vi.mocked(api.createUploadBatch).mockRejectedValue(new ApiError(404, "Not Found"));
    vi.mocked(api.initiateDocument).mockResolvedValue({
      documentId: "d1",
      uploadId: "u1",
      version: 1,
      blobId: "b1",
      uploadRef: "/internal/v1/blobs/b1",
      capabilityToken: "token",
      status: "UPLOADING",
    });
    vi.mocked(api.uploadDocumentContent).mockResolvedValue(undefined);
    vi.mocked(api.completeDocument).mockResolvedValue({
      documentId: "d1",
      name: "notes.txt",
      category: "OTHER",
      tags: [],
      status: "AVAILABLE",
      currentVersion: 1,
      updatedAt: new Date().toISOString(),
      current: null,
      businessObjectIds: [],
      businessWorkKeys: [],
      versions: [],
    });

    wrap(
      <DocumentUploadPanel
        tenantId="t1"
        projectId="p1"
        context={{ category: "OTHER" }}
      />,
    );

    const input = screen.getByLabelText<HTMLInputElement>("选择业务资料文件");
    const file = new File([Uint8Array.from([104, 101, 108, 108, 111])], "notes.txt", {
      type: "text/plain",
    });
    Object.defineProperty(file, "arrayBuffer", {
      configurable: true,
      value: () =>
        Promise.resolve(Uint8Array.from([104, 101, 108, 108, 111]).buffer),
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

    await waitFor(() => {
      expect(api.createUploadBatch).toHaveBeenCalled();
      expect(api.initiateDocument).toHaveBeenCalled();
    });
    expect(api.completeDocument).toHaveBeenCalledWith(
      "t1",
      "p1",
      "u1",
      expect.any(String),
      expect.objectContaining({ uploadBatchId: undefined }),
    );
    expect(screen.queryByText("Not Found")).not.toBeInTheDocument();
    expect(await screen.findByText("已完成")).toBeInTheDocument();
  });

  it("shows confirmed classification and fields as saved", async () => {
    const result: DocumentProcessingResultSnapshot = {
      resultId: "result-1",
      resultType: "PROCESSING",
      resultVersion: 3,
      status: "READY",
      schemaRef: null,
      producerRef: null,
      evidence: [],
      confirmedBy: "tester",
      confirmedAt: "2026-07-31T08:00:00Z",
      createdAt: "2026-07-31T08:00:00Z",
      result: {
        documentType: {
          label: "CONTRACT",
          displayName: "合同",
          confidence: 0.92,
          confirmedLabel: "CONTRACT",
        },
        extractions: [{
          fieldPath: "document.title",
          displayName: "标题",
          value: "采购合同",
          valueType: "string",
          confidence: 0.96,
          reviewStatus: "CONFIRMED",
          evidenceRefs: [],
          machineValue: "采购合同",
          confirmedValue: "采购合同",
        }],
      },
    };
    vi.mocked(api.getDocumentProcessingResult).mockResolvedValue(result);

    const classification = wrap(
      <DocumentClassificationReview tenantId="t1" projectId="p1" documentId="d1" />,
    );
    expect(await screen.findByText("已保存")).toBeVisible();
    expect(screen.queryByRole("button", { name: "确认分类" })).not.toBeInTheDocument();
    classification.unmount();

    wrap(
      <DocumentExtractionReviewForm tenantId="t1" projectId="p1" documentId="d1" />,
    );
    expect((await screen.findAllByText("已保存"))[0]).toBeVisible();
    expect(screen.queryByRole("button", { name: "保存字段确认" })).not.toBeInTheDocument();
    expect(screen.getAllByText("已保存").length).toBeGreaterThan(1);
  });

  it("marks existing bindings as saved and enables saving after a change", () => {
    const document: DocumentSnapshot = {
      documentId: "d1",
      name: "采购合同.pdf",
      category: "CONTRACT",
      tags: [],
      status: "AVAILABLE",
      currentVersion: 1,
      updatedAt: "2026-07-31T08:00:00Z",
      current: null,
      businessObjectIds: [],
      businessWorkKeys: ["review"],
      versions: [],
    };
    wrap(
      <DocumentBindingEditor
        tenantId="t1"
        projectId="p1"
        document={document}
        workOptions={[
          { key: "review", label: "合同审查" },
          { key: "report", label: "报告生成" },
        ]}
      />,
    );

    expect(screen.getByText("已保存")).toBeVisible();
    expect(screen.queryByRole("button", { name: "保存绑定" })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("checkbox", { name: "报告生成" }));
    expect(screen.getByRole("button", { name: "保存绑定" })).toBeEnabled();
    expect(screen.getByText("有更改")).toBeVisible();
  });

  it("summarizes processing as product stages and folds technical records", async () => {
    vi.mocked(api.getDocumentProcessing).mockResolvedValue({
      processingRunId: "run-1",
      businessDocumentVersionId: "version-1",
      profileRef: "document-profile://business-default@1",
      status: "REVIEW_REQUIRED",
      currentStage: "REVIEW_REQUIRED",
      stageLabel: "待人工确认",
      attempt: 1,
      parserRef: null,
      classifierRef: null,
      extractorRefs: [],
      errorCode: null,
      errorDetail: null,
      startedAt: "2026-07-29T06:38:06Z",
      completedAt: null,
      provenance: {},
    });
    vi.mocked(api.getDocumentProcessingEvents).mockResolvedValue({
      items: [
        processingEvent(1, "document.processing.started", "PENDING"),
        processingEvent(2, "document.scan.completed", "SCANNING"),
        processingEvent(3, "document.parse.completed", "PARSING"),
        processingEvent(4, "document.classification.completed", "CLASSIFYING"),
        processingEvent(5, "document.extraction.completed", "EXTRACTING"),
        processingEvent(6, "document.quality.checked", "QUALITY_CHECK"),
        processingEvent(7, "document.review.decided", "READY"),
      ],
      nextAfter: 7,
    });
    vi.mocked(api.getDocumentProcessingResult).mockResolvedValue({
      resultId: "result-1",
      resultType: "PROCESSING",
      resultVersion: 3,
      status: "READY",
      schemaRef: null,
      producerRef: null,
      result: {},
      evidence: [],
      confirmedBy: "tester",
      confirmedAt: "2026-07-29T08:13:12Z",
      createdAt: "2026-07-29T06:38:06Z",
    });

    wrap(<DocumentProcessingStatus tenantId="t1" projectId="p1" documentId="d1" />);

    expect(await screen.findByText("处理完成")).toBeVisible();
    expect(screen.getByText("安全检查")).toBeVisible();
    expect(screen.getByText("内容解析")).toBeVisible();
    expect(screen.getByText("字段提取")).toBeVisible();
    expect(screen.getByText("确认完成")).toBeVisible();
    expect(screen.getByText("查看处理记录（7 条）")).toBeVisible();
    expect(screen.queryByText("document.processing.started")).not.toBeInTheDocument();
    expect(screen.getByText(/处理方案 document-profile:\/\/business-default@1/)).not.toBeVisible();
  });
});

function processingEvent(sequence: number, type: string, stage: string) {
  return {
    eventId: `event-${sequence}`,
    eventSeq: sequence,
    processingRunId: "run-1",
    businessDocumentVersionId: "version-1",
    type,
    stage,
    payload: {},
    inputHash: null,
    outputHash: `${sequence}`.repeat(64),
    toolRef: `tool://document/${stage.toLowerCase()}@1`,
    actorId: "system",
    traceId: null,
    occurredAt: `2026-07-29T06:38:0${sequence}Z`,
  };
}
