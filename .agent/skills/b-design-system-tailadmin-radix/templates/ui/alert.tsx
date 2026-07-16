import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { CircleAlert, CircleCheck, ChevronDown, Info, TriangleAlert, X } from "lucide-react";
import { cn } from "@/lib/utils";

const alertSeverityValues = ["success", "error", "warning", "info", "neutral"] as const;
const alertAppearanceValues = ["subtle", "filled", "outlined"] as const;

type AlertSeverity = (typeof alertSeverityValues)[number];
type AlertAppearance = (typeof alertAppearanceValues)[number];

const alertVariants = cva("rounded-xl p-4", {
  variants: {
    severity: {
      success: "",
      error: "",
      warning: "",
      info: "",
      neutral: "",
    },
    appearance: {
      subtle: "border",
      filled: "border border-transparent",
      outlined: "border-2 bg-transparent",
    },
  },
  compoundVariants: [
    { severity: "success", appearance: "subtle", className: "border-success-500 bg-success-50 dark:border-success-500/30 dark:bg-success-500/15" },
    { severity: "error", appearance: "subtle", className: "border-error-500 bg-error-50 dark:border-error-500/30 dark:bg-error-500/15" },
    { severity: "warning", appearance: "subtle", className: "border-warning-500 bg-warning-50 dark:border-warning-500/30 dark:bg-warning-500/15" },
    { severity: "info", appearance: "subtle", className: "border-blue-light-500 bg-blue-light-50 dark:border-blue-light-500/30 dark:bg-blue-light-500/15" },
    { severity: "neutral", appearance: "subtle", className: "border-gray-300 bg-gray-50 dark:border-gray-700 dark:bg-white/[0.03]" },
    { severity: "success", appearance: "filled", className: "bg-success-500 text-white" },
    { severity: "error", appearance: "filled", className: "bg-error-500 text-white" },
    { severity: "warning", appearance: "filled", className: "bg-warning-500 text-white" },
    { severity: "info", appearance: "filled", className: "bg-blue-light-500 text-white" },
    { severity: "neutral", appearance: "filled", className: "bg-gray-700 text-white dark:bg-gray-600" },
    { severity: "success", appearance: "outlined", className: "border-success-500 text-success-700 dark:text-success-400" },
    { severity: "error", appearance: "outlined", className: "border-error-500 text-error-700 dark:text-error-400" },
    { severity: "warning", appearance: "outlined", className: "border-warning-500 text-warning-700 dark:text-warning-400" },
    { severity: "info", appearance: "outlined", className: "border-blue-light-500 text-blue-light-700 dark:text-blue-light-400" },
    { severity: "neutral", appearance: "outlined", className: "border-gray-400 text-gray-700 dark:text-gray-300" },
  ],
  defaultVariants: {
    severity: "info",
    appearance: "subtle",
  },
});

const alertIconVariants = cva("size-6 shrink-0", {
  variants: {
    severity: {
      success: "text-success-500",
      error: "text-error-500",
      warning: "text-warning-500",
      info: "text-blue-light-500",
      neutral: "text-gray-500",
    },
    appearance: {
      subtle: "",
      filled: "text-white",
      outlined: "",
    },
  },
  compoundVariants: [
    { severity: "success", appearance: "outlined", className: "text-success-500" },
    { severity: "error", appearance: "outlined", className: "text-error-500" },
    { severity: "warning", appearance: "outlined", className: "text-warning-500" },
    { severity: "info", appearance: "outlined", className: "text-blue-light-500" },
    { severity: "neutral", appearance: "outlined", className: "text-gray-500" },
  ],
  defaultVariants: {
    severity: "info",
    appearance: "subtle",
  },
});

const alertIcons = {
  success: CircleCheck,
  error: CircleAlert,
  warning: TriangleAlert,
  info: Info,
  neutral: Info,
} as const;

function resolveSeverity(
  severity?: AlertSeverity | null,
  variant?: AlertSeverity | null,
): AlertSeverity {
  return severity ?? variant ?? "info";
}

export interface AlertProps
  extends Omit<React.HTMLAttributes<HTMLDivElement>, "title">,
    VariantProps<typeof alertVariants> {
  /** @deprecated Use `severity` instead. Kept for antd/MUI migration alias. */
  variant?: AlertSeverity;
  severity?: AlertSeverity;
  appearance?: AlertAppearance;
  showIcon?: boolean;
  closable?: boolean;
  onClose?: () => void;
  closeLabel?: string;
  action?: React.ReactNode;
  banner?: boolean;
  collapsible?: boolean;
  defaultCollapsed?: boolean;
}

