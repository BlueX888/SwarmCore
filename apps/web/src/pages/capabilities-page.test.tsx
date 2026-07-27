import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes, useLocation } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { api } from "@/api/client";
import { CapabilitiesPage } from "./capabilities-page";

vi.mock("@/api/client", () => ({ api: {
  getCapabilityCenter: vi.fn(), listPresets: vi.fn(), runCapability: vi.fn(),
  createPreset: vi.fn(), updatePreset: vi.fn(), copyPreset: vi.fn(), deletePreset: vi.fn(),
  getModelProvider: vi.fn(), saveModelProvider: vi.fn(), testModelProvider: vi.fn(),
} }));

const ready = {
  ref: "tool://search@1", kind: "tool" as const, name: "受控检索", description: "在已配置的知识源中检索内容。", source: "system",
  readiness: { status: "READY" as const, reasons: [] }, risk: "LOW",
  inputSchema: { type: "object", properties: { query: { type: "string", title: "检索词" } }, required: ["query"] }, outputSchema: { type: "object" },
};
const notReady = {
  ref: "tool://missing@1", kind: "tool" as const, name: "未接入工具", description: "尚无执行器。", source: "system",
  readiness: { status: "NOT_READY" as const, reasons: [{ code: "EXECUTOR_MISSING" as const, message: "missing" }] }, risk: "LOW",
  inputSchema: { type: "object" }, outputSchema: { type: "object" },
};
const agent = {
  ref: "agent://builtin/researcher@1", kind: "agent" as const, name: "researcher", description: "使用受控检索调研主题，并整理结构化结论。", source: "system",
  readiness: { status: "READY" as const, reasons: [] },
  inputSchema: { type: "object", required: ["topic"], properties: {
    topic: { type: "string", title: "研究主题" },
    language: { type: "string", title: "输出语言", default: "简体中文" },
    maxSources: { type: "integer", title: "最多参考来源数", default: 8 },
  } }, outputSchema: { type: "object" },
};
const projectAgent = {
  ...agent,
  ref: "agent://project/7741c9d0-340e-4ef1-a0d0-a20961195c04@2",
  name: "项目研究员",
  source: "project",
};
const model = {
  ref: "model://general@1", kind: "model" as const, name: "general", description: "通用对话与结构化输出模型路由。", source: "system",
  readiness: { status: "READY" as const, reasons: [] }, inputSchema: { type: "object" }, outputSchema: { type: "object" },
};
const preset = {
  presetId: "preset-1", kind: "tool" as const, name: "日报检索", capabilityRef: ready.ref,
  parameters: { query: "daily" }, revision: 1, readiness: ready.readiness,
  createdBy: "test", updatedBy: "test", createdAt: new Date(0).toISOString(), updatedAt: new Date(0).toISOString(),
};

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  return render(<QueryClientProvider client={client}><MemoryRouter initialEntries={["/tools"]}><Routes><Route path="/tools" element={<CapabilitiesPage kind="tool" />} /><Route path="/tools/new" element={<p>新建工具页面</p>} /><Route path="/runs/:runId" element={<p>运行详情</p>} /></Routes></MemoryRouter></QueryClientProvider>);
}

function AgentConfigurationProbe() {
  const location = useLocation();
  return <p>智能体配置入口 {location.search}</p>;
}

function renderAgentPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  return render(<QueryClientProvider client={client}><MemoryRouter initialEntries={["/agents"]}><Routes><Route path="/agents" element={<CapabilitiesPage kind="agent" />} /><Route path="/agents/configure" element={<AgentConfigurationProbe />} /></Routes></MemoryRouter></QueryClientProvider>);
}

function renderModelPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  return render(<QueryClientProvider client={client}><MemoryRouter initialEntries={["/models"]}><Routes><Route path="/models" element={<CapabilitiesPage kind="model" />} /></Routes></MemoryRouter></QueryClientProvider>);
}

function renderPolicyPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  return render(<QueryClientProvider client={client}><MemoryRouter initialEntries={["/policies"]}><Routes><Route path="/policies" element={<CapabilitiesPage kind="policy" />} /><Route path="/policies/new" element={<p>新建策略页面</p>} /></Routes></MemoryRouter></QueryClientProvider>);
}

