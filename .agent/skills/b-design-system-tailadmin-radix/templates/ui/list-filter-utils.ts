import type { ListFilterField } from "@/components/ui/list-filter-types";

export function countActiveFilters(
  fields: ListFilterField[],
  values: Record<string, string | undefined>,
): number {
  return fields.reduce((count, field) => {
    const value = values[field.id];
    if (!value || value.trim() === "") return count;
    if (field.kind === "select" && value === (field.allValue ?? "all")) return count;
    if (field.kind === "checkbox") return value === "true" ? count + 1 : count;
    return count + 1;
  }, 0);
}

export function emptyFilterValues(fields: ListFilterField[]): Record<string, string | undefined> {
  const out: Record<string, string | undefined> = {};
  for (const field of fields) {
    if (field.kind === "select") out[field.id] = field.allValue ?? "all";
    else out[field.id] = undefined;
  }
  return out;
}

export function appliedToDraftValues(
  fields: ListFilterField[],
  applied: Record<string, string | undefined>,
): Record<string, string | undefined> {
  const out = emptyFilterValues(fields);
  for (const field of fields) {
    const value = applied[field.id];
    if (value !== undefined && value !== "") out[field.id] = value;
  }
  return out;
}
