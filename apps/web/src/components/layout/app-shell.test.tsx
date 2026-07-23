import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { api } from "@/api/client";
import { BUSINESS_WORKS } from "@/lib/business-works";
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

  it("groups business, execution, platform, governance, and observability navigation", async () => {
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(<QueryClientProvider client={client}><MemoryRouter initialEntries={["/canvas"]}><Navigation /></MemoryRouter></QueryClientProvider>);

    expect(screen.getByRole("link", { name: "工作台" })).toHaveAttribute("href", "/overview");

    const business = screen.getByRole("region", { name: "业务工作" });
    expect(within(business).getByRole("link", { name: "工作总览" })).toHaveAttribute("href", "/business-works");
    for (const work of BUSINESS_WORKS) {
      expect(within(business).getByRole("link", { name: work.shortName })).toHaveAttribute("href", `/business-works/${work.key}`);
    }
    expect(within(business).queryByRole("link", { name: "业务能力包" })).not.toBeInTheDocument();
    expect(within(business).queryByRole("link", { name: "合同后评价" })).not.toBeInTheDocument();
    expect(within(business).queryByRole("link", { name: "业务工作项" })).not.toBeInTheDocument();
    expect(within(business).queryByRole("link", { name: "规则集" })).not.toBeInTheDocument();

    const execution = screen.getByRole("region", { name: "执行管理" });
    expect(within(execution).getByRole("link", { name: "新建运行" })).toHaveAttribute("href", "/runs/new");
    expect(within(execution).getByRole("link", { name: "运行记录" })).toHaveAttribute("href", "/runs");
    expect(within(execution).getByRole("link", { name: "编排画布" })).toHaveAttribute("aria-current", "page");

    const platform = screen.getByRole("region", { name: "平台底座" });
    expect(within(platform).getByRole("link", { name: "业务资料库" })).toHaveAttribute("href", "/documents");
    expect(within(platform).queryByRole("link", { name: "资源中心" })).not.toBeInTheDocument();
    expect(within(platform).getByRole("link", { name: "智能体" })).toHaveAttribute("href", "/agents");
    expect(within(platform).getByRole("link", { name: "工具" })).toHaveAttribute("href", "/tools");
    expect(within(platform).getByRole("link", { name: "模型" })).toHaveAttribute("href", "/models");
    expect(within(platform).getByRole("link", { name: "策略" })).toHaveAttribute("href", "/policies");

    expect(within(screen.getByRole("region", { name: "系统治理" })).getByRole("link", { name: "审计日志" })).toBeInTheDocument();
    expect(within(screen.getByRole("region", { name: "系统观测" })).getByRole("link", { name: "Temporal（在新标签页打开）" })).toHaveAttribute("target", "_blank");

    await waitFor(() => expect(within(screen.getByRole("link", { name: "待办中心" })).getByText("3")).toBeVisible());
  });
});
