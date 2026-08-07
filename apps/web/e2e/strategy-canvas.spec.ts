import { expect, test, type Locator, type Page } from "@playwright/test";

const strategyId = "00000000-0000-0000-0000-000000000020";
const draftId = "00000000-0000-0000-0000-000000000021";
type TestEditorState = {
  positions: Record<string, { x: number; y: number }>;
  viewport: { x: number; y: number; zoom: number };
  agentBindings?: Record<string, { configurationId: string; revision: number; name: string; sourceRef: string }>;
};
type TestSpec = Record<string, unknown> & { spec: Record<string, unknown> & { graph: Record<string, unknown> & { entrypoint: string; nodes: Record<string, Record<string, unknown>> } } };

test("creates a draft from an empty canvas", async ({ page }) => {
  const captured: { body?: { name: string; spec: TestSpec; editorState: TestEditorState } } = {};
  await page.route("**/api/v1/projects/*/capabilities", (route) => route.fulfill({ json: capabilityCatalog() }));
  await page.route("**/api/v1/projects/*/strategies/compile", (route) => route.fulfill({ json: { valid: true, diagnostics: [], plan: { plan_hash: "b".repeat(64) } } }));
  await page.route(/\/api\/v1\/projects\/[^/]+\/strategies(?:\?.*)?$/, async (route) => {
    if (route.request().method() === "POST") {
      captured.body = route.request().postDataJSON() as typeof captured.body;
      await route.fulfill({ status: 201, json: { strategyId, draftId, revision: 1 } });
      return;
    }
    await route.fulfill({ json: { total: 0, items: [] } });
  });
  await page.route("**/api/v1/projects/*/strategies/*/versions", (route) => route.fulfill({ json: { total: 0, items: [] } }));
  await page.route("**/api/v1/projects/*/strategies/*/drafts/*", (route) => route.fulfill({ json: draftSnapshot(1, captured.body?.spec ?? initialSpec(), captured.body?.editorState ?? { positions: {}, viewport: { x: 0, y: 0, zoom: 1 } }) }));

  await page.goto("/canvas");
  await expect(page.getByRole("heading", { name: "编排画布" })).toBeVisible();
  await expect(page.locator(".react-flow__node")).toHaveCount(0);
  await page.getByRole("button", { name: "智能体", exact: true }).click();
  await page.getByRole("button", { name: "校验", exact: true }).click();
  await expect(page.getByRole("status")).toContainText("计划校验通过");
  await page.getByRole("button", { name: "创建草稿", exact: true }).click();
  await expect(page).toHaveURL(new RegExp(`/strategies/${strategyId}$`));
  expect(captured.body).toBeDefined();
  expect(captured.body?.spec.spec.graph.entrypoint).toBe("agent-1");
  expect(captured.body?.editorState.positions["agent-1"]).toBeDefined();
});

