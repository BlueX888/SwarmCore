import { act, cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ReportGenerationDemoPage } from "./report-generation-demo-page";

afterEach(() => {
  cleanup();
  vi.useRealTimers();
});

describe("report generation demo", () => {
  it("loads the public corpus with an explicit demo boundary", () => {
    render(<MemoryRouter><ReportGenerationDemoPage /></MemoryRouter>);

    expect(screen.getByRole("heading", { name: "报告生成智能体" })).toBeVisible();
    expect(screen.getByText("公开测试文件已载入")).toBeVisible();
    expect(screen.getByRole("region", { name: "数据覆盖" })).toBeVisible();
    expect(screen.getAllByText(/31 份分类材料/)).toHaveLength(2);
    expect(screen.getByText(/不冒充公开原件/)).toBeVisible();
    expect(screen.getByText(/结果仅用于验证系统功能/)).toBeVisible();
  });

  it("generates a seven-dimension report and can restart the demo", () => {
    vi.useFakeTimers();
    render(<MemoryRouter><ReportGenerationDemoPage /></MemoryRouter>);

    fireEvent.click(screen.getByRole("button", { name: "开始生成七维报告" }));
    expect(screen.getByRole("heading", { name: "正在生成后评价报告" })).toBeVisible();

    act(() => {
      vi.advanceTimersByTime(1800);
    });

    expect(screen.getByRole("heading", { name: "采购履约后评价报告" })).toBeVisible();
    expect(screen.getByLabelText("综合得分 84.55 分")).toBeVisible();
    const dimensions = screen.getByRole("region", { name: "七维评价结果" });
    expect(within(dimensions).getAllByRole("heading", { level: 3 })).toHaveLength(7);
    expect(within(dimensions).getByRole("heading", { name: "发票合规" })).toBeVisible();
    expect(screen.getByRole("button", { name: "下载 JSON" })).toBeEnabled();
    expect(screen.getByText(/不代表任何公开文件所涉真实项目/)).toBeVisible();

    fireEvent.click(screen.getByRole("button", { name: "重新生成" }));
    expect(screen.getByText("公开测试文件已载入")).toBeVisible();
  });
});
