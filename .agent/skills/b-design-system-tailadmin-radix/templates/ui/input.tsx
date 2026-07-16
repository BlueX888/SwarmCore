import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";
import { useFormContext } from "@/components/ui/form-context";

const fieldStateValues = ["default", "error", "success", "warning"] as const;
const inputSkinValues = ["outlined", "filled", "borderless", "underlined"] as const;

type FieldState = (typeof fieldStateValues)[number];
type InputSkin = (typeof inputSkinValues)[number];

const inputVariants = cva(
  "flex h-11 w-full px-4 py-2.5 text-sm transition-colors file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-gray-400 focus-visible:outline-hidden disabled:cursor-not-allowed disabled:opacity-40 dark:placeholder:text-gray-500",
  {
    variants: {
      inputSkin: {
        outlined:
          "rounded-lg border bg-transparent shadow-theme-xs disabled:bg-gray-100 dark:disabled:bg-gray-800",
        filled:
          "rounded-lg border border-transparent bg-gray-100 shadow-none dark:bg-white/5",
        borderless:
          "rounded-lg border border-transparent bg-transparent shadow-none",
        underlined:
          "rounded-none border-0 border-b bg-transparent px-0 shadow-none",
      },
      fieldState: {
        default:
          "border-gray-300 text-gray-800 focus-visible:border-brand-300 focus-visible:ring-3 focus-visible:ring-brand-500/20 dark:border-gray-700 dark:bg-gray-900 dark:text-white/90 dark:focus-visible:border-brand-800",
        error:
          "border-error-500 text-gray-800 focus-visible:ring-3 focus-visible:ring-error-500/20 dark:border-error-500 dark:text-white/90",
        success:
          "border-success-500 text-gray-800 focus-visible:ring-3 focus-visible:ring-success-500/20 dark:border-success-500 dark:text-white/90",
        warning:
          "border-warning-500 text-gray-800 focus-visible:ring-3 focus-visible:ring-warning-500/20 dark:border-warning-500 dark:text-white/90",
      },
      size: {
        sm: "h-9 px-3 py-2 text-xs",
        md: "h-11 px-4 py-2.5 text-sm",
        lg: "h-12 px-5 py-3 text-base",
      },
    },
    compoundVariants: [
      { inputSkin: "filled", fieldState: "default", className: "focus-visible:ring-3 focus-visible:ring-brand-500/20" },
      { inputSkin: "borderless", fieldState: "default", className: "focus-visible:ring-3 focus-visible:ring-brand-500/20" },
      { inputSkin: "underlined", fieldState: "default", className: "border-b-gray-300 focus-visible:border-b-brand-500 dark:border-b-gray-700" },
      { inputSkin: "underlined", fieldState: "error", className: "border-b-error-500" },
      { inputSkin: "underlined", fieldState: "success", className: "border-b-success-500" },
      { inputSkin: "underlined", fieldState: "warning", className: "border-b-warning-500" },
    ],
    defaultVariants: {
      inputSkin: "outlined",
      fieldState: "default",
      size: "md",
    },
  },
);

function resolveFieldState(
  fieldState?: FieldState | null,
  variant?: FieldState | null,
): FieldState {
  return fieldState ?? variant ?? "default";
}

export interface InputProps
  extends Omit<React.ComponentProps<"input">, "size">,
    VariantProps<typeof inputVariants> {
  /** @deprecated Use `fieldState` instead. */
  variant?: FieldState;
  fieldState?: FieldState;
  inputSkin?: InputSkin;
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type = "text", inputSkin: inputSkinProp, fieldState, variant, size, ...props }, ref) => {
    const formContext = useFormContext();
    const inputSkin = inputSkinProp ?? formContext.inputSkin;
    const resolvedFieldState = resolveFieldState(fieldState, variant);

    return (
      <input
        type={type}
        className={cn(
          inputVariants({
            inputSkin,
            fieldState: resolvedFieldState,
            size,
            className,
          }),
        )}
        ref={ref}
        {...props}
      />
    );
  },
);
Input.displayName = "Input";

export { Input, inputVariants, fieldStateValues, inputSkinValues };
