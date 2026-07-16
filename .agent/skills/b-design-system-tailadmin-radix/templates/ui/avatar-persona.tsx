import * as React from "react";
import { cn } from "@/lib/utils";
import { Avatar, type AvatarProps } from "@/components/ui/avatar";

export type AvatarPersonaProps = {
  name: React.ReactNode;
  subtitle?: React.ReactNode;
  avatar?: AvatarProps;
  trailing?: React.ReactNode;
  className?: string;
  size?: "sm" | "md" | "lg";
};

const gapBySize = {
  sm: "gap-2",
  md: "gap-3",
  lg: "gap-4",
} as const;

export function AvatarPersona({
  name,
  subtitle,
  avatar,
  trailing,
  className,
  size = "md",
}: AvatarPersonaProps) {
  const avatarSize = size === "sm" ? "sm" : size === "lg" ? "lg" : "md";

  return (
    <div className={cn("flex min-w-0 items-center", gapBySize[size], className)}>
      <Avatar size={avatarSize} name={typeof name === "string" ? name : undefined} {...avatar} />
      <div className="min-w-0 flex-1">
        <div
          className={cn(
            "truncate font-medium text-gray-800 dark:text-white/90",
            size === "sm" ? "text-theme-sm" : "text-sm",
          )}
        >
          {name}
        </div>
        {subtitle ? (
          <div className="truncate text-theme-xs text-gray-500 dark:text-gray-400">
            {subtitle}
          </div>
        ) : null}
      </div>
      {trailing ? <div className="shrink-0">{trailing}</div> : null}
    </div>
  );
}
