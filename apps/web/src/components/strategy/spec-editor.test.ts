import { describe, expect, it } from "vitest";
import { parseSpec, serializeSpec } from "./spec-editor";

describe("strategy spec formats", () => {
  const spec = { apiVersion: "swarmcore.io/v1", kind: "SwarmStrategy" };

  it("round trips JSON and YAML", () => {
    expect(parseSpec(serializeSpec(spec, "json"), "json")).toEqual(spec);
    expect(parseSpec(serializeSpec(spec, "yaml"), "yaml")).toEqual(spec);
  });

  it("rejects non-object documents", () => {
    expect(() => parseSpec("[]", "json")).toThrow("策略文档必须是对象");
  });
});
