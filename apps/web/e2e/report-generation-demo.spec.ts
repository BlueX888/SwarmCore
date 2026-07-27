import { expect, test } from "@playwright/test";

test("report generation demo completes the public-data flow", async ({ page }) => {
  await page.route("**/api/v1/projects/*/approvals", (route) => route.fulfill({ json: { total: 0, items: [] } }));
  await page.route("**/api/v1/projects/*/inputs", (route) => route.fulfill({ json: { total: 0, items: [] } }));

  await page.goto("/business-works/report-generation/demo");
  await expect(page.getByRole("heading", { name: "报告生成智能体" })).toBeVisible();
  await expect(page.getByText("公开测试文件已载入")).toBeVisible();

  await page.getByRole("button", { name: "开始生成七维报告" }).click();
  await expect(page.getByRole("heading", { name: "正在生成后评价报告" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "采购履约后评价报告" })).toBeVisible();

  await expect(page.getByLabel("综合得分 84.55 分")).toBeVisible();
  await expect(page.getByRole("region", { name: "七维评价结果" }).getByRole("heading", { level: 3 })).toHaveCount(7);
  await expect(page.getByRole("button", { name: "下载 JSON" })).toBeEnabled();
});
