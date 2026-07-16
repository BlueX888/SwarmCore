import * as React from "react";
import { cn } from "@/lib/utils";

export type OtpInputProps = {
  length?: 4 | 6 | 8;
  groupSize?: 2 | 3 | 4;
  value?: string;
  defaultValue?: string;
  disabled?: boolean;
  error?: boolean;
  expired?: boolean;
  resendPending?: boolean;
  onValueChange?: (value: string) => void;
  onResend?: () => void;
  className?: string;
};

export function OtpInput({
  length = 6,
  groupSize = 3,
  value,
  defaultValue = "",
  disabled = false,
  error = false,
  expired = false,
  resendPending = false,
  onValueChange,
  onResend,
  className,
}: OtpInputProps) {
  const isControlled = value !== undefined;
  const [internalValue, setInternalValue] = React.useState(defaultValue);
  const currentValue = (isControlled ? value : internalValue).slice(0, length);
  const inputsRef = React.useRef<Array<HTMLInputElement | null>>([]);

  const updateValue = (next: string) => {
    const trimmed = next.slice(0, length);
    if (!isControlled) {
      setInternalValue(trimmed);
    }
    onValueChange?.(trimmed);
  };

  const focusAt = (index: number) => {
    const target = inputsRef.current[index];
    target?.focus();
    target?.select();
  };

  const handleChange = (index: number, char: string) => {
    const digits = char.replace(/\D/g, "");
    if (!digits) return;
    const chars = currentValue.padEnd(length, " ").split("");
    chars[index] = digits[0];
    const next = chars.join("").trimEnd();
    updateValue(next);
    if (index < length - 1) {
      focusAt(index + 1);
    }
  };

  const handleKeyDown = (
    event: React.KeyboardEvent<HTMLInputElement>,
    index: number,
  ) => {
    if (event.key === "Backspace") {
      event.preventDefault();
      const chars = currentValue.padEnd(length, " ").split("");
      if (chars[index]?.trim()) {
        chars[index] = " ";
        updateValue(chars.join("").trimEnd());
      } else if (index > 0) {
        focusAt(index - 1);
      }
    }
    if (event.key === "ArrowLeft" && index > 0) focusAt(index - 1);
    if (event.key === "ArrowRight" && index < length - 1) focusAt(index + 1);
  };

  const handlePaste = (event: React.ClipboardEvent<HTMLInputElement>) => {
    event.preventDefault();
    const pasted = event.clipboardData.getData("text").replace(/\D/g, "").slice(0, length);
    updateValue(pasted);
    focusAt(Math.min(pasted.length, length - 1));
  };

  const cells = Array.from({ length }, (_, index) => index);
  const groups: number[][] = [];
  for (let i = 0; i < cells.length; i += groupSize) {
    groups.push(cells.slice(i, i + groupSize));
  }

  return (
    <div className={cn("space-y-3", className)}>
      <div className="flex flex-wrap items-center gap-2 sm:gap-4" role="group" aria-label="一次性验证码">
        {groups.map((group, groupIndex) => (
          <React.Fragment key={groupIndex}>
            <div className="flex gap-2 sm:gap-3">
              {group.map((index) => (
                <input
                  key={index}
                  ref={(node) => {
                    inputsRef.current[index] = node;
                  }}
                  type="text"
                  inputMode="numeric"
                  autoComplete="one-time-code"
                  maxLength={1}
                  value={currentValue[index] ?? ""}
                  disabled={disabled || expired}
                  aria-invalid={error || undefined}
                  onChange={(event) => handleChange(index, event.target.value)}
                  onKeyDown={(event) => handleKeyDown(event, index)}
                  onPaste={handlePaste}
                  className={cn(
                    "h-11 w-11 rounded-lg border bg-transparent text-center text-xl font-semibold text-gray-800 shadow-theme-xs focus:border-brand-300 focus:outline-hidden focus:ring-3 focus:ring-brand-500/10 dark:border-gray-700 dark:bg-gray-900 dark:text-white/90 sm:w-12",
                    error && "border-error-500 focus:ring-error-500/20",
                    (disabled || expired) && "cursor-not-allowed opacity-40",
                  )}
                />
              ))}
            </div>
            {groupIndex < groups.length - 1 ? (
              <span className="text-lg text-gray-400" aria-hidden="true">
                -
              </span>
            ) : null}
          </React.Fragment>
        ))}
      </div>
      {expired ? (
        <p className="text-xs text-error-500">Code expired. Request a new one.</p>
      ) : null}
      {onResend ? (
        <button
          type="button"
          onClick={onResend}
          disabled={resendPending || disabled}
          className="text-sm font-medium text-brand-500 hover:text-brand-600 disabled:opacity-50"
        >
          {resendPending ? "Sending…" : "Resend code"}
        </button>
      ) : null}
    </div>
  );
}
