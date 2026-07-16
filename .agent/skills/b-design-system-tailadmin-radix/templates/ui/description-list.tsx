import * as React from "react";
import { cn } from "@/lib/utils";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export type DescriptionItem = {
  label: React.ReactNode;
  value: React.ReactNode;
  /** 跨列占位，用于长文本或代码块 */
  span?: 1 | 2;
  className?: string;
};

export type DescriptionSectionProps = {
  title?: React.ReactNode;
  description?: React.ReactNode;
  items: DescriptionItem[];
  columns?: 1 | 2;
  layout?: DescriptionListLayout;
  bordered?: boolean;
  className?: string;
};

export type DescriptionListLayout = "horizontal" | "stack-on-mobile";

export type DescriptionListProps = {
  items: DescriptionItem[];
  columns?: 1 | 2;
  labelWidth?: "sm" | "md" | "lg";
  /** horizontal：始终 label/value 横排；stack-on-mobile：max-md 纵向堆叠 */
  layout?: DescriptionListLayout;
  className?: string;
};

const labelWidthClass: Record<NonNullable<DescriptionListProps["labelWidth"]>, string> = {
  sm: "sm:max-w-[120px]",
  md: "sm:max-w-[160px]",
  lg: "sm:max-w-[200px]",
};

/**
 * 查看态描述列表 — 不要用 disabled 表单冒充详情页。
 * @see references/layout-patterns/form-composition.md#查看态描述列表
 */
export function DescriptionList({
  items,
  columns = 2,
  labelWidth = "md",
  layout = "horizontal",
  className,
}: DescriptionListProps) {
  const stackOnMobile = layout === "stack-on-mobile";

  return (
    <dl
      className={cn(
        "grid gap-x-6 gap-y-4",
        columns === 2 ? "sm:grid-cols-2" : "grid-cols-1",
        className,
      )}
      data-layout={stackOnMobile ? "stack-on-mobile" : "horizontal"}
    >
      {items.map((item, index) => (
        <div
          key={index}
          className={cn(
            "grid gap-1",
            stackOnMobile
              ? "max-md:grid-cols-1 md:grid-cols-[minmax(0,1fr)_minmax(0,2fr)] md:items-start"
              : "sm:grid-cols-[minmax(0,1fr)_minmax(0,2fr)] sm:items-start",
            item.span === 2 && "sm:col-span-2",
            item.className,
          )}
        >
          <dt
            className={cn(
              "text-theme-sm font-medium text-gray-500 dark:text-gray-400",
              labelWidthClass[labelWidth],
            )}
          >
            {item.label}
          </dt>
          <dd className="text-theme-sm text-gray-800 dark:text-white/90">{item.value}</dd>
        </div>
      ))}
    </dl>
  );
}

/**
 * 分组描述列表 — 资源详情、配置详情等多段信息。
 */
export function DescriptionSection({
  title,
  description,
  items,
  columns = 2,
  layout,
  bordered = true,
  className,
}: DescriptionSectionProps) {
  if (!bordered) {
    return (
      <section className={cn("grid gap-4", className)}>
        {(title || description) && (
          <div className="grid gap-1">
            {title ? (
              <h3 className="text-base font-semibold text-gray-800 dark:text-white/90">
                {title}
              </h3>
            ) : null}
            {description ? (
              <p className="text-theme-sm text-gray-500 dark:text-gray-400">{description}</p>
            ) : null}
          </div>
        )}
        <DescriptionList items={items} columns={columns} layout={layout} />
      </section>
    );
  }

  return (
    <Card className={className}>
      {(title || description) && (
        <CardHeader>
          {title ? <CardTitle>{title}</CardTitle> : null}
          {description ? <CardDescription>{description}</CardDescription> : null}
        </CardHeader>
      )}
      <CardContent>
        <DescriptionList items={items} columns={columns} layout={layout} />
      </CardContent>
    </Card>
  );
}
