import * as React from "react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { AlertTriangle } from "lucide-react";

export type DangerAction = {
  id: string;
  label: string;
  description: string;
  confirmLabel?: string;
  requiresNameConfirm?: boolean;
  confirmPlaceholder?: string;
};

export type DangerZoneProps = {
  title?: string;
  description?: string;
  actions: DangerAction[];
  onAction?: (actionId: string) => void;
  className?: string;
};

export type RollbackDialogProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  currentVersion: string;
  targetVersion: string;
  environment: string;
  objectName?: string;
  onConfirm?: () => void;
};

/**
 * Destructive action zone with optional name-confirm dialogs.
 * @see references/layout-patterns/cicd-release.md
 */
export function DangerZone({
  title = "Danger zone",
  description = "Irreversible actions require explicit confirmation.",
  actions,
  onAction,
  className,
}: DangerZoneProps) {
  const [pending, setPending] = React.useState<DangerAction | null>(null);
  const [confirmText, setConfirmText] = React.useState("");

  const close = () => {
    setPending(null);
    setConfirmText("");
  };

  const canConfirm =
    !pending?.requiresNameConfirm ||
    (pending.confirmPlaceholder
      ? confirmText === pending.confirmPlaceholder
      : confirmText.length > 0);

  return (
    <>
      <section
        className={cn(
          "rounded-xl border border-error-200 bg-error-50/30 p-4 dark:border-error-500/30 dark:bg-error-500/5",
          className,
        )}
      >
        <div className="mb-4 flex items-start gap-2">
          <AlertTriangle className="mt-0.5 size-4 shrink-0 text-error-600 dark:text-error-500" />
          <div>
            <h3 className="text-theme-sm font-semibold text-error-700 dark:text-error-400">{title}</h3>
            <p className="mt-1 text-theme-sm text-error-600/80 dark:text-error-400/80">{description}</p>
          </div>
        </div>
        <div className="space-y-3">
          {actions.map((action) => (
            <div
              key={action.id}
              className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-error-200/60 bg-white px-4 py-3 dark:border-error-500/20 dark:bg-gray-900"
            >
              <div className="min-w-0">
                <p className="text-theme-sm font-medium text-gray-900 dark:text-white/90">
                  {action.label}
                </p>
                <p className="text-theme-xs text-gray-500">{action.description}</p>
              </div>
              <Button
                type="button"
                variant="destructive"
                size="sm"
                onClick={() => setPending(action)}
              >
                {action.confirmLabel ?? action.label}
              </Button>
            </div>
          ))}
        </div>
      </section>

      {pending ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-gray-900/50 p-4 backdrop-blur-sm">
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="danger-dialog-title"
            className="w-full max-w-md rounded-2xl border border-gray-200 bg-white p-6 shadow-xl dark:border-gray-800 dark:bg-gray-900"
          >
            <h4 id="danger-dialog-title" className="text-base font-semibold text-gray-900 dark:text-white/90">
              Confirm {pending.label}
            </h4>
            <p className="mt-2 text-theme-sm text-gray-600 dark:text-gray-400">{pending.description}</p>
            {pending.requiresNameConfirm ? (
              <div className="mt-4 space-y-2">
                <label className="text-theme-xs font-medium text-gray-700 dark:text-gray-300">
                  Type <code className="rounded bg-gray-100 px-1 dark:bg-gray-800">{pending.confirmPlaceholder}</code> to confirm
                </label>
                <Input
                  value={confirmText}
                  onChange={(e) => setConfirmText(e.target.value)}
                  placeholder={pending.confirmPlaceholder}
                  className="font-mono"
                />
              </div>
            ) : null}
            <div className="mt-6 flex justify-end gap-2">
              <Button type="button" variant="outline" onClick={close}>
                Cancel
              </Button>
              <Button
                type="button"
                variant="destructive"
                disabled={!canConfirm}
                onClick={() => {
                  onAction?.(pending.id);
                  close();
                }}
              >
                Confirm
              </Button>
            </div>
          </div>
        </div>
      ) : null}
    </>
  );
}

/**
 * Rollback confirmation dialog — current/target version + environment impact.
 */
export function RollbackDialog({
  open,
  onOpenChange,
  currentVersion,
  targetVersion,
  environment,
  objectName,
  onConfirm,
}: RollbackDialogProps) {
  const [confirmText, setConfirmText] = React.useState("");

  React.useEffect(() => {
    if (!open) setConfirmText("");
  }, [open]);

  if (!open) return null;

  const required = objectName ?? targetVersion;
  const canConfirm = confirmText === required;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-gray-900/50 p-4 backdrop-blur-sm">
      <div
        role="dialog"
        aria-modal="true"
        className="w-full max-w-lg rounded-2xl border border-error-200 bg-white p-6 shadow-xl dark:border-error-500/30 dark:bg-gray-900"
      >
        <h4 className="text-base font-semibold text-error-700 dark:text-error-400">回滚发布</h4>
        <p className="mt-2 text-theme-sm text-gray-600 dark:text-gray-400">
          This action is irreversible. Services in <strong>{environment}</strong> will revert to the target version.
        </p>
        <dl className="mt-4 grid grid-cols-2 gap-3 rounded-lg bg-gray-50 p-3 text-theme-sm dark:bg-white/[0.03]">
          <div>
            <dt className="text-theme-xs text-gray-500">当前版本</dt>
            <dd className="font-mono font-medium">{currentVersion}</dd>
          </div>
          <div>
            <dt className="text-theme-xs text-gray-500">目标版本</dt>
            <dd className="font-mono font-medium text-brand-600">{targetVersion}</dd>
          </div>
        </dl>
        <div className="mt-4 space-y-2">
          <label className="text-theme-xs font-medium text-gray-700 dark:text-gray-300">
            Type <code className="rounded bg-gray-100 px-1 dark:bg-gray-800">{required}</code> to confirm rollback
          </label>
          <Input
            value={confirmText}
            onChange={(e) => setConfirmText(e.target.value)}
            className="font-mono"
          />
        </div>
        <div className="mt-6 flex justify-end gap-2">
          <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
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
            Rollback
          </Button>
        </div>
      </div>
    </div>
  );
}
