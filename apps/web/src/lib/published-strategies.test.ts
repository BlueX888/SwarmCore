import { beforeEach, describe, expect, it, vi } from "vitest";
import { api } from "@/api/client";
import { listPublishedStrategyOptions } from "./published-strategies";

vi.mock("@/api/client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/api/client")>();
  return {
    ...actual,
    api: {
      ...actual.api,
      listStrategies: vi.fn(),
      listVersions: vi.fn(),
      listPublishedStrategyVersions: vi.fn(),
    },
  };
});

describe("listPublishedStrategyOptions", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("loads published and trusted versions with one project-scoped request", async () => {
    vi.mocked(api.listPublishedStrategyVersions).mockResolvedValue({
      items: Array.from({ length: 6 }, (_, index) => ({
        strategyVersionId: `strategy-${index + 1}-v1`,
        strategyId: `strategy-${index + 1}`,
        strategyName: `策略 ${index + 1}`,
        version: 1,
        lifecycle: "PUBLISHED",
      })),
      total: 6,
    });

    const options = await listPublishedStrategyOptions("tenant", "project");

    expect(api.listPublishedStrategyVersions).toHaveBeenCalledOnce();
    expect(options).toHaveLength(6);
    expect(options[0]?.strategyName).toMatch(/^策略/);
  });
});
