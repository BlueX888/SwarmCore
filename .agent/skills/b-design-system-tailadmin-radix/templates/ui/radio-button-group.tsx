import * as React from "react";
import * as RadioGroupPrimitive from "@radix-ui/react-radio-group";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const radioButtonGroupVariants = cva("flex gap-2", {
  variants: {
    orientation: {
      horizontal: "flex-row flex-wrap",
      vertical: "flex-col",
    },
    block: {
      true: "w-full",
      false: "",
    },
  },
  defaultVariants: {
    orientation: "horizontal",
    block: false,
  },
});

const radioButtonVariants = cva(
  "inline-flex shrink-0 items-center justify-center whitespace-nowrap rounded-lg text-sm font-medium transition-colors focus-visible:outline-hidden focus-visible:ring-3 focus-visible:ring-brand-500/20 disabled:pointer-events-none disabled:opacity-50 bg-white text-gray-700 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 dark:bg-gray-800 dark:text-gray-400 dark:ring-gray-700 dark:hover:bg-white/[0.03] dark:hover:text-gray-300 data-[state=checked]:bg-brand-50 data-[state=checked]:border-brand-500 data-[state=checked]:text-brand-700 data-[state=checked]:ring-brand-500 dark:data-[state=checked]:bg-brand-500/15 dark:data-[state=checked]:text-brand-300 dark:data-[state=checked]:ring-brand-500",
  {
    variants: {
      size: {
        sm: "h-9 px-3 text-xs",
        md: "h-11 px-4 text-sm",
        lg: "h-12 px-5 text-base",
      },
      block: {
        true: "flex-1",
        false: "",
      },
    },
    defaultVariants: {
      size: "md",
      block: false,
    },
  },
);

export type RadioButtonGroupProps = React.ComponentPropsWithoutRef<
  typeof RadioGroupPrimitive.Root
> &
  VariantProps<typeof radioButtonGroupVariants> & {
    size?: "sm" | "md" | "lg";
  };

const RadioButtonGroupContext = React.createContext<{
  size: "sm" | "md" | "lg";
  block: boolean;
}>({ size: "md", block: false });

export const RadioButtonGroup = React.forwardRef<
  React.ElementRef<typeof RadioGroupPrimitive.Root>,
  RadioButtonGroupProps
>(({ className, orientation = "horizontal", block = false, size = "md", ...props }, ref) => (
  <RadioButtonGroupContext.Provider value={{ size, block: Boolean(block) }}>
    <RadioGroupPrimitive.Root
      ref={ref}
      orientation={orientation ?? "horizontal"}
      className={cn(radioButtonGroupVariants({ orientation, block: Boolean(block) }), className)}
      {...props}
    />
  </RadioButtonGroupContext.Provider>
));
RadioButtonGroup.displayName = "RadioButtonGroup";

export type RadioButtonProps = React.ComponentPropsWithoutRef<
  typeof RadioGroupPrimitive.Item
>;

export const RadioButton = React.forwardRef<
  React.ElementRef<typeof RadioGroupPrimitive.Item>,
  RadioButtonProps
>(({ className, children, ...props }, ref) => {
  const { size, block } = React.useContext(RadioButtonGroupContext);
  return (
    <RadioGroupPrimitive.Item
      ref={ref}
      className={cn(radioButtonVariants({ size, block }), className)}
      {...props}
    >
      {children}
    </RadioGroupPrimitive.Item>
  );
});
RadioButton.displayName = "RadioButton";
