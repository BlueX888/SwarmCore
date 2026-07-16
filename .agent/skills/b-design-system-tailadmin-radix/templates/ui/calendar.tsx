import * as React from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { DayPicker } from "react-day-picker";

import { cn } from "@/lib/utils";
import { buttonVariants } from "@/components/ui/button";

export type CalendarSize = "sm" | "md" | "lg";

export type CalendarProps = React.ComponentProps<typeof DayPicker> & {
  size?: CalendarSize;
  selectionMode?: "single" | "multiple" | "range";
};

function Calendar({
  className,
  classNames,
  mode,
  size = "md",
  selectionMode,
  showOutsideDays = true,
  ...props
}: CalendarProps) {
  const daySize = {
    sm: "h-8 w-8",
    md: "h-9 w-9",
    lg: "h-10 w-10",
  }[size];
  const dayButtonSize = {
    sm: "size-8 text-xs",
    md: "size-9",
    lg: "size-10",
  }[size];

  return (
    <DayPicker
      mode={selectionMode ?? mode}
      showOutsideDays={showOutsideDays}
      className={cn("p-3", className)}
      classNames={{
        months: "flex flex-col gap-2 sm:flex-row sm:gap-4",
        month: "flex flex-col gap-4",
        month_caption: "relative flex items-center justify-center pt-1",
        caption_label: "text-sm font-medium text-gray-800 dark:text-white/90",
        nav: "flex items-center gap-1",
        button_previous: cn(
          buttonVariants({ variant: "outline" }),
          "absolute left-1 size-7 bg-transparent p-0 opacity-50 hover:opacity-100",
        ),
        button_next: cn(
          buttonVariants({ variant: "outline" }),
          "absolute right-1 size-7 bg-transparent p-0 opacity-50 hover:opacity-100",
        ),
        month_grid: "w-full border-collapse",
        weekdays: "flex",
        weekday:
          cn(daySize, "rounded-md text-[0.8rem] font-normal text-gray-500 dark:text-gray-400"),
        week: "mt-2 flex w-full",
        day: cn(
          "relative p-0 text-center text-sm focus-within:relative focus-within:z-20 [&:has([aria-selected])]:bg-brand-50 first:[&:has([aria-selected])]:rounded-l-md last:[&:has([aria-selected])]:rounded-r-md dark:[&:has([aria-selected])]:bg-brand-500/12",
          daySize,
        ),
        day_button: cn(
          buttonVariants({ variant: "ghost" }),
          "p-0 font-normal aria-selected:opacity-100",
          dayButtonSize,
        ),
        selected:
          "rounded-md bg-brand-500 text-white hover:bg-brand-500 hover:text-white focus:bg-brand-500 focus:text-white",
        today: "rounded-md bg-brand-50 text-brand-500 dark:bg-brand-500/12",
        outside: "text-gray-400 aria-selected:text-gray-400 dark:text-gray-500",
        disabled: "text-gray-400 opacity-50 dark:text-gray-500",
        range_middle:
          "aria-selected:bg-brand-50 aria-selected:text-brand-500 dark:aria-selected:bg-brand-500/12",
        hidden: "invisible",
        ...classNames,
      }}
      components={{
        Chevron: ({ orientation, className: iconClassName, ...iconProps }) => {
          const Icon = orientation === "left" ? ChevronLeft : ChevronRight;
          return (
            <Icon className={cn("size-4", iconClassName)} {...iconProps} />
          );
        },
      }}
      {...props}
    />
  );
}

Calendar.displayName = "Calendar";

export { Calendar };
