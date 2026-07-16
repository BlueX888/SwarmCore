import * as React from "react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";

export function scrollToFirstFormError(root: HTMLElement | Document = document) {
  const container = root instanceof Document ? root : root;
  const el = container.querySelector<HTMLElement>(
    '[data-field-state="error"], [aria-invalid="true"]',
  );
  el?.scrollIntoView({ behavior: "smooth", block: "center" });
  el?.focus();
}

export type FormPageBreadcrumb = {
  label: React.ReactNode;
  href?: string;
};

export type FormPageShellProps = {
  title: React.ReactNode;
  description?: React.ReactNode;
  breadcrumbs?: FormPageBreadcrumb[];
  actions?: React.ReactNode;
  children: React.ReactNode;
  dirty?: boolean;
  saving?: boolean;
  saveLabel?: string;
  cancelLabel?: string;
  onSave?: () => void | boolean;
  onCancel?: () => void;
  stickyActions?: boolean;
  className?: string;
  contentClassName?: string;
};

/**
 * 独立页面表单壳 — 标题、面包屑、分组、sticky actions。
 * @see references/layout-patterns/form-composition.md#承载容器选型
 */
export function FormPageShell({
  title,
  description,
  breadcrumbs = [],
  actions,
  children,
  dirty = false,
  saving = false,
  saveLabel = "保存",
  cancelLabel = "取消",
  onSave,
  onCancel,
  stickyActions = true,
  className,
  contentClassName,
}: FormPageShellProps) {
  const handleSave = () => {
    const result = onSave?.();
    if (result === false) {
      scrollToFirstFormError();
    }
  };

  const defaultActions = (
    <>
      <Button type="button" variant="outline" disabled={saving} onClick={onCancel}>
        {cancelLabel}
      </Button>
      <Button type="button" disabled={saving || !dirty} onClick={handleSave}>
        {saving ? "提交中…" : saveLabel}
      </Button>
    </>
  );

  return (
    <div className={cn("mx-auto w-full max-w-(--breakpoint-2xl)", className)}>
      <div className="mb-6 flex flex-col gap-4">
        {breadcrumbs.length > 0 ? (
          <Breadcrumb>
            <BreadcrumbList>
              {breadcrumbs.map((crumb, index) => {
                const isLast = index === breadcrumbs.length - 1;
                return (
                  <React.Fragment key={index}>
                    <BreadcrumbItem>
                      {isLast || !crumb.href ? (
                        <BreadcrumbPage>{crumb.label}</BreadcrumbPage>
                      ) : (
                        <BreadcrumbLink href={crumb.href}>{crumb.label}</BreadcrumbLink>
                      )}
                    </BreadcrumbItem>
                    {!isLast ? <BreadcrumbSeparator /> : null}
                  </React.Fragment>
                );
              })}
            </BreadcrumbList>
          </Breadcrumb>
        ) : null}

        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="grid gap-1">
            <h1 className="text-xl font-semibold text-gray-800 dark:text-white/90">{title}</h1>
            {description ? (
              <p className="text-theme-sm text-gray-500 dark:text-gray-400">{description}</p>
            ) : null}
            {dirty ? (
              <p className="text-theme-xs text-warning-500">有未保存的更改</p>
            ) : null}
          </div>
          {!stickyActions ? (
            <div className="flex items-center gap-2">{actions ?? defaultActions}</div>
          ) : null}
        </div>
      </div>

      <div className={cn("grid gap-6", contentClassName)}>{children}</div>

      {stickyActions ? (
        <div className="sticky bottom-0 z-10 -mx-4 mt-8 border-t border-gray-200 bg-white/90 px-4 py-4 backdrop-blur dark:border-gray-800 dark:bg-gray-900/90 sm:-mx-6 sm:px-6">
          <div className="flex items-center justify-end gap-2">
            {actions ?? defaultActions}
          </div>
        </div>
      ) : null}
    </div>
  );
}
