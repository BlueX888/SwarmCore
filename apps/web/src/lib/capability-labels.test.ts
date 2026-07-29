import { describe, expect, it } from "vitest";
import {
  capabilityDisplayName,
  capabilityLabel,
  logicalCapabilityRef,
  normalizeCapabilitySearch,
} from "./capability-labels";

describe("capability labels", () => {
  it("strips version suffixes from capability refs", () => {
    expect(logicalCapabilityRef("agent://procurement/clause-evidence-analyst@3")).toBe(
      "agent://procurement/clause-evidence-analyst",
    );
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
