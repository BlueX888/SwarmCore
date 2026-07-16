import * as React from "react";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export type DescriptionDiffItem = {
  label: React.ReactNode;
  before: React.ReactNode;
  after: React.ReactNode;
  changed?: boolean;
};

export type DescriptionDiffProps = {
  title?: React.ReactNode;
  description?: React.ReactNode;
  items: DescriptionDiffItem[];
  beforeLabel?: React.ReactNode;
  afterLabel?: React.ReactNode;
  className?: string;
};

/**
 * 变更前后对比描述列表 — 配置变更、审批、回滚场景。
 * @see references/layout-patterns/form-composition.md#对比描述列表
 */
export function DescriptionDiff({
  title = "配置变更对比",
  description,
  items,
  beforeLabel = "变更前",
  afterLabel = "变更后",
  className,
}: DescriptionDiffProps) {
  return (
    <Card className={className}>
      {(title || description) && (
        <CardHeader>
          {title ? <CardTitle>{title}</CardTitle> : null}
          {description ? <CardDescription>{description}</CardDescription> : null}
        </CardHeader>
      )}
      <CardContent className="overflow-x-auto">
        <table className="w-full min-w-[520px] text-left text-theme-sm">
          <thead>
            <tr className="border-b border-gray-200 text-gray-500 dark:border-gray-800 dark:text-gray-400">
              <th className="pb-3 pr-4 font-medium">字段</th>
              <th className="pb-3 pr-4 font-medium">{beforeLabel}</th>
              <th className="pb-3 font-medium">{afterLabel}</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item, index) => {
              const changed = item.changed ?? item.before !== item.after;
              return (
                <tr
                  key={index}
                  className={cn(
                    "border-b border-gray-100 last:border-0 dark:border-gray-800",
                    changed && "bg-warning-50/40 dark:bg-warning-500/5",
                  )}
                >
                  <td className="py-3 pr-4 align-top font-medium text-gray-700 dark:text-gray-300">
                    <div className="flex items-center gap-2">
                      <span>{item.label}</span>
                      {changed ? (
                        <Badge variant="light" color="warning">
                          已变更
                        </Badge>
                      ) : null}
                    </div>
                  </td>
                  <td className="py-3 pr-4 align-top text-gray-600 dark:text-gray-400">
                    {item.before}
                  </td>
                  <td className="py-3 align-top text-gray-800 dark:text-white/90">
                    {item.after}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </CardContent>
    </Card>
  );
}
