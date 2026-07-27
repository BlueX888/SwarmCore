import * as Dialog from "@radix-ui/react-dialog";
import { Trash2, X } from "lucide-react";
import * as React from "react";
import type { StrategyDeleteImpact } from "@/api/types";
import { Button } from "@/components/ui/button";

interface StrategyDeleteDialogProps {
  open: boolean;
  strategyName: string;
  impact: StrategyDeleteImpact | null;
  loadingImpact: boolean;
  deleting: boolean;
  error: string;
  onOpenChange: (open: boolean) => void;
  onConfirm: () => void;
}

export function StrategyDeleteDialog({
  open,
  strategyName,
  impact,
  loadingImpact,
  deleting,
  error,
  onOpenChange,
  onConfirm,
}: StrategyDeleteDialogProps) {
  const [confirmation, setConfirmation] = React.useState("");
  const deletable = impact?.deletable === true;
  const nameMatches = confirmation.trim() === strategyName;

  React.useEffect(() => {
    if (!open) setConfirmation("");
  }, [open]);

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-40 bg-gray-950/50 backdrop-blur-[2px]" />
        <Dialog.Content className="fixed left-1/2 top-1/2 z-50 w-[calc(100vw-2rem)] max-w-lg -translate-x-1/2 -translate-y-1/2 rounded-2xl border border-error-200 bg-white p-5 shadow-theme-xl outline-none dark:border-error-500/30 dark:bg-gray-900">
          <div className="flex items-start justify-between gap-4">
            <div className="flex gap-3">
              <span className="grid size-11 shrink-0 place-items-center rounded-xl bg-error-50 text-error-600 dark:bg-error-500/15">
                <Trash2 aria-hidden />
              </span>
              <div>
                <Dialog.Title className="font-semibold text-gray-900 dark:text-white">删除策略</Dialog.Title>
                <Dialog.Description className="mt-1 text-sm text-gray-500">
                  策略「{strategyName}」{deletable ? "将被永久删除。" : "当前无法删除。"}
                </Dialog.Description>
              </div>
            </div>
            <Dialog.Close asChild>
              <Button type="button" variant="ghost" size="icon" aria-label="关闭删除对话框">
                <X />
              </Button>
            </Dialog.Close>
          </div>

          <div className="mt-4 space-y-4">
            {loadingImpact ? <p className="text-sm text-gray-500">正在检查删除影响…</p> : null}
            {!loadingImpact && impact && !deletable ? (
              <div className="space-y-2 rounded-xl border border-error-200 bg-error-50/60 p-3 dark:border-error-500/30 dark:bg-error-500/10">
                <p className="text-sm font-medium text-error-700 dark:text-error-300">无法删除此策略</p>
                <ul className="space-y-1 text-sm text-error-700 dark:text-error-200">
                  {impact.blockers.map((blocker) => (
                    <li key={blocker.code}>{blocker.message}</li>
                  ))}
                </ul>
              </div>
            ) : null}
            {!loadingImpact && deletable ? (
              <>
                <ul className="list-disc space-y-1 pl-5 text-sm text-gray-600 dark:text-gray-300">
                  <li>将同时删除尚未发布的草稿</li>
                  <li>此操作不可恢复</li>
                </ul>
                <label className="block space-y-2 text-sm">
                  <span className="font-medium text-gray-700 dark:text-gray-200">
                    请输入策略名称 <code className="rounded bg-gray-100 px-1 dark:bg-gray-800">{strategyName}</code> 以确认
                  </span>
                  <input
                    aria-label="确认策略名称"
                    value={confirmation}
                    onChange={(event) => setConfirmation(event.target.value)}
                    className="h-11 w-full rounded-xl border border-gray-200 bg-white px-3 text-sm outline-none ring-brand-500/20 focus:ring-3 dark:border-gray-700 dark:bg-gray-950"
                    autoComplete="off"
                  />
                </label>
              </>
            ) : null}
            {error ? <p role="alert" className="text-sm text-error-600">{error}</p> : null}
          </div>

          <div className="mt-5 flex flex-wrap justify-end gap-2">
            <Dialog.Close asChild>
              <Button type="button" variant="outline" disabled={deleting}>
                {deletable ? "取消" : "关闭"}
              </Button>
            </Dialog.Close>
            {deletable ? (
              <Button
                type="button"
                variant="destructive"
                loading={deleting}
                disabled={!nameMatches || deleting || loadingImpact}
                onClick={onConfirm}
              >
                <Trash2 />
                确认删除
              </Button>
            ) : null}
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
