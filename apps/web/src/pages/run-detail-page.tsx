import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Background, Controls, type Edge, type Node, ReactFlow } from "@xyflow/react";
import { Ban, CircleDollarSign, Clock3, ExternalLink, Hash, RefreshCw } from "lucide-react";
import * as React from "react";
import { Link, useParams } from "react-router";
import { api } from "@/api/client";
import type { RunEvent, TaskSnapshot } from "@/api/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusBadge } from "@/components/ui/status-badge";
import { useRunEvents } from "@/hooks/use-run-events";
import { cn } from "@/lib/utils";
import { useRunEventStore } from "@/stores/run-event-store";

function graph(tasks: TaskSnapshot[]): { nodes: Node[]; edges: Edge[] } {
  const depths = new Map<string, number>();
  for (const task of tasks) depths.set(task.nodeKey, task.dependencies.length ? Math.max(...task.dependencies.map((key) => depths.get(key) ?? 0)) + 1 : 0);
  const rows = new Map<number, number>();
  const nodes = tasks.map((task) => {
    const depth = depths.get(task.nodeKey) ?? 0;
    const row = rows.get(depth) ?? 0;
    rows.set(depth, row + 1);
    return { id: task.nodeKey, position: { x: depth * 230, y: row * 100 }, data: { label: `${task.nodeKey} · ${task.status}` }, className: cn("run-node", `run-node-${task.status.toLowerCase()}`) };
  });
  const edges = tasks.flatMap((task) => task.dependencies.map((source) => ({ id: `${source}-${task.nodeKey}`, source, target: task.nodeKey })));
  return { nodes, edges };
}

