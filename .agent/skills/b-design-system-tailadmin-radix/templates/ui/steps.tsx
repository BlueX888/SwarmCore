import * as React from "react";
import { Check } from "lucide-react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

export type StepStatus = "wait" | "process" | "finish" | "error";

export type StepItem = {
  id: string;
  title: React.ReactNode;
  description?: React.ReactNode;
  status?: StepStatus;
};

const stepsVariants = cva("flex", {
  variants: {
    orientation: {
      horizontal: "flex-row items-start gap-2",
      vertical: "flex-col gap-4",
    },
    variant: {
      solid: "",
      subtle: "",
    },
    size: {
      sm: "text-xs",
      md: "text-sm",
      lg: "text-base",
    },
    type: {
      default: "",
      navigation: "",
      dot: "",
    },
  },
  defaultVariants: {
    orientation: "horizontal",
    variant: "solid",
    size: "md",
    type: "default",
  },
});

const stepIndicatorVariants = cva(
  "flex shrink-0 items-center justify-center rounded-full font-semibold",
  {
    variants: {
      variant: {
        solid: "",
        subtle: "ring-1 ring-inset",
      },
      status: {
        wait: "bg-gray-100 text-gray-500 ring-gray-200 dark:bg-white/5 dark:text-gray-400 dark:ring-gray-700",
        process: "bg-brand-500 text-white ring-brand-500",
        finish: "bg-success-500 text-white ring-success-500",
        error: "bg-error-500 text-white ring-error-500",
      },
      size: {
        sm: "size-6 text-[10px]",
        md: "size-8 text-xs",
        lg: "size-10 text-sm",
      },
      type: {
        default: "",
        navigation: "",
        dot: "size-2.5 p-0 text-transparent ring-2 ring-offset-2 ring-offset-white dark:ring-offset-gray-900",
      },
    },
    compoundVariants: [
      { type: "dot", size: "sm", className: "size-2 ring-offset-1" },
      { type: "dot", size: "lg", className: "size-3 ring-offset-2" },
      { type: "dot", status: "wait", className: "bg-gray-300 ring-gray-200 dark:bg-gray-600 dark:ring-gray-700" },
      { type: "dot", status: "process", className: "bg-brand-500 ring-brand-200 dark:ring-brand-500/40" },
      { type: "dot", status: "finish", className: "bg-success-500 ring-success-200 dark:ring-success-500/40" },
      { type: "dot", status: "error", className: "bg-error-500 ring-error-200 dark:ring-error-500/40" },
    ],
    defaultVariants: {
      variant: "solid",
      status: "wait",
      size: "md",
      type: "default",
    },
  },
);

function resolveStatus(step: StepItem, index: number, currentIndex: number): StepStatus {
  if (step.status) return step.status;
  if (index < currentIndex) return "finish";
  if (index === currentIndex) return "process";
  return "wait";
}

export type StepsMobileVariant = "dots" | "text" | "progress";

export type StepsProps = VariantProps<typeof stepsVariants> & {
  items: StepItem[];
  current?: number;
  className?: string;
  onStepClick?: (index: number, item: StepItem) => void;
  /** `<md` 时使用的紧凑布局；默认 `dots` */
  mobileVariant?: StepsMobileVariant;
  /** 为 true 时在 `<md` 自动切换 mobileVariant；默认 true */
  responsive?: boolean;
};

function abbreviateTitle(title: React.ReactNode, maxLength = 4): React.ReactNode {
  if (typeof title === "string") {
    return title.length > maxLength ? `${title.slice(0, maxLength)}…` : title;
  }
  return title;
}

function useIsBelowMd(enabled: boolean): boolean {
  const [isBelowMd, setIsBelowMd] = React.useState(false);

  React.useEffect(() => {
    if (!enabled) {
      setIsBelowMd(false);
      return;
    }

    const query = window.matchMedia("(max-width: 767px)");
    const update = () => setIsBelowMd(query.matches);
    update();
    query.addEventListener("change", update);
    return () => query.removeEventListener("change", update);
  }, [enabled]);

  return enabled && isBelowMd;
}

