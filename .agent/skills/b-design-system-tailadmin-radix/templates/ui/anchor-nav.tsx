import * as React from "react";
import { cn } from "@/lib/utils";
import { usePageNav, type PageNavSection } from "../lib/use-page-nav";

type AnchorNavContextValue = ReturnType<typeof usePageNav>;

const AnchorNavContext = React.createContext<AnchorNavContextValue | null>(null);

export type AnchorNavProps = {
  sections: PageNavSection[];
  offset?: number;
  affix?: boolean;
  orientation?: "vertical" | "horizontal";
  className?: string;
};

export function AnchorNav({
  sections,
  offset = 72,
  affix = true,
  orientation = "vertical",
  className,
}: AnchorNavProps) {
  const nav = usePageNav(sections, offset);

  return (
    <AnchorNavContext.Provider value={nav}>
      <nav
        aria-label="Page sections"
        data-state={nav.activeId}
        className={cn(
          affix && "sticky z-10 self-start",
          orientation === "vertical" ? "flex flex-col gap-0.5" : "flex flex-row flex-wrap gap-1",
          className,
        )}
        style={affix ? { top: offset } : undefined}
      >
        {sections.map((section) => {
          const isActive = nav.activeId === section.id;
          return (
            <button
              key={section.id}
              type="button"
              onClick={() => nav.scrollTo(section.id)}
              aria-current={isActive ? "true" : undefined}
              className={cn(
                "text-theme-sm font-medium transition-colors",
                orientation === "vertical"
                  ? "border-l-2 border-transparent px-3 py-2 text-left"
                  : "border-b-2 border-transparent px-2 py-2",
                isActive
                  ? "border-brand-500 text-brand-600 dark:text-brand-400"
                  : "text-gray-600 hover:text-gray-800 dark:text-gray-400 dark:hover:text-gray-200",
              )}
            >
              {section.label}
            </button>
          );
        })}
      </nav>
    </AnchorNavContext.Provider>
  );
}

export type AnchorSectionProps = {
  id: string;
  className?: string;
  children: React.ReactNode;
};

export function AnchorSection({ id, className, children }: AnchorSectionProps) {
  const ctx = React.useContext(AnchorNavContext);

  const ref = React.useCallback(
    (el: HTMLElement | null) => {
      ctx?.registerRef(id, el);
    },
    [ctx, id],
  );

  return (
    <section id={id} ref={ref} className={cn("scroll-mt-24", className)}>
      {children}
    </section>
  );
}
