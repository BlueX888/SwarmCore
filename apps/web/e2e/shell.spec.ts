import { expect, test } from "@playwright/test";
import type { ProjectOverviewSnapshot, ProjectOverviewWorkSnapshot } from "../src/api/types";
import { demoOverviewPath, demoRunsPath, demoWorkspacePath } from "../src/lib/demo-scope";

test("root redirects into the demo workspace", async ({ page }, testInfo) => {
  await page.route("**/api/v1/projects/*/overview", (route) => route.fulfill({ json: overviewSnapshot() }));
  await page.route("**/api/v1/projects/*/approvals", (route) => route.fulfill({ json: { total: 0, items: [] } }));
  await page.route("**/api/v1/projects/*/inputs", (route) => route.fulfill({ json: { total: 0, items: [] } }));
  await page.goto("/");
  await expect(page).toHaveURL(demoOverviewPath);
  await expect(page.getByRole("heading", { name: "项目工作台", exact: true })).toBeVisible();
  await expect(page.locator("#business-works-heading")).toBeVisible();
  await expect(page.getByRole("heading", { name: "基础与治理" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "最近动态" })).toBeVisible();
  await expect(page.getByRole("link", { name: "业务处理一：开始处理" })).toHaveAttribute("href", "/business-works/business-one/workbench");
  await expect(page.getByRole("heading", { name: "功能导航" })).toHaveCount(0);
  if (testInfo.project.name !== "desktop") await page.getByRole("button", { name: "打开导航" }).click();
  await expect(page.getByRole("link", { name: "工作台", exact: true })).toHaveAttribute("aria-current", "page");
});

test("overview routes exceptions and active work to their professional pages", async ({ page }) => {
  const activeRunId = "00000000-0000-0000-0000-000000000220";
  const snapshot = overviewSnapshot();
  snapshot.counts.documentsReviewRequired = 1;
  snapshot.businessWorks[0].activeRunId = activeRunId;
  await page.route("**/api/v1/projects/*/overview", (route) => route.fulfill({ json: snapshot }));
  await page.route("**/api/v1/projects/*/documents**", (route) => route.fulfill({ json: { total: 0, items: [] } }));
  await page.route("**/api/v1/projects/*/runs/*", (route) => route.fulfill({ json: {
    runId: activeRunId,
    status: "RUNNING",
    input: {},
    output: null,
    outputRef: null,
    snapshotSeq: 0,
    earliestAvailableSeq: 0,
    planHash: "a".repeat(64),
    usage: {},
    taskCounts: {},
    allowedActions: [],
    tasks: [],
  } }));

  await page.goto(demoOverviewPath);
  await page.getByRole("link", { name: /资料需处理/ }).click();
  await expect(page).toHaveURL("/documents?view=failed");

  await page.goto(demoOverviewPath);
  await page.getByRole("link", { name: "业务处理一：查看运行" }).click();
  await expect(page).toHaveURL(`/runs/${activeRunId}`);
});

test("overview business cards use one, two and three responsive columns", async ({ page }) => {
  await page.route("**/api/v1/projects/*/overview", (route) => route.fulfill({ json: overviewSnapshot() }));
  await page.goto(demoOverviewPath);

  for (const [width, columns] of [[390, 1], [1280, 2], [1600, 3]] as const) {
    await page.setViewportSize({ width, height: 900 });
    const actualColumns = await page.evaluate<number>(
      "getComputedStyle(document.querySelector('.overview-business-grid')).gridTemplateColumns.split(' ').length",
    );
    const overflow = await page.evaluate<boolean>(
      "document.documentElement.scrollWidth > document.documentElement.clientWidth",
    );
    expect({ columns: actualColumns, overflow }).toEqual({ columns, overflow: false });
  }
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
  await page.route(/\/api\/v1\/projects\/[^/]+\/strategies\?[^/]*$/, (route) => route.fulfill({ json: { total: 1, items: [{ strategyId, name: "demo", lifecycle: "ACTIVE", createdAt: new Date(0).toISOString(), updatedAt: new Date(0).toISOString(), draftId: "draft", draftRevision: 1, latestVersion: 1 }] } }));
  await page.route(/\/api\/v1\/projects\/[^/]+\/strategies\/[^/]+\/versions$/, (route) => route.fulfill({ json: { total: 1, items: [{ strategyVersionId: versionId, strategyId, version: 1, lifecycle: "PUBLISHED", planHash: "a".repeat(64), schemaVersion: "swarmcore.io/v1", runtimeVersion: "1.0.0", createdAt: new Date(0).toISOString() }] } }));
  await page.route("**/api/v1/projects/*/strategies/*/versions/*", (route) => route.fulfill({ json: { strategyVersionId: versionId, strategyId, version: 1, lifecycle: "PUBLISHED", planHash: "a".repeat(64), schemaVersion: "swarmcore.io/v1", runtimeVersion: "1.0.0", createdAt: new Date(0).toISOString(), spec: {}, normalizedSpec: {}, plan: { input_schema: { type: "object", required: ["topic"], properties: { topic: { type: "string" } } } } } }));
  await page.route("**/api/v1/projects/*/runs", async (route) => {
    if (route.request().method() === "POST") await route.fulfill({ json: { runId: createdRunId, status: "ACCEPTED", commandId: "command", commandStatus: "ACCEPTED" } });
    else await route.fulfill({ json: { total: 0, items: [] } });
  });
  await page.goto("/runs/new");
  await page.getByLabel("策略版本").selectOption(versionId);
  await page.getByRole("textbox", { name: /^主题/ }).fill("acceptance");
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
  await expect(page.getByRole("link", { name: "打开运行详情核对" })).toHaveAttribute("href", `/runs/${runId}`);
});