describe("capabilities page", () => {
  afterEach(cleanup);

  beforeEach(() => {
    vi.mocked(api.getCapabilityCenter).mockResolvedValue({ registrySnapshot: "registry:test", items: [ready, notReady] });
    vi.mocked(api.listPresets).mockResolvedValue({ items: [], total: 0 });
    vi.mocked(api.runCapability).mockResolvedValue({ runId: "run-1", status: "PENDING", commandId: "command-1", commandStatus: "PENDING", planHash: "hash" });
    vi.mocked(api.createPreset).mockResolvedValue(preset);
    vi.mocked(api.updatePreset).mockResolvedValue({ ...preset, name: "更新预设", revision: 2 });
    vi.mocked(api.copyPreset).mockResolvedValue({ ...preset, presetId: "preset-2", name: "日报检索 副本" });
    vi.mocked(api.deletePreset).mockResolvedValue(undefined);
    vi.mocked(api.getModelProvider).mockResolvedValue({ logicalModel: "model://general", providerUrl: "https://api.example.com/v1", modelName: "test-model", apiKeyConfigured: true, displayName: "test-model" });
    vi.mocked(api.saveModelProvider).mockResolvedValue({ logicalModel: "model://general", providerUrl: "https://api.example.com/v1", modelName: "test-model", apiKeyConfigured: true, displayName: "test-model" });
    vi.mocked(api.testModelProvider).mockResolvedValue({ connected: true, modelName: "test-model", latencyMs: 42 });
  });

  it("shows ready capabilities by default and explains not-ready resources on demand", async () => {
    renderPage();
    expect(screen.getByRole("heading", { name: "工具" })).toBeVisible();
    expect(screen.getByLabelText("搜索工具")).toBeVisible();
    expect(screen.queryByLabelText("能力类型")).not.toBeInTheDocument();
    expect(await screen.findByText("受控检索")).toBeVisible();
    expect(screen.queryByText("未接入工具")).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("checkbox", { name: "显示未就绪" }));
    fireEvent.click(await screen.findByRole("button", { name: /未接入工具/ }));
    const dialog = screen.getByRole("dialog", { name: "未接入工具" });
    expect(dialog).toBeVisible();
    expect(within(dialog).getByText("缺少执行器")).toBeVisible();
    expect(within(dialog).getByRole("button", { name: "立即运行" })).toBeDisabled();
  });

  it("shows source and risk as color-coded badges without repeating the capability kind", async () => {
    const mediumRisk = { ...ready, ref: "tool://medium@1", name: "中风险工具", risk: "MEDIUM" };
    const highRisk = { ...ready, ref: "tool://high@1", name: "高风险工具", risk: "HIGH" };
    vi.mocked(api.getCapabilityCenter).mockResolvedValue({ registrySnapshot: "registry:test", items: [ready, mediumRisk, highRisk] });
    renderPage();

    const lowCard = await screen.findByRole("button", { name: /受控检索/ });
    const mediumCard = screen.getByRole("button", { name: /中风险工具/ });
    const highCard = screen.getByRole("button", { name: /高风险工具/ });
    expect(within(lowCard).queryByText("工具", { exact: true })).not.toBeInTheDocument();
    expect(within(lowCard).getByText("系统内置")).toHaveClass("bg-gray-100");
    expect(within(lowCard).getByText("LOW 风险")).toHaveClass("bg-success-50", "text-success-600");
    expect(within(mediumCard).getByText("MEDIUM 风险")).toHaveClass("bg-warning-50", "text-warning-600");
    expect(within(highCard).getByText("HIGH 风险")).toHaveClass("bg-error-50", "text-error-600");
  });

  it("filters tools by risk classification", async () => {
    const mediumRisk = { ...ready, ref: "tool://medium@1", name: "中风险工具", description: "中风险描述。", risk: "MEDIUM" };
    const highRisk = { ...ready, ref: "tool://high@1", name: "高风险工具", description: "高风险描述。", risk: "HIGH" };
    vi.mocked(api.getCapabilityCenter).mockResolvedValue({ registrySnapshot: "registry:test", items: [ready, mediumRisk, highRisk] });
    renderPage();

    expect(await screen.findByText("受控检索")).toBeVisible();
    expect(screen.getByText("中风险工具")).toBeVisible();
    expect(screen.getByText("高风险工具")).toBeVisible();
    const riskGroup = screen.getByRole("group", { name: "按风险分类" });
    expect(within(riskGroup).getByRole("button", { name: "全部" })).toHaveAttribute("aria-pressed", "true");

    fireEvent.click(within(riskGroup).getByRole("button", { name: "HIGH" }));
    expect(screen.queryByText("受控检索")).not.toBeInTheDocument();
    expect(screen.queryByText("中风险工具")).not.toBeInTheDocument();
    expect(screen.getByText("高风险工具")).toBeVisible();
    expect(within(riskGroup).getByRole("button", { name: "HIGH" })).toHaveAttribute("aria-pressed", "true");

    fireEvent.click(within(riskGroup).getByRole("button", { name: "LOW" }));
    expect(screen.getByText("受控检索")).toBeVisible();
    expect(screen.queryByText("中风险工具")).not.toBeInTheDocument();
    expect(screen.queryByText("高风险工具")).not.toBeInTheDocument();

    fireEvent.click(within(riskGroup).getByRole("button", { name: "全部" }));
    expect(screen.getByText("受控检索")).toBeVisible();
    expect(screen.getByText("中风险工具")).toBeVisible();
    expect(screen.getByText("高风险工具")).toBeVisible();
  });

  it("opens capability details in a dialog and closes from the header action", async () => {
    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: /受控检索/ }));
    const dialog = screen.getByRole("dialog", { name: "受控检索" });
    expect(dialog).toBeVisible();
    expect(within(dialog).getByLabelText("检索词")).toBeVisible();
    expect(within(dialog).getByRole("heading", { name: "我的预设" })).toBeVisible();
    expect(within(dialog).getByText("高级详情")).toBeVisible();
    fireEvent.click(within(dialog).getByRole("button", { name: "关闭详情" }));
    await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
  });

  it("opens the user-facing tool creation flow", async () => {
    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: "新建工具" }));
    expect(await screen.findByText("新建工具页面")).toBeVisible();
  });

  it("generates a schema field, creates a standard capability run, and opens its detail", async () => {
    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: /受控检索/ }));
    const dialog = screen.getByRole("dialog", { name: "受控检索" });
    fireEvent.change(within(dialog).getByLabelText("检索词"), { target: { value: "swarm" } });
    fireEvent.click(within(dialog).getByRole("button", { name: "立即运行" }));
    await waitFor(() => expect(api.runCapability).toHaveBeenCalledWith(expect.any(String), expect.any(String), "tool://search@1", { query: "swarm" }, undefined));
    expect(await screen.findByText("运行详情")).toBeVisible();
  });

  it("creates, updates, copies, and deletes reusable presets", async () => {
    vi.mocked(api.listPresets).mockResolvedValue({ items: [preset], total: 1 });
    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: /受控检索/ }));
    const dialog = screen.getByRole("dialog", { name: "受控检索" });
    fireEvent.change(within(dialog).getByLabelText("检索词"), { target: { value: "swarm" } });
    fireEvent.change(within(dialog).getByLabelText("预设名称"), { target: { value: "新预设" } });
    fireEvent.click(within(dialog).getByRole("button", { name: "保存预设" }));
    await waitFor(() => expect(api.createPreset).toHaveBeenCalledWith(expect.any(String), expect.any(String), { name: "新预设", capabilityRef: ready.ref, parameters: { query: "swarm" } }));

    fireEvent.click(within(dialog).getByRole("button", { name: "日报检索" }));
    fireEvent.change(within(dialog).getByLabelText("预设名称"), { target: { value: "更新预设" } });
    fireEvent.click(within(dialog).getByRole("button", { name: "更新预设" }));
    await waitFor(() => expect(api.updatePreset).toHaveBeenCalledWith(expect.any(String), expect.any(String), preset.presetId, { name: "更新预设", capabilityRef: ready.ref, parameters: { query: "daily" } }));

    fireEvent.click(within(dialog).getByRole("button", { name: "复制预设 日报检索" }));
    await waitFor(() => expect(api.copyPreset).toHaveBeenCalledWith(expect.any(String), expect.any(String), preset.presetId, "日报检索 副本"));
    fireEvent.click(within(dialog).getByRole("button", { name: "删除预设 日报检索" }));
    await waitFor(() => expect(api.deletePreset).toHaveBeenCalledWith(expect.any(String), expect.any(String), preset.presetId));
  });

  it("offers visible editing for a built-in agent and starts with reasonable run defaults", async () => {
    vi.mocked(api.getCapabilityCenter).mockResolvedValue({ registrySnapshot: "registry:test", items: [agent] });
    renderAgentPage();
    expect(await screen.findByRole("button", { name: "创建智能体" })).toBeVisible();
    expect(screen.getByRole("button", { name: "编辑 researcher 配置" })).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: /可用 researcher/ }));
    const dialog = screen.getByRole("dialog", { name: "researcher" });
    expect(within(dialog).getByLabelText("输出语言")).toHaveValue("简体中文");
    expect(within(dialog).getByLabelText("最多参考来源数")).toHaveValue(8);
    expect(within(dialog).getByText(/系统内置版本保持只读/)).toBeVisible();
    fireEvent.click(within(dialog).getByRole("button", { name: "编辑当前智能体配置" }));
    expect(await screen.findByText(/智能体配置入口 \?copy=agent%3A%2F%2Fbuiltin%2Fresearcher%401/)).toBeVisible();
  });

  it("opens the agent editor in create mode", async () => {
    vi.mocked(api.getCapabilityCenter).mockResolvedValue({ registrySnapshot: "registry:test", items: [agent] });
    renderAgentPage();
    fireEvent.click(await screen.findByRole("button", { name: "创建智能体" }));
    expect(await screen.findByText("智能体配置入口 ?new=1")).toBeVisible();
  });

  it("opens the persisted definition when editing a project agent", async () => {
    vi.mocked(api.getCapabilityCenter).mockResolvedValue({ registrySnapshot: "registry:test", items: [projectAgent] });
    renderAgentPage();
    fireEvent.click(await screen.findByRole("button", { name: /可用 项目研究员/ }));
    const dialog = screen.getByRole("dialog", { name: "项目研究员" });
    expect(within(dialog).getByText(/运行时会由 Agno Adapter 创建真实实例/)).toBeVisible();
    fireEvent.click(within(dialog).getByRole("button", { name: "编辑当前智能体配置" }));
    expect(await screen.findByText(/智能体配置入口 \?configuration=7741c9d0-340e-4ef1-a0d0-a20961195c04/)).toBeVisible();
  });

  it("guides empty model catalog toward three-field creation", async () => {
    vi.mocked(api.getCapabilityCenter).mockResolvedValue({ registrySnapshot: "registry:test", items: [] });
    renderModelPage();
    expect(await screen.findByRole("heading", { name: "模型" })).toBeVisible();
    expect(screen.getByRole("checkbox", { name: "显示已配置但未就绪" })).toBeVisible();
    expect(screen.getByText("没有可用模型。")).toBeVisible();
    expect(screen.getByText(/点击“新建模型”，只需填写 API URL、ModelName 和 API Key/)).toBeVisible();
    fireEvent.click(screen.getByRole("checkbox", { name: "显示已配置但未就绪" }));
    expect(await screen.findByText("当前项目还没有模型配置。")).toBeVisible();
  });

  it("configures and performs a real model connectivity test without run controls", async () => {
    vi.mocked(api.getCapabilityCenter).mockResolvedValue({ registrySnapshot: "registry:test", items: [model] });
    renderModelPage();
    fireEvent.click(await screen.findByRole("button", { name: /general/ }));
    const dialog = screen.getByRole("dialog", { name: "general" });
    await waitFor(() => expect(within(dialog).getByLabelText("模型 API URL")).toHaveValue("https://api.example.com/v1"));
    expect(within(dialog).queryByRole("heading", { name: "我的预设" })).not.toBeInTheDocument();
    expect(within(dialog).queryByLabelText("运行输入 JSON")).not.toBeInTheDocument();
    expect(within(dialog).queryByRole("button", { name: "加入画布" })).not.toBeInTheDocument();
    expect(within(dialog).queryByRole("button", { name: "立即运行" })).not.toBeInTheDocument();
    expect(within(dialog).getByText(/提示词在配置智能体或策略节点时填写/)).toBeVisible();
    fireEvent.click(within(dialog).getByRole("button", { name: "检测连接" }));
    await waitFor(() => expect(api.testModelProvider).toHaveBeenCalledWith(expect.any(String), expect.any(String), {
      logicalModel: "model://general", providerUrl: "https://api.example.com/v1", modelName: "test-model", displayName: "test-model",
    }));
    expect(await within(dialog).findByText(/连接成功.*42 ms/)).toBeVisible();
  });

  it("shows a visual API key mask when configured and toggles only local typed values", async () => {
    vi.mocked(api.getCapabilityCenter).mockResolvedValue({ registrySnapshot: "registry:test", items: [model] });
    renderModelPage();
    fireEvent.click(await screen.findByRole("button", { name: /general/ }));
    const dialog = screen.getByRole("dialog", { name: "general" });
    const apiKeyInput = await within(dialog).findByLabelText("模型 API Key");
    await waitFor(() => expect(apiKeyInput).toHaveValue("••••••••"));
    expect(apiKeyInput).toHaveAttribute("type", "password");
    expect(within(dialog).getByText(/已有密钥保存在 Vault/)).toBeVisible();
    const vaultMaskToggle = within(dialog).getByRole("button", { name: "已保存密钥不可回显" });
    expect(vaultMaskToggle).toBeDisabled();
    expect(vaultMaskToggle.querySelector("svg.lucide-eye-off")).toBeTruthy();

    fireEvent.focus(apiKeyInput);
    expect(apiKeyInput).toHaveValue("");
    fireEvent.change(apiKeyInput, { target: { value: "sk-local-secret" } });
    expect(apiKeyInput).toHaveValue("sk-local-secret");
    expect(apiKeyInput).toHaveAttribute("type", "password");
    const revealToggle = within(dialog).getByRole("button", { name: "显示 API Key" });
    expect(revealToggle.querySelector("svg.lucide-eye-off")).toBeTruthy();

    fireEvent.click(revealToggle);
    expect(apiKeyInput).toHaveAttribute("type", "text");
    const hideToggle = within(dialog).getByRole("button", { name: "隐藏 API Key" });
    expect(hideToggle.querySelector("svg.lucide-eye")).toBeTruthy();
    fireEvent.click(hideToggle);
    expect(apiKeyInput).toHaveAttribute("type", "password");
    expect(within(dialog).getByRole("button", { name: "显示 API Key" }).querySelector("svg.lucide-eye-off")).toBeTruthy();

    fireEvent.change(apiKeyInput, { target: { value: "" } });
    fireEvent.blur(apiKeyInput);
    await waitFor(() => expect(apiKeyInput).toHaveValue("••••••••"));
    expect(within(dialog).getByRole("button", { name: "已保存密钥不可回显" })).toBeDisabled();
  });

  it("creates a project model from three fields without picking a logical route", async () => {
    vi.mocked(api.getCapabilityCenter).mockResolvedValue({ registrySnapshot: "registry:test", items: [] });
    vi.mocked(api.saveModelProvider).mockResolvedValue({
      logicalModel: "model://project/11111111-1111-1111-1111-111111111111",
      providerUrl: "https://api.example.com/v1",
      modelName: "gpt-4.1-mini",
      apiKeyConfigured: true,
      displayName: "业务模型",
    });
    renderModelPage();
    fireEvent.click(await screen.findByRole("button", { name: "新建模型" }));
    const dialog = screen.getByRole("dialog", { name: "新建模型配置" });
    expect(within(dialog).queryByLabelText("逻辑模型路由")).not.toBeInTheDocument();
    expect(within(dialog).getByText(/填写三要素即可创建项目级可用模型/)).toBeVisible();
    fireEvent.change(within(dialog).getByLabelText("模型显示名称"), { target: { value: "业务模型" } });
    fireEvent.change(within(dialog).getByLabelText("模型 API URL"), { target: { value: "https://api.example.com/v1" } });
    fireEvent.change(within(dialog).getByLabelText("模型名称"), { target: { value: "gpt-4.1-mini" } });
    fireEvent.change(within(dialog).getByLabelText("模型 API Key"), { target: { value: "sk-test" } });
    fireEvent.click(within(dialog).getByRole("button", { name: "创建并保存" }));
    await waitFor(() => expect(api.saveModelProvider).toHaveBeenCalledWith(
      expect.any(String),
      expect.any(String),
      expect.objectContaining({
        providerUrl: "https://api.example.com/v1",
        modelName: "gpt-4.1-mini",
        displayName: "业务模型",
        apiKey: "sk-test",
        logicalModel: expect.stringMatching(/^model:\/\/project\/[0-9a-f-]{36}$/),
      }),
    ));
    expect(await within(dialog).findByText(/已创建项目模型/)).toBeVisible();
  });

  it("opens the policy creation flow from the page header", async () => {
    vi.mocked(api.getCapabilityCenter).mockResolvedValue({ registrySnapshot: "registry:test", items: [] });
    renderPolicyPage();
    expect(await screen.findByRole("heading", { name: "策略能力" })).toBeVisible();
    fireEvent.click(await screen.findByRole("button", { name: "新建策略" }));
    expect(await screen.findByText("新建策略页面")).toBeVisible();
  });
});
