import * as React from "react";
import { cn } from "@/lib/utils";
import { confirm } from "@/lib/use-confirm";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetClose,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { DescriptionList, type DescriptionItem } from "@/components/ui/description-list";

export type FormDrawerMode = "view" | "edit";

export type FormDrawerProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: React.ReactNode;
  description?: React.ReactNode;
  mode?: FormDrawerMode;
  onModeChange?: (mode: FormDrawerMode) => void;
  viewItems?: DescriptionItem[];
  dirty?: boolean;
  saving?: boolean;
  onSave?: () => void;
  onCancel?: () => void;
  size?: "filter" | "edit" | "full";
  children?: React.ReactNode;
  className?: string;
};

/**
 * Drawer 内查看/编辑切换 — 表格行详情、局部保存、关闭确认。
 * @see references/layout-patterns/form-composition.md#承载容器选型
 */
export function FormDrawer({
  open,
  onOpenChange,
  title,
  description,
  mode = "view",
  onModeChange,
  viewItems = [],
  dirty = false,
  saving = false,
  onSave,
  onCancel,
  size = "edit",
  children,
  className,
}: FormDrawerProps) {
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

  const switchMode = async (next: FormDrawerMode) => {
    if (mode === "edit" && next === "view" && dirty) {
      const confirmed = await confirm({
        title: "有未保存的更改",
        description: "确定返回查看态吗？",
        confirmLabel: "返回查看",
        destructive: true,
      });
      if (!confirmed) return;
    }
    onModeChange?.(next);
  };

  return (
    <Sheet open={open} onOpenChange={handleOpenChange}>
      <SheetContent side="right" size={size} className={cn("flex flex-col", className)}>
        <SheetHeader className="border-b border-gray-200 pb-4 dark:border-gray-800">
          <div className="flex items-start justify-between gap-3">
            <div className="grid gap-1 pr-8">
              <SheetTitle>{title}</SheetTitle>
              {description ? <SheetDescription>{description}</SheetDescription> : null}
            </div>
          </div>
          {onModeChange ? (
            <div
              className="mt-3 inline-flex rounded-lg border border-gray-200 p-1 dark:border-gray-800"
              role="tablist"
              aria-label="详情与编辑切换"
            >
              {(["view", "edit"] as const).map((tab) => (
                <button
                  key={tab}
                  type="button"
                  role="tab"
                  aria-selected={mode === tab}
                  className={cn(
                    "rounded-md px-3 py-1.5 text-theme-sm font-medium transition-colors",
                    mode === tab
                      ? "bg-brand-500 text-white"
                      : "text-gray-600 hover:text-gray-800 dark:text-gray-400 dark:hover:text-white/90",
                  )}
                  onClick={() => switchMode(tab)}
                >
                  {tab === "view" ? "详情" : "编辑"}
                </button>
              ))}
            </div>
          ) : null}
        </SheetHeader>

        <div className="flex-1 overflow-y-auto px-1 py-5">
          {mode === "view" ? (
            <DescriptionList items={viewItems} columns={1} labelWidth="md" />
          ) : (
            children
          )}
        </div>

        {mode === "edit" ? (
          <SheetFooter className="border-t border-gray-200 pt-4 dark:border-gray-800">
            <SheetClose asChild>
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  onCancel?.();
                }}
              >
                取消
              </Button>
            </SheetClose>
            <Button type="button" disabled={saving} onClick={onSave}>
              {saving ? "保存中…" : "保存"}
            </Button>
          </SheetFooter>
        ) : onModeChange ? (
          <SheetFooter className="border-t border-gray-200 pt-4 dark:border-gray-800">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              关闭
            </Button>
            <Button type="button" onClick={() => switchMode("edit")}>
              编辑
            </Button>
          </SheetFooter>
        ) : null}
      </SheetContent>
    </Sheet>
  );
}
