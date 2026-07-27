/** Central product mapping: pack name ↔ business work key (mirrors backend). */
export const PACK_TO_WORK_KEY: Record<string, string> = {
  "contract-integrity": "document-integrity",
  "contract-post-evaluation": "contract-post-evaluation",
};

export const WORK_KEY_TO_PACK: Record<string, string> = Object.fromEntries(
  Object.entries(PACK_TO_WORK_KEY).map(([pack, work]) => [work, pack]),
);

export function workKeyForPackName(packName: string): string | undefined {
  return PACK_TO_WORK_KEY[packName];
}

export function packNameForWorkKey(workKey: string): string | undefined {
  return WORK_KEY_TO_PACK[workKey];
}

export const LEGACY_CAPABILITY_PACKS_ROUTE = "capability-packs";