test("edits, persists and publishes a Strategy Canvas", async ({ page }, testInfo) => {
  let revision = 1;
  let savedSpec = initialSpec();
  let savedEditorState: TestEditorState = {
    positions: { planner: { x: 80, y: 100 } },
    viewport: { x: 0, y: 0, zoom: 1 },
  };
  let published = false;

  if (testInfo.project.name === "desktop") {
    await page.addInitScript(() => localStorage.setItem("theme", "dark"));
  }

  await page.route("**/api/v1/projects/*/approvals", (route) => route.fulfill({ json: { total: 0, items: [] } }));
  await page.route("**/api/v1/projects/*/inputs", (route) => route.fulfill({ json: { total: 0, items: [] } }));
  await page.route("**/api/v1/projects/*/configurations/agent", (route) => route.fulfill({ json: { total: 0, items: [] } }));
  await page.route("**/api/v1/projects/*/capabilities", (route) => route.fulfill({ json: capabilityCatalog() }));
  await page.route("**/api/v1/projects/*/strategies/compile", (route) => route.fulfill({ json: { valid: true, diagnostics: [], plan: { plan_hash: "a".repeat(64) } } }));
  await page.route(/\/api\/v1\/projects\/[^/]+\/strategies(?:\?.*)?$/, (route) => route.fulfill({ json: { total: 1, items: [{ strategyId, name: "canvas-e2e", lifecycle: "ACTIVE", createdAt: new Date(0).toISOString(), updatedAt: new Date(0).toISOString(), draftId, draftRevision: revision, latestVersion: null }] } }));
  await page.route("**/api/v1/projects/*/strategies/*/versions", (route) => route.fulfill({ json: { total: 0, items: [] } }));
  await page.route("**/api/v1/projects/*/strategies/*/publish", (route) => {
    published = true;
    return route.fulfill({ json: { strategyId, strategyVersionId: "version-1", version: 1, planHash: "a".repeat(64) } });
  });
  await page.route("**/api/v1/projects/*/strategies/*/drafts/*", async (route) => {
    if (route.request().method() === "PUT") {
      const body = route.request().postDataJSON() as { spec: typeof savedSpec; editorState: typeof savedEditorState };
      savedSpec = body.spec;
      savedEditorState = body.editorState;
      revision += 1;
    }
    await route.fulfill({ json: draftSnapshot(revision, savedSpec, savedEditorState), headers: { ETag: `"${revision}"` } });
  });

  await page.goto(`/strategies/${strategyId}`);
  await expect(page.getByTestId("strategy-canvas")).toBeVisible();
  await page.getByRole("button", { name: "并行", exact: true }).click();
  await page.getByRole("button", { name: "外部输入", exact: true }).click();
  await page.getByRole("button", { name: "Fit View" }).click();
  await expect(page.locator('.react-flow__node[data-id="parallel-1"]')).toBeVisible();
  await connect(page, "planner", "parallel-1");
  await connect(page, "parallel-1", "input-1");
  await page.getByRole("button", { name: "汇合", exact: true }).click();
  await expect(page.locator('.react-flow__node[data-id="join-1"]')).toBeVisible();
  await page.keyboard.press("Delete");
  await expect(page.locator('.react-flow__node[data-id="join-1"]')).toHaveCount(0);

  const inputNode = page.locator('.react-flow__node[data-id="input-1"]');
  await page.getByRole("button", { name: "Fit View" }).click();
  await inputNode.scrollIntoViewIfNeeded();
  await inputNode.dragTo(page.getByTestId("strategy-canvas"), { force: true, targetPosition: { x: 700, y: 400 } });
  await page.getByRole("button", { name: "保存草稿" }).click();
  await expect(page.getByRole("status")).toContainText("草稿已保存");
  expect(savedSpec.spec.graph.nodes["input-1"]?.dependsOn).toEqual(["parallel-1"]);
  expect(savedSpec.spec.graph.nodes["parallel-1"]?.branches).toEqual(["input-1"]);
  expect(savedEditorState.positions["input-1"]).toBeDefined();

  await page.reload();
  await expect(page.locator('.react-flow__node[data-id="input-1"]')).toBeVisible();
  await page.getByRole("button", { name: "保存并发布" }).click();
  await expect(page.getByRole("status")).toContainText("已发布版本 1");
  expect(published).toBe(true);
});

async function connect(page: Page, sourceId: string, targetId: string) {
  const source = page.locator(`.react-flow__node[data-id="${sourceId}"] .react-flow__handle.source`);
  const target = page.locator(`.react-flow__node[data-id="${targetId}"] .react-flow__handle.target`);
  await dragHandle(page, source, target);
  await expect(page.locator(".react-flow__edge")).toHaveCount(sourceId === "planner" ? 1 : 2);
}

async function dragHandle(page: Page, source: Locator, target: Locator) {
  await source.click();
  await target.click();
}

function initialSpec(): TestSpec {
  return {
    apiVersion: "swarmcore.io/v1",
    kind: "SwarmStrategy",
    metadata: { name: "canvas-e2e" },
    spec: {
      inputSchema: { type: "object" }, outputSchema: { type: "object" }, defaults: {}, budget: {},
      agents: { planner: { role: "Planner", instructions: "Plan the work." } },
      graph: { entrypoint: "planner", nodes: { planner: { type: "agent", agent: "planner", dependsOn: [] } }, output: {} },
      $defs: {},
    },
  };
}

function draftSnapshot(revision: number, spec: TestSpec, editorState: TestEditorState) {
  return { draftId, strategyId, revision, spec, editorState, diagnostics: [], updatedBy: "e2e", updatedAt: new Date(0).toISOString() };
}

function capabilityCatalog() {
  return {
    schemaVersion: "swarmcore.io/capabilities/v1",
    registrySnapshot: "e2e",
    agents: [],
    tools: [],
    models: [{ ref: "model://general@1", runtime: "agno", environments: ["development"] }],
    limits: {},
    swarmSpecSchema: {},
    nodeTypes: ["agent", "parallel", "join", "reducer", "approval", "input"].map((type) => ({ type, schema: {} })),
  };
}
