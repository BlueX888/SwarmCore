import * as React from "react";
import * as SheetPrimitive from "@radix-ui/react-dialog";
import { cva, type VariantProps } from "class-variance-authority";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";

const Sheet = SheetPrimitive.Root;
const SheetTrigger = SheetPrimitive.Trigger;
const SheetClose = SheetPrimitive.Close;
const SheetPortal = SheetPrimitive.Portal;

export type SheetOverlayProps = React.ComponentPropsWithoutRef<typeof SheetPrimitive.Overlay> & {
  blur?: boolean;
};

const SheetOverlay = React.forwardRef<
  React.ElementRef<typeof SheetPrimitive.Overlay>,
  SheetOverlayProps
>(({ className, blur = true, ...props }, ref) => (
  <SheetPrimitive.Overlay
    className={cn(
      "fixed inset-0 z-99999 bg-gray-400/50 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0",
      blur && "backdrop-blur-[32px]",
      className,
    )}
    {...props}
    ref={ref}
  />
));
SheetOverlay.displayName = SheetPrimitive.Overlay.displayName;

const sheetVariants = cva(
  "fixed z-99999 flex flex-col bg-white shadow-lg transition ease-in-out data-[state=closed]:duration-300 data-[state=open]:duration-300 data-[state=open]:animate-in data-[state=closed]:animate-out dark:bg-gray-900",
  {
    variants: {
      side: {
        top: "inset-x-0 top-0 border-b border-gray-200 data-[state=closed]:slide-out-to-top data-[state=open]:slide-in-from-top dark:border-gray-800",
        bottom:
          "inset-x-0 bottom-0 border-t border-gray-200 data-[state=closed]:slide-out-to-bottom data-[state=open]:slide-in-from-bottom dark:border-gray-800",
        left: "inset-y-0 left-0 h-full w-3/4 border-r border-gray-200 data-[state=closed]:slide-out-to-left data-[state=open]:slide-in-from-left sm:max-w-sm dark:border-gray-800",
        right:
          "inset-y-0 right-0 h-full border-l border-gray-200 data-[state=closed]:slide-out-to-right data-[state=open]:slide-in-from-right dark:border-gray-800",
      },
      size: {
        filter: "w-[400px] sm:max-w-[400px]",
        edit: "w-[480px] sm:max-w-[480px]",
        default: "w-[378px] sm:max-w-[378px]",
        large: "w-[736px] sm:max-w-[736px]",
        full: "w-full sm:max-w-lg",
      },
      variant: {
        /** 浮层 + 遮罩（默认） */
        temporary: "",
        /**
         * 无遮罩，挤占主内容区；父级需 flex/grid 布局为 Sheet 留出空间。
         * @see references/component-styles/overlay-template.md#sheet-variant-语义
         */
        persistent: "shadow-none ring-1 ring-gray-200 dark:ring-gray-800",
        /** 窄侧栏面板，宽度对齐 AppSidebar 折叠态 w-[90px] */
        mini: "w-[90px] sm:max-w-[90px]",
      },
    },
    defaultVariants: {
      side: "right",
      size: "filter",
      variant: "temporary",
    },
  },
);

export interface SheetContentProps
  extends React.ComponentPropsWithoutRef<typeof SheetPrimitive.Content>,
    VariantProps<typeof sheetVariants> {
  resizable?: boolean;
  push?: boolean;
  stackIndex?: number;
  overlayBlur?: boolean;
  /** 默认 true；`variant="persistent"` 时为 false */
  showOverlay?: boolean;
}

const MIN_SHEET_WIDTH = 320;
const MAX_SHEET_WIDTH = 960;

const SheetContent = React.forwardRef<
  React.ElementRef<typeof SheetPrimitive.Content>,
  SheetContentProps