test("splits the capability center into agent, tool, model and policy pages", async ({ page }) => {
  const runId = "00000000-0000-0000-0000-000000000103";
  await page.route("**/api/v1/projects/*/capability-center", (route) => route.fulfill({ json: capabilityCenter() }));
  await page.route("**/api/v1/projects/*/presets", (route) => route.fulfill({ json: { total: 0, items: [] } }));
  await page.route("**/api/v1/projects/*/capability-runs", (route) => route.fulfill({ status: 202, json: { runId, status: "ACCEPTED", commandId: "command-1", commandStatus: "ACCEPTED", planHash: "a".repeat(64) } }));
  await page.route("**/api/v1/projects/*/runs/*", (route) => route.fulfill({ json: { runId, status: "ACCEPTED", input: {}, output: null, outputRef: null, snapshotSeq: 0, earliestAvailableSeq: 0, planHash: "a".repeat(64), usage: {}, taskCounts: {}, allowedActions: [], tasks: [] } }));
  await page.route("**/api/v1/projects/*/capabilities", (route) => route.fulfill({ json: configurationCatalog() }));
  await page.route("**/api/v1/projects/*/configurations/agent", (route) => route.fulfill({ json: { total: 0, items: [] } }));
  await page.route("**/api/v1/projects/*/rule-sets", (route) => route.fulfill({ status: 201, json: { ruleSetId: "rule-1", draftId: "draft-1", revision: 1, rules: {} } }));
  await page.route("**/api/v1/projects/*/rule-set-drafts/*:validate", (route) => route.fulfill({ json: { valid: true, normalizedRules: {}, preview: null } }));
  await page.route("**/api/v1/projects/*/rule-set-drafts/*:publish", (route) => route.fulfill({ json: { ruleSetId: "rule-1", ruleSetVersionId: "version-1", version: 1, schemaVersion: "schema://contract/checklist-rule@1", contentHash: "abcdef1234567890", rules: {} } }));
  await page.goto("/agents");
  await expect(page.getByRole("heading", { name: "智能体", exact: true })).toBeVisible();
  await expect(page.getByLabel("能力类型")).toHaveCount(0);
  await expect(page.getByRole("button", { name: "编辑 合同文件分类智能体 配置" })).toBeVisible();
  await expect(page.getByRole("button", { name: /受控检索/ })).toHaveCount(0);
  await page.getByRole("button", { name: "编辑 合同文件分类智能体 配置" }).click();
  await expect(page.getByRole("heading", { name: "智能体配置", exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "运行时可用智能体" })).toHaveCount(0);
  await expect(page.getByRole("heading", { name: "已配置智能体" })).toHaveCount(0);
  await expect(page.getByLabel("配置名称")).toHaveValue("contract-document-classifier 项目配置");
  await expect(page.getByLabel("角色与目标")).toHaveValue("contract-document-classifier");
  await expect(page.getByLabel("首选逻辑模型")).toHaveValue("model://general@1");
  await expect(page.getByRole("checkbox", { name: /tool:\/\/document\/read@1/ })).toBeChecked();
  await page.goto("/tools");
  await expect(page.getByRole("heading", { name: "工具", exact: true })).toBeVisible();
  await expect(page.getByRole("group", { name: "按风险分类" })).toBeVisible();
  await expect(page.getByRole("button", { name: /受控检索/ })).toBeVisible();
  await expect(page.getByRole("button", { name: /未接入工具/ })).toHaveCount(0);
  await page.getByRole("checkbox", { name: "显示未就绪" }).check();
  await page.getByRole("button", { name: /未接入工具/ }).click();
  await expect(page.getByText("缺少执行器")).toBeVisible();
  await expect(page.getByRole("button", { name: "立即运行" })).toBeDisabled();
  await page.getByRole("button", { name: "关闭详情" }).click();
  await page.getByRole("button", { name: /受控检索/ }).click();
  await page.getByLabel("检索词").fill("capability e2e");
  await page.getByRole("button", { name: "立即运行" }).click();
  await expect(page).toHaveURL(new RegExp(`/runs/${runId}$`));
  await page.goto("/models");
  await expect(page.getByRole("heading", { name: "模型", exact: true })).toBeVisible();
  await expect(page.getByRole("checkbox", { name: "显示已配置但未就绪" })).toBeVisible();
  await expect(page.getByRole("button", { name: "新建模型" })).toBeVisible();
  await expect(page.getByRole("button", { name: /kimi-k2.5/ })).toBeVisible();
  await expect(page.getByText("通用模型")).toHaveCount(0);
  await page.goto("/policies");
  await expect(page.getByRole("heading", { name: "策略能力", exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: /默认策略/ })).toBeVisible();
  await page.getByRole("button", { name: "新建策略" }).click();
  await expect(page).toHaveURL("/policies/new");
  await page.getByLabel("策略名称").fill("采购资料策略");
  await page.getByLabel("策略用途").fill("采购合同资料校验");
  await page.getByRole("button", { name: "校验并发布" }).click();
  await expect(page.getByRole("status")).toContainText("策略版本 1 已发布");
  await page.goto("/capabilities");
  await expect(page).toHaveURL("/agents");
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
    agents: [
      { id: "inline/agno", runtime: "agno", environments: ["development"], declarationSchema: {} },
      { id: "agent://contract/document-classifier@1", runtime: "registry/agno", environments: ["development"], declarationSchema: {}, role: "contract-document-classifier", instructions: "Classify contract documents from evidence.", model: "model://general@1", tools: ["tool://document/read@1"] },
    ],
    tools: [
      { ref: "tool://search@1", risk: "LOW", inputSchema: { type: "object" }, outputSchema: { type: "object" } },
      { ref: "tool://document/read@1", risk: "LOW", inputSchema: { type: "object" }, outputSchema: { type: "object" } },
    ],
    models: [{ ref: "model://general@1", runtime: "agno", environments: ["development"] }],
    limits: {},
    swarmSpecSchema: {},
  };
}

