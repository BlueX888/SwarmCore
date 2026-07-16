import * as React from "react";
import { cn } from "@/lib/utils";
import { FormField, type FormFieldProps } from "@/components/ui/form-field";
import { Button } from "@/components/ui/button";

export type AsyncFieldState =
  | "idle"
  | "validating"
  | "success"
  | "warning"
  | "error";

export type AsyncFieldProps = Omit<FormFieldProps, "status" | "children"> & {
  state?: AsyncFieldState;
  retryLabel?: string;
  onRetry?: () => void;
  children: React.ReactNode;
};

const stateToField: Record<
  AsyncFieldState,
  Pick<FormFieldProps, "status" | "success" | "warning" | "error" | "loading">
> = {
  idle: {},
  validating: { status: "validating", loading: true },
  success: { status: "success" },
  warning: { status: "warning" },
  error: { status: "error" },
};

export function AsyncField({
  state = "idle",
  retryLabel = "重试",
  onRetry,
  helper,
  success,
  warning,
  error,
  className,
  children,
  ...fieldProps
}: AsyncFieldProps) {
  const mapped = stateToField[state];

  return (
    <FormField
      {...fieldProps}
      className={cn(className)}
      status={mapped.status}
      loading={mapped.loading}
      helper={state === "validating" ? helper ?? "Checking…" : helper}
      success={state === "success" ? success : undefined}
      warning={state === "warning" ? warning : undefined}
      error={state === "error" ? error : undefined}
    >
      {children}
      {state === "error" && onRetry ? (
        <div className="mt-2">
          <Button type="button" variant="outline" size="sm" onClick={onRetry}>
            {retryLabel}
          </Button>
        </div>
      ) : null}
    </FormField>
  );
}

/** Example async validators for connectivity / uniqueness / schema checks. */
export async function simulateAsyncValidation(
  fn: () => Promise<boolean>,
  delayMs = 600,
): Promise<boolean> {
  await new Promise((resolve) => setTimeout(resolve, delayMs));
  return fn();
}
