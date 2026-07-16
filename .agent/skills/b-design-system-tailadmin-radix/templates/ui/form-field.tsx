import * as React from "react";
import { cn } from "@/lib/utils";
import { Spinner } from "@/components/ui/spinner";
import { labelWidthClass, useFormContext } from "@/components/ui/form-context";

export type FormFieldStatus =
  | "default"
  | "error"
  | "success"
  | "warning"
  | "validating";

export type FormFieldProps = {
  label?: React.ReactNode;
  htmlFor?: string;
  required?: boolean;
  optional?: boolean;
  helper?: React.ReactNode;
  error?: React.ReactNode;
  success?: React.ReactNode;
  warning?: React.ReactNode;
  status?: FormFieldStatus;
  loading?: boolean;
  disabled?: boolean;
  readOnly?: boolean;
  className?: string;
  children: React.ReactNode;
};

function resolveMessage(props: FormFieldProps): {
  tone: FormFieldStatus;
  text: React.ReactNode;
} | null {
  if (props.error) return { tone: "error", text: props.error };
  if (props.warning) return { tone: "warning", text: props.warning };
  if (props.success) return { tone: "success", text: props.success };
  if (props.status === "validating") {
    return { tone: "validating", text: props.helper ?? "Validating…" };
  }
  if (props.helper) return { tone: "default", text: props.helper };
  return null;
}

const messageToneClass: Record<FormFieldStatus, string> = {
  default: "text-gray-500 dark:text-gray-400",
  error: "text-error-500",
  success: "text-success-500",
  warning: "text-warning-500",
  validating: "text-gray-500 dark:text-gray-400",
};

export function FormField({
  label,
  htmlFor: htmlForProp,
  required,
  optional,
  helper,
  error,
  success,
  warning,
  status = "default",
  loading = false,
  disabled = false,
  readOnly = false,
  className,
  children,
}: FormFieldProps) {
  const generatedId = React.useId();
  const htmlFor = htmlForProp ?? generatedId;
  const invalid = Boolean(error) || status === "error";
  const { layout, labelWidth, requiredMark } = useFormContext();
  const message = resolveMessage({
    label,
    htmlFor,
    required,
    optional,
    helper,
    error,
    success,
    warning,
    status,
    loading,
    disabled,
    readOnly,
    children,
  });
  const tone = error
    ? "error"
    : warning
      ? "warning"
      : success
        ? "success"
        : status === "validating"
          ? "validating"
          : "default";

  return (
    <div
      id={htmlFor}
      tabIndex={invalid ? -1 : undefined}
      className={cn(
        layout === "horizontal"
          ? "grid gap-2 sm:grid-cols-[var(--form-label-width,7.5rem)_1fr] sm:items-start"
          : layout === "inline"
            ? "inline-flex min-w-[200px] flex-col gap-1.5"
            : "grid gap-1.5",
        className,
      )}
      style={
        layout === "horizontal"
          ? ({ "--form-label-width": labelWidth === "sm" ? "5rem" : labelWidth === "lg" ? "10rem" : "7.5rem" } as React.CSSProperties)
          : undefined
      }
      data-disabled={disabled || undefined}
      data-readonly={readOnly || undefined}
      data-loading={loading || undefined}
      data-field-state={tone === "default" ? undefined : tone}
      data-field-invalid={invalid || undefined}
    >
      {label ? (
        <label
          htmlFor={htmlFor}
          className={cn(
            "flex items-center gap-1 text-sm font-medium text-gray-700 dark:text-gray-300",
            layout === "horizontal" && cn("sm:pt-2.5", labelWidthClass[labelWidth]),
          )}
        >
          <span>{label}</span>
          {required || (requiredMark === "required" && !optional) ? (
            <span className="text-error-500" aria-hidden="true">
              *
            </span>
          ) : null}
          {!required && (optional || requiredMark === "optional") ? (
            <span className="text-xs font-normal text-gray-400">选填</span>
          ) : null}
        </label>
      ) : null}
      <div className="relative">
        {children}
        {loading ? (
          <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2">
            <Spinner className="size-5" />
          </span>
        ) : null}
      </div>
      {message ? (
        <p
          className={cn("text-xs", messageToneClass[tone])}
          role={tone === "error" ? "alert" : undefined}
        >
          {message.text}
        </p>
      ) : null}
    </div>
  );
}
