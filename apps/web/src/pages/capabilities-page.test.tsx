import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes, useLocation } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { api } from "@/api/client";
import { CapabilitiesPage } from "./capabilities-page";

vi.mock("@/api/client", () => ({ api: {
  getCapabilityCenter: vi.fn(), listPresets: vi.fn(), runCapability: vi.fn(),
  createPreset: vi.fn(), updatePreset: vi.fn(), copyPreset: vi.fn(), deletePreset: vi.fn(),
} }));

const ready = {
  ref: "tool://search@1", kind: "tool" as const, name: "受控检索", description: "搜索项目知识。", source: "system",
  readiness: { status: "READY" as const, reasons: [] }, risk: "LOW",
  inputSchema: { type: "object", properties: { query: { type: "string", title: "检索词" } }, required: ["query"] }, outputSchema: { type: "object" },
};
const notReady = {
  ref: "tool://missing@1", kind: "tool" as const, name: "未接入工具", description: "尚无执行器。", source: "system",
  readiness: { status: "NOT_READY" as const, reasons: [{ code: "EXECUTOR_MISSING" as const, message: "missing" }] }, risk: "LOW",
  inputSchema: { type: "object" }, outputSchema: { type: "object" },
};
const agent = {
  ref: "agent://builtin/researcher@1", kind: "agent" as const, name: "researcher", description: "Research the assigned topic.", source: "system",
  readiness: { status: "READY" as const, reasons: [] },
  inputSchema: { type: "object", required: ["topic"], properties: {
    topic: { type: "string", title: "研究主题" },
    language: { type: "string", title: "输出语言", default: "简体中文" },
    maxSources: { type: "integer", title: "最多参考来源数", default: 8 },
  } }, outputSchema: { type: "object" },
};
const preset = {
  presetId: "preset-1", kind: "tool" as const, name: "日报检索", capabilityRef: ready.ref,
  parameters: { query: "daily" }, revision: 1, readiness: ready.readiness,
  createdBy: "test", updatedBy: "test", createdAt: new Date(0).toISOString(), updatedAt: new Date(0).toISOString(),
};

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  return render(<QueryClientProvider client={client}><MemoryRouter initialEntries={["/tools"]}><Routes><Route path="/tools" element={<CapabilitiesPage kind="tool" />} /><Route path="/runs/:runId" element={<p>运行详情</p>} /></Routes></MemoryRouter></QueryClientProvider>);
}

function AgentConfigurationProbe() {
  const location = useLocation();
  return <p>智能体配置入口 {location.search}</p>;
}

function renderAgentPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  return render(<QueryClientProvider client={client}><MemoryRouter initialEntries={["/agents"]}><Routes><Route path="/agents" element={<CapabilitiesPage kind="agent" />} /><Route path="/agents/configure" element={<AgentConfigurationProbe />} /></Routes></MemoryRouter></QueryClientProvider>);
}

describe("capabilities page", () => {
  beforeEach(() => {
    vi.mocked(api.getCapabilityCenter).mockResolvedValue({ registrySnapshot: "registry:test", items: [ready, notReady] });
    vi.mocked(api.listPresets).mockResolvedValue({ items: [], total: 0 });
    vi.mocked(api.runCapability).mockResolvedValue({ runId: "run-1", status: "PENDING", commandId: "command-1", commandStatus: "PENDING", planHash: "hash" });
    vi.mocked(api.createPreset).mockResolvedValue(preset);
    vi.mocked(api.updatePreset).mockResolvedValue({ ...preset, name: "更新预设", revision: 2 });
    vi.mocked(api.copyPreset).mockResolvedValue({ ...preset, presetId: "preset-2", name: "日报检索 副本" });
    vi.mocked(api.deletePreset).mockResolvedValue(undefined);
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
    expect(screen.getByText("缺少执行器")).toBeVisible();
    expect(screen.getByRole("button", { name: "立即运行" })).toBeDisabled();
  });

  it("generates a schema field, creates a standard capability run, and opens its detail", async () => {
    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: /受控检索/ }));
    fireEvent.change(screen.getByLabelText("检索词"), { target: { value: "swarm" } });
    fireEvent.click(screen.getByRole("button", { name: "立即运行" }));
    await waitFor(() => expect(api.runCapability).toHaveBeenCalledWith(expect.any(String), expect.any(String), "tool://search@1", { query: "swarm" }, undefined));
    expect(await screen.findByText("运行详情")).toBeVisible();
  });

  it("creates, updates, copies, and deletes reusable presets", async () => {
    vi.mocked(api.listPresets).mockResolvedValue({ items: [preset], total: 1 });
    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: /受控检索/ }));
    fireEvent.change(screen.getByLabelText("检索词"), { target: { value: "swarm" } });
    fireEvent.change(screen.getByLabelText("预设名称"), { target: { value: "新预设" } });
    fireEvent.click(screen.getByRole("button", { name: "保存预设" }));
    await waitFor(() => expect(api.createPreset).toHaveBeenCalledWith(expect.any(String), expect.any(String), { name: "新预设", capabilityRef: ready.ref, parameters: { query: "swarm" } }));

    fireEvent.click(screen.getByRole("button", { name: "日报检索" }));
    fireEvent.change(screen.getByLabelText("预设名称"), { target: { value: "更新预设" } });
    fireEvent.click(screen.getByRole("button", { name: "更新预设" }));
    await waitFor(() => expect(api.updatePreset).toHaveBeenCalledWith(expect.any(String), expect.any(String), preset.presetId, { name: "更新预设", capabilityRef: ready.ref, parameters: { query: "daily" } }));

    fireEvent.click(screen.getByRole("button", { name: "复制预设 日报检索" }));
    await waitFor(() => expect(api.copyPreset).toHaveBeenCalledWith(expect.any(String), expect.any(String), preset.presetId, "日报检索 副本"));
    fireEvent.click(screen.getByRole("button", { name: "删除预设 日报检索" }));
    await waitFor(() => expect(api.deletePreset).toHaveBeenCalledWith(expect.any(String), expect.any(String), preset.presetId));
  });

  it("offers visible editing for a built-in agent and starts with reasonable run defaults", async () => {
    vi.mocked(api.getCapabilityCenter).mockResolvedValue({ registrySnapshot: "registry:test", items: [agent] });
    renderAgentPage();
    expect(await screen.findByRole("button", { name: "创建智能体" })).toBeVisible();
    expect(screen.getByRole("button", { name: "编辑 researcher 配置" })).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: /可用 researcher/ }));
    expect(screen.getByLabelText("输出语言")).toHaveValue("简体中文");
    expect(screen.getByLabelText("最多参考来源数")).toHaveValue(8);
    expect(screen.getByText(/系统内置版本保持只读/)).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "编辑当前智能体配置" }));
    expect(await screen.findByText(/智能体配置入口 \?copy=agent%3A%2F%2Fbuiltin%2Fresearcher%401/)).toBeVisible();
  });

  it("opens the agent editor in create mode", async () => {
    vi.mocked(api.getCapabilityCenter).mockResolvedValue({ registrySnapshot: "registry:test", items: [agent] });
    renderAgentPage();
    fireEvent.click(await screen.findByRole("button", { name: "创建智能体" }));
    expect(await screen.findByText("智能体配置入口 ?new=1")).toBeVisible();
  });
});
