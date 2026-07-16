import * as React from "react";
import { ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button, type ButtonProps } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

export type SplitButtonMenuItem = {
  key: string;
  label: React.ReactNode;
  onSelect?: () => void;
  disabled?: boolean;
};

export type SplitButtonProps = Omit<ButtonProps, "onClick"> & {
  label: React.ReactNode;
  onClick?: () => void;
  menuItems: SplitButtonMenuItem[];
  menuAlign?: "start" | "end";
};

export function SplitButton({
  label,
  onClick,
  menuItems,
  menuAlign = "end",
  className,
  variant = "solid",
  size = "md",
  disabled,
  ...props
}: SplitButtonProps) {
  return (
    <div
      className={cn(
        "inline-flex overflow-hidden rounded-lg shadow-theme-xs [&>button]:rounded-none",
        className,
      )}
    >
      <Button
        type="button"
        variant={variant}
        size={size}
        disabled={disabled}
        onClick={onClick}
        className="rounded-l-lg rounded-r-none border-r border-white/20"
        {...props}
      >
        {label}
      </Button>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            type="button"
            variant={variant}
            size={size}
            disabled={disabled}
            className="rounded-l-none rounded-r-lg px-2.5"
            aria-label="更多操作"
          >
            <ChevronDown className="size-4" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align={menuAlign}>
          {menuItems.map((item) => (
            <DropdownMenuItem
              key={item.key}
              disabled={item.disabled}
              onSelect={item.onSelect}
            >
              {item.label}
            </DropdownMenuItem>
          ))}
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
}
