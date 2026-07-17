import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import type * as React from "react";
import { MemoryRouter } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { api } from "@/api/client";
import type { CapabilityCatalog, SavedConfiguration } from "@/api/types";
import { AgentConfigurationPage, ModelConfigurationPage, ToolConfigurationPage } from "./registry-config-page";

vi.mock("@/api/client", () => ({ api: {
  getCapabilities: vi.fn(),
  listConfigurations: vi.fn(),
  createConfiguration: vi.fn(),
  updateConfiguration: vi.fn(),
  deleteConfiguration: vi.fn(),
} }));

const catalog: CapabilityCatalog = {
  schemaVersion: "swarmcore.io/capabilities/v1",
  registrySnapshot: "registry:test",
  nodeTypes: [],
  agents: [
    { id: "inline/agno", runtime: "agno", environments: ["development"], declarationSchema: {} },
    { id: "agent://builtin/researcher@1", runtime: "registry/agno", environments: ["development", "production"], declarationSchema: {} },
  ],
  tools: [{ ref: "tool://search@1", risk: "LOW", inputSchema: { type: "object" }, outputSchema: { type: "object" } }],
  models: [{ ref: "model://general@1", runtime: "agno", environments: ["development", "production"] }],
  limits: {},
  swarmSpecSchema: {},
};

function renderPage(page: React.ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}><MemoryRouter>{page}</MemoryRouter></QueryClientProvider>);
}

describe("registry configuration pages", () => {
  afterEach(cleanup);
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.getCapabilities).mockResolvedValue(catalog);
    vi.mocked(api.listConfigurations).mockResolvedValue({ items: [], total: 0 });
  });

  it("generates a registered agent node configuration", async () => {
    vi.mocked(api.listConfigurations).mockResolvedValue({ items: [{
      configurationId: "agent-config", kind: "agent", name: "资料智能体", sourceRef: "inline/agno",
      configuration: { spec: { agents: { analyst: { role: "资料分析", instructions: "整理资料", model: "model://general@1", tools: ["tool://search@1"] } }, graph: { entrypoint: "analyst", nodes: {} } } }, revision: 3,
      createdBy: "tester", updatedBy: "tester", createdAt: "2026-07-17T00:00:00Z", updatedAt: "2026-07-17T00:00:00Z",
    }], total: 1 });
    renderPage(<AgentConfigurationPage />);
    expect(await screen.findByRole("heading", { name: "智能体配置" })).toBeVisible();
    expect(await screen.findByRole("heading", { name: "已配置智能体" })).toBeVisible();
    expect(screen.queryByLabelText("配置名称")).not.toBeInTheDocument();
    fireEvent.click(await screen.findByRole("button", { name: "打开：资料智能体" }));
    expect(await screen.findByRole("textbox", { name: "角色" })).toHaveValue("资料分析");
    expect(await screen.findByRole("checkbox", { name: "tool://search@1" })).toBeChecked();
    fireEvent.change(await screen.findByLabelText("智能体来源"), { target: { value: "agent://builtin/researcher@1" } });
    expect(screen.getByLabelText("智能体节点配置预览")).toHaveTextContent('"ref": "agent://builtin/researcher@1"');
  });

  it("validates tool node input and exposes its schema", async () => {
    vi.mocked(api.listConfigurations).mockResolvedValue({ items: [{
      configurationId: "tool-config", kind: "tool", name: "检索工具", sourceRef: "tool://search@1",
      configuration: { search: { type: "tool", tool: "tool://search@1", dependsOn: [], input: { query: "测试" } } }, revision: 2,
      createdBy: "tester", updatedBy: "tester", createdAt: "2026-07-17T00:00:00Z", updatedAt: "2026-07-17T00:00:00Z",
    }], total: 1 });
    renderPage(<ToolConfigurationPage />);
    expect(await screen.findByRole("heading", { name: "工具配置" })).toBeVisible();
    fireEvent.click(await screen.findByRole("button", { name: "打开：检索工具" }));
    expect((await screen.findByLabelText<HTMLTextAreaElement>("节点输入（JSON 对象）")).value).toContain('"query": "测试"');
    expect(await screen.findByText("低风险")).toBeVisible();
    fireEvent.change(screen.getByLabelText("节点输入（JSON 对象）"), { target: { value: "[" } });
    expect(screen.getByRole("alert")).toHaveTextContent("不是有效的 JSON");
  });

  it("generates a strategy default model configuration", async () => {
    renderPage(<ModelConfigurationPage />);
    expect(await screen.findByRole("heading", { name: "模型配置" })).toBeVisible();
    expect(screen.queryByLabelText("策略默认模型配置预览")).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "新建模型配置" }));
    expect(await screen.findByLabelText("策略默认模型配置预览")).toHaveTextContent('"model": "model://general@1"');
  });

  it("saves a named configuration and displays saved project configurations", async () => {
    const saved: SavedConfiguration = {
      configurationId: "config-1", kind: "model", name: "生产模型", sourceRef: "model://general@1",
      configuration: { spec: { defaults: { model: "model://general@1" } } }, revision: 1,
      createdBy: "tester", updatedBy: "tester", createdAt: "2026-07-17T00:00:00Z", updatedAt: "2026-07-17T00:00:00Z",
    };
    vi.mocked(api.listConfigurations).mockResolvedValue({ items: [saved], total: 1 });
    const updated = { ...saved, name: "生产模型（更新）", revision: 2 };
    vi.mocked(api.updateConfiguration).mockResolvedValue(updated);
    vi.mocked(api.createConfiguration).mockResolvedValue(saved);
    vi.mocked(api.deleteConfiguration).mockResolvedValue(undefined);
    renderPage(<ModelConfigurationPage />);
    fireEvent.click(await screen.findByRole("button", { name: "打开：生产模型" }));
    fireEvent.change(await screen.findByLabelText("配置名称"), { target: { value: "生产模型（更新）" } });
    fireEvent.click(screen.getByRole("button", { name: "保存修改" }));
    await waitFor(() => expect(api.updateConfiguration).toHaveBeenCalledWith(expect.any(String), expect.any(String), "model", "config-1", expect.objectContaining({ name: "生产模型（更新）", sourceRef: "model://general@1" })));
    fireEvent.click(screen.getByRole("button", { name: "新建模型配置" }));
    fireEvent.change(screen.getByLabelText("配置名称"), { target: { value: "备用模型" } });
    fireEvent.click(screen.getByRole("button", { name: "创建模型配置" }));
    await waitFor(() => expect(api.createConfiguration).toHaveBeenCalledWith(expect.any(String), expect.any(String), "model", expect.objectContaining({ name: "备用模型" })));
    fireEvent.click(screen.getByRole("button", { name: "删除生产模型" }));
    await waitFor(() => expect(api.deleteConfiguration).toHaveBeenCalledWith(expect.any(String), expect.any(String), "model", "config-1"));
  });
});
