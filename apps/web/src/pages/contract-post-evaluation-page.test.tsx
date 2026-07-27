import { describe, expect, it } from "vitest";

// Compatibility shim: configuration lives on BusinessWorkSettingsPage.
describe("contract-post-evaluation configuration redirect", () => {
  it("keeps the legacy export name", async () => {
    const module = await import("./contract-post-evaluation-page");
    expect(module.ContractPostEvaluationPage).toBeTypeOf("function");
    expect(module.CapabilityPackConfigurationPage).toBe(module.ContractPostEvaluationPage);
  });
});
