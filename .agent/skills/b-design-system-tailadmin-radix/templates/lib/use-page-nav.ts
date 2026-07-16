import * as React from "react";

export type PageNavSection = { id: string; label: React.ReactNode };

export function usePageNav(sections: PageNavSection[], offset = 72) {
  const [activeId, setActiveId] = React.useState(sections[0]?.id ?? "");
  const refs = React.useRef<Map<string, HTMLElement>>(new Map());

  const registerRef = React.useCallback((id: string, el: HTMLElement | null) => {
    if (el) refs.current.set(id, el);
    else refs.current.delete(id);
  }, []);

  const scrollTo = React.useCallback(
    (id: string) => {
      const el = refs.current.get(id) ?? document.getElementById(id);
      if (!el) return;
      const top = el.getBoundingClientRect().top + window.scrollY - offset;
      window.scrollTo({ top, behavior: "smooth" });
      setActiveId(id);
    },
    [offset],
  );

  React.useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((e) => e.isIntersecting)
          .sort((a, b) => b.intersectionRatio - a.intersectionRatio);
        if (visible[0]?.target.id) setActiveId(visible[0].target.id);
      },
      { rootMargin: `-${offset}px 0px -60% 0px`, threshold: [0, 0.25, 0.5] },
    );
    sections.forEach((s) => {
      const el = refs.current.get(s.id) ?? document.getElementById(s.id);
      if (el) observer.observe(el);
    });
    return () => observer.disconnect();
  }, [sections, offset]);

  return { activeId, scrollTo, registerRef };
}
