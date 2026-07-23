import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { api } from "@/api/client";
import { CapabilityPackConfigurationPage } from "./contract-post-evaluation-page";

vi.mock("@/api/client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/api/client")>();
  return {
    ...actual,
    api: {
      ...actual.api,
      listCapabilityPacks: vi.fn(),
      listDocuments: vi.fn(),
      enableCapabilityPack: vi.fn(),
    },
  };
});

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}><MemoryRouter><CapabilityPackConfigurationPage /></MemoryRouter></QueryClientProvider>);
}

describe("capability pack configuration", () => {
  beforeEach(() => {
    vi.mocked(api.listCapabilityPacks).mockResolvedValue({ items: [{
      packId: "pack-1", name: "contract-post-evaluation", versionId: "version-1", version: "1.6.0",
      contentHash: "a".repeat(64), enabled: true, bindingStatus: "ENABLED", configuration: { timeoutSeconds: 300 }, blockers: [],
      manifest: { spec: {
        strategies: { execute: "strategy://contract-post-evaluation/generate@7" },
        agents: ["agent://contract/post-evaluation-analyst@1"],
        tools: ["tool://document/read-versions@1"],
        permissions: ["document.read"],
        documents: [{ category: "CONTRACT", required: true }],
      } },
    }] });
    vi.mocked(api.listDocuments).mockResolvedValue({ items: [{
      documentId: "document-1", name: "采购合同.pdf", category: "CONTRACT", tags: [], status: "AVAILABLE",
      currentVersion: 1, updatedAt: "2026-07-23T00:00:00Z", current: null,
      businessObjectIds: [], businessWorkKeys: ["document-integrity"], versions: [],
    }] });
    vi.mocked(api.enableCapabilityPack).mockResolvedValue({});
  });
  afterEach(() => { cleanup(); vi.clearAllMocks(); });

  it("shows business document requirements without connection configuration", async () => {
    renderPage();

    expect(await screen.findByRole("heading", { name: "合同后评价" })).toBeVisible();
    expect(screen.getByText("业务资料要求")).toBeVisible();
    expect(screen.getByText("底座能力编排")).toBeVisible();
    expect(screen.getByText("项目运行配置")).toBeVisible();
    expect(screen.getByText("contract/post-evaluation-analyst")).toBeVisible();
    expect(screen.getByRole("link", { name: "打开业务资料库" })).toHaveAttribute("href", "/documents");
    expect(screen.queryByText("创建连接")).not.toBeInTheDocument();
    expect(screen.queryByText("资源槽位")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "开始执行" })).not.toBeInTheDocument();

    expect(screen.getByText("已准备")).toBeVisible();
  });

  it("saves project runtime configuration without changing the pack version", async () => {
    renderPage();
    const editor = await screen.findByLabelText("项目运行配置 JSON");
    expect(editor).toHaveValue(JSON.stringify({ timeoutSeconds: 300 }, null, 2));
    fireEvent.change(editor, { target: { value: JSON.stringify({ timeoutSeconds: 600 }) } });
    fireEvent.click(screen.getByRole("button", { name: "保存配置" }));
    await waitFor(() => expect(api.enableCapabilityPack).toHaveBeenCalledWith(expect.any(String), expect.any(String), "version-1", { timeoutSeconds: 600 }));
  });
});
