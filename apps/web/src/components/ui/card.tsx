import * as React from "react";
import { cn } from "@/lib/utils";

export const Card = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(({ className, ...props }, ref) => (
  <div ref={ref} className={cn("rounded-2xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-white/[0.03]", className)} {...props} />
));
Card.displayName = "Card";
export function CardHeader(props: React.HTMLAttributes<HTMLDivElement>) { return <div {...props} className={cn("flex items-center justify-between gap-4 px-5 py-4", props.className)} />; }
export function CardTitle(props: React.HTMLAttributes<HTMLHeadingElement>) { return <h2 {...props} className={cn("font-semibold text-gray-800 dark:text-white/90", props.className)} />; }
export function CardContent(props: React.HTMLAttributes<HTMLDivElement>) { return <div {...props} className={cn("p-5 pt-0", props.className)} />; }
