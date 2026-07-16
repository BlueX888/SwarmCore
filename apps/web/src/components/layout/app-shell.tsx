import * as Dialog from "@radix-ui/react-dialog";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@radix-ui/react-tooltip";
import { Activity, Bot, ChevronLeft, ChevronRight, Menu, Moon, Sun, Workflow } from "lucide-react";
import * as React from "react";
import { NavLink, Outlet, useParams } from "react-router";
import { Button } from "@/components/ui/button";
import { useTheme } from "@/context/theme-context";
import { cn } from "@/lib/utils";

interface NavigationProps { collapsed?: boolean; onNavigate?: () => void; }
function Navigation({ collapsed, onNavigate }: NavigationProps) {
  const { tenantId = "", projectId = "" } = useParams();
  const base = `/t/${tenantId}/p/${projectId}`;
  const items = [
    { label: "Runs", to: `${base}/runs`, icon: Activity },
    { label: "Strategies", to: `${base}/strategies`, icon: Workflow },
  ];
  return <nav aria-label="Primary" className="space-y-1">{items.map(({ label, to, icon: Icon }) => <NavLink key={label} to={to} onClick={onNavigate} className={({ isActive }) => cn("menu-item", isActive ? "menu-item-active" : "menu-item-inactive", collapsed && "justify-center px-0")}><Icon aria-hidden />{collapsed ? null : <span>{label}</span>}</NavLink>)}</nav>;
}

function Brand({ collapsed }: { collapsed?: boolean }) { return <div className={cn("flex h-20 items-center gap-3 font-semibold text-gray-900 dark:text-white", collapsed && "justify-center")}><span className="grid size-10 place-items-center rounded-xl bg-brand-500 text-white"><Bot /></span>{collapsed ? null : <span>SwarmCore</span>}</div>; }

export function AppShell() {
  const [collapsed, setCollapsed] = React.useState(false);
  const [mobileOpen, setMobileOpen] = React.useState(false);
  const { theme, toggleTheme } = useTheme();
  return <TooltipProvider>
    <div className="min-h-screen overflow-x-hidden bg-gray-50 dark:bg-gray-900">
      <aside className={cn("fixed inset-y-0 left-0 hidden border-r border-gray-200 bg-white px-4 transition-[width] xl:block dark:border-gray-800 dark:bg-gray-900", collapsed ? "w-[90px]" : "w-[290px]")}>
        <Brand collapsed={collapsed} /><Navigation collapsed={collapsed} />
        <Tooltip><TooltipTrigger asChild><Button variant="ghost" size="icon" aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"} onClick={() => setCollapsed((value) => !value)} className="absolute right-4 bottom-5">{collapsed ? <ChevronRight /> : <ChevronLeft />}</Button></TooltipTrigger><TooltipContent side="right" className="z-99999 rounded-lg bg-gray-900 px-3 py-2 text-xs text-white">Toggle sidebar</TooltipContent></Tooltip>
      </aside>
      <div className={cn("transition-[margin]", collapsed ? "xl:ml-[90px]" : "xl:ml-[290px]")}>
        <header className="z-99999 sticky top-0 flex h-16 items-center justify-between border-b border-gray-200 bg-white/95 px-4 backdrop-blur md:px-6 dark:border-gray-800 dark:bg-gray-900/95">
          <div className="flex items-center gap-3"><Button variant="ghost" size="icon" aria-label="Open navigation" className="xl:hidden" onClick={() => setMobileOpen(true)}><Menu /></Button><div><p className="text-sm font-medium text-gray-800 dark:text-white/90">Execution Console</p><p className="text-xs text-gray-500">Durable swarm operations</p></div></div>
          <Button variant="outline" size="icon" aria-label="Toggle color theme" onClick={toggleTheme}>{theme === "dark" ? <Sun /> : <Moon />}</Button>
        </header>
        <main className="mx-auto w-full max-w-(--breakpoint-2xl) p-4 pb-20 md:p-6 md:pb-24"><Outlet /></main>
      </div>
      <Dialog.Root open={mobileOpen} onOpenChange={setMobileOpen}><Dialog.Portal><Dialog.Overlay className="z-99999 fixed inset-0 bg-gray-900/50" /><Dialog.Content aria-describedby={undefined} className="z-99999 fixed inset-y-0 left-0 w-[290px] bg-white px-5 shadow-theme-sm focus:outline-hidden dark:bg-gray-900"><Dialog.Title className="sr-only">Navigation</Dialog.Title><Brand /><Navigation onNavigate={() => setMobileOpen(false)} /></Dialog.Content></Dialog.Portal></Dialog.Root>
    </div>
  </TooltipProvider>;
}
