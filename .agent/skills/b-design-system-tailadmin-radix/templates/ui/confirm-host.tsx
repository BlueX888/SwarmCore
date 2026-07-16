import * as React from "react";
import * as DialogPrimitive from "@radix-ui/react-dialog";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  resolveConfirm,
  useConfirmState,
  type ConfirmOptions,
} from "@/lib/use-confirm";

const ConfirmDialog = DialogPrimitive.Root;
const ConfirmDialogPortal = DialogPrimitive.Portal;

const ConfirmDialogOverlay = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Overlay>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Overlay>
>(({ className, ...props }, ref) => (
  <DialogPrimitive.Overlay
    ref={ref}
    className={cn(
      "fixed inset-0 z-[100] bg-gray-400/50 backdrop-blur-[32px] data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0",
      className,
    )}
    {...props}
  />
));
ConfirmDialogOverlay.displayName = DialogPrimitive.Overlay.displayName;

const ConfirmDialogContent = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Content>
>(({ className, children, ...props }, ref) => (
  <ConfirmDialogPortal>
    <ConfirmDialogOverlay />
    <DialogPrimitive.Content
      ref={ref}
      className={cn(
        "fixed top-1/2 left-1/2 z-[100] grid w-full max-w-[400px] -translate-x-1/2 -translate-y-1/2 gap-4 rounded-2xl border border-gray-200 bg-white p-6 shadow-theme-lg duration-200 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 dark:border-gray-800 dark:bg-gray-dark",
        className,
      )}
      {...props}
    >
      {children}
    </DialogPrimitive.Content>
  </ConfirmDialogPortal>
));
ConfirmDialogContent.displayName = DialogPrimitive.Content.displayName;

function ConfirmDialogBody({
  title,
  description,
  confirmLabel = "确认",
  cancelLabel = "取消",
  destructive = false,
  onConfirm,
  onCancel,
}: ConfirmOptions & {
  onConfirm: () => void;
  onCancel: () => void;
}) {
  return (
    <>
      <div className="grid gap-2">
        <DialogPrimitive.Title className="text-base font-semibold text-gray-800 dark:text-white/90">
          {title}
        </DialogPrimitive.Title>
        {description ? (
          <DialogPrimitive.Description className="text-theme-sm text-gray-500 dark:text-gray-400">
            {description}
          </DialogPrimitive.Description>
        ) : null}
      </div>
      <div className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end sm:gap-3">
        <Button type="button" variant="outline" onClick={onCancel}>
          {cancelLabel}
        </Button>
        <Button
          type="button"
          variant={destructive ? "destructive" : "primary"}
          onClick={onConfirm}
        >
          {confirmLabel}
        </Button>
      </div>
    </>
  );
}

/**
 * 应用根节点挂载一次 — 为 confirm() 提供 AlertDialog 式确认。
 */
export function ConfirmHost() {
  const state = useConfirmState();

  const handleOpenChange = (open: boolean) => {
    if (!open) resolveConfirm(false);
  };

  return (
    <ConfirmDialog open={state.open} onOpenChange={handleOpenChange}>
      <ConfirmDialogContent
        onEscapeKeyDown={() => resolveConfirm(false)}
        onPointerDownOutside={() => resolveConfirm(false)}
      >
        <ConfirmDialogBody
          title={state.title}
          description={state.description}
          confirmLabel={state.confirmLabel}
          cancelLabel={state.cancelLabel}
          destructive={state.destructive}
          onConfirm={() => resolveConfirm(true)}
          onCancel={() => resolveConfirm(false)}
        />
      </ConfirmDialogContent>
    </ConfirmDialog>
  );
}

export { confirm, setConfirmState } from "@/lib/use-confirm";
export type { ConfirmOptions } from "@/lib/use-confirm";
