/**
 * Shared deep-merge for third-party options objects (Chart, FullCalendar, Swiper, Maps).
 * Shallow spread loses nested keys like chart.toolbar or navigation.nextEl.
 */

function isPlainObject(value: unknown): value is Record<string, unknown> {
  return (
    value !== null &&
    typeof value === "object" &&
    !Array.isArray(value)
  );
}

/** Deep merge plain objects; arrays and primitives are replaced by override. */
export function deepMergeOptions<T extends Record<string, unknown>>(
  base: T,
  overrides?: Partial<T> & Record<string, unknown>
): T & Record<string, unknown> {
  if (!overrides) {
    return { ...base };
  }

  const result = { ...base } as T & Record<string, unknown>;

  for (const key of Object.keys(overrides)) {
    const overrideVal = overrides[key];
    const baseVal = result[key];

    if (isPlainObject(baseVal) && isPlainObject(overrideVal)) {
      (result as Record<string, unknown>)[key] = deepMergeOptions(baseVal, overrideVal);
    } else if (overrideVal !== undefined) {
      (result as Record<string, unknown>)[key] = overrideVal;
    }
  }

  return result;
}
