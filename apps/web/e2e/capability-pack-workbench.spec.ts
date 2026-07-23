import { expect, test } from "@playwright/test";

test("runs an enabled capability pack from its workbench", async ({ page }) => {
  const runId = "00000000-0000-0000-0000-000000000501";
  let submittedPayload: Record<string, unknown> | undefined;
  await page.route("**/api/v1/projects/*/approvals", (route) => route.fulfill({ json: { total: 0, items: [] } }));
  await page.route("**/api/v1/projects/*/inputs", (route) => route.fulfill({ json: { total: 0, items: [] } }));
  await page.route("**/api/v1/projects/*/capability-packs", async (route) => {
    if (route.request().method() !== "GET") return route.fallback();
    await route.fulfill({ json: { items: [{
      packId: "pack-1", name: "contract-integrity", versionId: "version-1", version: "1.1.0", contentHash: "a".repeat(64),
      manifest: { spec: { workItemType: "contract-case", agents: [], tools: [] } }, enabled: true, bindingStatus: "ENABLED", configuration: {}, blockers: [],
    }] } });
  });
  await page.route("**/api/v1/projects/*/work-items", async (route) => {
    submittedPayload = (await route.request().postDataJSON()) as Record<string, unknown>;
    await route.fulfill({ status: 201, json: { workItemId: "item-1", workItemType: "contract-case", status: "DRAFT", revisionId: "revision-1", revision: 1 } });
  });
  await page.route("**/api/v1/projects/*/work-items/*:execute", (route) => route.fulfill({ status: 202, json: {
    evaluationId: "evaluation-1", workItemId: "item-1", workItemRevisionId: "revision-1", runId, status: "RUNNING", result: null,
    capabilityPackVersionId: "version-1", ruleSetVersionId: null, planHash: "a".repeat(64), attachmentManifestHash: "b".repeat(64), registrySnapshot: {}, createdAt: new Date(0).toISOString(),
  } }));
  await page.route("**/api/v1/projects/*/runs/*", (route) => route.fulfill({ json: {
    runId, status: "RUNNING", input: {}, output: null, outputRef: null, snapshotSeq: 0, earliestAvailableSeq: 0,
    planHash: "a".repeat(64), usage: {}, taskCounts: {}, allowedActions: [], tasks: [],
  } }));
  await page.route("**/api/v1/projects/*/runs/*/event-history**", (route) => route.fulfill({ json: { items: [], nextAfter: 0 } }));

  await page.goto("/capability-packs");
  await expect(page.getByText("已启用")).toBeVisible();
  await page.getByRole("link", { name: "进入工作台" }).click();
  await expect(page.getByRole("heading", { name: "contract-integrity 工作台" })).toBeVisible();
  await page.getByRole("button", { name: "开始运行" }).click();

  await expect(page).toHaveURL(new RegExp(`/runs/${runId}$`));
  expect(submittedPayload).toMatchObject({ workItemType: "contract-case", payload: { title: "采购合同检查", contractType: "purchase" } });
});
