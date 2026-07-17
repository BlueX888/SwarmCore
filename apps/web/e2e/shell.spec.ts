import { expect, test } from "@playwright/test";
import { demoOverviewPath, demoRunsPath, demoWorkspacePath } from "../src/lib/demo-scope";

test("root redirects into the demo workspace", async ({ page }, testInfo) => {
  await page.route("**/api/v1/projects/*/runs", (route) => route.fulfill({ json: { total: 0, items: [] } }));
  await page.route("**/api/v1/projects/*/strategies", (route) => route.fulfill({ json: { total: 0, items: [] } }));
  await page.route("**/api/v1/projects/*/approvals", (route) => route.fulfill({ json: { total: 0, items: [] } }));
  await page.route("**/api/v1/projects/*/inputs", (route) => route.fulfill({ json: { total: 0, items: [] } }));
  await page.route("**/api/v1/projects/*/capabilities", (route) => route.fulfill({ json: configurationCatalog() }));
  await page.goto("/");
  await expect(page).toHaveURL(demoOverviewPath);
  await expect(page.getByRole("heading", { name: "工作台", exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "功能导航" })).toBeVisible();
  if (testInfo.project.name !== "desktop") await page.getByRole("button", { name: "打开导航" }).click();
  await expect(page.getByRole("link", { name: "工作台", exact: true })).toHaveAttribute("aria-current", "page");
});

test("legacy demo workspace URLs redirect to the short path", async ({ page }) => {
  await page.route("**/api/v1/projects/*/runs", (route) => route.fulfill({ json: { total: 0, items: [] } }));
  await page.goto(`${demoWorkspacePath}/runs`);
  await expect(page).toHaveURL(demoRunsPath);
});

test("explicit workspace URLs keep their tenant and project scope", async ({ page }) => {
  const tenantId = "10000000-0000-0000-0000-000000000001";
  const projectId = "10000000-0000-0000-0000-000000000002";
  const request = page.waitForRequest(`**/api/v1/projects/${projectId}/runs`);
  await page.route("**/api/v1/projects/*/runs", (route) => route.fulfill({ json: { total: 0, items: [] } }));
  await page.goto(`/t/${tenantId}/p/${projectId}/runs`);
  await expect(page).toHaveURL(`/t/${tenantId}/p/${projectId}/runs`);
  expect((await request).headers()["x-tenant-id"]).toBe(tenantId);
});

test("unknown routes show a readable fallback", async ({ page }) => {
  await page.goto("/does-not-exist");
  await expect(page.getByRole("heading", { name: "页面不存在" })).toBeVisible();
});

test("creates a run from a published strategy version", async ({ page }) => {
  const strategyId = "00000000-0000-0000-0000-000000000010";
  const versionId = "00000000-0000-0000-0000-000000000011";
  const createdRunId = "00000000-0000-0000-0000-000000000012";
  await page.route("**/api/v1/projects/*/strategies", (route) => route.fulfill({ json: { total: 1, items: [{ strategyId, name: "demo", lifecycle: "ACTIVE", createdAt: new Date(0).toISOString(), updatedAt: new Date(0).toISOString(), draftId: "draft", draftRevision: 1, latestVersion: 1 }] } }));
  await page.route("**/api/v1/projects/*/strategies/*/versions", (route) => route.fulfill({ json: { total: 1, items: [{ strategyVersionId: versionId, strategyId, version: 1, lifecycle: "PUBLISHED", planHash: "a".repeat(64), schemaVersion: "swarmcore.io/v1", runtimeVersion: "1.0.0", createdAt: new Date(0).toISOString() }] } }));
  await page.route("**/api/v1/projects/*/strategies/*/versions/*", (route) => route.fulfill({ json: { strategyVersionId: versionId, strategyId, version: 1, lifecycle: "PUBLISHED", planHash: "a".repeat(64), schemaVersion: "swarmcore.io/v1", runtimeVersion: "1.0.0", createdAt: new Date(0).toISOString(), spec: {}, normalizedSpec: {}, plan: { input_schema: { type: "object", required: ["topic"], properties: { topic: { type: "string" } } } } } }));
  await page.route("**/api/v1/projects/*/runs", async (route) => {
    if (route.request().method() === "POST") await route.fulfill({ json: { runId: createdRunId, status: "ACCEPTED", commandId: "command", commandStatus: "ACCEPTED" } });
    else await route.fulfill({ json: { total: 0, items: [] } });
  });
  await page.goto("/runs/new");
  await page.getByLabel("策略版本").selectOption(versionId);
  await page.getByLabel(/topic/).fill("acceptance");
  await page.getByRole("button", { name: "创建运行" }).click();
  await expect(page).toHaveURL(new RegExp(`/runs/${createdRunId}$`));
});

test("opens pending human work from the action inbox", async ({ page }) => {
  const runId = "00000000-0000-0000-0000-000000000090";
  await page.route("**/api/v1/projects/*/approvals", (route) => route.fulfill({ json: { total: 1, items: [{ approvalId: "approval-1", runId, nodeKey: "review", prompt: "Approve release?", inputSchema: { type: "object", properties: {} }, status: "PENDING", allowedActions: ["approve", "reject"], requestedBy: "worker", handledBy: null, createdAt: new Date(0).toISOString(), handledAt: null }] } }));
  await page.route("**/api/v1/projects/*/inputs", (route) => route.fulfill({ json: { total: 0, items: [] } }));
  await page.goto("/actions");
  await expect(page.getByRole("heading", { name: "待办中心" })).toBeVisible();
  await expect(page.getByText("Approve release?")).toBeVisible();
  await expect(page.getByRole("link", { name: "打开 review 所在运行" })).toHaveAttribute("href", `/runs/${runId}`);
});

