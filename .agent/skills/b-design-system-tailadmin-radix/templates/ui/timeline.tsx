import * as React from "react";
import { Check, Clock, X } from "lucide-react";
import { cn } from "@/lib/utils";
import { Spinner } from "@/components/ui/spinner";

export type TimelineItemStatus = "default" | "success" | "error" | "warning" | "pending";

export type TimelineItem = {
  id: string;
  title: React.ReactNode;
  description?: React.ReactNode;
  timestamp?: React.ReactNode;
  icon?: React.ReactNode;
  status?: TimelineItemStatus;
};

export type TimelineProps = {
  items: TimelineItem[];
  mode?: "left" | "alternate" | "right";
  pending?: React.ReactNode;
  size?: "sm" | "md";
  className?: string;
  ariaLabel?: string;
};

const statusNodeClass: Record<TimelineItemStatus, string> = {
  default: "border-gray-200 text-gray-500 dark:border-gray-700",
  success: "border-success-500/40 text-success-600",
  error: "border-error-500/40 text-error-600",
  warning: "border-warning-500/40 text-warning-600",
  pending: "border-warning-500/40 text-warning-600",
};

const defaultStatusIcon: Record<TimelineItemStatus, React.ReactNode> = {
  default: null,
  success: <Check className="size-4" aria-hidden />,
  error: <X className="size-4" aria-hidden />,
  warning: <Clock className="size-4" aria-hidden />,
  pending: <Spinner size="sm" className="text-warning-600" />,
};

function TimelineNode({
  status = "default",
  icon,
  className,
}: {
  status?: TimelineItemStatus;
  icon?: React.ReactNode;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "relative z-10 flex size-8 shrink-0 items-center justify-center rounded-full border bg-white dark:bg-gray-900",
        statusNodeClass[status],
        className,
      )}
    >
      {icon ?? defaultStatusIcon[status]}
    </span>
  );
}

function TimelineContent({
  item,
  size,
  align,
}: {
  item: TimelineItem;
  size: "sm" | "md";
  align?: "left" | "right" | "center";
}) {
  return (
    <div
      className={cn(
        "min-w-0 flex-1 pt-0.5",
        align === "right" && "text-right",
        align === "center" && "text-center",
      )}
    >
      <div
        className={cn(
          size === "sm" ? "text-theme-sm" : "text-theme-sm md:text-base",
          "font-medium text-gray-900 dark:text-white/90",
        )}
      >
        {item.title}
      </div>
      {item.timestamp ? (
        <p
          className={cn(
            "mt-0.5 tabular-nums text-gray-500",
            size === "sm" ? "text-theme-xs" : "text-theme-sm",
          )}
        >
          {item.timestamp}
        </p>
      ) : null}
      {item.description ? (
        <div
          className={cn(
            "mt-2 text-gray-600 dark:text-gray-400",
            size === "sm" ? "text-theme-sm" : "text-theme-sm",
          )}
        >
          {item.description}
        </div>
      ) : null}
    </div>
  );
}

function TimelineConnector({
  className,
  isLast,
}: {
  className?: string;
  isLast: boolean;
}) {
  if (isLast) return null;
  return (
    <span
      className={cn(
        "absolute top-8 h-[calc(100%-1rem)] w-px bg-gray-200 dark:bg-gray-800",
        className,
      )}
      aria-hidden
    />
  );
}

export function Timeline({
  items,
  mode = "left",
  pending,
  size = "md",
  className,
  ariaLabel = "时间线",
}: TimelineProps) {
  const allItems = pending
    ? [
        ...items,
        {
          id: "__pending__",
          title: pending,
          status: "pending" as const,
        },
      ]
    : items;

  if (mode === "alternate") {
    return (
      <ol className={cn("space-y-0", className)} aria-label={ariaLabel}>
        {allItems.map((item, index) => {
          const isLast = index === allItems.length - 1;
          const isRight = index % 2 === 0;

          return (
            <li
              key={item.id}
              className={cn("relative grid grid-cols-[1fr_auto_1fr] gap-x-4", size === "sm" ? "pb-4" : "pb-6")}
            >
              <div className="col-start-1 min-w-0">
                {!isRight ? (
                  <TimelineContent item={item} size={size} align="right" />
                ) : null}
              </div>
              <div className="relative col-start-2 flex flex-col items-center">
                <TimelineConnector className="left-1/2 -translate-x-1/2" isLast={isLast} />
                <TimelineNode status={item.status} icon={item.icon} />
              </div>
              <div className="col-start-3 min-w-0">
                {isRight ? <TimelineContent item={item} size={size} align="left" /> : null}
              </div>
            </li>
          );
        })}
      </ol>
    );
  }

  const isRight = mode === "right";

  return (
    <ol className={cn("space-y-0", className)} aria-label={ariaLabel}>
      {allItems.map((item, index) => {
        const isLast = index === allItems.length - 1;

        return (
          <li
            key={item.id}
            className={cn(
              "relative flex gap-3",
              isRight && "flex-row-reverse",
              size === "sm" ? "pb-4 last:pb-0" : "pb-6 last:pb-0",
            )}
          >
            <TimelineConnector
              className={isRight ? "right-[15px]" : "left-[15px]"}
              isLast={isLast}
            />
            <TimelineNode status={item.status} icon={item.icon} />
            <TimelineContent item={item} size={size} align={isRight ? "right" : "left"} />
          </li>
        );
      })}
    </ol>
  );
}
