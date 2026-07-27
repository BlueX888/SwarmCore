import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, Navigate, Route, Routes } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { api } from "@/api/client";
import type { DocumentSnapshot } from "@/api/types";
import {
  DOCUMENT_LIBRARY_ROUTE,
  LEGACY_RESOURCE_REDIRECT,
  LEGACY_RESOURCE_ROUTE,
} from "@/lib/document-library-routes";
import { DocumentLibraryPage } from "@/pages/resource-center-page";

vi.mock("@/api/client", async () => {
  const actual = await vi.importActual<typeof import("@/api/client")>("@/api/client");
  return {
    ...actual,
    api: {
      ...actual.api,
      listDocuments: vi.fn(),
      getDocument: vi.fn(),
      getDocumentProcessing: vi.fn(),
      getDocumentProcessingResult: vi.fn(),
      initiateDocument: vi.fn(),
      uploadDocumentContent: vi.fn(),
      completeDocument: vi.fn(),
      createUploadBatch: vi.fn(),
      getUploadBatch: vi.fn(),
      createBusinessObject: vi.fn(),
    },
  };
});

const document: DocumentSnapshot = {
  documentId: "document-1",
  name: "采购合同.pdf",
  category: "CONTRACT",
  tags: ["采购", "2026"],
  status: "AVAILABLE",
  currentVersion: 2,
  updatedAt: "2026-07-23T08:00:00Z",
  current: {
    documentVersionId: "version-2",
    blobId: "blob-2",
    version: 2,
    filename: "采购合同.pdf",
    mediaType: "application/pdf",
    sizeBytes: 2048,
    sha256: "a".repeat(64),
    processingStatus: "AVAILABLE",
    createdAt: "2026-07-23T08:00:00Z",
  },
  businessObjectIds: ["object-1"],
  businessWorkKeys: ["document-integrity", "report-generation"],
  versions: [],
};

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<MemoryRouter><QueryClientProvider client={client}><DocumentLibraryPage /></QueryClientProvider></MemoryRouter>);
}