export function RunDetailPage() {
  const { tenantId = "", projectId = "", runId = "" } = useParams();
  const queryClient = useQueryClient();
  const runQuery = useQuery({ queryKey: ["run", tenantId, projectId, runId], queryFn: () => api.getRun(tenantId, projectId, runId), refetchInterval: (query) => query.state.data?.allowedActions.length ? 3000 : false });
  const historyQuery = useQuery({ queryKey: ["events", tenantId, projectId, runId], queryFn: () => api.history(tenantId, projectId, runId, 0) });
  useRunEvents(tenantId, projectId, runQuery.data);
  const stream = useRunEventStore((state) => state.runs[runId]);
  const cancel = useMutation({ mutationFn: () => api.cancelRun(tenantId, projectId, runId), onSuccess: () => queryClient.invalidateQueries({ queryKey: ["run", tenantId, projectId, runId] }) });
  const events = React.useMemo(() => mergeEvents(historyQuery.data?.items ?? [], stream?.events ?? []), [historyQuery.data?.items, stream?.events]);
  if (runQuery.isPending) return <div className="space-y-5"><Skeleton className="h-20" /><Skeleton className="h-96" /></div>;
  if (runQuery.isError) return <Card><CardContent className="flex min-h-60 flex-col items-center justify-center gap-3 pt-5"><p className="font-medium text-error-600">Run could not be loaded</p><Button onClick={() => void runQuery.refetch()}>Retry</Button></CardContent></Card>;
  const run = runQuery.data;
  const flow = graph(run.tasks);
  const failedTasks = run.tasks.filter((task) => task.status === "FAILED");
  return <div className="space-y-6">
    <div><Link to=".." className="text-sm text-brand-500 hover:text-brand-600">← Runs</Link><div className="mt-3 flex flex-wrap items-start justify-between gap-4"><div><div className="flex flex-wrap items-center gap-3"><h1 className="text-2xl font-semibold text-gray-900 dark:text-white">Run detail</h1><StatusBadge status={run.status} /><StatusBadge status={stream?.connection ?? "CONNECTING"} /></div><p className="mt-2 font-mono text-xs text-gray-500">{run.runId}</p></div><div className="flex flex-wrap gap-2"><Button asChild variant="outline"><a href={api.temporalUrl(tenantId, runId)} target="_blank" rel="noreferrer">Temporal <ExternalLink /></a></Button><Button asChild variant="outline"><a href={api.phoenixUrl} target="_blank" rel="noreferrer">Phoenix <ExternalLink /></a></Button><Button variant="outline" onClick={() => void runQuery.refetch()}><RefreshCw />Refresh</Button>{run.allowedActions.includes("cancel") ? <Button variant="destructive" loading={cancel.isPending} onClick={() => { if (window.confirm("Cancel this Run? In-flight work will be stopped.")) cancel.mutate(); }}><Ban />Cancel run</Button> : null}</div></div></div>
    {cancel.isError ? <div role="alert" className="rounded-xl border border-error-500 bg-error-50 p-4 text-sm text-error-600 dark:bg-error-500/15">Cancellation was not accepted. Retry with a new command.</div> : null}
    {stream?.connection === "STALE" ? <div role="alert" className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-warning-300 bg-warning-50 p-4 text-sm text-warning-700 dark:bg-warning-500/10"><span>The event cursor expired. The latest snapshot was loaded; reconnecting from the new cursor.</span><Button size="sm" variant="outline" onClick={() => { void historyQuery.refetch(); void runQuery.refetch(); }}>Reload history</Button></div> : null}
    {failedTasks.length ? <Card><CardHeader><CardTitle className="text-error-600">Failed tasks</CardTitle></CardHeader><CardContent><ul className="space-y-3">{failedTasks.map((task) => <li key={task.taskId} className="rounded-xl border border-error-200 p-3 dark:border-error-500/30"><p className="font-medium">{task.nodeKey}</p><pre className="mt-2 whitespace-pre-wrap break-words text-xs text-error-600">{JSON.stringify(task.error ?? { message: "No structured error was recorded." }, null, 2)}</pre></li>)}</ul></CardContent></Card> : null}
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4"><Metric icon={<Clock3 />} label="Duration" value={formatDuration(run.startedAt, run.completedAt)} /><Metric icon={<Hash />} label="Tokens" value={formatTokens(run.usage)} /><Metric icon={<CircleDollarSign />} label="Cost" value={formatCost(run.usage)} /><Metric icon={<Hash />} label="Plan" value={run.planHash.slice(0, 10)} mono /></div>
    <div className="grid gap-4 sm:grid-cols-2"><Metric icon={<Clock3 />} label="Started" value={formatTime(run.startedAt)} /><Metric icon={<Clock3 />} label="Finished" value={formatTime(run.completedAt)} /></div>
    <Card><CardHeader><CardTitle>Execution graph</CardTitle><span className="text-xs text-gray-500">{run.tasks.length} task nodes</span></CardHeader><CardContent><div className="h-[420px] overflow-hidden rounded-xl border border-gray-200 dark:border-gray-800">{run.tasks.length ? <ReactFlow nodes={flow.nodes} edges={flow.edges} fitView minZoom={0.25} maxZoom={1.5}><Background /><Controls /></ReactFlow> : <div className="grid h-full place-items-center text-sm text-gray-500">Tasks appear when the worker starts execution.</div>}</div></CardContent></Card>
    <div className="grid gap-6 xl:grid-cols-[minmax(0,1.4fr)_minmax(320px,.6fr)]"><Timeline events={events} loading={historyQuery.isPending} /><Card><CardHeader><CardTitle>Structured result</CardTitle></CardHeader><CardContent><pre className="max-h-[480px] overflow-auto rounded-xl bg-gray-900 p-4 text-xs text-white">{JSON.stringify(run.output ?? { status: "Result pending" }, null, 2)}</pre></CardContent></Card></div>
  </div>;
}

function Metric({ icon, label, value, mono }: { icon: React.ReactNode; label: string; value: string; mono?: boolean }) { return <Card><CardContent className="flex items-center gap-4 pt-5"><span className="grid size-11 place-items-center rounded-xl bg-brand-50 text-brand-500 dark:bg-brand-500/15">{icon}</span><div><p className="text-xs text-gray-500">{label}</p><p className={cn("mt-1 font-semibold text-gray-900 dark:text-white", mono && "font-mono text-sm")}>{value}</p></div></CardContent></Card>; }
function formatCost(usage: Record<string, unknown>) { const value = usage.costUsd; return typeof value === "number" ? `$${value.toFixed(4)}` : "—"; }
function formatTokens(usage: Record<string, unknown>) { const direct = usage.tokens; const input = usage.input_tokens; const output = usage.output_tokens; const value = typeof direct === "number" ? direct : (typeof input === "number" ? input : 0) + (typeof output === "number" ? output : 0); return value ? value.toLocaleString() : "—"; }
function formatTime(value?: string | null) { return value ? new Date(value).toLocaleString() : "—"; }
function formatDuration(start?: string | null, end?: string | null) { if (!start) return "—"; const milliseconds = new Date(end ?? Date.now()).getTime() - new Date(start).getTime(); if (milliseconds < 1000) return `${milliseconds} ms`; return `${(milliseconds / 1000).toFixed(1)} s`; }
function mergeEvents(first: RunEvent[], second: RunEvent[]) { return [...new Map([...first, ...second].map((event) => [event.seq, event])).values()].sort((a,b) => b.seq-a.seq); }
function Timeline({ events, loading }: { events: RunEvent[]; loading: boolean }) { return <Card><CardHeader><CardTitle>Event timeline</CardTitle><span className="text-xs text-gray-500">Newest first</span></CardHeader><CardContent>{loading ? <div className="space-y-3"><Skeleton className="h-14" /><Skeleton className="h-14" /></div> : events.length ? <ol className="max-h-[480px] space-y-4 overflow-y-auto pr-2">{events.map((event) => <li key={event.id} className="relative border-l border-gray-200 pl-5 dark:border-gray-700"><span className="absolute -left-1.5 top-1 size-3 rounded-full border-2 border-white bg-brand-500 dark:border-gray-900" /><div className="flex flex-wrap items-center justify-between gap-2"><p className="text-sm font-medium text-gray-800 dark:text-white/90">{event.type}</p><time className="text-xs text-gray-500">#{event.seq} · {new Date(event.occurredAt).toLocaleTimeString()}</time></div><p className="mt-1 truncate font-mono text-xs text-gray-500">{JSON.stringify(event.data)}</p></li>)}</ol> : <div className="grid min-h-60 place-items-center text-sm text-gray-500">No durable events are available.</div>}</CardContent></Card>; }