function StepsMobileLayout({
  items,
  current,
  mobileVariant,
  variant,
  size,
  onStepClick,
}: Pick<StepsProps, "items" | "current" | "mobileVariant" | "variant" | "size" | "onStepClick">) {
  const activeIndex = current ?? 0;
  const progressPercent = items.length > 0 ? ((activeIndex + 1) / items.length) * 100 : 0;

  if (mobileVariant === "progress") {
    return (
      <div className="space-y-2" aria-label="步骤进度">
        <div
          className="h-1 w-full overflow-hidden rounded-full bg-gray-200 dark:bg-gray-700"
          role="progressbar"
          aria-valuemin={0}
          aria-valuemax={items.length}
          aria-valuenow={activeIndex + 1}
        >
          <div
            className="h-full rounded-full bg-brand-500 transition-[width]"
            style={{ width: `${progressPercent}%` }}
          />
        </div>
        <p className="text-sm font-medium text-gray-800 dark:text-white/90">{items[activeIndex]?.title}</p>
      </div>
    );
  }

  return (
    <ol
      className={cn(
        "flex items-center gap-2",
        mobileVariant === "dots" && "justify-center",
        mobileVariant === "text" && "gap-1 overflow-x-auto",
      )}
      aria-label="步骤进度"
    >
      {items.map((item, index) => {
        const status = resolveStatus(item, index, activeIndex);
        const isClickable = Boolean(onStepClick);

        const indicator = (
          <span className={cn(stepIndicatorVariants({ variant, status, size, type: "dot" }))} />
        );

        const content =
          mobileVariant === "dots" ? (
            indicator
          ) : (
            <>
              {indicator}
              <span
                className={cn(
                  "text-xs font-medium text-gray-600 dark:text-gray-300",
                  status === "process" && "text-brand-600 dark:text-brand-400",
                )}
              >
                {abbreviateTitle(item.title)}
              </span>
            </>
          );

        return (
          <li key={item.id} className="flex shrink-0 items-center gap-1">
            {isClickable ? (
              <button
                type="button"
                className="inline-flex items-center gap-1 rounded-md px-1 py-0.5"
                onClick={() => onStepClick?.(index, item)}
                aria-current={index === activeIndex ? "step" : undefined}
              >
                {content}
              </button>
            ) : (
              <div className="inline-flex items-center gap-1" aria-current={index === current ? "step" : undefined}>
                {content}
              </div>
            )}
          </li>
        );
      })}
    </ol>
  );
}

export function Steps({
  items,
  current = 0,
  orientation = "horizontal",
  variant = "solid",
  size = "md",
  type = "default",
  className,
  onStepClick,
  mobileVariant = "dots",
  responsive = true,
}: StepsProps) {
  const isNavigation = type === "navigation";
  const isDot = type === "dot";
  const showMobile = useIsBelowMd(responsive);

  const desktopSteps = (
    <ol
      className={cn(stepsVariants({ orientation, variant, size, type }), !showMobile ? className : "hidden md:flex")}
      aria-label="步骤进度"
    >
      {items.map((item, index) => {
        const status = resolveStatus(item, index, current);
        const isLast = index === items.length - 1;
        const isClickable = isNavigation && Boolean(onStepClick);

        const stepContent = (
          <>
            <div className={cn("flex items-center gap-2", orientation === "horizontal" && "w-full")}>
              <span className={cn(stepIndicatorVariants({ variant, status, size, type }))}>
                {!isDot && (status === "finish" ? <Check className="size-3.5" /> : index + 1)}
              </span>
              {!isLast && orientation === "horizontal" ? (
                <span
                  className={cn(
                    "hidden h-px flex-1 sm:block",
                    status === "finish" ? "bg-success-500" : "bg-gray-200 dark:bg-gray-700",
                  )}
                  aria-hidden
                />
              ) : null}
            </div>
            <div className="min-w-0 space-y-0.5">
              <p
                className={cn(
                  "font-medium text-gray-800 dark:text-white/90",
                  isNavigation && status === "process" && "text-brand-600 dark:text-brand-400",
                  isClickable && "transition-colors hover:text-brand-500",
                )}
              >
                {item.title}
              </p>
              {item.description ? (
                <p className="text-theme-xs text-gray-500 dark:text-gray-400">{item.description}</p>
              ) : null}
            </div>
          </>
        );

        return (
          <li
            key={item.id}
            className={cn(
              "flex min-w-0",
              orientation === "horizontal" ? "flex-1 flex-col gap-2" : "flex-row gap-3",
            )}
          >
            {isClickable ? (
              <button
                type="button"
                className={cn(
                  "flex min-w-0 text-left",
                  orientation === "horizontal" ? "flex-1 flex-col gap-2" : "flex-row gap-3",
                )}
                onClick={() => onStepClick?.(index, item)}
                aria-current={index === activeIndex ? "step" : undefined}
              >
                {stepContent}
              </button>
            ) : (
              <div
                className={cn(
                  "flex min-w-0",
                  orientation === "horizontal" ? "flex-1 flex-col gap-2" : "flex-row gap-3",
                )}
                aria-current={index === activeIndex ? "step" : undefined}
              >
                {stepContent}
              </div>
            )}
          </li>
        );
      })}
    </ol>
  );

  if (!responsive) {
    return desktopSteps;
  }

  return (
    <>
      <div className={cn("md:hidden", className)}>
        <StepsMobileLayout
          items={items}
          current={current}
          mobileVariant={mobileVariant}
          variant={variant}
          size={size}
          onStepClick={onStepClick}
        />
      </div>
      {desktopSteps}
    </>
  );
}

export { stepsVariants, stepIndicatorVariants };
