import * as React from "react";
import { cn } from "@/lib/utils";

export const Card = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(({ className, ...props }, ref) => (
  <div ref={ref} className={cn("rounded-[20px] border border-gray-200/80 bg-white/90 shadow-theme-card backdrop-blur-sm dark:border-gray-800 dark:bg-white/[0.035]", className)} {...props} />
));
Card.displayName = "Card";
export function CardHeader(props: React.HTMLAttributes<HTMLDivElement>) { return <div {...props} className={cn("flex items-center justify-between gap-4 px-5 py-4.5", props.className)} />; }
export function CardTitle(props: React.HTMLAttributes<HTMLHeadingElement>) { return <h2 {...props} className={cn("font-semibold tracking-[-0.01em] text-gray-900 dark:text-white", props.className)} />; }
export function CardContent(props: React.HTMLAttributes<HTMLDivElement>) { return <div {...props} className={cn("p-5 pt-0", props.className)} />; }
