import { ArrowLeft } from "lucide-react";
import type * as React from "react";
import { Link, type LinkProps } from "react-router";
import { cn } from "@/lib/utils";

export function BackLink({ className, children, ...props }: LinkProps & { children: React.ReactNode }) {
  return <Link {...props} className={cn("group inline-flex items-center gap-2 rounded-full border border-gray-200/80 bg-white/75 px-3 py-1.5 text-sm font-semibold text-gray-600 shadow-theme-xs backdrop-blur transition hover:-translate-x-0.5 hover:border-brand-300 hover:text-brand-600 focus-visible:outline-hidden focus-visible:ring-3 focus-visible:ring-brand-500/20 dark:border-gray-700 dark:bg-gray-800/70 dark:text-gray-300 dark:hover:border-brand-500/50 dark:hover:text-brand-400", className)}><ArrowLeft aria-hidden className="size-4 transition-transform group-hover:-translate-x-0.5" />{children}</Link>;
}
