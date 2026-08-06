import { expect, test } from "@playwright/test";

const documentId = "00000000-0000-0000-0000-000000000101";
const document = {
  documentId,
  name: "采购合同.pdf",
  category: "CONTRACT",
  tags: ["采购"],
  status: "AVAILABLE",
  currentVersion: 1,
  updatedAt: "2026-07-31T00:00:00Z",
  current: {
    documentVersionId: "00000000-0000-0000-0000-000000000102",
    blobId: "00000000-0000-0000-0000-000000000103",
    version: 1,
    filename: "采购合同.pdf",
    mediaType: "application/pdf",
    sizeBytes: 2048,
    sha256: "a".repeat(64),
    processingStatus: "AVAILABLE",
    createdAt: "2026-07-31T00:00:00Z",
  },
  businessObjectIds: [],
  businessWorkKeys: ["document-integrity"],
  versions: [],
};

test("opens an external file directly from business work details", async ({ page }) => {
  await page.route("**/api/v1/projects/*/business-works/document-integrity", (route) => route.fulfill({
    json: {
      workKey: "document-integrity",
      name: "文件完整性校验智能体",
      shortName: "文件完整性校验",
      category: "business",
      summary: "检查业务资料完整性。",
      status: "runnable",
      statusLabel: "可运行",
      packName: "contract-integrity",
      packVersionId: "pack-version-1",
      packVersion: "1.0.0",
      enabled: true,
      bindingStatus: "READY",
      blockers: [],
      agents: [],
      tools: [],
      models: [],
      documentRequirements: [{ category: "CONTRACT", required: true }],
      decisionSlots: [],
      functions: [],
      configuration: {},
      workItemType: null,
      caseBased: false,
      boundStrategyVersionId: null,
      boundStrategyName: null,
      boundStrategyVersion: null,
    },
  }));
  await page.route(`**/api/v1/projects/*/documents/${documentId}`, (route) => route.fulfill({
    json: document,
  }));
  await page.route("**/api/v1/projects/*/documents", (route) => route.fulfill({
    json: { items: [document] },
  }));

  await page.goto("/business-works/document-integrity");
  await page.getByRole("link", { name: "采购合同.pdf" }).click();

  await expect(page).toHaveURL(`/documents/${documentId}`);
  const dialog = page.getByRole("dialog");
  await expect(dialog).toBeVisible();
  await expect(dialog).toContainText("采购合同.pdf");
});
