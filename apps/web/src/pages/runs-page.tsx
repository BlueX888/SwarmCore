import { useEffect, useMemo, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ArrowRight, ChevronDown, Plus, RefreshCw, Search } from "lucide-react";
import { Link } from "react-router";
import { api } from "@/api/client";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusBadge } from "@/components/ui/status-badge";
import { useWorkspaceScope } from "@/lib/demo-scope";
import { statusLabel } from "@/lib/display-text";
import { cn } from "@/lib/utils";

const fieldClass =
  "h-11 w-full rounded-xl border border-gray-200 bg-white px-3 text-sm outline-none focus:border-brand-500 dark:border-gray-700 dark:bg-gray-900";

const menuClass =
  "absolute inset-x-0 z-20 mt-1.5 max-h-64 overflow-auto rounded-xl border border-gray-200 bg-white py-1 shadow-theme-sm dark:border-gray-700 dark:bg-gray-900";

const optionClass = "w-full px-3 py-2 text-left text-sm";

const RUN_STATUS_FILTERS = [
  "RUNNING",
  "QUEUED",
  "SUCCEEDED",
  "FAILED",
  "WAITING_INPUT",
  "WAITING_APPROVAL",
  "PAUSED",
  "PAUSING",
  "CANCELLED",
  "CANCELLING",
  "TIMED_OUT",
  "REJECTED",
  "ACCEPTED",
  "VALIDATING",
  "COMPENSATING",
] as const;

const STATUS_FILTER_OPTIONS = [
  { value: "", label: "全部状态" },
  ...RUN_STATUS_FILTERS.map((value) => ({ value, label: statusLabel(value) })),
] as const;

