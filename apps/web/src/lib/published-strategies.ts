import { api } from "@/api/client";

export type PublishedStrategyOption = {
  strategyVersionId: string;
  strategyName: string;
  version: number;
};

/** Load all published/trusted strategy versions with one project-scoped request. */
export async function listPublishedStrategyOptions(
  tenantId: string,
  projectId: string,
): Promise<PublishedStrategyOption[]> {
  const listed = await api.listPublishedStrategyVersions(tenantId, projectId);
  return listed.items.map((version) => ({
    strategyVersionId: version.strategyVersionId,
    strategyName: version.strategyName,
    version: version.version,
  })).sort((left, right) => {
    const byName = left.strategyName.localeCompare(right.strategyName);
    return byName !== 0 ? byName : right.version - left.version;
  });
}
