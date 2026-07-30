import { describe, expect, it } from "vitest";
import { documentBindingKeys } from "./business-works";

describe("documentBindingKeys", () => {
  it("lets report generation reuse contract post-evaluation documents", () => {
    expect(documentBindingKeys("report-generation", "contract-post-evaluation-case")).toEqual(
      expect.arrayContaining([
        "report-generation",
        "contract-post-evaluation",
        "contract-post-evaluation-case",
      ]),
    );
  });
});
