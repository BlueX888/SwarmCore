import { describe, expect, it } from "vitest";
import { apiErrorMessage } from "./client";

describe("apiErrorMessage", () => {
  it("keeps short plain-text bodies", () => {
    expect(apiErrorMessage(404, "assessment not found", "Not Found")).toBe("assessment not found");
  });

  it("replaces HTML proxy 404 pages with an actionable message", () => {
    const html =
      '<!DOCTYPE html><head> <meta name="viewport" content="width=device-width"/> <style> body { margin: 0; }</style>';
    expect(apiErrorMessage(404, html, "Not Found")).toContain("API 不可用或代理未生效");
  });

  it("falls back when the body is empty", () => {
    expect(apiErrorMessage(502, "", "Bad Gateway")).toBe("Bad Gateway");
  });
});
