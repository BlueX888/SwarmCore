import { expect, test } from "@playwright/test";

test("legacy capability-pack URLs redirect to the current business-work routes", async ({ page }) => {
  await page.goto("/capability-packs");
  await expect(page).toHaveURL("/overview");

  await page.goto("/capability-packs/contract-integrity/workbench");
  await expect(page).toHaveURL("/business-works/document-integrity/workbench");

  await page.goto("/capability-packs/unknown-pack");
  await expect(page).toHaveURL("/overview");
});
