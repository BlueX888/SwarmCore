import * as React from "react";
import { cn } from "@/lib/utils";
import { Surface } from "@/components/ui/surface";

export type OrgChartNode = {
  id: string;
  label: React.ReactNode;
  subtitle?: React.ReactNode;
  children?: OrgChartNode[];
};

export type OrganizationChartProps = {
  data: OrgChartNode;
  className?: string;
};

function OrgNode({ node }: { node: OrgChartNode }) {
  const hasChildren = (node.children?.length ?? 0) > 0;

  return (
    <li className="flex flex-col items-center">
      <Surface
        variant="outlined"
        elevation={1}
        className="min-w-[140px] px-4 py-3 text-center"
      >
        <div className="text-theme-sm font-medium text-gray-800 dark:text-white/90">
          {node.label}
        </div>
        {node.subtitle ? (
          <div className="mt-0.5 text-theme-xs text-gray-500 dark:text-gray-400">
            {node.subtitle}
          </div>
        ) : null}
      </Surface>
      {hasChildren ? (
        <>
          <div className="h-6 w-px bg-gray-200 dark:bg-gray-700" aria-hidden />
          <ul className="flex gap-6 pt-0">
            {node.children!.map((child) => (
              <OrgNode key={child.id} node={child} />
            ))}
          </ul>
        </>
      ) : null}
    </li>
  );
}

export function OrganizationChart({ data, className }: OrganizationChartProps) {
  return (
    <div className={cn("overflow-x-auto p-4", className)}>
      <ul className="inline-flex min-w-full justify-center">
        <OrgNode node={data} />
      </ul>
    </div>
  );
}
