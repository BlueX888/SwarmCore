import * as React from "react";
import { Outlet } from "react-router";
import { cn } from "@/lib/utils";
import { SidebarProvider, useSidebar } from "@/context/sidebar-context";
import { AppHeader, type AppHeaderProps } from "@/components/layout/app-header";
import { AppSidebar, type AppSidebarProps } from "@/components/layout/app-sidebar";
import { Backdrop } from "@/components/layout/backdrop";

export type AppLayoutProps = {
  sidebar: AppSidebarProps;
  header?: Omit<AppHeaderProps, "onOpenCommand">;
  onOpenCommand?: () => void;
  backdrop?: React.ReactNode;
  mainClassName?: string;
  children?: React.ReactNode;
};

function LayoutContent({
  sidebar,
  header,
  onOpenCommand,
  backdrop,
  mainClassName,
  children,
}: AppLayoutProps) {
  const { isExpanded, isHovered, isMobileOpen } = useSidebar();

  return (
    <div className="h-full min-h-screen">
      <AppSidebar {...sidebar} />
      {backdrop ?? <Backdrop />}

      <div
        className={cn(
          "flex h-full min-h-0 flex-col transition-[margin] duration-300 ease-in-out",
          isExpanded || isHovered ? "xl:ml-[290px]" : "xl:ml-[90px]",
          isMobileOpen ? "ml-0" : "",
        )}
      >
        <AppHeader {...header} onOpenCommand={onOpenCommand} />
        <main
          className={cn(
            "mx-auto min-h-0 w-full max-w-(--breakpoint-2xl) flex-1 overflow-y-auto p-4 pb-20 md:p-6 md:pb-24",
            mainClassName,
          )}
        >
          {children ?? <Outlet />}
        </main>
      </div>
    </div>
  );
}

export function AppLayout(props: AppLayoutProps) {
  return (
    <SidebarProvider>
      <LayoutContent {...props} />
    </SidebarProvider>
  );
}