export function RunsPage() {
  const { tenantId, projectId } = useWorkspaceScope();
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const query = useQuery({
    queryKey: ["runs", tenantId, projectId],
    queryFn: () => api.listRuns(tenantId, projectId),
    refetchInterval: 5000,
  });
  const items = useMemo(() => {
    const needle = search.trim().toLowerCase();
    return (query.data?.items ?? []).filter((run) => {
      const matchesStatus = !status || run.status === status;
      const matchesSearch = !needle || run.runId.toLowerCase().includes(needle);
      return matchesStatus && matchesSearch;
    });
  }, [query.data?.items, search, status]);
  const hasFilter = Boolean(search.trim() || status);

  return (
    <div className="min-w-0 space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-brand-500">运行管理</p>
          <h1 className="mt-1 text-2xl font-semibold text-gray-900 dark:text-white">运行记录</h1>
          <p className="mt-1 text-sm text-gray-500">
            查看耐久运行、任务、事件和结构化结果。
          </p>
        </div>
        <div className="flex gap-2"><Button variant="outline" onClick={() => void query.refetch()} loading={query.isFetching}><RefreshCw />刷新</Button><Button asChild><Link to="new"><Plus />新建运行</Link></Button></div>
      </div>
      {query.isPending ? (
        <Card><CardContent className="space-y-4 pt-5">{[1, 2, 3].map((item) => <Skeleton key={item} className="h-14 w-full" />)}</CardContent></Card>
      ) : null}
      {query.isError ? (
        <Card><CardContent className="flex min-h-60 flex-col items-center justify-center gap-3 pt-5 text-center"><p className="font-medium text-error-600">无法加载运行记录</p><p className="text-sm text-gray-500">请检查 API 连接后重试。</p><Button onClick={() => void query.refetch()}>重试</Button></CardContent></Card>
      ) : null}
      {query.data?.items.length === 0 ? (
        <Card><CardContent className="flex min-h-60 flex-col items-center justify-center gap-2 pt-5 text-center"><ActivityIcon /><p className="font-medium">暂无运行记录</p><p className="text-sm text-gray-500">请选择已发布的策略版本开始运行。</p><Button asChild className="mt-2"><Link to="new">创建运行</Link></Button></CardContent></Card>
      ) : null}
      {query.data?.items.length ? (
        <Card className="min-w-0 overflow-visible">
          <CardHeader>
            <CardTitle>最近运行</CardTitle>
            <span className="text-sm text-gray-500">
              {hasFilter ? `匹配 ${items.length} / 共 ${query.data.total} 条` : `共 ${query.data.total} 条`}
            </span>
          </CardHeader>
          <CardContent className="w-full max-w-full overflow-visible px-0">
            <div className="relative z-10 grid gap-3 border-b border-gray-100 px-5 pb-4 dark:border-gray-800 md:grid-cols-[minmax(0,1fr)_12rem]">
              <label className="relative">
                <span className="sr-only">搜索运行 ID</span>
                <Search className="pointer-events-none absolute left-3 top-1/2 size-5 -translate-y-1/2 text-gray-400" />
                <input
                  aria-label="搜索运行 ID"
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  placeholder="搜索运行 ID"
                  className={`${fieldClass} pl-10`}
                />
              </label>
              <StatusFilterSelect value={status} onChange={setStatus} />
            </div>
            {!items.length ? (
              <div className="flex min-h-48 flex-col items-center justify-center px-5 py-10 text-center">
                <p className="font-medium text-gray-900 dark:text-white">没有匹配的运行</p>
                <p className="mt-1 text-sm text-gray-500">调整搜索或状态筛选后再试。</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <div className="divide-y divide-gray-100 px-5 md:hidden dark:divide-gray-800">
                  {items.map((run) => (
                    <div key={run.runId} className="space-y-3 py-4">
                      <div className="flex items-center justify-between gap-3"><StatusBadge status={run.status} /><Button asChild variant="ghost" size="sm"><Link to={run.runId}>查看 <ArrowRight /></Link></Button></div>
                      <p className="break-all font-mono text-xs text-gray-700 dark:text-gray-300">{run.runId}</p>
                      <p className="text-xs text-gray-500">{Object.values(run.taskCounts).reduce((a, b) => a + b, 0)} 个任务 · {run.snapshotSeq} 个事件</p>
                    </div>
                  ))}
                </div>
                <table className="hidden w-full min-w-[720px] text-left text-sm md:table">
                  <thead className="border-y border-gray-100 bg-gray-50 text-xs text-gray-500 dark:border-gray-800 dark:bg-gray-800/50"><tr><th className="px-5 py-3 font-medium">运行 ID</th><th className="px-5 py-3 font-medium">状态</th><th className="px-5 py-3 font-medium">任务</th><th className="px-5 py-3 font-medium">事件</th><th className="px-5 py-3"><span className="sr-only">打开</span></th></tr></thead>
                  <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                    {items.map((run) => (
                      <tr key={run.runId} className="hover:bg-gray-50 dark:hover:bg-white/[0.03]"><td className="px-5 py-4 font-mono text-xs text-gray-700 dark:text-gray-300">{run.runId}</td><td className="px-5 py-4"><StatusBadge status={run.status} /></td><td className="px-5 py-4 text-gray-500">{Object.values(run.taskCounts).reduce((a, b) => a + b, 0)}</td><td className="px-5 py-4 text-gray-500">{run.snapshotSeq}</td><td className="px-5 py-4 text-right"><Button asChild variant="ghost" size="sm"><Link to={run.runId}>查看 <ArrowRight /></Link></Button></td></tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}

function StatusFilterSelect({
  value,
  onChange,
}: {
  value: string;
  onChange: (value: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const selected = STATUS_FILTER_OPTIONS.find((option) => option.value === value) ?? STATUS_FILTER_OPTIONS[0];

  useEffect(() => {
    if (!open) return;
    const onPointerDown = (event: MouseEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) setOpen(false);
    };
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };
    document.addEventListener("mousedown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("mousedown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [open]);

  return (
    <div ref={rootRef} className="relative">
      <button
        type="button"
        aria-label="按状态筛选"
        aria-haspopup="listbox"
        aria-expanded={open}
        onClick={() => setOpen((current) => !current)}
        className={cn(
          fieldClass,
          "flex items-center justify-between gap-2 pr-2.5 text-left",
          open && "border-brand-500",
        )}
      >
        <span className="truncate">{selected.label}</span>
        <ChevronDown
          className={cn("size-4 shrink-0 text-gray-400", open && "rotate-180")}
          aria-hidden
        />
      </button>
      {open ? (
        <ul role="listbox" aria-label="运行状态" className={menuClass}>
          {STATUS_FILTER_OPTIONS.map((option) => {
            const active = option.value === value;
            return (
              <li key={option.value || "all"} role="presentation">
                <button
                  type="button"
                  role="option"
                  aria-selected={active}
                  className={cn(
                    optionClass,
                    active ? "bg-brand-50 font-medium text-brand-600" : "hover:bg-gray-50",
                  )}
                  onClick={() => {
                    onChange(option.value);
                    setOpen(false);
                  }}
                >
                  {option.label}
                </button>
              </li>
            );
          })}
        </ul>
      ) : null}
    </div>
  );
}

function ActivityIcon() {
  return <span className="grid size-12 place-items-center rounded-full bg-brand-50 text-brand-500 dark:bg-brand-500/15">●</span>;
}
