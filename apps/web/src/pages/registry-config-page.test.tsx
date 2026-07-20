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
    { id: "agent://builtin/researcher@1", runtime: "registry/agno", environments: ["development", "production"], declarationSchema: {}, role: "researcher", instructions: "Research with authoritative sources and cite every material claim.", model: "model://general@1", tools: ["tool://search@1"] },
    { id: "agent://contract/document-classifier@1", runtime: "registry/agno", environments: ["development", "production"], declarationSchema: {}, role: "contract-document-classifier", instructions: "Classify contract documents from evidence.", model: "model://general@1", tools: ["tool://document/read@1"] },
    { id: "agent://contract/field-extractor@1", runtime: "registry/agno", environments: ["development", "production"], declarationSchema: {}, role: "contract-field-extractor", instructions: "Extract requested fields with evidence.", model: "model://general@1", tools: ["tool://document/read@1"] },
    { id: "inline/fake-deterministic", runtime: "fake-deterministic", environments: ["development", "test"], declarationSchema: {} },
  ],
  tools: [
    { ref: "tool://search@1", risk: "LOW", inputSchema: { type: "object" }, outputSchema: { type: "object" } },
    { ref: "tool://publish-report@1", risk: "HIGH", inputSchema: { type: "object" }, outputSchema: { type: "object" } },
    { ref: "tool://document/read@1", risk: "LOW", inputSchema: { type: "object" }, outputSchema: { type: "object" } },
    { ref: "tool://rules/evaluate@1", risk: "LOW", inputSchema: { type: "object" }, outputSchema: { type: "object" } },
    { ref: "tool://contract/cross-file-consistency@1", risk: "LOW", inputSchema: { type: "object" }, outputSchema: { type: "object" } },
    { ref: "tool://workbench/record-evaluation@1", risk: "MEDIUM", inputSchema: { type: "object" }, outputSchema: { type: "object" } },
    { ref: "tool://report/render@1", risk: "LOW", inputSchema: { type: "object" }, outputSchema: { type: "object" } },
  ],
  models: [{ ref: "model://general@1", runtime: "agno", environments: ["development", "production"] }],
  limits: {},
  swarmSpecSchema: {},
};

function renderPage(page: React.ReactNode, initialEntry = "/") {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}><MemoryRouter initialEntries={[initialEntry]}>{page}</MemoryRouter></QueryClientProvider>);
}

describe("registry configuration pages", () => {
  afterEach(cleanup);
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.getCapabilities).mockResolvedValue(catalog);
    vi.mocked(api.listConfigurations).mockResolvedValue({ items: [], total: 0 });
  });

  it("opens the dedicated agent editor without repeating runtime and configuration libraries", async () => {
    renderPage(<AgentConfigurationPage />);
    expect(await screen.findByRole("heading", { name: "智能体配置" })).toBeVisible();
    expect(screen.getByLabelText("打开已有智能体配置")).toBeVisible();
    expect(screen.getByLabelText("配置名称")).toBeVisible();
    expect(screen.queryByRole("heading", { name: "运行时可用智能体" })).not.toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "已配置智能体" })).not.toBeInTheDocument();
  });

  it("shows all runtime tools before project configurations", async () => {
    renderPage(<ToolConfigurationPage />);
    expect(await screen.findByRole("heading", { name: "运行时可用工具" })).toBeVisible();
    expect(screen.getByText("系统注册表共 7 项；点击“新建工具配置”可保存当前项目参数。")).toBeVisible();
    expect(screen.getByText("tool://contract/cross-file-consistency@1")).toBeVisible();
    expect(screen.getByText("tool://workbench/record-evaluation@1")).toBeVisible();
  });

  it("generates a registered agent node configuration", async () => {
    vi.mocked(api.listConfigurations).mockResolvedValue({ items: [{
      configurationId: "agent-config", kind: "agent", name: "资料智能体", sourceRef: "inline/agno",
      configuration: { spec: { agents: { analyst: { role: "资料分析", instructions: "整理资料", model: "model://general@1", tools: ["tool://search@1"] } }, graph: { entrypoint: "analyst", nodes: {} } } }, revision: 3,
      createdBy: "tester", updatedBy: "tester", createdAt: "2026-07-17T00:00:00Z", updatedAt: "2026-07-17T00:00:00Z",
    }], total: 1 });
    renderPage(<AgentConfigurationPage />);
    expect(await screen.findByRole("heading", { name: "智能体配置" })).toBeVisible();
    fireEvent.change(screen.getByLabelText("打开已有智能体配置"), { target: { value: "agent-config" } });
    expect(await screen.findByRole("textbox", { name: "角色与目标" })).toHaveValue("资料分析");
    expect(await screen.findByRole("checkbox", { name: /tool:\/\/search@1/ })).toBeChecked();
    fireEvent.change(await screen.findByLabelText("智能体来源"), { target: { value: "agent://builtin/researcher@1" } });
    expect(screen.getByLabelText("智能体节点配置预览")).toHaveTextContent('"ref": "agent://builtin/researcher@1"');
  });

  it.each([
    ["agent://builtin/researcher@1", "researcher", "tool://search@1"],
    ["agent://contract/document-classifier@1", "contract-document-classifier", "tool://document/read@1"],
    ["agent://contract/field-extractor@1", "contract-field-extractor", "tool://document/read@1"],
  ])("copies %s into an editable model, tool, and prompt definition", async (reference, role, tool) => {
    renderPage(<AgentConfigurationPage />, `/agents/configure?copy=${encodeURIComponent(reference)}`);
    expect(await screen.findByText(new RegExp(`已从“${role}”复制模型、工具和提示词`))).toBeVisible();
    expect(screen.getByLabelText("配置名称")).toHaveValue(`${role} 项目配置`);
    expect(screen.getByLabelText("角色与目标")).toHaveValue(role);
    expect(screen.getByLabelText("系统指令")).not.toHaveValue("");
    expect(screen.getByLabelText("首选逻辑模型")).toHaveValue("model://general@1");
    expect(screen.getByRole("checkbox", { name: new RegExp(tool.replaceAll("/", "\\/")) })).toBeChecked();
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