test("opens agent, tool and model configuration from dedicated routes", async ({ page }) => {
  const savedByKind: Record<string, Array<Record<string, unknown>>> = {
    agent: [],
    tool: [],
    model: [{ configurationId: "00000000-0000-0000-0000-000000000101", kind: "model", name: "生产模型", sourceRef: "model://general@1", configuration: { spec: { defaults: { model: "model://general@1" } } }, revision: 1, createdBy: "e2e", updatedBy: "e2e", createdAt: new Date(0).toISOString(), updatedAt: new Date(0).toISOString() }],
  };
  await page.route("**/api/v1/projects/*/capabilities", (route) => route.fulfill({ json: configurationCatalog() }));
  await page.route("**/api/v1/projects/*/configurations/**", async (route) => {
    const parts = new URL(route.request().url()).pathname.split("/");
    const kind = parts[parts.indexOf("configurations") + 1] ?? "model";
    const savedConfigurations = savedByKind[kind] ?? [];
    if (route.request().method() === "POST") {
      const body = route.request().postDataJSON() as Record<string, unknown>;
      const saved = { ...body, configurationId: "00000000-0000-0000-0000-000000000102", kind, revision: 1, createdBy: "e2e", updatedBy: "e2e", createdAt: new Date(0).toISOString(), updatedAt: new Date(0).toISOString() };
      savedConfigurations.push(saved);
      await route.fulfill({ status: 201, json: saved });
    } else if (route.request().method() === "PUT") {
      const body = route.request().postDataJSON() as Record<string, unknown>;
      const saved = { ...savedConfigurations[0], ...body, revision: 2, updatedAt: new Date().toISOString() };
      savedConfigurations[0] = saved;
      await route.fulfill({ json: saved });
    } else if (route.request().method() === "DELETE") {
      savedConfigurations.length = 0;
      await route.fulfill({ status: 204, body: "" });
    } else {
      await route.fulfill({ json: { total: savedConfigurations.length, items: savedConfigurations } });
    }
  });
  await page.goto("/agents");
  await expect(page.getByRole("heading", { name: "智能体配置", exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "已配置智能体", exact: true })).toBeVisible();
  await expect(page.getByLabel("智能体节点配置预览")).toHaveCount(0);
  await page.getByRole("button", { name: "新建智能体配置" }).click();
  await expect(page.getByLabel("智能体节点配置预览")).toContainText("执行助手");
  await page.goto("/tools");
  await expect(page.getByRole("heading", { name: "工具配置", exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "已配置工具", exact: true })).toBeVisible();
  await expect(page.getByLabel("工具节点配置预览")).toHaveCount(0);
  await page.getByRole("button", { name: "新建工具配置" }).click();
  await expect(page.getByLabel("工具节点配置预览")).toContainText("tool://search@1");
  await page.goto("/models");
  await expect(page.getByRole("heading", { name: "模型配置", exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "已配置模型", exact: true })).toBeVisible();
  await expect(page.getByLabel("策略默认模型配置预览")).toHaveCount(0);
  await page.getByRole("button", { name: "打开：生产模型" }).click();
  await expect(page.getByLabel("策略默认模型配置预览")).toContainText("model://general@1");
  await page.getByLabel("配置名称").fill("生产模型（更新）");
  await page.getByRole("button", { name: "保存修改" }).click();
  await expect(page.getByText("“生产模型（更新）”的修改已保存。", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "返回已配置模型" }).click();
  await expect(page.getByRole("button", { name: "打开：生产模型（更新）" })).toBeVisible();
  await expect(page.getByText("版本 2", { exact: false })).toBeVisible();
});

const runId = "00000000-0000-0000-0000-000000000003";

for (const theme of ["light", "dark"] as const) {
  test(`run console remains framed in ${theme} mode`, async ({ page }) => {
    await page.addInitScript((value) => localStorage.setItem("theme", value), theme);
    await page.route("**/api/v1/projects/*/runs", async (route) => {
      await route.fulfill({ json: { total: 1, items: [{ runId, status: "RUNNING", input: {}, output: null, outputRef: null, snapshotSeq: 4, earliestAvailableSeq: 1, planHash: "a".repeat(64), usage: {}, taskCounts: { RUNNING: 1 }, allowedActions: ["cancel"], tasks: [] }] } });
    });
    await page.goto("/runs");
    await expect(page.getByRole("heading", { name: "运行记录", exact: true })).toBeVisible();
    await expect(page.getByText("运行中").filter({ visible: true })).toBeVisible();
    if (theme === "dark") {
      await expect(page.locator("html")).toHaveClass(/dark/);
    } else {
      await expect(page.locator("html")).not.toHaveClass(/dark/);
    }
    const overflow = await page.evaluate<boolean>(
      "window.scrollTo(10000, 0); window.scrollX > 0",
    );
    expect(overflow).toBe(false);
    await expect(page).toHaveScreenshot(`runs-${theme}.png`, {
      animations: "disabled",
      fullPage: true,
    });
  });
}

function configurationCatalog() {
  return {
    schemaVersion: "swarmcore.io/capabilities/v1",
    registrySnapshot: "registry:e2e",
    nodeTypes: [],
    agents: [{ id: "inline/agno", runtime: "agno", environments: ["development"], declarationSchema: {} }],
    tools: [{ ref: "tool://search@1", risk: "LOW", inputSchema: { type: "object" }, outputSchema: { type: "object" } }],
    models: [{ ref: "model://general@1", runtime: "agno", environments: ["development"] }],
    limits: {},
    swarmSpecSchema: {},
  };
}
