import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError, api } from "@/api/client";
import {
  DocumentRequirementChecklist,
  DocumentUploadPanel,
} from "@/components/documents/document-intake";

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
});
