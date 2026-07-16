import { Toaster as Sonner, type ToasterProps } from "sonner";

export type ToasterPositionPreset = Pick<ToasterProps, "position">;

/**
 * Sonner 六位置 preset — 传给 `<TailAdminToaster {...toasterPositionPresets["top-center"]} />`。
 *
 * **选型（Message vs Notification）：**
 * - **Message**（页面内操作反馈）：优先 `top-center`，居中短提示，不打断阅读流。
 * - **Notification**（系统/后台事件）：优先四角 `top-right` / `bottom-right`，可堆叠多条。
 */
export const toasterPositionPresets = {
  "top-left": { position: "top-left" },
  "top-center": { position: "top-center" },
  "top-right": { position: "top-right" },
  "bottom-left": { position: "bottom-left" },
  "bottom-center": { position: "bottom-center" },
  "bottom-right": { position: "bottom-right" },
} as const satisfies Record<string, ToasterPositionPreset>;

export type ToasterPositionKey = keyof typeof toasterPositionPresets;

/**
 * TailAdmin × Sonner 主题包装。
 * 在 App 根节点放置一次：`<TailAdminToaster />`
 */
export function TailAdminToaster(props: ToasterProps) {
  return (
    <Sonner
      theme="system"
      position="top-right"
      closeButton
      duration={4000}
      toastOptions={{
        classNames: {
          toast:
            "group rounded-lg border shadow-theme-lg bg-white dark:bg-gray-900 text-gray-800 dark:text-white/90",
          title: "text-sm font-medium",
          description: "text-xs text-gray-500 dark:text-gray-400",
          actionButton:
            "bg-brand-500 text-white text-xs font-medium rounded-lg px-3 py-1.5",
          cancelButton:
            "bg-gray-100 text-gray-700 text-xs font-medium rounded-lg px-3 py-1.5 dark:bg-gray-800 dark:text-gray-300",
          closeButton:
            "bg-white border border-gray-200 text-gray-500 dark:bg-gray-800 dark:border-gray-700",
          success:
            "border-success-500 bg-success-50 dark:bg-success-500/10 dark:border-success-500",
          error:
            "border-error-500 bg-error-50 dark:bg-error-500/10 dark:border-error-500",
          warning:
            "border-warning-500 bg-warning-50 dark:bg-warning-500/10 dark:border-warning-500",
          info: "border-blue-light-500 bg-blue-light-50 dark:bg-blue-light-500/10",
        },
      }}
      {...props}
    />
  );
}

/** 常用 toast 调用示例 */
export const tailAdminToast = {
  success: (title: string, description?: string) =>
    import("sonner").then(({ toast }) => toast.success(title, { description })),
  error: (title: string, description?: string) =>
    import("sonner").then(({ toast }) => toast.error(title, { description })),
  warning: (title: string, description?: string) =>
    import("sonner").then(({ toast }) => toast.warning(title, { description })),
  info: (title: string, description?: string) =>
    import("sonner").then(({ toast }) => toast.info(title, { description })),
};
