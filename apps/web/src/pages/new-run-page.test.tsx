import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { api } from "@/api/client";
import { DEMO_PROJECT_ID, DEMO_TENANT_ID } from "@/lib/demo-scope";
import { NewRunPage } from "./new-run-page";

vi.mock("@/api/client", () => ({ api: {
  listStrategies: vi.fn(),
  listVersions: vi.fn(),
  getVersion: vi.fn(),
  createRun: vi.fn(),
} }));

describe("new run input", () => {
  beforeEach(() => {
    vi.mocked(api.listStrategies).mockResolvedValue({ total: 1, items: [{ strategyId: "strategy-1", name: "内容策略", lifecycle: "ACTIVE", createdAt: new Date(0).toISOString(), updatedAt: new Date(0).toISOString(), draftId: "draft-1", draftRevision: 1, latestVersion: 1 }] });
    vi.mocked(api.listVersions).mockResolvedValue({ total: 1, items: [{ strategyVersionId: "version-1", strategyId: "strategy-1", version: 1, lifecycle: "PUBLISHED", planHash: "a".repeat(64), schemaVersion: "swarmcore.io/v1", runtimeVersion: "1.0.0", createdAt: new Date(0).toISOString() }] });
    vi.mocked(api.getVersion).mockResolvedValue({ strategyVersionId: "version-1", strategyId: "strategy-1", version: 1, lifecycle: "PUBLISHED", planHash: "a".repeat(64), schemaVersion: "swarmcore.io/v1", runtimeVersion: "1.0.0", createdAt: new Date(0).toISOString(), spec: {}, normalizedSpec: {}, plan: { input_schema: { type: "object", required: ["topic"], properties: { topic: { type: "string", title: "主题", description: "请输入需要处理的主题。" }, reviewed: { type: "boolean", title: "已审核" } } } } });
    vi.mocked(api.createRun).mockResolvedValue({ runId: "run-1", status: "ACCEPTED", commandId: "command-1", commandStatus: "ACCEPTED", planHash: "a".repeat(64) });
  });

  it("generates a friendly form from the strategy input schema", async () => {
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(<QueryClientProvider client={client}><MemoryRouter initialEntries={["/runs/new"]}><Routes><Route path="/runs/new" element={<NewRunPage />} /><Route path="/runs/:runId" element={<p>运行已创建</p>} /></Routes></MemoryRouter></QueryClientProvider>);

    fireEvent.change(await screen.findByLabelText("策略版本"), { target: { value: "version-1" } });
    expect(await screen.findByRole("button", { name: "表单填写" })).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByText("请输入需要处理的主题。")).toBeVisible();
    fireEvent.change(screen.getByLabelText(/主题/), { target: { value: "中文表单" } });
    fireEvent.click(screen.getByLabelText(/已审核/));
    fireEvent.click(screen.getByRole("button", { name: "创建运行" }));

    await waitFor(() => expect(api.createRun).toHaveBeenCalledWith(DEMO_TENANT_ID, DEMO_PROJECT_ID, "version-1", { topic: "中文表单", reviewed: true }, expect.any(String)));
    expect(await screen.findByText("运行已创建")).toBeVisible();
  });

  it("keeps JSON editing available as an advanced mode", async () => {
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(<QueryClientProvider client={client}><MemoryRouter><NewRunPage /></MemoryRouter></QueryClientProvider>);

    fireEvent.change(await screen.findByLabelText("策略版本"), { target: { value: "version-1" } });
    fireEvent.click(await screen.findByRole("button", { name: "JSON 编辑" }));
    expect(screen.getByLabelText<HTMLTextAreaElement>("JSON 输入").value).toContain('"reviewed": false');
  });
});
