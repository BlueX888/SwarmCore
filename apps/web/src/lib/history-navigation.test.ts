import { describe, expect, it } from "vitest";
import { canGoBackInHistory } from "./history-navigation";

describe("canGoBackInHistory", () => {
  it("returns false for missing or non-positive idx", () => {
    expect(canGoBackInHistory(null)).toBe(false);
    expect(canGoBackInHistory(undefined)).toBe(false);
    expect(canGoBackInHistory({})).toBe(false);
    expect(canGoBackInHistory({ idx: 0 })).toBe(false);
    expect(canGoBackInHistory({ idx: -1 })).toBe(false);
    expect(canGoBackInHistory({ idx: "1" })).toBe(false);
  });

  it("returns true when idx is greater than zero", () => {
    expect(canGoBackInHistory({ idx: 1 })).toBe(true);
    expect(canGoBackInHistory({ idx: 3, key: "abc" })).toBe(true);
  });
});