>(
  (
    {
      side = "right",
      size = "filter",
      variant = "temporary",
      className,
      children,
      resizable = false,
      push = false,
      stackIndex = 0,
      overlayBlur = true,
      showOverlay: showOverlayProp,
      style,
      ...props
    },
    ref,
  ) => {
    const [width, setWidth] = React.useState<number | null>(null);
    const isHorizontal = side === "left" || side === "right";

    const handleResizePointerDown = (event: React.PointerEvent<HTMLDivElement>) => {
      if (!resizable || !isHorizontal) return;
      event.preventDefault();
      const startX = event.clientX;
      const startWidth = (event.currentTarget.parentElement as HTMLElement | null)?.offsetWidth ?? 400;

      const handleMove = (moveEvent: PointerEvent) => {
        const delta = side === "right" ? startX - moveEvent.clientX : moveEvent.clientX - startX;
        const next = Math.min(MAX_SHEET_WIDTH, Math.max(MIN_SHEET_WIDTH, startWidth + delta));
        setWidth(next);
      };

      const handleUp = () => {
        window.removeEventListener("pointermove", handleMove);
        window.removeEventListener("pointerup", handleUp);
      };

      window.addEventListener("pointermove", handleMove);
      window.addEventListener("pointerup", handleUp);
    };

    const isMini = variant === "mini";
    const showOverlay = showOverlayProp ?? variant !== "persistent";

    return (
      <SheetPortal>
        {showOverlay ? <SheetOverlay blur={overlayBlur} /> : null}
        <SheetPrimitive.Content
          ref={ref}
          data-stack-index={push ? stackIndex : undefined}
          className={cn(
            sheetVariants({ side, size: isMini ? undefined : size, variant: isMini ? "mini" : variant }),
            "p-0",
            push && stackIndex > 0 && "translate-x-[calc(var(--sheet-stack-index,0)*-12px)]",
            className,
          )}
          style={{
            ...style,
            ...(width != null && isHorizontal
              ? { width, maxWidth: width }
              : undefined),
            ...(push ? ({ "--sheet-stack-index": stackIndex } as React.CSSProperties) : undefined),
          }}
          {...props}
        >
          {resizable && isHorizontal ? (
            <div
              role="separator"
              aria-orientation="vertical"
              aria-label="调整面板宽度"
              className={cn(
                "absolute top-0 z-10 h-full w-1 cursor-col-resize bg-transparent hover:bg-brand-500/30",
                side === "right" ? "left-0" : "right-0",
              )}
              onPointerDown={handleResizePointerDown}
            />
          ) : null}
          {children}
          <SheetPrimitive.Close className="absolute right-4 top-4 rounded-lg p-1 text-gray-500 opacity-70 ring-offset-white transition-opacity hover:bg-gray-100 hover:opacity-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500/20 disabled:pointer-events-none dark:text-gray-400 dark:ring-offset-gray-900 dark:hover:bg-white/5">
            <X className="size-4" />
            <span className="sr-only">关闭</span>
          </SheetPrimitive.Close>
        </SheetPrimitive.Content>
      </SheetPortal>
    );
  },
);
SheetContent.displayName = SheetPrimitive.Content.displayName;

const SheetHeader = ({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) => (
  <div
    className={cn(
      "flex flex-col gap-1 border-b border-gray-200 px-6 py-5 dark:border-gray-800",
      className,
    )}
    {...props}
  />
);
SheetHeader.displayName = "SheetHeader";

const SheetFooter = ({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) => (
  <div
    className={cn(
      "flex flex-col-reverse gap-2 border-t border-gray-100 px-6 py-4 sm:flex-row sm:justify-end sm:gap-3 dark:border-white/[0.05]",
      className,
    )}
    {...props}
  />
);
SheetFooter.displayName = "SheetFooter";

const SheetTitle = React.forwardRef<
  React.ElementRef<typeof SheetPrimitive.Title>,
  React.ComponentPropsWithoutRef<typeof SheetPrimitive.Title>
>(({ className, ...props }, ref) => (
  <SheetPrimitive.Title
    ref={ref}
    className={cn(
      "text-base font-semibold text-gray-800 dark:text-white/90",
      className,
    )}
    {...props}
  />
));
SheetTitle.displayName = SheetPrimitive.Title.displayName;

const SheetDescription = React.forwardRef<
  React.ElementRef<typeof SheetPrimitive.Description>,
  React.ComponentPropsWithoutRef<typeof SheetPrimitive.Description>
>(({ className, ...props }, ref) => (
  <SheetPrimitive.Description
    ref={ref}
    className={cn("text-sm text-gray-500 dark:text-gray-400", className)}
    {...props}
  />
));
SheetDescription.displayName = SheetPrimitive.Description.displayName;

export {
  Sheet,
  SheetPortal,
  SheetOverlay,
  SheetTrigger,
  SheetClose,
  SheetContent,
  SheetHeader,
  SheetFooter,
  SheetTitle,
  SheetDescription,
  sheetVariants,
};
