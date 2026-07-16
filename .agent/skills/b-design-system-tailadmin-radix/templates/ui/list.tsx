import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva } from "class-variance-authority";
import { cn } from "@/lib/utils";
import { Separator } from "@/components/ui/separator";

const listContext = React.createContext<{
  density: "comfortable" | "compact";
}>({ density: "comfortable" });

const listItemVariants = cva(
  "flex w-full items-center gap-3 px-4 text-left transition-colors",
  {
    variants: {
      density: {
        comfortable: "py-3.5",
        compact: "py-2.5",
      },
      interactive: {
        true: "cursor-pointer hover:bg-gray-50 dark:hover:bg-white/[0.03]",
        false: "",
      },
      destructive: {
        true: "text-error-600 dark:text-error-400",
        false: "text-gray-800 dark:text-white/90",
      },
    },
    defaultVariants: {
      density: "comfortable",
      interactive: false,
      destructive: false,
    },
  },
);

export type ListProps = React.HTMLAttributes<HTMLUListElement> & {
  density?: "comfortable" | "compact";
  divided?: boolean;
};

function List({
  density = "comfortable",
  divided = false,
  className,
  children,
  ...props
}: ListProps) {
  const items = React.Children.toArray(children).filter(React.isValidElement);

  return (
    <listContext.Provider value={{ density }}>
      <ul className={cn("flex flex-col", className)} role="list" {...props}>
        {items.map((child, index) => (
          <React.Fragment key={child.key ?? index}>
            {child}
            {divided && index < items.length - 1 ? (
              <li className="list-none px-4" aria-hidden="true">
                <Separator />
              </li>
            ) : null}
          </React.Fragment>
        ))}
      </ul>
    </listContext.Provider>
  );
}

export type ListItemProps = React.HTMLAttributes<HTMLElement> & {
  asChild?: boolean;
  onClick?: React.MouseEventHandler<HTMLElement>;
  destructive?: boolean;
};

const ListItem = React.forwardRef<HTMLElement, ListItemProps>(
  ({ className, asChild = false, onClick, destructive = false, children, ...props }, ref) => {
    const { density } = React.useContext(listContext);
    const Comp = asChild ? Slot : onClick ? "button" : "div";

    return (
      <li className="list-none">
        <Comp
          ref={ref as React.Ref<HTMLButtonElement & HTMLDivElement>}
          type={onClick && !asChild ? "button" : undefined}
          onClick={onClick}
          className={cn(
            listItemVariants({
              density,
              interactive: Boolean(onClick),
              destructive,
            }),
            className,
          )}
          {...props}
        >
          {children}
        </Comp>
      </li>
    );
  },
);
ListItem.displayName = "ListItem";

const ListItemIcon = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        "flex size-10 shrink-0 items-center justify-center text-gray-500 dark:text-gray-400 [&_svg]:size-5",
        className,
      )}
      {...props}
    />
  ),
);
ListItemIcon.displayName = "ListItemIcon";

const ListItemText = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn("min-w-0 flex-1 grid gap-0.5", className)} {...props} />
  ),
);
ListItemText.displayName = "ListItemText";

const ListItemTrailing = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn("ml-auto flex shrink-0 items-center gap-2", className)} {...props} />
  ),
);
ListItemTrailing.displayName = "ListItemTrailing";

export { List, ListItem, ListItemIcon, ListItemText, ListItemTrailing, listItemVariants };
