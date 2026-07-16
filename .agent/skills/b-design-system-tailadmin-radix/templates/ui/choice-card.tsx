import * as React from "react";
import { cn } from "@/lib/utils";
import { Checkbox } from "@/components/ui/checkbox";
import { RadioGroupItem } from "@/components/ui/radio-group";

export type ChoiceCardProps = {
  type: "checkbox" | "radio";
  selected: boolean;
  onSelectedChange: (selected: boolean) => void;
  title: React.ReactNode;
  description?: React.ReactNode;
  icon?: React.ReactNode;
  disabled?: boolean;
  /** radio 类型必填，须置于 RadioGroup 内 */
  value?: string;
  className?: string;
};

function choiceCardSurfaceClass(selected: boolean, disabled?: boolean, className?: string) {
  return cn(
    "flex w-full items-start gap-4 rounded-2xl border p-5 text-left transition-all",
    "border-gray-200 bg-white dark:border-gray-800 dark:bg-white/[0.03]",
    "hover:border-gray-300 dark:hover:border-gray-700",
    "focus-visible:outline-hidden focus-visible:ring-3 focus-visible:ring-brand-500/20",
    selected && "border-brand-500 ring-2 ring-brand-500/20",
    disabled ? "cursor-not-allowed opacity-60" : "cursor-pointer",
    className,
  );
}

function ChoiceCardBody({
  title,
  description,
  icon,
  control,
}: {
  title: React.ReactNode;
  description?: React.ReactNode;
  icon?: React.ReactNode;
  control: React.ReactNode;
}) {
  return (
    <>
      {icon ? (
        <div className="shrink-0 text-gray-500 dark:text-gray-400">{icon}</div>
      ) : null}
      <div className="min-w-0 flex-1 grid gap-1">
        <div className="text-base font-semibold text-gray-800 dark:text-white/90">{title}</div>
        {description ? (
          <p className="text-theme-sm text-gray-500 dark:text-gray-400">{description}</p>
        ) : null}
      </div>
      <div className="pointer-events-none shrink-0">{control}</div>
    </>
  );
}

/**
 * 可点击的选择卡片 — checkbox 独立使用；radio 须包在 RadioGroup 内并传 value。
 */
export function ChoiceCard({
  type,
  selected,
  onSelectedChange,
  title,
  description,
  icon,
  disabled = false,
  value,
  className,
}: ChoiceCardProps) {
  if (type === "radio" && value == null) {
    throw new Error("ChoiceCard: radio 类型必须提供 value，且置于 RadioGroup 内。");
  }

  if (type === "checkbox") {
    return (
      <button
        type="button"
        disabled={disabled}
        data-state={selected ? "selected" : "unselected"}
        aria-pressed={selected}
        className={choiceCardSurfaceClass(selected, disabled, className)}
        onClick={() => {
          if (!disabled) onSelectedChange(!selected);
        }}
      >
        <ChoiceCardBody
          title={title}
          description={description}
          icon={icon}
          control={<Checkbox checked={selected} disabled={disabled} tabIndex={-1} aria-hidden />}
        />
      </button>
    );
  }

  return (
    <RadioGroupItem value={value!} disabled={disabled} asChild>
      <button
        type="button"
        data-state={selected ? "selected" : "unselected"}
        className={choiceCardSurfaceClass(selected, disabled, className)}
        onClick={() => {
          if (!disabled) onSelectedChange(true);
        }}
      >
        <ChoiceCardBody
          title={title}
          description={description}
          icon={icon}
          control={
            <span
              aria-hidden
              className={cn(
                "flex size-5 items-center justify-center rounded-full border-[1.25px]",
                selected
                  ? "border-brand-500 bg-brand-500"
                  : "border-gray-300 bg-transparent dark:border-gray-700",
              )}
            >
              {selected ? <span className="size-2 rounded-full bg-white" /> : null}
            </span>
          }
        />
      </button>
    </RadioGroupItem>
  );
}
