import { describe, expect, it } from "vitest";
import { previewMissing } from "./rule-sets-page";

describe("rule set sample preview", () => {
  it("returns deterministic missing document types", () => {
    const requirements = [
      { key: "contract", documentType: "contract", mediaTypes: "application/pdf", required: true, severity: "HIGH" },
      { key: "authorization", documentType: "authorization", mediaTypes: "application/pdf", required: true, severity: "HIGH" },
      { key: "optional", documentType: "note", mediaTypes: "text/plain", required: false, severity: "LOW" },
    ];
    expect(previewMissing(requirements, ["contract"])).toEqual(["authorization"]);
    expect(previewMissing(requirements, ["contract", "authorization"])).toEqual([]);
  });
});
