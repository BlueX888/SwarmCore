import * as React from "react";
import * as AccordionPrimitive from "@radix-ui/react-accordion";
import { ChevronDown } from "lucide-react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const accordionItemVariants = cva("overflow-hidden", {
  variants: {
    variant: {
      outline: "rounded-xl border border-gray-200 dark:border-gray-800",
      enclosed: "rounded-lg bg-gray-50 dark:bg-white/[0.03]",
      ghost: "rounded-lg border border-transparent bg-transparent",
    },
    size: {
      sm: "text-sm",
      md: "text-sm",
      lg: "text-base",
    },
  },
  defaultVariants: { variant: "outline", size: "md" },
});

const Accordion = AccordionPrimitive.Root;

type AccordionItemProps = React.ComponentPropsWithoutRef<typeof AccordionPrimitive.Item> &
  VariantProps<typeof accordionItemVariants>;

const AccordionItem = React.forwardRef<React.ElementRef<typeof AccordionPrimitive.Item>, AccordionItemProps>(
  ({ className, variant, size, ...props }, ref) => (
    <AccordionPrimitive.Item
      ref={ref}
      className={cn(accordionItemVariants({ variant, size }), className)}
      {...props}
    />
  ),
);
AccordionItem.displayName = AccordionItem.displayName;

const AccordionTrigger = React.forwardRef<
  React.ElementRef<typeof AccordionPrimitive.Trigger>,
  React.ComponentPropsWithoutRef<typeof AccordionPrimitive.Trigger>
>(({ className, children, ...props }, ref) => (
  <AccordionPrimitive.Header className="flex">
    <AccordionPrimitive.Trigger
      ref={ref}
      className={cn(
        "flex flex-1 items-center justify-between px-4 py-3 font-medium text-gray-800 transition-all hover:text-brand-600 focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-brand-500/20 dark:text-white/90 [&[data-state=open]>svg]:rotate-180",
        className,
      )}
      {...props}
    >
      {children}
      <ChevronDown className="size-4 shrink-0 text-gray-400 transition-transform duration-200" />
    </AccordionPrimitive.Trigger>
  </AccordionPrimitive.Header>
));
AccordionTrigger.displayName = AccordionPrimitive.Trigger.displayName;

const AccordionContent = React.forwardRef<
  React.ElementRef<typeof AccordionPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof AccordionPrimitive.Content>
>(({ className, children, ...props }, ref) => (
  <AccordionPrimitive.Content
    ref={ref}
    className="overflow-hidden text-sm text-gray-500 data-[state=closed]:animate-accordion-up data-[state=open]:animate-accordion-down dark:text-gray-400"
    {...props}
  >
    <div className={cn("px-4 pb-4 pt-0", className)}>{children}</div>
  </AccordionPrimitive.Content>
));
AccordionContent.displayName = AccordionPrimitive.Content.displayName;

export { Accordion, AccordionItem, AccordionTrigger, AccordionContent, accordionItemVariants };
