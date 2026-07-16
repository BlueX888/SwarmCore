import { expect, test } from "@playwright/test";
import { DEMO_PROJECT_ID, DEMO_TENANT_ID, demoRunsPath } from "../src/lib/demo-scope";

test("root redirects into the demo workspace", async ({ page }) => {
  await page.route("**/api/v1/projects/*/runs", async (route) => {
    await route.fulfill({ json: { total: 0, items: [] } });
  });
  await page.goto("/");
  await expect(page).toHaveURL(demoRunsPath);
  await expect(page.getByRole("heading", { name: "Runs", exact: true })).toBeVisible();
});

test("unknown routes show a readable fallback", async ({ page }) => {
  await page.goto("/does-not-exist");
  await expect(page.getByRole("heading", { name: "Page not found" })).toBeVisible();
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
  await page.goto(`/t/${DEMO_TENANT_ID}/p/${DEMO_PROJECT_ID}/runs/new`);
  await page.getByLabel("Strategy version").selectOption(versionId);
  await page.getByLabel("JSON input").fill('{"topic":"acceptance"}');
  await page.getByRole("button", { name: "Create Run" }).click();
  await expect(page).toHaveURL(new RegExp(`/runs/${createdRunId}$`));
});

const runId = "00000000-0000-0000-0000-000000000003";

for (const theme of ["light", "dark"] as const) {
  test(`run console remains framed in ${theme} mode`, async ({ page }) => {
    await page.addInitScript((value) => localStorage.setItem("theme", value), theme);
    await page.route("**/api/v1/projects/*/runs", async (route) => {
      await route.fulfill({ json: { total: 1, items: [{ runId, status: "RUNNING", input: {}, output: null, outputRef: null, snapshotSeq: 4, earliestAvailableSeq: 1, planHash: "a".repeat(64), usage: {}, taskCounts: { RUNNING: 1 }, allowedActions: ["cancel"], tasks: [] }] } });
    });
    await page.goto(`/t/${DEMO_TENANT_ID}/p/${DEMO_PROJECT_ID}/runs`);
    await expect(page.getByRole("heading", { name: "Runs", exact: true })).toBeVisible();
    await expect(page.getByText("RUNNING").filter({ visible: true })).toBeVisible();
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
