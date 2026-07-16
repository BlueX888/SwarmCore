import * as React from "react";
import * as TabsPrimitive from "@radix-ui/react-tabs";
import { Plus, X } from "lucide-react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const tabsListVariants = cva("inline-flex items-center text-gray-500 dark:text-gray-400", {
  variants: {
    variant: {
      line: "gap-6 border-b border-gray-200 dark:border-gray-800",
      enclosed: "gap-1 rounded-lg bg-gray-100 p-1 dark:bg-gray-900",
      outline: "gap-1 rounded-lg p-1 ring-1 ring-inset ring-gray-200 dark:ring-gray-800",
      plain: "gap-4 bg-transparent",
    },
    size: { sm: "text-xs", md: "text-sm", lg: "text-base" },
    orientation: { horizontal: "flex-row", vertical: "flex-col items-stretch" },
    fitted: { true: "grid w-full auto-cols-fr grid-flow-col", false: "" },
  },
  defaultVariants: { variant: "line", size: "md", orientation: "horizontal", fitted: false },
});

const tabsTriggerVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap font-medium transition-colors focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-brand-500/20 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        line: "border-b-2 border-transparent pb-3 data-[state=active]:border-brand-500 data-[state=active]:text-brand-600 dark:data-[state=active]:text-brand-400",
        enclosed:
          "rounded-md px-3 py-2 data-[state=active]:bg-white data-[state=active]:text-gray-900 data-[state=active]:shadow-theme-xs dark:data-[state=active]:bg-white/[0.06] dark:data-[state=active]:text-white",
        outline:
          "rounded-md px-3 py-2 data-[state=active]:bg-gray-50 data-[state=active]:text-gray-900 dark:data-[state=active]:bg-white/5 dark:data-[state=active]:text-white",
        plain: "px-0 pb-1 data-[state=active]:text-gray-900 dark:data-[state=active]:text-white",
      },
      size: { sm: "h-8 px-2", md: "h-9 px-3", lg: "h-11 px-4" },
    },
    defaultVariants: { variant: "line", size: "md" },
  },
);

const Tabs = TabsPrimitive.Root;

type TabsListContextValue = Pick<VariantProps<typeof tabsListVariants>, "variant" | "size"> & {
  editable?: boolean;
  onEdit?: (targetKey: string, action: "add" | "remove") => void;
};

const TabsListContext = React.createContext<TabsListContextValue>({
  variant: "line",
  size: "md",
});

type TabsListProps = React.ComponentPropsWithoutRef<typeof TabsPrimitive.List> &
  VariantProps<typeof tabsListVariants> & {
    /** antd editable-card：显示 tab 关闭与末尾添加按钮 */
    editable?: boolean;
    onEdit?: (targetKey: string, action: "add" | "remove") => void;
    hideAdd?: boolean;
  };

const TabsList = React.forwardRef<React.ElementRef<typeof TabsPrimitive.List>, TabsListProps>(
  ({ className, variant = "line", size = "md", orientation, fitted, editable, onEdit, hideAdd, children, ...props }, ref) => {
    const handleAdd = () => {
      onEdit?.("", "add");
    };

    return (
      <TabsListContext.Provider value={{ variant, size, editable, onEdit }}>
        <TabsPrimitive.List
          ref={ref}
          className={cn(tabsListVariants({ variant, size, orientation, fitted }), className)}
          {...props}
        >
          {children}
          {editable && !hideAdd ? (
            <button
              type="button"
              className={cn(
                tabsTriggerVariants({ variant, size }),
                "aspect-square px-2 text-gray-500 hover:text-brand-600 dark:hover:text-brand-400",
              )}
              aria-label="添加标签页"
              onClick={handleAdd}
            >
              <Plus className="size-4" />
            </button>
          ) : null}
        </TabsPrimitive.List>
      </TabsListContext.Provider>
    );
  },
);
TabsList.displayName = TabsPrimitive.List.displayName;

type TabsTriggerProps = React.ComponentPropsWithoutRef<typeof TabsPrimitive.Trigger> & {
  icon?: React.ReactNode;
  badge?: React.ReactNode;
};

const TabsTrigger = React.forwardRef<React.ElementRef<typeof TabsPrimitive.Trigger>, TabsTriggerProps>(
  ({ className, icon, badge, children, value, ...props }, ref) => {
    const { variant, size, editable, onEdit } = React.useContext(TabsListContext);

    const handleClose = (event: React.MouseEvent<HTMLButtonElement>) => {
      event.stopPropagation();
      if (value != null) {
        onEdit?.(String(value), "remove");
      }
      requestAnimationFrame(() => {
        const active = event.currentTarget
          .closest('[role="tablist"]')
          ?.querySelector<HTMLElement>('[data-state="active"]');
        active?.focus();
      });
    };

    return (
      <TabsPrimitive.Trigger
        ref={ref}
        value={value}
        className={cn(tabsTriggerVariants({ variant, size }), editable && "gap-1", className)}
        {...props}
      >
        {icon}
        {children}
        {badge}
        {editable ? (
          <span
            aria-label="关闭标签页"
            className="ml-0.5 inline-flex rounded-sm p-0.5 text-gray-400 hover:bg-gray-100 hover:text-gray-700 dark:hover:bg-white/10 dark:hover:text-white"
            onClick={handleClose}
            onPointerDown={(event) => event.stopPropagation()}
          >
            <X className="size-3" />
          </span>
        ) : null}
      </TabsPrimitive.Trigger>
    );
  },
);
TabsTrigger.displayName = TabsPrimitive.Trigger.displayName;

const TabsContent = React.forwardRef<
  React.ElementRef<typeof TabsPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof TabsPrimitive.Content>
>(({ className, ...props }, ref) => (
  <TabsPrimitive.Content
    ref={ref}
    className={cn("mt-4 focus-visible:outline-hidden", className)}
    {...props}
  />
));
TabsContent.displayName = TabsPrimitive.Content.displayName;

export { Tabs, TabsList, TabsTrigger, TabsContent, tabsListVariants, tabsTriggerVariants };
