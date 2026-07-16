import * as React from "react";
import { cn } from "@/lib/utils";

export type StatCountdownFormat = "dhms" | "hms";

export type StatCountdownProps = {
  value: number | Date;
  format?: StatCountdownFormat;
  onFinish?: () => void;
  className?: string;
};

function resolveTargetMs(value: number | Date): number {
  if (value instanceof Date) return value.getTime();
  return value > 1e12 ? value : value * 1000;
}

function pad(n: number): string {
  return String(n).padStart(2, "0");
}

function formatRemaining(ms: number, format: StatCountdownFormat): string {
  if (ms <= 0) return format === "dhms" ? "0天 00:00:00" : "00:00:00";

  const totalSeconds = Math.floor(ms / 1000);
  const days = Math.floor(totalSeconds / 86400);
  const hours = Math.floor((totalSeconds % 86400) / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;

  if (format === "hms") {
    const totalHours = days * 24 + hours;
    return `${pad(totalHours)}:${pad(minutes)}:${pad(seconds)}`;
  }

  return `${days}天 ${pad(hours)}:${pad(minutes)}:${pad(seconds)}`;
}

/**
 * 倒计时 KPI — 对标 antd Statistic.Countdown；可嵌入 StatMetric value slot。
 */
export function StatCountdown({
  value,
  format = "dhms",
  onFinish,
  className,
}: StatCountdownProps) {
  const targetMs = resolveTargetMs(value);
  const [remaining, setRemaining] = React.useState(() =>
    Math.max(0, targetMs - Date.now()),
  );
  const finishedRef = React.useRef(false);

  React.useEffect(() => {
    finishedRef.current = false;
    setRemaining(Math.max(0, targetMs - Date.now()));

    const tick = () => {
      const next = Math.max(0, targetMs - Date.now());
      setRemaining(next);
      if (next <= 0 && !finishedRef.current) {
        finishedRef.current = true;
        onFinish?.();
      }
    };

    tick();
    const id = window.setInterval(tick, 1000);
    return () => window.clearInterval(id);
  }, [targetMs, onFinish]);

  return (
    <span
      className={cn(
        "font-semibold tabular-nums text-gray-800 dark:text-white/90",
        remaining <= 0 && "text-gray-400 dark:text-gray-500",
        className,
      )}
      aria-live="polite"
    >
      {formatRemaining(remaining, format)}
    </span>
  );
}
