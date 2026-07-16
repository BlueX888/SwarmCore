import * as React from "react";
import { Eye, EyeOff } from "lucide-react";
import { cn } from "@/lib/utils";
import { Input, type InputProps } from "@/components/ui/input";

export type PasswordInputProps = Omit<InputProps, "type"> & {
  showToggle?: boolean;
};

export const PasswordInput = React.forwardRef<HTMLInputElement, PasswordInputProps>(
  ({ showToggle = true, className, disabled, ...props }, ref) => {
    const [visible, setVisible] = React.useState(false);

    return (
      <div className={cn("relative", className)}>
        <Input
          ref={ref}
          type={visible ? "text" : "password"}
          disabled={disabled}
          className={showToggle ? "pr-11" : undefined}
          {...props}
        />
        {showToggle ? (
          <button
            type="button"
            tabIndex={-1}
            disabled={disabled}
            onClick={() => setVisible((prev) => !prev)}
            className="absolute right-3 top-1/2 inline-flex size-8 -translate-y-1/2 items-center justify-center rounded-md text-gray-400 hover:bg-gray-100 hover:text-gray-600 disabled:opacity-40 dark:hover:bg-white/5"
            aria-label={visible ? "隐藏密码" : "显示密码"}
          >
            {visible ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
          </button>
        ) : null}
      </div>
    );
  },
);
PasswordInput.displayName = "PasswordInput";
