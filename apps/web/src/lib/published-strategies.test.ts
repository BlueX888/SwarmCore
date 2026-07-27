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
    },
  };
});

describe("listPublishedStrategyOptions", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("skips draft-only strategies and loads published versions in bounded batches", async () => {
    const active = Array.from({ length: 6 }, (_, index) => ({
      strategyId: `strategy-${index + 1}`,
      name: `策略 ${index + 1}`,
      lifecycle: "ACTIVE",
      createdAt: "2026-01-01",
      updatedAt: "2026-01-01",
      draftId: null,
      draftRevision: null,
      latestVersion: index + 1,
    }));
    vi.mocked(api.listStrategies).mockResolvedValue({
      items: [
        ...active,
        {
          strategyId: "draft-only",
          name: "仅草稿",
          lifecycle: "ACTIVE",
          createdAt: "2026-01-01",
          updatedAt: "2026-01-01",
          draftId: "draft-1",
          draftRevision: 1,
          latestVersion: null,
        },
      ],
      total: active.length + 1,
    });
    vi.mocked(api.listVersions).mockImplementation((_tenant, _project, strategyId) => Promise.resolve({
      items: [{
        strategyVersionId: `${strategyId}-v1`,
        strategyId,
        version: 1,
        lifecycle: "PUBLISHED",
        planHash: "a".repeat(64),
        schemaVersion: "swarmcore.io/v1",
        runtimeVersion: "1.1.0",
        createdAt: "2026-01-01",
      }],
      total: 1,
    }));

    const options = await listPublishedStrategyOptions("tenant", "project");

    expect(api.listVersions).toHaveBeenCalledTimes(6);
    expect(api.listVersions).not.toHaveBeenCalledWith("tenant", "project", "draft-only");
    expect(options).toHaveLength(6);
    expect(options[0]?.strategyName).toMatch(/^策略/);
  });
});