const Alert = React.forwardRef<HTMLDivElement, AlertProps>(
  (
    {
      className,
      severity,
      variant,
      appearance = "subtle",
      showIcon = true,
      closable = false,
      onClose,
      closeLabel = "关闭",
      action,
      banner = false,
      collapsible = false,
      defaultCollapsed = false,
      children,
      ...props
    },
    ref,
  ) => {
    const resolvedSeverity = resolveSeverity(severity, variant);
    const filled = appearance === "filled";
    const [collapsed, setCollapsed] = React.useState(defaultCollapsed);

    return (
      <div
        ref={ref}
        role="alert"
        className={cn(
          alertVariants({ severity: resolvedSeverity, appearance }),
          banner && "w-full rounded-none border-x-0",
          className,
        )}
        data-collapsed={collapsible && collapsed ? "true" : undefined}
        {...props}
      >
        <div className="flex items-start gap-3">
          {showIcon ? (
            <AlertIcon severity={resolvedSeverity} appearance={appearance} />
          ) : null}
          <div className="min-w-0 flex-1">
            {collapsible ? (
              <div
                className={cn(
                  "grid transition-[grid-template-rows] duration-200 ease-in-out",
                  collapsed ? "grid-rows-[0fr]" : "grid-rows-[1fr]",
                )}
              >
                <div className="overflow-hidden">{children}</div>
              </div>
            ) : (
              children
            )}
          </div>
          {action ? <div className="shrink-0">{action}</div> : null}
          {collapsible ? (
            <button
              type="button"
              aria-label={collapsed ? "展开" : "收起"}
              aria-expanded={!collapsed}
              onClick={() => setCollapsed((open) => !open)}
              className={cn(
                "inline-flex size-8 shrink-0 items-center justify-center rounded-lg transition-colors hover:bg-black/5 dark:hover:bg-white/10",
                filled ? "text-white/90" : "text-gray-500",
              )}
            >
              <ChevronDown
                className={cn(
                  "size-4 transition-transform duration-200",
                  !collapsed && "rotate-180",
                )}
              />
            </button>
          ) : null}
          {closable ? (
            <button
              type="button"
              aria-label={closeLabel}
              onClick={onClose}
              className={cn(
                "inline-flex size-8 shrink-0 items-center justify-center rounded-lg transition-colors hover:bg-black/5 dark:hover:bg-white/10",
                filled ? "text-white/90" : "text-gray-500",
              )}
            >
              <X className="size-4" />
            </button>
          ) : null}
        </div>
      </div>
    );
  },
);
Alert.displayName = "Alert";

const AlertIcon = ({
  severity = "info",
  appearance = "subtle",
  className,
}: {
  severity?: AlertSeverity;
  appearance?: AlertAppearance;
  className?: string;
}) => {
  const Icon = alertIcons[severity];
  return (
    <Icon
      className={cn(alertIconVariants({ severity, appearance }), className)}
      aria-hidden
    />
  );
};

const AlertContent = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn("min-w-0 flex-1", className)} {...props} />
  ),
);
AlertContent.displayName = "AlertContent";

const AlertTitle = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLHeadingElement> & { filled?: boolean }
>(({ className, filled, ...props }, ref) => (
  <h4
    ref={ref}
    className={cn(
      "mb-1 text-sm font-semibold",
      filled ? "text-white" : "text-gray-800 dark:text-white/90",
      className,
    )}
    {...props}
  />
));
AlertTitle.displayName = "AlertTitle";

const AlertDescription = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLParagraphElement> & { filled?: boolean }
>(({ className, filled, ...props }, ref) => (
  <p
    ref={ref}
    className={cn(
      "text-sm",
      filled ? "text-white/90" : "text-gray-500 dark:text-gray-400",
      className,
    )}
    {...props}
  />
));
AlertDescription.displayName = "AlertDescription";

const AlertLink = React.forwardRef<
  HTMLAnchorElement,
  React.AnchorHTMLAttributes<HTMLAnchorElement>
>(({ className, ...props }, ref) => (
  <a
    ref={ref}
    className={cn(
      "mt-3 inline-block text-sm font-medium text-gray-500 underline dark:text-gray-400",
      className,
    )}
    {...props}
  />
));
AlertLink.displayName = "AlertLink";

const AlertAction = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn("shrink-0", className)} {...props} />
  ),
);
AlertAction.displayName = "AlertAction";

export {
  Alert,
  AlertAction,
  AlertContent,
  AlertDescription,
  AlertIcon,
  AlertLink,
  AlertTitle,
  alertVariants,
  alertSeverityValues,
  alertAppearanceValues,
};
