import * as React from "react";
import { cn } from "@/lib/utils";
import { Alert } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

export type ConfigChangeType = "added" | "removed" | "changed";

export type ConfigDiffRow = {
  id: string;
  key: string;
  before?: string;
  after?: string;
  type: ConfigChangeType;
};

export type ConfigDiffProps = {
  rows: ConfigDiffRow[];
  resourceName?: string;
  requiresRestart?: boolean;
  riskLevel?: "low" | "medium" | "high";
  maintenanceWindow?: string;
  onApply?: () => void;
  onCancel?: () => void;
  className?: string;
};

const typeBadge: Record<ConfigChangeType, { label: string; color: "success" | "error" | "warning" }> = {
  added: { label: "新增", color: "success" },
  removed: { label: "删除", color: "error" },
  changed: { label: "变更", color: "warning" },
};

const riskCopy: Record<"low" | "medium" | "high", string> = {
  low: "低风险：变更可在线生效，无需重启实例。",
  medium: "中风险：部分参数需滚动重启，建议在维护窗口执行。",
  high: "高风险：变更可能导致短暂不可用，请确认影响范围并准备回滚方案。",
};

/**
 * 配置 Diff — before/after、风险提示、重启提示。
 * @see references/layout-patterns/paas-resource.md
 */
export function ConfigDiff({
  rows,
  resourceName,
  requiresRestart = false,
  riskLevel = "medium",
  maintenanceWindow,
  onApply,
  onCancel,
  className,
}: ConfigDiffProps) {
  return (
    <section
      className={cn(
        "overflow-hidden rounded-xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-900",
        className,
      )}
      aria-label="配置变更对比"
    >
      <header className="flex flex-wrap items-center justify-between gap-3 border-b border-gray-200 px-4 py-3 dark:border-gray-800">
        <div className="min-w-0">
          <h3 className="text-theme-sm font-semibold text-gray-900 dark:text-white">参数变更预览</h3>
          {resourceName ? (
            <p className="truncate font-mono text-theme-xs text-gray-500">{resourceName}</p>
          ) : null}
        </div>
        {requiresRestart ? (
          <Badge variant="light" color="warning" size="sm">
            需要重启
          </Badge>
        ) : (
          <Badge variant="light" color="success" size="sm">
            在线生效
          </Badge>
        )}
      </header>

      <div className="space-y-3 p-4">
        <Alert variant="warning" title="变更风险提示">
          {riskCopy[riskLevel]}
          {maintenanceWindow ? ` 建议维护窗口：${maintenanceWindow}。` : null}
        </Alert>

        <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-800">
          <table className="w-full min-w-[520px] border-collapse text-theme-xs">
            <thead>
              <tr className="border-b border-gray-200 text-left text-gray-500 dark:border-gray-800">
                <th className="px-3 py-2 font-medium">参数键</th>
                <th className="px-3 py-2 font-medium">变更前</th>
                <th className="px-3 py-2 font-medium">变更后</th>
                <th className="px-3 py-2 font-medium">类型</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => {
                const badge = typeBadge[row.type];
                return (
                  <tr key={row.id} className="border-b border-gray-100 last:border-0 dark:border-white/[0.05]">
                    <td className="max-w-[160px] truncate px-3 py-2 font-mono font-medium text-gray-800 dark:text-white/90">
                      {row.key}
                    </td>
                    <td className="max-w-[140px] truncate px-3 py-2 font-mono text-gray-500">
                      {row.before ?? "—"}
                    </td>
                    <td className="max-w-[140px] truncate px-3 py-2 font-mono text-brand-600 dark:text-brand-400">
                      {row.after ?? "—"}
                    </td>
                    <td className="px-3 py-2">
                      <Badge variant="light" color={badge.color} size="sm">
                        {badge.label}
                      </Badge>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        <div className="flex flex-wrap justify-end gap-2">
          <Button type="button" variant="outline" size="sm" onClick={onCancel}>
            取消
          </Button>
          <Button type="button" size="sm" onClick={onApply}>
            确认应用变更
          </Button>
        </div>
      </div>
    </section>
  );
}
