import * as React from "react";
import { cn } from "@/lib/utils";
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  FormProvider,
  type FormLayout,
  type InputSkin,
  type LabelWidth,
  type RequiredMark,
} from "@/components/ui/form-context";

export type FormSectionProps = {
  title?: React.ReactNode;
  description?: React.ReactNode;
  actions?: React.ReactNode;
  columns?: 1 | 2;
  bordered?: boolean;
  layout?: FormLayout;
  labelWidth?: LabelWidth;
  inputSkin?: InputSkin;
  requiredMark?: RequiredMark;
  className?: string;
  contentClassName?: string;
  children: React.ReactNode;
};

export function FormSection({
  title,
  description,
  actions,
  columns = 1,
  bordered = true,
  layout,
  labelWidth,
  inputSkin,
  requiredMark,
  className,
  contentClassName,
  children,
}: FormSectionProps) {
  const gridClass = columns === 2 ? "grid gap-5 sm:grid-cols-2" : "grid gap-5";

  const content = !bordered ? (
    <section className={cn("grid gap-4", className)}>
      {(title || description || actions) && (
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="grid gap-1">
            {title ? (
              <h3 className="text-base font-semibold text-gray-800 dark:text-white/90">{title}</h3>
            ) : null}
            {description ? (
              <p className="text-theme-sm text-gray-500 dark:text-gray-400">{description}</p>
            ) : null}
          </div>
          {actions ? <div className="flex shrink-0 items-center gap-2">{actions}</div> : null}
        </div>
      )}
      <div className={cn(gridClass, contentClassName)}>{children}</div>
    </section>
  ) : (
    <Card className={className}>
      {(title || description || actions) && (
        <CardHeader>
          <div className="grid gap-1">
            {title ? <CardTitle>{title}</CardTitle> : null}
            {description ? <CardDescription>{description}</CardDescription> : null}
          </div>
          {actions ? <CardAction>{actions}</CardAction> : null}
        </CardHeader>
      )}
      <CardContent className={cn(gridClass, contentClassName)}>{children}</CardContent>
    </Card>
  );

  return (
    <FormProvider layout={layout} labelWidth={labelWidth} inputSkin={inputSkin} requiredMark={requiredMark}>
      {content}
    </FormProvider>
  );
}
