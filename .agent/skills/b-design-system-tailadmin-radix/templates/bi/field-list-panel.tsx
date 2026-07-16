import * as React from "react";
import { cn } from "@/lib/utils";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";

export type FieldGroup = "dimension" | "measure" | "time" | "calculated" | "hidden";

export type BiFieldDef = {
  id: string;
  name: string;
  type: string;
  group: FieldGroup;
  hidden?: boolean;
};

export type FieldListPanelProps = {
  fields: BiFieldDef[];
  search?: string;
  onSearchChange?: (value: string) => void;
  onFieldDragStart?: (field: BiFieldDef) => void;
  className?: string;
};

const groupMeta: Record<FieldGroup, { label: string; color: string }> = {
  dimension: { label: "Dimensions", color: "text-brand-500" },
  measure: { label: "Measures", color: "text-success-500" },
  time: { label: "Time", color: "text-warning-500" },
  calculated: { label: "Calculated", color: "text-purple-500" },
  hidden: { label: "Hidden", color: "text-gray-400" },
};

/**
 * BI field browser — grouped dimensions/measures/time for chart builder.
 * @see references/layout-patterns/bi-chart-builder.md
 */
export function FieldListPanel({
  fields,
  search,
  onSearchChange,
  onFieldDragStart,
  className,
}: FieldListPanelProps) {
  const groups = React.useMemo(() => {
    const map = new Map<FieldGroup, BiFieldDef[]>();
    for (const f of fields) {
      if (f.hidden && f.group !== "hidden") continue;
      const g = f.group;
      if (!map.has(g)) map.set(g, []);
      map.get(g)!.push(f);
    }
    return map;
  }, [fields]);

  return (
    <div className={cn("flex flex-col border-r border-gray-200 dark:border-gray-800", className)}>
      <div className="border-b border-gray-200 p-3 dark:border-gray-800">
        <Input
          type="search"
          placeholder="搜索字段..."
          value={search}
          onChange={(e) => onSearchChange?.(e.target.value)}
          aria-label="搜索字段"
        />
      </div>
      <div className="flex-1 overflow-y-auto p-2">
        {Array.from(groups.entries()).map(([group, items]) => (
          <div key={group} className="mb-4">
            <h4 className={cn("px-2 py-1 text-theme-xs font-semibold uppercase", groupMeta[group].color)}>
              {groupMeta[group].label}
            </h4>
            <ul className="space-y-0.5">
              {items.map((field) => (
                <li key={field.id}>
                  <button
                    type="button"
                    draggable
                    onDragStart={() => onFieldDragStart?.(field)}
                    className="flex w-full items-center justify-between gap-2 rounded-lg px-2 py-2 text-left text-theme-sm hover:bg-gray-50 dark:hover:bg-white/[0.03]"
                  >
                    <span className="min-w-0 truncate font-medium text-gray-800 dark:text-white/90">
                      {group === "calculated" ? "ƒ " : ""}
                      {field.name}
                    </span>
                    <Badge variant="light" className="shrink-0 text-theme-xs">
                      {field.type}
                    </Badge>
                  </button>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </div>
  );
}
