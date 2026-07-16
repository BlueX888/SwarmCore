import { describe, expect, it } from "vitest";
import { statusColor } from "./status-badge";

describe("statusColor", () => {
  it("uses stable semantic colors", () => {
    expect(statusColor("SUCCEEDED")).toBe("success");
    expect(statusColor("FAILED")).toBe("error");
    expect(statusColor("RUNNING")).toBe("primary");
  });
});
