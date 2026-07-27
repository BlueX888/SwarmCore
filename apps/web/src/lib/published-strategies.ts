import { api } from "@/api/client";

export type PublishedStrategyOption = {
  strategyVersionId: string;
  strategyName: string;
  version: number;
};

/** Keep below typical browser per-host connection limits to avoid queue stalls. */
const VERSION_FETCH_CONCURRENCY = 4;

async function mapPool<T, R>(
  items: readonly T[],
  concurrency: number,
  mapper: (item: T) => Promise<R>,
): Promise<R[]> {
  if (!items.length) return [];
  const output: R[] = [];
  let nextIndex = 0;
  const workers = Array.from({ length: Math.min(concurrency, items.length) }, async () => {
    while (nextIndex < items.length) {
      const index = nextIndex;
      nextIndex += 1;
      const item = items[index];
      if (item === undefined) continue;
      output[index] = await mapper(item);
    }
  });
  await Promise.all(workers);
  return output;
}

/** Load published/trusted strategy versions without unbounded parallel fan-out. */
export async function listPublishedStrategyOptions(
  tenantId: string,
  projectId: string,
): Promise<PublishedStrategyOption[]> {
  const listed = await api.listStrategies(tenantId, projectId, 100);
  const candidates = listed.items.filter((strategy) => strategy.latestVersion != null);
  const groups = await mapPool(candidates, VERSION_FETCH_CONCURRENCY, async (strategy) => {
    const versions = await api.listVersions(tenantId, projectId, strategy.strategyId);
    return versions.items
      .filter((version) => version.lifecycle === "PUBLISHED" || version.lifecycle === "TRUSTED")
      .map((version) => ({
        strategyVersionId: version.strategyVersionId,
        strategyName: strategy.name,
        version: version.version,
      }));
  });
  return groups.flat().sort((left, right) => {
    const byName = left.strategyName.localeCompare(right.strategyName);
    return byName !== 0 ? byName : right.version - left.version;
  });
}
