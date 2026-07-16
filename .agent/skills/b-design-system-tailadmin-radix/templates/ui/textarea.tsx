import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const textareaVariants = cva(
  "flex w-full resize-y rounded-lg border bg-transparent px-4 py-3 text-sm shadow-theme-xs transition-colors placeholder:text-gray-400 focus-visible:outline-hidden disabled:cursor-not-allowed disabled:opacity-40 disabled:bg-gray-100 dark:disabled:bg-gray-800 dark:placeholder:text-gray-500",
  {
    variants: {
      variant: {
        default:
          "border-gray-300 text-gray-800 focus-visible:border-brand-300 focus-visible:ring-3 focus-visible:ring-brand-500/20 dark:border-gray-700 dark:bg-gray-900 dark:text-white/90 dark:focus-visible:border-brand-800",
        error:
          "border-error-500 text-gray-800 focus-visible:ring-3 focus-visible:ring-error-500/20 dark:border-error-500 dark:text-white/90",
        success:
          "border-success-500 text-gray-800 focus-visible:ring-3 focus-visible:ring-success-500/20 dark:border-success-500 dark:text-white/90",
      },
      autosize: {
        true: "resize-none overflow-hidden",
        false: "min-h-[120px]",
      },
    },
    defaultVariants: {
      variant: "default",
      autosize: false,
    },
  },
);

const LINE_HEIGHT_PX = 20;
const VERTICAL_PADDING_PX = 24;

export interface TextareaProps
  extends React.ComponentProps<"textarea">,
    VariantProps<typeof textareaVariants> {
  autosize?: boolean;
  minRows?: number;
  maxRows?: number;
}

function resizeTextarea(
  element: HTMLTextAreaElement,
  minRows: number,
  maxRows?: number,
) {
  element.style.height = "auto";
  const minHeight = minRows * LINE_HEIGHT_PX + VERTICAL_PADDING_PX;
  const maxHeight = maxRows ? maxRows * LINE_HEIGHT_PX + VERTICAL_PADDING_PX : undefined;
  const nextHeight = Math.max(minHeight, element.scrollHeight);
  element.style.height = `${maxHeight ? Math.min(nextHeight, maxHeight) : nextHeight}px`;
  element.style.overflowY = maxHeight && nextHeight > maxHeight ? "auto" : "hidden";
}

const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  (
    {
      className,
      variant,
      autosize = false,
      minRows = 3,
      maxRows,
      onChange,
      value,
      defaultValue,
      ...props
    },
    ref,
  ) => {
    const innerRef = React.useRef<HTMLTextAreaElement | null>(null);

    const setRefs = React.useCallback(
      (node: HTMLTextAreaElement | null) => {
        innerRef.current = node;
        if (typeof ref === "function") {
          ref(node);
        } else if (ref) {
          ref.current = node;
        }
      },
      [ref],
    );

    React.useEffect(() => {
      if (!autosize || !innerRef.current) return;
      resizeTextarea(innerRef.current, minRows, maxRows);
    }, [autosize, minRows, maxRows, value, defaultValue]);

    const handleChange = (event: React.ChangeEvent<HTMLTextAreaElement>) => {
      if (autosize) {
        resizeTextarea(event.currentTarget, minRows, maxRows);
      }
      onChange?.(event);
    };

    return (
      <textarea
        className={cn(textareaVariants({ variant, autosize }), className)}
        ref={setRefs}
        rows={autosize ? minRows : undefined}
        value={value}
        defaultValue={defaultValue}
        onChange={handleChange}
        {...props}
      />
    );
  },
);
Textarea.displayName = "Textarea";

export { Textarea, textareaVariants };
