import { describe, expect, it } from "vitest";
import { humanActionErrorMessage } from "./action-center-page";

describe("humanActionErrorMessage", () => {
  it("maps legacy English approval expiry to Chinese guidance", () => {
    expect(humanActionErrorMessage(new Error("approval request expired"))).toContain("建议处理时限");
  });

  it("keeps unknown messages intact", () => {
    expect(humanActionErrorMessage(new Error("network down"))).toBe("network down");
  });
});
