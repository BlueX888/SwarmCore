import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { api } from "@/api/client";
import type { CapabilityPackSnapshot, EvaluationSnapshot } from "@/api/types";
import { CapabilityPackWorkbenchPage } from "./capability-pack-workbench-page";

vi.mock("@/api/client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/api/client")>();
  return {
    ...actual,
    api: {
      ...actual.api,
      listCapabilityPacks: vi.fn(),
      listDocuments: vi.fn(),
      getPackBindings: vi.fn(),
      createWorkItem: vi.fn(),
      executeWorkItem: vi.fn(),
      createBusinessObject: vi.fn(),
      createCase: vi.fn(),
      assessCase: vi.fn(),
    },
  };
});

const evaluation: EvaluationSnapshot = {
  evaluationId: "evaluation-1", workItemId: "item-1", workItemRevisionId: "revision-1", runId: "run-1",
  status: "RUNNING", result: null, capabilityPackVersionId: "version-1", planHash: "a".repeat(64), attachmentManifestHash: "b".repeat(64), createdAt: "2026-07-22T00:00:00Z",
};

function v1Pack(): CapabilityPackSnapshot {
  return {
    packId: "pack-1", name: "contract-integrity", versionId: "version-1", version: "1.1.0", contentHash: "a".repeat(64),
    manifest: { spec: { workItemType: "contract-case" } }, enabled: true, bindingStatus: "ENABLED", configuration: {}, blockers: [],
  };
}

function renderPage(packName = "contract-integrity") {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}><MemoryRouter initialEntries={[`/capability-packs/${packName}/workbench`]}><Routes>
    <Route path="/capability-packs/:packName/workbench" element={<CapabilityPackWorkbenchPage />} />
    <Route path="/runs/:runId" element={<h1>运行详情</h1>} />
  </Routes></MemoryRouter></QueryClientProvider>);
}

describe("capability pack workbench", () => {
  beforeEach(() => {
    vi.mocked(api.listCapabilityPacks).mockResolvedValue({ items: [v1Pack()] });
    vi.mocked(api.listDocuments).mockResolvedValue({ items: [] });
    vi.mocked(api.getPackBindings).mockResolvedValue({ decisions: [], resources: [] });
    vi.mocked(api.createWorkItem).mockResolvedValue({ workItemId: "item-1", workItemType: "contract-case", status: "DRAFT", revisionId: "revision-1", revision: 1 });
    vi.mocked(api.executeWorkItem).mockResolvedValue(evaluation);
    vi.mocked(api.createBusinessObject).mockResolvedValue({ businessObjectId: "object-1", versionId: "object-version-1", objectType: "contract", canonicalKey: "HT-2026-001", currentVersion: 1, schemaRef: "schema://contract/facts@1", data: {} });
    vi.mocked(api.createCase).mockResolvedValue({ caseId: "case-1", scenarioType: "contract-post-evaluation-case", caseRevisionId: "case-revision-1", revision: 1, payload: {}, status: "DRAFT", owner: null, subjects: [], createdAt: "2026-07-22T00:00:00Z", updatedAt: "2026-07-22T00:00:00Z" });
    vi.mocked(api.assessCase).mockResolvedValue(evaluation);
  });
  afterEach(() => { cleanup(); vi.clearAllMocks(); });

  it("creates and executes a v1 work item, then opens the durable run", async () => {
    renderPage();

    expect(await screen.findByRole("heading", { name: "contract-integrity 工作台" })).toBeVisible();
    fireEvent.change(screen.getByLabelText("负责人"), { target: { value: "采购部" } });
    fireEvent.click(screen.getByRole("button", { name: "开始运行" }));

    await waitFor(() => expect(api.createWorkItem).toHaveBeenCalledWith(expect.any(String), expect.any(String), {
      workItemType: "contract-case", payload: { title: "采购合同检查", contractType: "purchase" }, owner: "采购部",
    }));
    expect(api.executeWorkItem).toHaveBeenCalledWith(expect.any(String), expect.any(String), "item-1");
    expect(await screen.findByRole("heading", { name: "运行详情" })).toBeVisible();
  });

  it("creates required v2 subjects and assesses the case", async () => {
    const pack: CapabilityPackSnapshot = {
      ...v1Pack(), name: "contract-post-evaluation", manifest: { spec: {
        case: { type: "contract-post-evaluation-case", subjectRoles: [{ key: "contract", objectType: "contract", role: "PRIMARY", min: 1, max: 1 }] },
        documents: [{ category: "CONTRACT", required: true }],
      } },
    };
    vi.mocked(api.listCapabilityPacks).mockResolvedValue({ items: [pack] });
    vi.mocked(api.listDocuments).mockResolvedValue({ items: [{
      documentId: "document-1", name: "采购合同.pdf", category: "CONTRACT", tags: [], status: "AVAILABLE",
      currentVersion: 1, updatedAt: "2026-07-23T00:00:00Z", current: null,
      businessObjectIds: ["object-1"], businessWorkKeys: ["document-integrity"], versions: [],
    }] });
    renderPage("contract-post-evaluation");

    expect(await screen.findByRole("heading", { name: "合同后评价工作台" })).toBeVisible();
    await waitFor(() => expect(screen.getByRole("button", { name: "开始运行" })).toBeEnabled());
    fireEvent.click(screen.getByRole("button", { name: "开始运行" }));

    await waitFor(() => expect(api.createBusinessObject).toHaveBeenCalledWith(expect.any(String), expect.any(String), expect.objectContaining({
      objectType: "contract", canonicalKey: "HT-2026-001", schemaRef: "schema://contract/facts@1",
    })));
    expect(api.createCase).toHaveBeenCalledWith(expect.any(String), expect.any(String), expect.objectContaining({
      scenarioType: "contract-post-evaluation-case",
      subjects: [{ businessObjectId: "object-1", businessObjectVersionId: "object-version-1", role: "PRIMARY", subjectKey: "contract" }],
    }));
    expect(api.assessCase).toHaveBeenCalledWith(expect.any(String), expect.any(String), "case-1");
  });

  it("blocks execution while a required document is unavailable", async () => {
    vi.mocked(api.listCapabilityPacks).mockResolvedValue({ items: [{
      ...v1Pack(), manifest: { spec: { workItemType: "contract-case", documents: [{ category: "CONTRACT", required: true }] } },
    }] });
    renderPage();

    expect(await screen.findByText("CONTRACT 类资料尚未准备")).toBeVisible();
    expect(screen.getByRole("link", { name: "选择业务资料" })).toHaveAttribute("href", "/documents");
    expect(screen.getByRole("button", { name: "开始运行" })).toBeDisabled();
    expect(api.createWorkItem).not.toHaveBeenCalled();
  });
});
