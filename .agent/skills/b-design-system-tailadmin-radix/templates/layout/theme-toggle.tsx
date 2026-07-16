import * as React from "react";
import { Moon, Sun } from "lucide-react";
import { cn } from "@/lib/utils";
import { useTheme } from "@/context/theme-context";

export type ThemeToggleButtonProps = {
  className?: string;
  "aria-label"?: string;
};

export function ThemeToggleButton({
  className,
  "aria-label": ariaLabel = "切换深浅色主题",
}: ThemeToggleButtonProps) {
  const { toggleTheme } = useTheme();

  return (
    <button
      type="button"
      onClick={toggleTheme}
      className={cn(
        "relative flex size-11 items-center justify-center rounded-full border border-gray-200 bg-white text-gray-500 transition-colors hover:bg-gray-100 hover:text-gray-700 dark:border-gray-800 dark:bg-gray-900 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-white",
        className,
      )}
      aria-label={ariaLabel}
    >
      <Sun className="size-5 dark:hidden" aria-hidden />
      <Moon className="hidden size-5 dark:block" aria-hidden />
    </button>
  );
}

/** 概念名 alias，与索引/文档用语一致。见 migration-notes/MN-01 */
export const ThemeToggle = ThemeToggleButton;
