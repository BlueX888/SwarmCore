import { describe, expect, it } from "vitest";
import {
  capabilityDisplayName,
  capabilityLabel,
  capabilityRefDisplayName,
  logicalCapabilityRef,
  normalizeCapabilitySearch,
} from "./capability-labels";

describe("capability labels", () => {
  it("strips version suffixes from capability refs", () => {
    expect(logicalCapabilityRef("agent://procurement/clause-evidence-analyst@3")).toBe(
      "agent://procurement/clause-evidence-analyst",
    );
  });

  it("derives short display names from capability URIs", () => {
    expect(capabilityRefDisplayName("model://general@1")).toBe("general");
    expect(capabilityRefDisplayName("model://reasoner@1")).toBe("reasoner");
    expect(capabilityRefDisplayName("tool://search@1")).toBe("search");
    expect(capabilityRefDisplayName("tool://document/read@1")).toBe("document/read");
    expect(capabilityRefDisplayName("model://project/11111111-1111-1111-1111-111111111111@1")).toBe(
      "项目模型 · 11111111",
    );
    expect(capabilityRefDisplayName("tool://project/22222222-2222-2222-2222-222222222222@2")).toBe(
      "项目工具 · 22222222",
    );
    expect(capabilityRefDisplayName("not-a-uri")).toBe("not-a-uri");
  });

  it("maps known agent refs to Chinese names", () => {
    expect(capabilityLabel("agent://procurement/clause-evidence-analyst@3")).toBe(
      "招采条款证据分析智能体",
    );
    expect(capabilityDisplayName({
      ref: "agent://procurement/clause-evidence-analyst@3",
      name: "procurement-clause-evidence-analyst",
    })).toBe("招采条款证据分析智能体");
  });

  it("normalizes search queries that are raw capability refs", () => {
    expect(normalizeCapabilitySearch("agent://contract/baseline-analyst@2")).toBe(
      "合同基准分析智能体",
    );
    expect(normalizeCapabilitySearch("条款证据")).toBe("条款证据");
  });

  it("keeps project display names when no mapped label exists", () => {
    expect(capabilityDisplayName({
      ref: "agent://project/abc@1",
      name: "我的调研助手",
    })).toBe("我的调研助手");
  });
});