describe("business document library", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.listDocuments).mockResolvedValue({ items: [document] });
    vi.mocked(api.getDocument).mockResolvedValue(document);
    vi.mocked(api.getDocumentProcessing).mockRejectedValue(new Error("not ready"));
    vi.mocked(api.getDocumentProcessingResult).mockRejectedValue(new Error("not ready"));
    vi.mocked(api.initiateDocument).mockResolvedValue({
      documentId: "document-2",
      uploadId: "upload-2",
      blobId: "blob-3",
      version: 1,
      uploadRef: "/internal/v1/blobs/blob-3",
      capabilityToken: "token",
      status: "PENDING",
    });
    vi.mocked(api.uploadDocumentContent).mockResolvedValue();
    vi.mocked(api.completeDocument).mockResolvedValue(document);
    vi.mocked(api.createUploadBatch).mockResolvedValue({
      batchId: "batch-1",
      source: "web",
      context: {},
      status: "OPEN",
      fileCount: 0,
      succeededCount: 0,
      failedCount: 0,
      createdBy: "tester",
      createdAt: "2026-07-23T08:00:00Z",
      completedAt: null,
    });
    vi.mocked(api.getUploadBatch).mockResolvedValue({
      batchId: "batch-1",
      source: "web",
      context: {},
      status: "COMPLETED",
      fileCount: 1,
      succeededCount: 1,
      failedCount: 0,
      createdBy: "tester",
      createdAt: "2026-07-23T08:00:00Z",
      completedAt: "2026-07-23T08:01:00Z",
    });
    vi.stubGlobal("crypto", {
      randomUUID: () => "request-id",
      subtle: { digest: vi.fn().mockResolvedValue(new Uint8Array(32).buffer) },
    });
  });
  afterEach(() => cleanup());

  it("shows file metadata and no connection creation workflow", async () => {
    renderPage();
    expect(await screen.findByRole("heading", { name: "业务资料库" })).toBeVisible();
    expect(screen.getAllByText("采购合同.pdf")[0]).toBeVisible();
    expect(screen.getAllByText("合同文件")[0]).toBeVisible();
    expect(screen.getByText("2.0 KB")).toBeVisible();
    expect(screen.getByText("v2")).toBeVisible();
    expect(screen.queryByText("创建连接")).not.toBeInTheDocument();
    expect(screen.queryByText("Secret 引用")).not.toBeInTheDocument();
  });

  it("opens document details in a dialog", async () => {
    renderPage();
    await screen.findAllByText("采购合同.pdf");
    fireEvent.click(screen.getByRole("button", { name: "详情" }));
    expect(await screen.findByRole("dialog")).toBeVisible();
    expect(screen.getByRole("heading", { name: "采购合同.pdf" })).toBeVisible();
    expect(screen.getByText("文件详情与处理确认")).toBeVisible();
    expect(screen.getByLabelText("关闭文件详情")).toBeVisible();
  });

  it("registers a file with the shared upload panel", async () => {
    renderPage();
    await screen.findAllByText("采购合同.pdf");
    fireEvent.click(screen.getByRole("button", { name: "上传文件" }));
    const file = new File(["contract"], "新合同.txt", { type: "text/plain" });
    Object.defineProperty(file, "arrayBuffer", {
      value: () => Promise.resolve(new TextEncoder().encode("contract").buffer),
    });
    fireEvent.change(screen.getByLabelText("选择业务资料文件"), { target: { files: [file] } });
    fireEvent.click(screen.getByRole("button", { name: "开始上传" }));
    await waitFor(() => expect(api.createUploadBatch).toHaveBeenCalled());
    await waitFor(() => expect(api.initiateDocument).toHaveBeenCalledWith(
      expect.any(String),
      expect.any(String),
      expect.objectContaining({
        name: "新合同.txt",
        category: "CONTRACT",
        filename: "新合同.txt",
        businessWorkKeys: [],
        businessObjectIds: [],
        sha256: "0".repeat(64),
      }),
    ));
    await waitFor(() => expect(api.uploadDocumentContent).toHaveBeenCalledWith(
      expect.objectContaining({ uploadId: "upload-2" }),
      file,
    ));
    expect(api.completeDocument).toHaveBeenCalledWith(
      expect.any(String),
      expect.any(String),
      "upload-2",
      "0".repeat(64),
      expect.objectContaining({ uploadBatchId: "batch-1" }),
    );
  });

  it("supports search and status filtering", async () => {
    vi.mocked(api.listDocuments).mockResolvedValue({
      items: [document, {
        ...document,
        documentId: "document-2",
        name: "验收报告.docx",
        category: "REPORT",
        status: "REVIEW_REQUIRED",
        current: document.current === null ? null : {
          ...document.current,
          filename: "验收报告.docx",
        },
      }],
    });
    renderPage();
    await screen.findAllByText("采购合同.pdf");
    fireEvent.change(screen.getByLabelText("搜索文件"), { target: { value: "验收" } });
    expect(screen.queryAllByText("采购合同.pdf")).toHaveLength(0);
    expect(screen.getAllByText("验收报告.docx")[0]).toBeVisible();
    fireEvent.change(screen.getByLabelText("按状态筛选"), { target: { value: "AVAILABLE" } });
    expect(screen.getByText("没有匹配的文件")).toBeVisible();
  });

  it("redirects the legacy resource route to the document library", async () => {
    render(
      <MemoryRouter initialEntries={[`/${LEGACY_RESOURCE_ROUTE}`]}>
        <Routes>
          <Route path={LEGACY_RESOURCE_ROUTE} element={<Navigate to={LEGACY_RESOURCE_REDIRECT} replace />} />
          <Route path={DOCUMENT_LIBRARY_ROUTE} element={<h1>业务资料库</h1>} />
        </Routes>
      </MemoryRouter>,
    );
    expect(await screen.findByRole("heading", { name: "业务资料库" })).toBeVisible();
  });
});
