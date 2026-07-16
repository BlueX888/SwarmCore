import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const cardVariants = cva("rounded-2xl bg-white dark:bg-white/[0.03]", {
  variants: {
    variant: {
      elevated: "border border-transparent",
      outlined: "border border-gray-200 dark:border-gray-800",
    },
    elevation: {
      0: "shadow-none",
      1: "shadow-theme-xs",
      2: "shadow-theme-sm",
      4: "shadow-theme-md",
      8: "shadow-theme-lg",
    },
    square: {
      true: "rounded-none",
      false: "",
    },
  },
  defaultVariants: {
    variant: "outlined",
    elevation: 0,
    square: false,
  },
});

export interface CardProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof cardVariants> {}

const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className, variant, elevation, square, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(cardVariants({ variant, elevation, square }), className)}
      {...props}
    />
  ),
);
Card.displayName = "Card";

const CardHeader = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        "flex flex-col gap-1 px-6 py-5 sm:flex-row sm:items-center sm:justify-between",
        className,
      )}
      {...props}
    />
  ),
);
CardHeader.displayName = "CardHeader";

const CardTitle = React.forwardRef<HTMLParagraphElement, React.HTMLAttributes<HTMLHeadingElement>>(
  ({ className, ...props }, ref) => (
    <h3
      ref={ref}
      className={cn(
        "text-base font-semibold leading-none text-gray-800 dark:text-white/90",
        className,
      )}
      {...props}
    />
  ),
);
CardTitle.displayName = "CardTitle";

const CardDescription = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => (
  <p
    ref={ref}
    className={cn("text-theme-sm text-gray-500 dark:text-gray-400", className)}
    {...props}
  />
));
CardDescription.displayName = "CardDescription";

const CardAction = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn("flex shrink-0 items-center gap-2", className)} {...props} />
  ),
);
CardAction.displayName = "CardAction";

const CardContent = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn("p-6 pt-0", className)} {...props} />
  ),
);
CardContent.displayName = "CardContent";

const CardFooter = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        "flex items-center border-t border-gray-100 px-6 py-4 dark:border-white/[0.05]",
        className,
      )}
      {...props}
    />
  ),
);
CardFooter.displayName = "CardFooter";

export interface CardActionAreaProps extends React.HTMLAttributes<HTMLElement> {
  asChild?: boolean;
}

const CardActionArea = React.forwardRef<HTMLElement, CardActionAreaProps>(
  ({ className, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return (
      <Comp
        ref={ref as React.Ref<HTMLButtonElement>}
        type={asChild ? undefined : "button"}
        className={cn(
          "block w-full cursor-pointer text-left transition-colors hover:bg-gray-50 focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-brand-500/20 dark:hover:bg-white/[0.03]",
          className,
        )}
        {...props}
      />
    );
  },
);
CardActionArea.displayName = "CardActionArea";

const CardActions = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        "flex items-center justify-end gap-2 border-t border-gray-100 px-6 py-4 dark:border-white/[0.05]",
        className,
      )}
      {...props}
    />
  ),
);
CardActions.displayName = "CardActions";

export type CardTabItem = {
  key: string;
  tab: React.ReactNode;
  content: React.ReactNode;
};

export type TabbedCardProps = CardProps & {
  tabList: CardTabItem[];
  activeKey?: string;
  defaultActiveKey?: string;
  onTabChange?: (key: string) => void;
  title?: React.ReactNode;
};

export function TabbedCard({
  tabList,
  activeKey: activeKeyProp,
  defaultActiveKey,
  onTabChange,
  title,
  className,
  variant,
  elevation,
  square,
}: TabbedCardProps) {
  const [internalKey, setInternalKey] = React.useState(
    defaultActiveKey ?? tabList[0]?.key ?? "",
  );
  const activeKey = activeKeyProp ?? internalKey;
  const setActiveKey = (key: string) => {
    if (activeKeyProp == null) setInternalKey(key);
    onTabChange?.(key);
  };
  const activeTab = tabList.find((t) => t.key === activeKey) ?? tabList[0];

  return (
    <Card className={className} variant={variant} elevation={elevation} square={square}>
      {title ? (
        <CardHeader>
          <CardTitle>{title}</CardTitle>
        </CardHeader>
      ) : null}
      <div className="flex gap-1 border-b border-gray-100 px-6 dark:border-white/[0.05]">
        {tabList.map((item) => (
          <button
            key={item.key}
            type="button"
            role="tab"
            aria-selected={item.key === activeKey}
            className={cn(
              "border-b-2 px-3 py-2 text-theme-sm font-medium transition-colors",
              item.key === activeKey
                ? "border-brand-500 text-brand-600 dark:text-brand-400"
                : "border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400",
            )}
            onClick={() => setActiveKey(item.key)}
          >
            {item.tab}
          </button>
        ))}
      </div>
      <CardContent>{activeTab?.content}</CardContent>
    </Card>
  );
}

export {
  Card,
  CardHeader,
  CardFooter,
  CardTitle,
  CardDescription,
  CardContent,
  CardAction,
  CardActionArea,
  CardActions,
  TabbedCard,
  cardVariants,
};
export type { CardTabItem, TabbedCardProps };
