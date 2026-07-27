import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import * as ReactRouter from "react-router";
import { MemoryRouter } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { api } from "@/api/client";
import { ThemeProvider } from "@/context/theme-context";
import { BUSINESS_WORKS } from "@/lib/business-works";
import { AppShell, Navigation } from "./app-shell";

vi.mock("@/api/client", () => ({
  api: {
    listApprovals: vi.fn(),
    listInputs: vi.fn(),
    temporalUiUrl: "http://localhost:8088",
    phoenixUrl: "http://localhost:6006",
  },
}));

function stubHistoryIdx(idx: number) {
  Object.defineProperty(window.history, "state", {
    configurable: true,
    value: { idx },
  });
}

afterEach(() => {
  cleanup();
  stubHistoryIdx(0);
  vi.restoreAllMocks();
});

function renderAppShell(idx: number) {
  stubHistoryIdx(idx);
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <ThemeProvider>
      <QueryClientProvider client={client}>
        <MemoryRouter initialEntries={["/overview"]}>
          <AppShell />
        </MemoryRouter>
      </QueryClientProvider>
    </ThemeProvider>,
  );
}

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
    expect(within(business).getByRole("link", { name: "合同后评价" })).toHaveAttribute("href", "/business-works/contract-post-evaluation");
    expect(within(business).queryByRole("link", { name: "业务工作项" })).not.toBeInTheDocument();
    expect(within(business).queryByRole("link", { name: "规则集" })).not.toBeInTheDocument();

    const execution = screen.getByRole("region", { name: "执行管理" });
    expect(within(execution).getByRole("link", { name: "新建运行" })).toHaveAttribute("href", "/runs/new");
    expect(within(execution).getByRole("link", { name: "运行记录" })).toHaveAttribute("href", "/runs");
    expect(within(execution).getByRole("link", { name: "编排画布" })).toHaveAttribute("aria-current", "page");
    expect(within(execution).queryByRole("link", { name: "策略管理" })).not.toBeInTheDocument();

    const platform = screen.getByRole("region", { name: "平台底座" });
    expect(within(platform).getByRole("link", { name: "业务资料库" })).toHaveAttribute("href", "/documents");
    expect(within(platform).queryByRole("link", { name: "资源中心" })).not.toBeInTheDocument();
    expect(within(platform).getByRole("link", { name: "智能体" })).toHaveAttribute("href", "/agents");
    expect(within(platform).getByRole("link", { name: "工具" })).toHaveAttribute("href", "/tools");
    expect(within(platform).getByRole("link", { name: "模型" })).toHaveAttribute("href", "/models");
    expect(within(platform).getByRole("link", { name: "策略管理" })).toHaveAttribute("href", "/strategies");
    expect(within(platform).getByRole("link", { name: "策略能力" })).toHaveAttribute("href", "/policies");
    expect(within(platform).queryByRole("link", { name: /^策略$/ })).not.toBeInTheDocument();

    const platformLabels = within(platform).getAllByRole("link").map((link) => link.getAttribute("aria-label"));
    expect(platformLabels.indexOf("策略管理")).toBeLessThan(platformLabels.indexOf("策略能力"));

    expect(within(screen.getByRole("region", { name: "系统治理" })).getByRole("link", { name: "审计日志" })).toBeInTheDocument();
    expect(within(screen.getByRole("region", { name: "系统观测" })).getByRole("link", { name: "Temporal（在新标签页打开）" })).toHaveAttribute("target", "_blank");

    await waitFor(() => expect(within(screen.getByRole("link", { name: "待办中心" })).getByText("3")).toBeVisible());
  });

  it("activates 策略管理 and 策略能力 independently under 平台底座", () => {
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    const { unmount } = render(<QueryClientProvider client={client}><MemoryRouter initialEntries={["/strategies"]}><Navigation /></MemoryRouter></QueryClientProvider>);

    const platform = screen.getByRole("region", { name: "平台底座" });
    expect(within(platform).getByRole("link", { name: "策略管理" })).toHaveAttribute("aria-current", "page");
    expect(within(platform).getByRole("link", { name: "策略能力" })).not.toHaveAttribute("aria-current");
    expect(within(screen.getByRole("region", { name: "执行管理" })).queryByRole("link", { name: "策略管理" })).not.toBeInTheDocument();
    unmount();

    render(<QueryClientProvider client={client}><MemoryRouter initialEntries={["/policies"]}><Navigation /></MemoryRouter></QueryClientProvider>);
    const platformOnPolicies = screen.getByRole("region", { name: "平台底座" });
    expect(within(platformOnPolicies).getByRole("link", { name: "策略能力" })).toHaveAttribute("aria-current", "page");
    expect(within(platformOnPolicies).getByRole("link", { name: "策略管理" })).not.toHaveAttribute("aria-current");
  });
});

describe("AppShell history back button", () => {
  beforeEach(() => {
    vi.mocked(api.listApprovals).mockResolvedValue({ items: [], total: 0 });
    vi.mocked(api.listInputs).mockResolvedValue({ items: [], total: 0 });
  });

  it("renders a disabled history back button when there is no prior history", () => {
    renderAppShell(0);
    expect(screen.getByRole("button", { name: "返回上一页" })).toBeDisabled();
  });

  it("calls navigate(-1) when the history back button is clicked with prior history", () => {
    const navigate = vi.fn();
    vi.spyOn(ReactRouter, "useNavigate").mockReturnValue(navigate);
    renderAppShell(1);
    const back = screen.getByRole("button", { name: "返回上一页" });
    expect(back).toBeEnabled();
    fireEvent.click(back);
    expect(navigate).toHaveBeenCalledWith(-1);
  });
});
