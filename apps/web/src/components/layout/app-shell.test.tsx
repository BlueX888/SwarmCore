import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { api } from "@/api/client";
import { Navigation } from "./app-shell";

vi.mock("@/api/client", () => ({
  api: {
    listApprovals: vi.fn(),
    listInputs: vi.fn(),
    temporalUiUrl: "http://localhost:8088",
    phoenixUrl: "http://localhost:6006",
  },
}));

describe("workspace navigation", () => {
  beforeEach(() => {
    vi.mocked(api.listApprovals).mockResolvedValue({ items: [], total: 2 });
    vi.mocked(api.listInputs).mockResolvedValue({ items: [], total: 1 });
  });

  it("promotes high-frequency operations and the Canvas to primary navigation", async () => {
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(<QueryClientProvider client={client}><MemoryRouter initialEntries={["/canvas"]}><Navigation /></MemoryRouter></QueryClientProvider>);

    expect(screen.getByRole("link", { name: "工作台" })).toHaveAttribute("href", "/overview");
    expect(screen.getByRole("link", { name: "运行记录" })).toHaveAttribute("href", "/runs");
    expect(screen.getByRole("link", { name: "新建运行" })).toHaveAttribute("href", "/runs/new");
    expect(screen.getByRole("link", { name: "编排画布" })).toHaveAttribute("aria-current", "page");
    expect(screen.getByRole("link", { name: "能力目录" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "智能体配置" })).toHaveAttribute("href", "/agents");
    expect(screen.getByRole("link", { name: "工具配置" })).toHaveAttribute("href", "/tools");
    expect(screen.getByRole("link", { name: "模型配置" })).toHaveAttribute("href", "/models");
    expect(screen.getByRole("link", { name: "审计日志" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Temporal（在新标签页打开）" })).toHaveAttribute("target", "_blank");

    await waitFor(() => expect(within(screen.getByRole("link", { name: "待办中心" })).getByText("3")).toBeVisible());
  });
});
