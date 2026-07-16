import * as React from "react";
import { cn } from "@/lib/utils";
import { Input, type InputProps } from "@/components/ui/input";

export type MaskPreset = "phone" | "id" | "license" | "ip" | "cidr" | "custom";

export type MaskedInputProps = Omit<InputProps, "value" | "defaultValue" | "onChange"> & {
  preset?: MaskPreset;
  mask?: string;
  maskChar?: string;
  value?: string;
  defaultValue?: string;
  hint?: string;
  onValueChange?: (raw: string, normalized: string) => void;
};

const PRESET_MASKS: Record<Exclude<MaskPreset, "custom">, string> = {
  phone: "(###) ###-####",
  id: "###-##-####",
  license: "XXXX-XXXX-XXXX-XXXX",
  ip: "###.###.###.###",
  cidr: "##.##.##.##/##",
};

function applyMask(raw: string, mask: string, maskChar = "#"): string {
  const digits = raw.replace(/\D/g, "");
  let cursor = 0;
  let output = "";
  for (const char of mask) {
    if (char === maskChar || char === "X") {
      if (cursor >= digits.length) break;
      output += digits[cursor];
      cursor += 1;
    } else {
      if (cursor < digits.length || output.length > 0) {
        output += char;
      }
    }
  }
  return output;
}

function normalizeValue(raw: string, preset: MaskPreset): string {
  if (preset === "ip" || preset === "cidr") {
    return raw.replace(/[^\d./]/g, "");
  }
  return raw.replace(/\D/g, "");
}

export const MaskedInput = React.forwardRef<HTMLInputElement, MaskedInputProps>(
  (
    {
      className,
      preset = "phone",
      mask,
      maskChar = "#",
      value,
      defaultValue = "",
      hint,
      disabled,
      readOnly,
      onValueChange,
      variant,
      ...props
    },
    ref,
  ) => {
    const resolvedMask =
      preset === "custom" ? mask ?? "" : PRESET_MASKS[preset as Exclude<MaskPreset, "custom">];
    const isControlled = value !== undefined;
    const [internalValue, setInternalValue] = React.useState(defaultValue);
    const currentValue = isControlled ? value ?? "" : internalValue;
    const displayValue = resolvedMask
      ? applyMask(currentValue, resolvedMask, maskChar)
      : currentValue;

    const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
      const normalized = normalizeValue(event.target.value, preset);
      if (!isControlled) {
        setInternalValue(normalized);
      }
      onValueChange?.(normalized, applyMask(normalized, resolvedMask, maskChar));
    };

    const handlePaste = (event: React.ClipboardEvent<HTMLInputElement>) => {
      event.preventDefault();
      const pasted = event.clipboardData.getData("text");
      const normalized = normalizeValue(pasted, preset);
      if (!isControlled) {
        setInternalValue(normalized);
      }
      onValueChange?.(normalized, applyMask(normalized, resolvedMask, maskChar));
    };

    return (
      <div className={cn("space-y-1", className)}>
        <Input
          ref={ref}
          value={displayValue}
          disabled={disabled}
          readOnly={readOnly}
          variant={variant}
          onChange={handleChange}
          onPaste={handlePaste}
          inputMode={preset === "ip" || preset === "cidr" ? "text" : "numeric"}
          {...props}
        />
        {hint ? <p className="text-xs text-gray-500 dark:text-gray-400">{hint}</p> : null}
      </div>
    );
  },
);
MaskedInput.displayName = "MaskedInput";
