import * as React from "react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Pause, Play, Search } from "lucide-react";

export type LogSeverity = "debug" | "info" | "warn" | "error";

export type LogLine = {
  id: string;
  timestamp: string;
  severity: LogSeverity;
  message: string;
};

export type LogStreamPanelProps = {
  lines: LogLine[];
  height?: number;
  paused?: boolean;
  onPauseToggle?: () => void;
  search?: string;
  onSearchChange?: (value: string) => void;
  severityFilter?: LogSeverity | "all";
  onSeverityFilterChange?: (severity: LogSeverity | "all") => void;
  autoScroll?: boolean;
  className?: string;
};

const severityColor: Record<LogSeverity, string> = {
  debug: "text-gray-500",
  info: "text-brand-500",
  warn: "text-warning-600 dark:text-orange-400",
  error: "text-error-600 dark:text-error-500",
};

/**
 * Fixed-height build log stream — auto-scroll, pause, search, severity filter.
 * @see references/layout-patterns/cicd-release.md
 */
export function LogStreamPanel({
  lines,
  height = 180,
  paused = false,
  onPauseToggle,
  search = "",
  onSearchChange,
  severityFilter = "all",
  onSeverityFilterChange,
  autoScroll = true,
  className,
}: LogStreamPanelProps) {
  const scrollRef = React.useRef<HTMLDivElement>(null);

  const filtered = lines.filter((line) => {
    const matchesSeverity = severityFilter === "all" || line.severity === severityFilter;
    const matchesSearch =
      !search || line.message.toLowerCase().includes(search.toLowerCase());
    return matchesSeverity && matchesSearch;
  });

  React.useEffect(() => {
    if (!autoScroll || paused || !scrollRef.current) return;
    scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [filtered.length, autoScroll, paused]);

  return (
    <div
      className={cn(
        "flex flex-col overflow-hidden rounded-xl border border-gray-200 bg-gray-900 dark:border-gray-800",
        className,
      )}
    >
      <div className="flex flex-wrap items-center gap-2 border-b border-gray-800 bg-gray-950 px-3 py-2">
        <div className="relative min-w-[140px] flex-1">
          <Search className="pointer-events-none absolute left-2.5 top-1/2 size-3.5 -translate-y-1/2 text-gray-500" />
          <Input
            value={search}
            onChange={(e) => onSearchChange?.(e.target.value)}
            placeholder="搜索日志..."
            className="h-8 border-gray-700 bg-gray-900 pl-8 text-xs text-gray-200 placeholder:text-gray-500"
          />
        </div>
        <div className="flex items-center gap-1">
          {(["all", "info", "warn", "error"] as const).map((sev) => (
            <Button
              key={sev}
              type="button"
              size="sm"
              variant={severityFilter === sev ? "default" : "outline"}
              className="h-7 px-2 text-xs"
              onClick={() => onSeverityFilterChange?.(sev)}
            >
              {sev}
            </Button>
          ))}
        </div>
        <Button
          type="button"
          size="sm"
          variant="outline"
          className="h-7 gap-1 px-2 text-xs"
          onClick={onPauseToggle}
        >
          {paused ? <Play className="size-3" /> : <Pause className="size-3" />}
          {paused ? "Resume" : "Pause"}
        </Button>
        {paused ? (
          <Badge variant="light" color="warning" size="sm">
            paused
          </Badge>
        ) : null}
      </div>

      <div
        ref={scrollRef}
        className="overflow-y-auto font-mono text-[11px] leading-relaxed"
        style={{ height }}
        role="log"
        aria-live={paused ? "off" : "polite"}
      >
        {filtered.length === 0 ? (
          <p className="p-4 text-center text-gray-500">No log lines match the current filter.</p>
        ) : (
          filtered.map((line) => (
            <div
              key={line.id}
              className="flex gap-3 border-b border-gray-800/60 px-3 py-1 hover:bg-white/[0.03]"
            >
              <span className="shrink-0 tabular-nums text-gray-500">{line.timestamp}</span>
              <span className={cn("w-12 shrink-0 uppercase", severityColor[line.severity])}>
                {line.severity}
              </span>
              <span className="min-w-0 flex-1 whitespace-pre-wrap break-words text-gray-200">
                {line.message}
              </span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
