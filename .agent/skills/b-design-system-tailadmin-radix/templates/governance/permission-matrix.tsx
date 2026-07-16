import * as React from "react";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { AlertTriangle } from "lucide-react";

export type PermissionSource = "inherited" | "custom" | "disabled";

export type PermissionCell = {
  resource: string;
  action: string;
  granted: boolean;
  source: PermissionSource;
  conflict?: boolean;
};

export type PermissionMatrixProps = {
  roles: string[];
  permissions: PermissionCell[];
  selectedRole?: string;
  onRoleChange?: (role: string) => void;
  onToggle?: (resource: string, action: string, granted: boolean) => void;
  readOnly?: boolean;
  className?: string;
};

const sourceMeta: Record<
  PermissionSource,
  { label: string; color: "primary" | "success" | "warning" }
> = {
  inherited: { label: "继承", color: "primary" },
  custom: { label: "自定义", color: "success" },
  disabled: { label: "禁用", color: "warning" },
};

/**
 * RBAC 权限矩阵 — inherited/custom/disabled、批量勾选、冲突提示。
 * @see references/component-styles/governance-template.md
 */
export function PermissionMatrix({
  roles,
  permissions,
  selectedRole,
  onRoleChange,
  onToggle,
  readOnly = false,
  className,
}: PermissionMatrixProps) {
  const actions = [...new Set(permissions.map((p) => p.action))];
  const resources = [...new Set(permissions.map((p) => p.resource))];
  const conflicts = permissions.filter((p) => p.conflict);

  const cellFor = (resource: string, action: string) =>
    permissions.find((p) => p.resource === resource && p.action === action);

  return (
    <section className={cn("space-y-4", className)} aria-label="权限矩阵">
      {roles.length > 1 ? (
        <div
          className="inline-flex flex-wrap gap-2 rounded-lg border border-gray-200 p-1 dark:border-gray-800"
          role="tablist"
          aria-label="角色切换"
        >
          {roles.map((role) => (
            <button
              key={role}
              type="button"
              role="tab"
              aria-selected={selectedRole === role}
              className={cn(
                "rounded-md px-3 py-1.5 text-theme-sm font-medium transition-colors",
                selectedRole === role
                  ? "bg-brand-500 text-white"
                  : "text-gray-600 hover:text-gray-800 dark:text-gray-400 dark:hover:text-white/90",
              )}
              onClick={() => onRoleChange?.(role)}
            >
              {role}
            </button>
          ))}
        </div>
      ) : null}

      {conflicts.length > 0 ? (
        <div
          className="flex items-start gap-2 rounded-lg border border-warning-200 bg-warning-50 px-3 py-2 text-theme-sm text-warning-700 dark:border-warning-500/30 dark:bg-warning-500/10 dark:text-warning-400"
          role="alert"
        >
          <AlertTriangle className="mt-0.5 size-4 shrink-0" aria-hidden />
          <span>
            检测到 {conflicts.length} 项权限冲突：继承策略与自定义策略不一致，请逐项确认。
          </span>
        </div>
      ) : null}

      <div className="overflow-x-auto rounded-xl border border-gray-200 dark:border-gray-800">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="min-w-[140px]">资源</TableHead>
              {actions.map((action) => (
                <TableHead key={action} className="text-center">
                  {action}
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {resources.map((resource) => (
              <TableRow key={resource}>
                <TableCell className="font-medium text-gray-800 dark:text-white/90">
                  {resource}
                </TableCell>
                {actions.map((action) => {
                  const cell = cellFor(resource, action);
                  if (!cell) {
                    return <TableCell key={action} className="text-center">—</TableCell>;
                  }
                  const meta = sourceMeta[cell.source];
                  return (
                    <TableCell key={action} className="text-center">
                      <div className="inline-flex flex-col items-center gap-1">
                        <Checkbox
                          checked={cell.granted}
                          disabled={readOnly || cell.source === "disabled"}
                          aria-label={`${resource} ${action}`}
                          onCheckedChange={(checked) =>
                            onToggle?.(resource, action, checked === true)
                          }
                        />
                        <Badge variant="light" color={meta.color} size="sm">
                          {meta.label}
                        </Badge>
                      </div>
                    </TableCell>
                  );
                })}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </section>
  );
}
