import * as React from "react";
import { cn } from "@/lib/utils";
import { confirm } from "@/lib/use-confirm";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

export type FormDialogProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: React.ReactNode;
  description?: React.ReactNode;
  dirty?: boolean;
  saving?: boolean;
  onSubmit?: () => void;
  onCancel?: () => void;
  submitLabel?: string;
  cancelLabel?: string;
  /** xs(400) / sm(480) / md(560) / lg(720) / xl(960) / full(全屏) */
  size?: "xs" | "sm" | "md" | "lg" | "xl" | "full";
  /** 与 size="full" 等价 */
  fullScreen?: boolean;
  children: React.ReactNode;
  className?: string;
};

const sizeClass: Record<NonNullable<FormDialogProps["size"]>, string> = {
  xs: "sm:max-w-[400px]",
  sm: "sm:max-w-[480px]",
  md: "sm:max-w-[560px]",
  lg: "sm:max-w-[720px]",
  xl: "sm:max-w-[960px]",
  full: "sm:max-w-none h-[100dvh] max-h-[100dvh] rounded-none m-0",
};

/**
 * Dialog 短表单 — 1-6 字段、关闭确认、错误聚焦；不承载复杂配置。
 * @see references/layout-patterns/form-composition.md#承载容器选型
 */
export function FormDialog({
  open,
  onOpenChange,
  title,
  description,
  dirty = false,
  saving = false,
  onSubmit,
  onCancel,
  submitLabel = "保存",
  cancelLabel = "取消",
  size = "sm",
  fullScreen = false,
  children,
  className,
}: FormDialogProps) {
  const handleOpenChange = async (next: boolean) => {
    if (!next && dirty) {
      const confirmed = await confirm({
        title: "有未保存的更改",
        description: "确定关闭吗？",
        confirmLabel: "关闭",
        destructive: true,
      });
      if (!confirmed) return;
    }
    onOpenChange(next);
  };

  const handleCancel = async () => {
    if (dirty) {
      const confirmed = await confirm({
        title: "有未保存的更改",
        description: "确定取消吗？",
        confirmLabel: "取消编辑",
        destructive: true,
      });
      if (!confirmed) return;
    }
    onCancel?.();
    onOpenChange(false);
  };

  const isFullScreen = fullScreen || size === "full";
  const resolvedSize = isFullScreen ? "full" : size;

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className={cn(sizeClass[resolvedSize], className)}>
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          {description ? <DialogDescription>{description}</DialogDescription> : null}
        </DialogHeader>

        <form
          className="grid gap-4 py-2"
          onSubmit={(event) => {
            event.preventDefault();
            onSubmit?.();
          }}
        >
          {children}
          <DialogFooter className="gap-2 sm:gap-0">
            <Button type="button" variant="outline" disabled={saving} onClick={handleCancel}>
              {cancelLabel}
            </Button>
            <Button type="submit" disabled={saving}>
              {saving ? "提交中…" : submitLabel}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
