import * as React from "react";
import { Button } from "@/components/ui/button";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { cn } from "@/lib/utils";

export type PopconfirmProps = {
  children: React.ReactElement;
  title: React.ReactNode;
  description?: React.ReactNode;
  open?: boolean;
  defaultOpen?: boolean;
  onOpenChange?: (open: boolean) => void;
  onConfirm?: () => void | Promise<void>;
  onCancel?: () => void;
  okText?: string;
  cancelText?: string;
  okType?: "default" | "danger";
  confirmLoading?: boolean;
  side?: React.ComponentProps<typeof PopoverContent>["side"];
  align?: React.ComponentProps<typeof PopoverContent>["align"];
  className?: string;
};

export function Popconfirm({
  children,
  title,
  description,
  open,
  defaultOpen,
  onOpenChange,
  onConfirm,
  onCancel,
  okText = "确定",
  cancelText = "取消",
  okType = "default",
  confirmLoading = false,
  side = "top",
  align = "center",
  className,
}: PopconfirmProps) {
  const [internalOpen, setInternalOpen] = React.useState(defaultOpen ?? false);
  const [loading, setLoading] = React.useState(false);
  const isControlled = open !== undefined;
  const resolvedOpen = isControlled ? open : internalOpen;

  const setOpen = (next: boolean) => {
    if (!isControlled) setInternalOpen(next);
    onOpenChange?.(next);
  };

  const handleConfirm = async () => {
    try {
      setLoading(true);
      await onConfirm?.();
      setOpen(false);
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    onCancel?.();
    setOpen(false);
  };

  return (
    <Popover open={resolvedOpen} onOpenChange={setOpen}>
      <PopoverTrigger asChild>{children}</PopoverTrigger>
      <PopoverContent side={side} align={align} className={cn("w-72 p-4", className)}>
        <div className="space-y-3">
          <div className="space-y-1">
            <p className="text-sm font-semibold text-gray-800 dark:text-white/90">{title}</p>
            {description ? (
              <p className="text-theme-xs text-gray-500 dark:text-gray-400">{description}</p>
            ) : null}
          </div>
          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" size="sm" onClick={handleCancel}>
              {cancelText}
            </Button>
            <Button
              type="button"
              variant={okType === "danger" ? "destructive" : "primary"}
              size="sm"
              loading={confirmLoading || loading}
              onClick={handleConfirm}
            >
              {okText}
            </Button>
          </div>
        </div>
      </PopoverContent>
    </Popover>
  );
}
