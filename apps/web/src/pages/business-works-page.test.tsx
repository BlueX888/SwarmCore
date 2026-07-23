import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { afterEach, describe, expect, it } from "vitest";
import { BUSINESS_WORKS } from "@/lib/business-works";
import { BusinessWorksPage } from "./business-works-page";

function renderPage(path = "/business-works") {
  return render(<MemoryRouter initialEntries={[path]}><Routes>
    <Route path="/business-works" element={<BusinessWorksPage />} />
    <Route path="/business-works/:workKey" element={<BusinessWorksPage />} />
  </Routes></MemoryRouter>);
}

describe("business works page", () => {
  afterEach(cleanup);

  it("lists every planned work as an independent entry", () => {
    renderPage();

    expect(screen.getByRole("heading", { name: "业务工作" })).toBeVisible();
    expect(screen.getByText(String(BUSINESS_WORKS.length))).toBeVisible();
    expect(screen.getAllByText("规划中")).toHaveLength(BUSINESS_WORKS.length);
    for (const work of BUSINESS_WORKS) {
      expect(screen.getByRole("heading", { name: work.name })).toBeVisible();
      expect(screen.getByRole("link", { name: `查看${work.name}的 ${work.functions.length} 项功能` })).toHaveAttribute("href", `/business-works/${work.key}`);
    }
  });

  it("filters by category and searches function descriptions", () => {
    renderPage();

    fireEvent.click(screen.getByRole("button", { name: "调度治理" }));
    expect(screen.getByRole("heading", { name: "智能体调度校准智能体" })).toBeVisible();
    expect(screen.queryByRole("heading", { name: "发票一致性校验智能体" })).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "全部" }));
    fireEvent.change(screen.getByRole("textbox", { name: "搜索业务工作或功能" }), { target: { value: "甘特图" } });
    expect(screen.getByRole("heading", { name: "履约计划与执行采集智能体" })).toBeVisible();
    expect(screen.queryByRole("heading", { name: "文件完整性校验智能体" })).not.toBeInTheDocument();
  });

  it("shows the selected work functions and shared configuration entries", () => {
    renderPage("/business-works/invoice-assurance");

    expect(screen.getByRole("heading", { name: "发票一致性校验智能体" })).toBeVisible();
    expect(screen.getByText("规划中")).toBeVisible();
    const functions = screen.getByRole("region", { name: "工作功能" });
    expect(within(functions).getByRole("heading", { name: /发票信息识别/ })).toBeVisible();
    expect(within(functions).getByRole("heading", { name: /付款前置条件/ })).toBeVisible();
    expect(screen.getByRole("link", { name: "编排此工作" })).toHaveAttribute("href", "/canvas");
    expect(screen.getByRole("link", { name: "配置 Agent" })).toHaveAttribute("href", "/agents/configure");
    expect(screen.getByRole("link", { name: "准备业务资料" })).toHaveAttribute("href", "/documents");
  });
});
