import * as React from "react";
import * as SwitchPrimitives from "@radix-ui/react-switch";
import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

export type SwitchProps = React.ComponentPropsWithoutRef<typeof SwitchPrimitives.Root> & {
  loading?: boolean;
};

const Switch = React.forwardRef<
  React.ElementRef<typeof SwitchPrimitives.Root>,
  SwitchProps
>(({ className, loading = false, disabled, ...props }, ref) => (
  <SwitchPrimitives.Root
    className={cn(
      "peer relative inline-flex h-6 w-11 shrink-0 cursor-pointer items-center rounded-full border-2 border-transparent shadow-theme-sm transition-colors duration-150 ease-linear focus-visible:outline-hidden focus-visible:ring-3 focus-visible:ring-brand-500/20 disabled:cursor-not-allowed disabled:opacity-50 data-[state=checked]:bg-brand-500 data-[state=unchecked]:bg-gray-200 dark:data-[state=unchecked]:bg-white/10",
      loading && "cursor-wait opacity-80",
      className,
    )}
    disabled={disabled || loading}
    aria-busy={loading || undefined}
    data-loading={loading || undefined}
    {...props}
    ref={ref}
  >
    <SwitchPrimitives.Thumb
      className={cn(
        "pointer-events-none block size-5 rounded-full bg-white shadow-theme-sm ring-0 transition-transform duration-150 ease-linear data-[state=checked]:translate-x-5 data-[state=unchecked]:translate-x-0",
      )}
    />
    {loading ? (
      <Loader2
        className="pointer-events-none absolute left-1/2 top-1/2 size-3.5 -translate-x-1/2 -translate-y-1/2 animate-spin text-brand-600"
        aria-hidden
      />
    ) : null}
  </SwitchPrimitives.Root>
));
Switch.displayName = SwitchPrimitives.Root.displayName;

export { Switch };
