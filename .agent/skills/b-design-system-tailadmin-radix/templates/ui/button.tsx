import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex shrink-0 items-center justify-center gap-2 whitespace-nowrap rounded-lg text-sm font-medium transition-colors focus-visible:outline-hidden focus-visible:ring-3 focus-visible:ring-brand-500/20 disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-5 [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        solid:
          "bg-brand-500 text-white shadow-theme-xs hover:bg-brand-600 disabled:bg-brand-300",
        primary:
          "bg-brand-500 text-white shadow-theme-xs hover:bg-brand-600 disabled:bg-brand-300",
        subtle:
          "bg-brand-50 text-brand-700 hover:bg-brand-100 dark:bg-brand-500/15 dark:text-brand-300 dark:hover:bg-brand-500/20",
        surface:
          "bg-brand-50 text-brand-700 ring-1 ring-inset ring-brand-200 hover:bg-brand-100 dark:bg-brand-500/10 dark:text-brand-300 dark:ring-brand-500/20 dark:hover:bg-brand-500/15",
        outline:
          "bg-white text-gray-700 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 dark:bg-gray-800 dark:text-gray-400 dark:ring-gray-700 dark:hover:bg-white/[0.03] dark:hover:text-gray-300",
        ghost:
          "text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-white/5",
        dashed:
          "border border-dashed border-gray-300 bg-white text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-900 dark:text-gray-300 dark:hover:bg-white/[0.03]",
        filled:
          "bg-gray-100 text-gray-800 hover:bg-gray-200 dark:bg-white/10 dark:text-white/90 dark:hover:bg-white/15",
        plain:
          "h-auto min-h-0 px-0 py-0 text-brand-500 hover:text-brand-600 dark:text-brand-400 dark:hover:text-brand-300",
        destructive:
          "bg-error-500 text-white shadow-theme-xs hover:bg-error-600",
      },
      size: {
        xs: "h-8 min-w-8 px-3 text-xs",
        sm: "px-4 py-3",
        md: "px-5 py-3.5",
        lg: "px-6 py-4 text-base",
        icon: "size-11",
      },
    },
    defaultVariants: {
      variant: "primary",
      size: "md",
    },
  },
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
  loading?: boolean;
  loadingText?: React.ReactNode;
  spinner?: React.ReactNode;
  spinnerPlacement?: "start" | "end";
}

function ButtonSpinner({ className }: { className?: string }) {
  return (
    <span
      aria-hidden="true"
      className={cn(
        "size-4 animate-spin rounded-full border-2 border-current border-t-transparent opacity-80",
        className,
      )}
    />
  );
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant,
      size,
      asChild = false,
      disabled,
      loading = false,
      loadingText,
      spinner,
      spinnerPlacement = "start",
      children,
      ...props
    },
    ref,
  ) => {
    const Comp = asChild ? Slot : "button";
    const loadingIndicator = spinner ?? <ButtonSpinner />;
    const content = loading && loadingText ? loadingText : children;
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        aria-busy={loading || undefined}
        disabled={!asChild ? disabled || loading : undefined}
        data-loading={loading || undefined}
        ref={ref}
        {...props}
      >
        {loading && spinnerPlacement === "start" ? loadingIndicator : null}
        {content}
        {loading && spinnerPlacement === "end" ? loadingIndicator : null}
      </Comp>
    );
  },
);
Button.displayName = "Button";

export interface IconButtonProps extends Omit<ButtonProps, "size"> {
  "aria-label": string;
  size?: "xs" | "sm" | "md" | "lg" | "icon";
  rounded?: "default" | "full";
}

const IconButton = React.forwardRef<HTMLButtonElement, IconButtonProps>(
  ({ className, size = "icon", rounded = "default", children, ...props }, ref) => {
    const iconSizeClass = {
      xs: "size-8",
      sm: "size-9",
      md: "size-11",
      lg: "size-12",
      icon: "size-11",
    }[size];

    return (
      <Button
        ref={ref}
        size="icon"
        className={cn(iconSizeClass, rounded === "full" && "rounded-full", className)}
        {...props}
      >
        {children}
      </Button>
    );
  },
);
IconButton.displayName = "IconButton";

export interface CloseButtonProps extends Omit<IconButtonProps, "aria-label"> {
  "aria-label"?: string;
}

const CloseButton = React.forwardRef<HTMLButtonElement, CloseButtonProps>(
  ({ children, variant = "ghost", "aria-label": ariaLabel = "Close", ...props }, ref) => (
    <IconButton ref={ref} aria-label={ariaLabel} variant={variant} {...props}>
      {children ?? <X />}
    </IconButton>
  ),
);
CloseButton.displayName = "CloseButton";

type DownloadPayload = string | Blob | File;

export interface DownloadTriggerProps
  extends Omit<ButtonProps, "onClick"> {
  data: DownloadPayload | Promise<DownloadPayload>;
  fileName: string;
  mimeType?: string;
  onClick?: React.MouseEventHandler<HTMLButtonElement>;
  onDownloaded?: () => void;
}

const DownloadTrigger = React.forwardRef<HTMLButtonElement, DownloadTriggerProps>(
  ({ data, fileName, mimeType = "application/octet-stream", onClick, onDownloaded, children = "Download", ...props }, ref) => {
    const handleClick: React.MouseEventHandler<HTMLButtonElement> = async (event) => {
      onClick?.(event);
      if (event.defaultPrevented || typeof document === "undefined") return;

      const payload = await data;
      const blob = payload instanceof Blob ? payload : new Blob([payload], { type: mimeType });
      const objectUrl = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = objectUrl;
      link.download = payload instanceof File ? payload.name : fileName;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(objectUrl);
      onDownloaded?.();
    };

    return (
      <Button ref={ref} onClick={handleClick} {...props}>
        {children}
      </Button>
    );
  },
);
DownloadTrigger.displayName = "DownloadTrigger";

export { Button, ButtonSpinner, CloseButton, DownloadTrigger, IconButton, buttonVariants };
