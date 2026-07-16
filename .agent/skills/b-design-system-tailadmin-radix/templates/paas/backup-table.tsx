import * as React from "react";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { RotateCcw } from "lucide-react";

export type BackupStatus = "available" | "expired" | "restoring" | "failed";

export type BackupRow = {
  id: string;
  name: string;
  createdAt: string;
  size: string;
  retention?: string;
  status: BackupStatus;
};

export type BackupTableProps = {
  backups: BackupRow[];
  resourceName?: string;
  onRestore?: (id: string) => void;
  className?: string;
};

const statusBadge: Record<
  BackupStatus,
  { label: string; color: "success" | "warning" | "error" | "primary" }
> = {
  available: { label: "可用", color: "success" },
  expired: { label: "已过期", color: "warning" },
  restoring: { label: "恢复中", color: "primary" },
  failed: { label: "失败", color: "error" },
};

export type RestoreConfirmDialogProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  backupName: string;
  resourceName: string;
  namespace?: string;
  onConfirm?: () => void;
};

/**
 * 备份恢复确认 — 目标资源、命名空间、二次确认。
 */
export function RestoreConfirmDialog({
  open,
  onOpenChange,
  backupName,
  resourceName,
  namespace,
  onConfirm,
}: RestoreConfirmDialogProps) {
  const [confirmText, setConfirmText] = React.useState("");

  React.useEffect(() => {
    if (!open) setConfirmText("");
  }, [open]);

  if (!open) return null;

  const required = resourceName;
  const canConfirm = confirmText === required;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-gray-900/50 p-4 backdrop-blur-sm">
      <div
        role="dialog"
        aria-modal="true"
        className="w-full max-w-lg rounded-2xl border border-error-200 bg-white p-6 shadow-xl dark:border-error-500/30 dark:bg-gray-900"
      >
        <h4 className="text-base font-semibold text-error-700 dark:text-error-400">确认恢复备份</h4>
        <p className="mt-2 text-theme-sm text-gray-600 dark:text-gray-400">
          将把 <strong>{backupName}</strong> 恢复到目标实例。当前数据将被覆盖，此操作不可撤销。
        </p>
        <dl className="mt-4 grid grid-cols-2 gap-3 rounded-lg bg-gray-50 p-3 text-theme-sm dark:bg-white/[0.03]">
          <div>
            <dt className="text-theme-xs text-gray-500">目标资源</dt>
            <dd className="font-mono font-medium">{resourceName}</dd>
          </div>
          <div>
            <dt className="text-theme-xs text-gray-500">命名空间</dt>
            <dd className="font-mono font-medium">{namespace ?? "default"}</dd>
          </div>
        </dl>
        <div className="mt-4 space-y-2">
          <label className="text-theme-xs font-medium text-gray-700 dark:text-gray-300">
            输入 <code className="rounded bg-gray-100 px-1 dark:bg-gray-800">{required}</code> 以确认恢复
          </label>
          <Input
            value={confirmText}
            onChange={(e) => setConfirmText(e.target.value)}
            placeholder={required}
            className="font-mono"
          />
        </div>
        <div className="mt-6 flex justify-end gap-2">
          <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button
            type="button"
            variant="destructive"
            disabled={!canConfirm}
            onClick={() => {
              onConfirm?.();
              onOpenChange(false);
            }}
          >
            确认恢复
          </Button>
        </div>
      </div>
    </div>
  );
}

/**
 * 备份列表 — available/expired/restoring/failed + 恢复确认。
 * @see references/layout-patterns/paas-resource.md
 */
export function BackupTable({ backups, resourceName, onRestore, className }: BackupTableProps) {
  const [pending, setPending] = React.useState<BackupRow | null>(null);

  return (
    <>
      <div className={cn("overflow-hidden rounded-xl border border-gray-200 dark:border-gray-800", className)}>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>备份点</TableHead>
              <TableHead>创建时间</TableHead>
              <TableHead>大小</TableHead>
              <TableHead>保留策略</TableHead>
              <TableHead>状态</TableHead>
              <TableHead className="text-right">操作</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {backups.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="py-8 text-center text-theme-sm text-gray-500">
                  暂无可用备份点，请先创建手动或自动备份策略。
                </TableCell>
              </TableRow>
            ) : (
              backups.map((row) => {
                const badge = statusBadge[row.status];
                const canRestore = row.status === "available";

                return (
                  <TableRow key={row.id}>
                    <TableCell className="max-w-[160px] truncate font-medium">{row.name}</TableCell>
                    <TableCell className="tabular-nums text-theme-xs text-gray-500">{row.createdAt}</TableCell>
                    <TableCell className="tabular-nums">{row.size}</TableCell>
                    <TableCell className="text-theme-xs text-gray-500">{row.retention ?? "—"}</TableCell>
                    <TableCell>
                      <Badge variant="light" color={badge.color} size="sm">
                        {badge.label}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <Button
                        type="button"
                        size="sm"
                        variant="outline"
                        className="h-7 gap-1 px-2"
                        disabled={!canRestore}
                        onClick={() => setPending(row)}
                      >
                        <RotateCcw className="size-3" />
                        恢复
                      </Button>
                    </TableCell>
                  </TableRow>
                );
              })
            )}
          </TableBody>
        </Table>
      </div>

      <RestoreConfirmDialog
        open={Boolean(pending)}
        onOpenChange={(open) => !open && setPending(null)}
        backupName={pending?.name ?? ""}
        resourceName={resourceName ?? "mysql-prod-01"}
        namespace="prod-data"
        onConfirm={() => pending && onRestore?.(pending.id)}
      />
    </>
  );
}
