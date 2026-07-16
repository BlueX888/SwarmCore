import * as React from "react";
import { Link } from "react-router";
import { Menu, Search, X } from "lucide-react";
import { cn } from "@/lib/utils";
import { useSidebar } from "@/context/sidebar-context";

const XL_BREAKPOINT = 1280;

export type HeaderSearchProps = {
  placeholder?: string;
  className?: string;
  onOpenCommand?: () => void;
};

export function HeaderSearch({
  placeholder = "搜索或输入命令...",
  className,
  onOpenCommand,
}: HeaderSearchProps) {
  const inputRef = React.useRef<HTMLInputElement>(null);

  React.useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        if (onOpenCommand) {
          onOpenCommand();
        } else {
          inputRef.current?.focus();
        }
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [onOpenCommand]);

  return (
    <div className={cn("relative hidden xl:block", className)}>
      <span className="pointer-events-none absolute top-1/2 left-4 -translate-y-1/2 text-gray-500 dark:text-gray-400">
        <Search className="size-5" aria-hidden />
      </span>
      <input
        ref={inputRef}
        type="search"
        placeholder={placeholder}
        onFocus={onOpenCommand}
        onClick={onOpenCommand}
        readOnly={Boolean(onOpenCommand)}
        className="h-11 w-full max-w-[430px] rounded-lg border border-gray-200 bg-transparent py-2.5 pr-14 pl-12 text-sm text-gray-800 shadow-theme-xs placeholder:text-gray-400 focus:border-brand-300 focus:outline-hidden focus:ring-3 focus:ring-brand-500/10 dark:border-gray-800 dark:bg-gray-900 dark:text-white/90 dark:placeholder:text-white/30 dark:focus:border-brand-800"
        aria-label={placeholder}
      />
      <kbd className="absolute top-1/2 right-2.5 inline-flex -translate-y-1/2 items-center gap-0.5 rounded-lg border border-gray-200 bg-gray-50 px-[7px] py-[4.5px] text-xs tracking-tight text-gray-500 dark:border-gray-800 dark:bg-white/[0.03] dark:text-gray-400">
        <span>⌘</span>
        <span>K</span>
      </kbd>
    </div>
  );
}

export type AppHeaderVariant = "default" | "transparent" | "elevated-on-scroll";

export type AppHeaderProps = {
  logo?: React.ReactNode;
  search?: React.ReactNode;
  actions?: React.ReactNode;
  onOpenCommand?: () => void;
  /** default | transparent | elevated-on-scroll（滚动后 shadow） */
  variant?: AppHeaderVariant;
  className?: string;
};

export function AppHeader({
  logo,
  search,
  actions,
  onOpenCommand,
  variant = "default",
  className,
}: AppHeaderProps) {
  const { isMobileOpen, toggleSidebar, toggleMobileSidebar } = useSidebar();
  const [isApplicationMenuOpen, setApplicationMenuOpen] = React.useState(false);
  const [elevated, setElevated] = React.useState(false);

  React.useEffect(() => {
    if (variant !== "elevated-on-scroll") {
      setElevated(false);
      return;
    }

    const handleScroll = () => {
      setElevated(window.scrollY > 0);
    };

    handleScroll();
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, [variant]);

  const handleToggle = () => {
    if (window.innerWidth >= XL_BREAKPOINT) {
      toggleSidebar();
    } else {
      toggleMobileSidebar();
    }
  };

  const defaultSearch = <HeaderSearch onOpenCommand={onOpenCommand} />;

  return (
    <header
      className={cn(
        "sticky top-0 z-99999 flex w-full border-gray-200 xl:border-b dark:border-gray-800",
        variant === "transparent"
          ? "bg-transparent"
          : "bg-white dark:bg-gray-900",
        variant === "elevated-on-scroll" && elevated && "shadow-theme-sm",
        className,
      )}
      data-variant={variant}
      data-elevated={variant === "elevated-on-scroll" && elevated ? "true" : undefined}
    >
      <div className="flex grow flex-col items-center justify-between xl:flex-row xl:px-6">
        <div className="flex w-full items-center justify-between gap-2 border-b border-gray-200 px-3 py-3 sm:gap-4 xl:justify-normal xl:border-b-0 xl:px-0 lg:py-4 dark:border-gray-800">
          <button
            type="button"
            onClick={handleToggle}
            className={cn(
              "z-99999 flex size-10 items-center justify-center rounded-lg border-gray-200 text-gray-500 lg:size-11 xl:border dark:border-gray-800 dark:text-gray-400",
              isMobileOpen && "bg-gray-100 dark:bg-white/[0.03]",
            )}
            aria-label="切换侧边栏"
          >
            {isMobileOpen ? (
              <X className="size-6" aria-hidden />
            ) : (
              <Menu className="size-4" aria-hidden />
            )}
          </button>

          {logo ? (
            <Link to="/" className="xl:hidden">
              {logo}
            </Link>
          ) : null}

          <button
            type="button"
            onClick={() => setApplicationMenuOpen((open) => !open)}
            className="flex size-10 items-center justify-center rounded-lg text-gray-700 hover:bg-gray-100 xl:hidden dark:text-gray-400 dark:hover:bg-gray-800"
            aria-label="切换应用菜单"
            aria-expanded={isApplicationMenuOpen}
          >
            <span className="size-1.5 rounded-full bg-current shadow-[6px_0_0_currentColor,-6px_0_0_currentColor]" />
          </button>

          {search ?? defaultSearch}
        </div>

        <div
          className={cn(
            "w-full items-center justify-between gap-4 px-5 py-4 shadow-theme-md xl:flex xl:justify-end xl:px-0 xl:shadow-none",
            isApplicationMenuOpen ? "flex" : "hidden",
          )}
        >
          {actions}
        </div>
      </div>
    </header>
  );
}
