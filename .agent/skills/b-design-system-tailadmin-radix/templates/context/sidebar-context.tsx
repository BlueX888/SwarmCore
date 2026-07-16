import * as React from "react";

export type SidebarContextType = {
  isExpanded: boolean;
  isMobileOpen: boolean;
  isHovered: boolean;
  toggleSidebar: () => void;
  toggleMobileSidebar: () => void;
  setIsHovered: (hovered: boolean) => void;
  setIsMobileOpen: (open: boolean) => void;
};

const SidebarContext = React.createContext<SidebarContextType | undefined>(
  undefined,
);

const XL_BREAKPOINT = 1280;

export function SidebarProvider({ children }: { children: React.ReactNode }) {
  const [isExpanded, setIsExpanded] = React.useState(true);
  const [isMobileOpen, setIsMobileOpen] = React.useState(false);
  const [isHovered, setIsHovered] = React.useState(false);
  const [isMobile, setIsMobile] = React.useState(false);

  React.useEffect(() => {
    const handleResize = () => {
      const mobile = window.innerWidth < XL_BREAKPOINT;
      setIsMobile(mobile);
      if (!mobile) {
        setIsMobileOpen(false);
      }
    };

    handleResize();
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  const toggleSidebar = React.useCallback(() => {
    setIsExpanded((prev) => !prev);
  }, []);

  const toggleMobileSidebar = React.useCallback(() => {
    setIsMobileOpen((prev) => !prev);
  }, []);

  const value = React.useMemo<SidebarContextType>(
    () => ({
      isExpanded: isMobile ? false : isExpanded,
      isMobileOpen,
      isHovered,
      toggleSidebar,
      toggleMobileSidebar,
      setIsHovered,
      setIsMobileOpen,
    }),
    [
      isExpanded,
      isHovered,
      isMobile,
      isMobileOpen,
      toggleMobileSidebar,
      toggleSidebar,
    ],
  );

  return (
    <SidebarContext.Provider value={value}>{children}</SidebarContext.Provider>
  );
}

export function useSidebar() {
  const context = React.useContext(SidebarContext);
  if (!context) {
    throw new Error("useSidebar must be used within a SidebarProvider");
  }
  return context;
}
