import * as React from "react";
import { cn } from "@/lib/utils";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

export type ComplianceLevel = "low" | "medium" | "high" | "critical";

export type ComplianceAlertProps = {
  level: ComplianceLevel;
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
  dismissible?: boolean;
  onDismiss?: () => void;
  className?: string;
};

const levelMeta: Record<
  ComplianceLevel,
  { label: string; variant: "info" | "warning" | "error"; badgeColor: "primary" | "warning" | "error" }
> = {
  low: { label: "低风险", variant: "info", badgeColor: "primary" },
  medium: { label: "中风险", variant: "warning", badgeColor: "warning" },
  high: { label: "高风险", variant: "warning", badgeColor: "warning" },
  critical: { label: "严重", variant: "error", badgeColor: "error" },
};

/**
 * 合规提示 — 克制说明、风险等级、操作入口；避免营销化大卡片。
 * @see references/component-styles/governance-template.md
 */
export function ComplianceAlert({
  level,
  title,
  description,
  actionLabel,
  onAction,
  dismissible = false,
  onDismiss,
  className,
}: ComplianceAlertProps) {
  const meta = levelMeta[level];

  return (
    <div
      className={cn(
        "rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-800 dark:bg-gray-900",
        className,
      )}
      role="region"
      aria-label="合规提示"
    >
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <Badge variant="light" color={meta.badgeColor} size="sm">
          {meta.label}
        </Badge>
        <span className="text-theme-xs text-gray-500">合规检查</span>
      </div>
      <Alert variant={meta.variant} title={title}>
        {description}
      </Alert>
      {(actionLabel || dismissible) && (
        <div className="mt-4 flex flex-wrap gap-2">
          {actionLabel ? (
            <Button type="button" size="sm" variant={level === "critical" ? "destructive" : "default"} onClick={onAction}>
              {actionLabel}
            </Button>
          ) : null}
          {dismissible ? (
            <Button type="button" size="sm" variant="outline" onClick={onDismiss}>
              已知悉
            </Button>
          ) : null}
        </div>
      )}
    </div>
  );
}
