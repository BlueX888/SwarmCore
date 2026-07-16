import * as React from "react";
import { Link, useLocation } from "react-router";
import { ChevronDown, MoreHorizontal } from "lucide-react";
import * as Collapsible from "@radix-ui/react-collapsible";
import { cn } from "@/lib/utils";
import { useSidebar } from "@/context/sidebar-context";

export type NavSubItem = {
  name: string;
  path: string;
  new?: boolean;
  pro?: boolean;
  target?: string;
};

export type NavItem = {
  name: string;
  icon: React.ReactNode;
  path?: string;
  new?: boolean;
  target?: string;
  subItems?: NavSubItem[];
};

export type NavSection = {
  title: string;
  items: NavItem[];
};

export type AppSidebarProps = {
  sections: NavSection[];
  logo?: React.ReactNode;
  collapsedLogo?: React.ReactNode;
  widget?: React.ReactNode;
  className?: string;
};

function NavBadge({
  label,
  variant,
  active,
}: {
  label: string;
  variant: "new" | "pro";
  active?: boolean;
}) {
  const base =
    variant === "pro" ? "menu-dropdown-badge-pro" : "menu-dropdown-badge";
  const state =
    variant === "pro"
      ? active
        ? "menu-dropdown-badge-pro-active"
        : "menu-dropdown-badge-pro-inactive"
      : active
        ? "menu-dropdown-badge-active"
        : "menu-dropdown-badge-inactive";

  return <span className={cn("ml-auto", state, base)}>{label}</span>;
}

function SidebarNavItem({
  item,
  showLabels,
}: {
  item: NavItem;
  showLabels: boolean;
}) {
  const location = useLocation();
  const isActive = (path: string) => location.pathname === path;
  const hasActiveChild =
    item.subItems?.some((sub) => isActive(sub.path)) ?? false;
  const [open, setOpen] = React.useState(hasActiveChild);

  React.useEffect(() => {
    if (hasActiveChild) {
      setOpen(true);
    }
  }, [hasActiveChild]);

  if (item.subItems?.length) {
    return (
      <Collapsible.Root open={open} onOpenChange={setOpen}>
        <Collapsible.Trigger
          className={cn(
            "group menu-item w-full cursor-pointer",
            open || hasActiveChild
              ? "menu-item-active"
              : "menu-item-inactive",
            !showLabels && "xl:justify-center",
          )}
        >
          <span
            className={cn(
              "menu-item-icon-size",
              open || hasActiveChild
                ? "menu-item-icon-active"
                : "menu-item-icon-inactive",
            )}
          >
            {item.icon}
          </span>
          {showLabels && <span className="menu-item-text">{item.name}</span>}
          {item.new && showLabels && (
            <NavBadge label="new" variant="new" active={open} />
          )}
          {showLabels && (
            <ChevronDown
              className={cn(
                "ml-auto size-5 transition-transform duration-200",
                open && "rotate-180 text-brand-500",
              )}
            />
          )}
        </Collapsible.Trigger>
        {showLabels && (
          <Collapsible.Content className="overflow-hidden data-[state=closed]:animate-accordion-up data-[state=open]:animate-accordion-down">
            <ul className="mt-2 ml-9 space-y-1">
              {item.subItems.map((subItem) => {
                const active = isActive(subItem.path);
                return (
                  <li key={subItem.path}>
                    <Link
                      to={subItem.path}
                      target={subItem.target}
                      className={cn(
                        "menu-dropdown-item",
                        active
                          ? "menu-dropdown-item-active"
                          : "menu-dropdown-item-inactive",
                      )}
                    >
                      {subItem.name}
                      <span className="ml-auto flex items-center gap-1">
                        {subItem.new && (
                          <NavBadge label="new" variant="new" active={active} />
                        )}
                        {subItem.pro && (
                          <NavBadge label="pro" variant="pro" active={active} />
                        )}
                      </span>
                    </Link>
                  </li>
                );
              })}
            </ul>
          </Collapsible.Content>
        )}
      </Collapsible.Root>
    );
  }

  if (!item.path) {
    return null;
  }

  const active = isActive(item.path);

  return (
    <Link
      to={item.path}
      target={item.target}
      className={cn(
        "group menu-item",
        active ? "menu-item-active" : "menu-item-inactive",
        !showLabels && "xl:justify-center",
      )}
    >
      <span
        className={cn(
          "menu-item-icon-size",
          active ? "menu-item-icon-active" : "menu-item-icon-inactive",
        )}
      >
        {item.icon}
      </span>
      {showLabels && <span className="menu-item-text">{item.name}</span>}
    </Link>
  );
}

export function AppSidebar({
  sections,
  logo,
  collapsedLogo,
  widget,
  className,
}: AppSidebarProps) {
  const {
    isExpanded,
    isMobileOpen,
    isHovered,
    setIsHovered,
    setIsMobileOpen,
  } = useSidebar();
  const location = useLocation();

  const showLabels = isExpanded || isHovered || isMobileOpen;
  const isWide = isExpanded || isMobileOpen || isHovered;

  React.useEffect(() => {
    if (isMobileOpen) {
      setIsMobileOpen(false);
    }
    // Close mobile drawer after navigation.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.pathname]);

  return (
    <aside
      className={cn(
        "fixed top-0 left-0 z-50 flex h-screen flex-col border-r border-gray-200 bg-white px-5 text-gray-900 transition-all duration-300 ease-in-out xl:translate-x-0 dark:border-gray-800 dark:bg-gray-900",
        isWide ? "w-[290px]" : "w-[90px]",
        isMobileOpen ? "translate-x-0" : "-translate-x-full",
        className,
      )}
      onMouseEnter={() => !isExpanded && setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <div
        className={cn(
          "flex py-8",
          !showLabels ? "xl:justify-center" : "justify-start",
        )}
      >
        {showLabels ? logo : (collapsedLogo ?? logo)}
      </div>

      <div className="no-scrollbar flex flex-1 flex-col overflow-y-auto duration-300 ease-linear">
        <nav className="mb-6 flex flex-col gap-4">
          {sections.map((section) => (
            <div key={section.title}>
              <h2
                className={cn(
                  "mb-4 flex text-xs leading-5 text-gray-400 uppercase",
                  !showLabels ? "xl:justify-center" : "justify-start",
                )}
              >
                {showLabels ? (
                  section.title
                ) : (
                  <MoreHorizontal className="size-6" aria-hidden />
                )}
              </h2>
              <ul className="flex flex-col gap-1">
                {section.items.map((item) => (
                  <li key={item.name}>
                    <SidebarNavItem item={item} showLabels={showLabels} />
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </nav>
        {showLabels && widget ? widget : null}
      </div>
    </aside>
  );
}
