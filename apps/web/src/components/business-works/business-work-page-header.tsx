import type { ReactNode } from "react";
import type { LucideIcon } from "lucide-react";
import { BackLink } from "@/components/ui/back-link";

interface BusinessWorkPageHeaderProps {
  backTo: string;
  icon: LucideIcon;
  meta: ReactNode;
  title: string;
  description: string;
  actions?: ReactNode;
  summary?: ReactNode;
}

export function BusinessWorkPageHeader({
  backTo,
  icon: Icon,
  meta,
  title,
  description,
  actions,
  summary,
}: BusinessWorkPageHeaderProps) {
  return (
    <header data-testid="business-work-page-header">
      <BackLink to={backTo}>返回业务工作</BackLink>
      <div className="mt-4 rounded-[20px] border border-gray-200/80 bg-white/90 p-5 shadow-theme-card dark:border-gray-800 dark:bg-white/[0.035]">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div className="min-w-0 flex-1">
            <div className="flex min-w-0 items-start gap-3">
              <span className="grid size-11 shrink-0 place-items-center rounded-2xl bg-brand-50 text-brand-600 dark:bg-brand-500/15 dark:text-brand-400">
                <Icon className="size-5" />
              </span>
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-2">{meta}</div>
                <h1 className="mt-1 text-2xl font-semibold tracking-tight text-gray-900 dark:text-white">{title}</h1>
                <p className="mt-1 max-w-2xl text-sm leading-6 text-gray-500">{description}</p>
              </div>
            </div>
            {summary ? (
              <div className="mt-4 border-t border-gray-100 pt-3 dark:border-gray-800">{summary}</div>
            ) : null}
          </div>
          {actions ? (
            <div className="flex shrink-0 flex-wrap gap-2 lg:min-w-44 lg:flex-col lg:items-stretch">
              {actions}
            </div>
          ) : null}
        </div>
      </div>
    </header>
  );
}
