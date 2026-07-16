import * as React from "react";
import { ArrowUp } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

export type FloatButtonProps = {
  mode?: "fab" | "backTop";
  icon?: React.ReactNode;
  label?: string;
  onClick?: () => void;
  /** backTop 模式：滚动超过该像素后显示 */
  visibilityHeight?: number;
  className?: string;
};

export function FloatButton({
  mode = "fab",
  icon,
  label,
  onClick,
  visibilityHeight = 400,
  className,
}: FloatButtonProps) {
  const [visible, setVisible] = React.useState(mode === "fab");

  React.useEffect(() => {
    if (mode !== "backTop") return;
    const onScroll = () => setVisible(window.scrollY > visibilityHeight);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, [mode, visibilityHeight]);

  const handleClick = () => {
    if (mode === "backTop") {
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
    onClick?.();
  };

  if (!visible) return null;

  return (
    <Button
      type="button"
      variant="solid"
      size="md"
      onClick={handleClick}
      className={cn(
        "fixed bottom-6 right-6 z-40 size-12 rounded-full p-0 shadow-theme-lg",
        className,
      )}
      aria-label={label ?? (mode === "backTop" ? "回到顶部" : "浮动按钮")}
    >
      {icon ?? (mode === "backTop" ? <ArrowUp className="size-5" /> : null)}
    </Button>
  );
}
