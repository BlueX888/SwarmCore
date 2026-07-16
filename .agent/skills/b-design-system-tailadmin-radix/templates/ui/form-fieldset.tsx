import * as React from "react";
import { cn } from "@/lib/utils";

export type FormFieldsetProps = {
  legend?: React.ReactNode;
  description?: React.ReactNode;
  disabled?: boolean;
  className?: string;
  children: React.ReactNode;
};

export function FormFieldset({
  legend,
  description,
  disabled,
  className,
  children,
}: FormFieldsetProps) {
  return (
    <fieldset disabled={disabled} className={cn("grid gap-4", className)}>
      {legend ? (
        <legend className="text-base font-semibold text-gray-800 dark:text-white/90">
          {legend}
        </legend>
      ) : null}
      {description ? (
        <p className="text-theme-sm text-gray-500 dark:text-gray-400">{description}</p>
      ) : null}
      {children}
    </fieldset>
  );
}