function overviewSnapshot(): ProjectOverviewSnapshot {
  const makeWork = (workKey: string, name: string, category: "business" | "foundation" | "governance"): ProjectOverviewWorkSnapshot => ({
    workKey,
    name,
    shortName: name,
    category,
    status: "runnable",
    statusLabel: "可运行",
    qualificationStatus: "local_verified",
    qualificationLabel: "本地验证，待生产准入",
    blockers: [],
    readiness: { requiredDocuments: 0, satisfiedDocuments: 0, documentsReady: true, readyToStart: true },
    activeRunId: null,
    latestRun: null,
  });
  return {
    generatedAt: new Date(0).toISOString(),
    counts: { pendingApprovals: 0, pendingInputs: 0, documentsAvailable: 0, documentsReviewRequired: 0, documentsFailed: 0, activeRuns: 0, waitingRuns: 0 },
    businessWorks: [
      makeWork("business-one", "业务处理一", "business"),
      ...Array.from({ length: 6 }, (_, index) => makeWork(`business-${index + 2}`, `业务处理${index + 2}`, "business")),
      makeWork("foundation-one", "基础能力一", "foundation"),
      makeWork("foundation-two", "基础能力二", "foundation"),
      makeWork("governance-one", "调度治理", "governance"),
    ],
    recentRuns: [],
  };
}

function capabilityCenter() {
  const ready = { status: "READY", reasons: [] };
  return {
    registrySnapshot: "registry:e2e",
    items: [
      { ref: "agent://contract/document-classifier@1", kind: "agent", name: "合同分类", description: "识别合同类型。", source: "system", readiness: ready, inputSchema: { type: "object" }, outputSchema: { type: "object" } },
      { ref: "tool://search@1", kind: "tool", name: "受控检索", description: "在已配置的知识源中检索内容。", source: "system", readiness: ready, risk: "LOW", inputSchema: { type: "object", required: ["query"], properties: { query: { type: "string", title: "检索词" } }, additionalProperties: false }, outputSchema: { type: "object" } },
      { ref: "tool://missing@1", kind: "tool", name: "未接入工具", description: "尚无执行器。", source: "system", readiness: { status: "NOT_READY", reasons: [{ code: "EXECUTOR_MISSING", message: "missing" }] }, risk: "LOW", inputSchema: { type: "object" }, outputSchema: { type: "object" } },
      { ref: "model://general@1", kind: "model", name: "通用模型", description: "通用模型路由。", source: "system", readiness: ready, inputSchema: { type: "object" }, outputSchema: { type: "object" } },
      { ref: "model://project/11111111-1111-1111-1111-111111111111@1", kind: "model", name: "kimi-k2.5", description: "项目模型配置 · kimi-k2.5", source: "project", readiness: ready, inputSchema: { type: "object" }, outputSchema: { type: "object" } },
      { ref: "policy://default@1", kind: "policy", name: "默认策略", description: "默认能力治理策略。", source: "system", readiness: ready, inputSchema: { type: "object" }, outputSchema: { type: "object" } },
    ],
  };
}
