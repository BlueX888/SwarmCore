import * as React from "react";
import * as DialogPrimitive from "@radix-ui/react-dialog";
import { cn } from "@/lib/utils";
import {
  closeDialog,
  useDialogState,
  type DialogSize,
} from "@/lib/use-dialog";

const sizeClass: Record<DialogSize, string> = {
  xs: "sm:max-w-[400px]",
  sm: "sm:max-w-[480px]",
  md: "sm:max-w-[560px]",
  lg: "sm:max-w-[720px]",
  xl: "sm:max-w-[960px]",
  full: "sm:max-w-none h-[100dvh] max-h-[100dvh] rounded-none m-0",
};

const DialogHostRoot = DialogPrimitive.Root;
const DialogHostPortal = DialogPrimitive.Portal;

const DialogHostOverlay = React.forwardRef<
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
DialogHostOverlay.displayName = DialogPrimitive.Overlay.displayName;

const DialogHostContent = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Content> & { size?: DialogSize }
>(({ className, size = "sm", children, ...props }, ref) => (
  <DialogHostPortal>
    <DialogHostOverlay />
    <DialogPrimitive.Content
      ref={ref}
      className={cn(
        "fixed top-1/2 left-1/2 z-[100] grid w-full max-w-[calc(100%-2rem)] -translate-x-1/2 -translate-y-1/2 gap-4 rounded-2xl border border-gray-200 bg-white p-6 shadow-theme-lg duration-200 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 dark:border-gray-800 dark:bg-gray-dark",
        sizeClass[size],
        className,
      )}
      {...props}
    >
      {children}
    </DialogPrimitive.Content>
  </DialogHostPortal>
));
DialogHostContent.displayName = "DialogHostContent";

/**
 * 应用根节点挂载一次 — 为 openDialog() 提供命令式 Dialog 宿主。
 * 与 ConfirmHost 并存；对标 PrimeVue DynamicDialog。
 */
export function DialogHost() {
  const state = useDialogState();

  const handleOpenChange = (open: boolean) => {
    if (!open) closeDialog();
  };

  return (
    <DialogHostRoot open={state.open} onOpenChange={handleOpenChange}>
      <DialogHostContent
        size={state.size ?? "sm"}
        onEscapeKeyDown={() => closeDialog()}
        onPointerDownOutside={() => closeDialog()}
      >
        {state.title ? (
          <DialogPrimitive.Title className="text-base font-semibold text-gray-800 dark:text-white/90">
            {state.title}
          </DialogPrimitive.Title>
        ) : null}
        <div className="text-theme-sm text-gray-700 dark:text-gray-300">{state.content}</div>
      </DialogHostContent>
    </DialogHostRoot>
  );
}

export { openDialog, closeDialog, useDialog } from "@/lib/use-dialog";
export type { DialogOpenOptions, DialogSize } from "@/lib/use-dialog";
