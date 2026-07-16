import * as React from "react";
import { cn } from "@/lib/utils";

export type FloatLabelMode = "float" | "ifta";

export type FloatLabelProps = {
  label: React.ReactNode;
  mode?: FloatLabelMode;
  children: React.ReactElement<{ className?: string; id?: string }>;
  className?: string;
  required?: boolean;
};

export function FloatLabel({
  label,
  mode = "float",
  children,
  className,
  required,
}: FloatLabelProps) {
  const id = React.useId();
  const [focused, setFocused] = React.useState(false);
  const [filled, setFilled] = React.useState(false);
  const childId = children.props.id ?? id;

  const checkFilled = (el: HTMLElement | null) => {
    if (!el) return;
    if (el instanceof HTMLInputElement || el instanceof HTMLTextAreaElement) {
      setFilled(Boolean(el.value));
    }
  };

  const floated = mode === "float" && (focused || filled);

  return (
    <div
      className={cn(
        "relative",
        mode === "ifta" && "pt-5",
        className,
      )}
      onFocusCapture={() => setFocused(true)}
      onBlurCapture={(e) => {
        setFocused(false);
        checkFilled(e.currentTarget as HTMLElement);
      }}
    >
      <label
        htmlFor={childId}
        className={cn(
          "pointer-events-none absolute z-10 text-gray-500 transition-all dark:text-gray-400",
          mode === "ifta" && "left-3 top-1.5 text-theme-xs font-medium text-gray-400",
          mode === "float" && floated
            ? "left-3 top-0 -translate-y-1/2 bg-white px-1 text-theme-xs dark:bg-gray-900"
            : mode === "float"
              ? "left-3 top-1/2 -translate-y-1/2 text-theme-sm"
              : "",
        )}
      >
        {label}
        {required ? <span className="text-error-500"> *</span> : null}
      </label>
      {React.cloneElement(children, {
        id: childId,
        className: cn(children.props.className, mode === "float" && "pt-3"),
        onChange: (e: React.ChangeEvent<HTMLInputElement>) => {
          setFilled(Boolean(e.target.value));
          children.props.onChange?.(e);
        },
      })}
    </div>
  );
}
