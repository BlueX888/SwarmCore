import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import * as React from "react";
import { cn } from "@/lib/utils";

export const buttonVariants = cva(
  "inline-flex shrink-0 items-center justify-center gap-2 rounded-xl text-sm font-semibold transition-all duration-200 focus-visible:outline-hidden focus-visible:ring-3 focus-visible:ring-brand-500/20 active:scale-[0.98] disabled:pointer-events-none disabled:opacity-50 disabled:shadow-none [&_svg]:size-5",
  {
    variants: {
      variant: {
        primary: "bg-brand-500 text-white shadow-theme-float hover:-translate-y-0.5 hover:bg-brand-600",
        outline: "bg-white/80 text-gray-700 shadow-theme-xs ring-1 ring-gray-200 backdrop-blur hover:-translate-y-0.5 hover:bg-white hover:ring-gray-300 dark:bg-gray-800/80 dark:text-gray-300 dark:ring-gray-700 dark:hover:bg-gray-800",
        ghost: "text-gray-700 hover:bg-gray-100/80 hover:text-gray-900 dark:text-gray-300 dark:hover:bg-white/5 dark:hover:text-white",
        destructive: "bg-error-500 text-white shadow-theme-xs hover:-translate-y-0.5 hover:bg-error-600",
      },
      size: { sm: "h-10 px-4", md: "h-11 px-5", icon: "size-11" },
    },
    defaultVariants: { variant: "primary", size: "md" },
  },
);

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement>, VariantProps<typeof buttonVariants> {
  asChild?: boolean;
  loading?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, loading = false, disabled, children, ...props }, ref) => {
    if (asChild) {
      return (
        <Slot ref={ref} className={cn(buttonVariants({ variant, size }), className)} {...props}>
          {children}
        </Slot>
      );
    }
    return (
      <button ref={ref} className={cn(buttonVariants({ variant, size }), className)} disabled={disabled || loading} aria-busy={loading || undefined} {...props}>
        {loading ? <span aria-hidden className="size-4 animate-spin rounded-full border-2 border-current border-t-transparent" /> : null}
        {children}
      </button>
    );
  },
);
Button.displayName = "Button";
