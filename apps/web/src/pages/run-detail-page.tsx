import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Background, Controls, type Edge, type Node, ReactFlow } from "@xyflow/react";
import { Ban, Check, CircleDollarSign, Clock3, ExternalLink, Hash, Pause, Play, RefreshCw, RotateCcw, X } from "lucide-react";
import * as React from "react";
import { Link, useParams } from "react-router";
import { api } from "@/api/client";
import type { ApprovalRequest, CommandHandle, ExternalInputRequest, RunEvent, TaskSnapshot } from "@/api/types";
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
  const approvalsQuery = useQuery({ queryKey: ["approvals", tenantId, projectId, runId], queryFn: () => api.listApprovals(tenantId, projectId, runId), refetchInterval: 3000 });
  const inputsQuery = useQuery({ queryKey: ["inputs", tenantId, projectId, runId], queryFn: () => api.listInputs(tenantId, projectId, runId), refetchInterval: 3000 });
  useRunEvents(tenantId, projectId, runQuery.data);
  const stream = useRunEventStore((state) => state.runs[runId]);
  const [lastCommand, setLastCommand] = React.useState<CommandHandle | null>(null);
  const commandQuery = useQuery({ queryKey: ["command", tenantId, projectId, lastCommand?.commandId], queryFn: () => api.getCommand(tenantId, projectId, lastCommand?.commandId ?? ""), enabled: Boolean(lastCommand), refetchInterval: (query) => ["ACCEPTED", "DELIVERING"].includes(query.state.data?.status ?? "ACCEPTED") ? 1000 : false });
  const control = useMutation({ mutationFn: (operation: () => Promise<CommandHandle>) => operation(), onSuccess: (command) => { setLastCommand(command); void queryClient.invalidateQueries({ queryKey: ["run", tenantId, projectId, runId] }); void queryClient.invalidateQueries({ queryKey: ["approvals", tenantId, projectId, runId] }); void queryClient.invalidateQueries({ queryKey: ["inputs", tenantId, projectId, runId] }); } });
  const events = React.useMemo(() => mergeEvents(historyQuery.data?.items ?? [], stream?.events ?? []), [historyQuery.data?.items, stream?.events]);
  if (runQuery.isPending) return <div className="space-y-5"><Skeleton className="h-20" /><Skeleton className="h-96" /></div>;
  if (runQuery.isError) return <Card><CardContent className="flex min-h-60 flex-col items-center justify-center gap-3 pt-5"><p className="font-medium text-error-600">Run could not be loaded</p><Button onClick={() => void runQuery.refetch()}>Retry</Button></CardContent></Card>;
  const run = runQuery.data;
  const flow = graph(run.tasks);
  const failedTasks = run.tasks.filter((task) => task.status === "FAILED");
  return <div className="space-y-6">
    <div><Link to=".." className="text-sm text-brand-500 hover:text-brand-600">← Runs</Link><div className="mt-3 flex flex-wrap items-start justify-between gap-4"><div><div className="flex flex-wrap items-center gap-3"><h1 className="text-2xl font-semibold text-gray-900 dark:text-white">Run detail</h1><StatusBadge status={run.status} /><StatusBadge status={stream?.connection ?? "CONNECTING"} /></div><p className="mt-2 break-all font-mono text-xs text-gray-500">{run.runId}</p></div><div className="flex w-full flex-wrap gap-2 sm:w-auto"><Button asChild variant="outline"><a href={api.temporalUrl(tenantId, runId)} target="_blank" rel="noreferrer">Temporal <ExternalLink /></a></Button><Button asChild variant="outline"><a href={api.phoenixUrl} target="_blank" rel="noreferrer">Phoenix <ExternalLink /></a></Button><Button variant="outline" onClick={() => void runQuery.refetch()}><RefreshCw />Refresh</Button>{run.allowedActions.includes("pause") ? <Button variant="outline" loading={control.isPending} onClick={() => control.mutate(() => api.pauseRun(tenantId, projectId, runId))}><Pause />Pause</Button> : null}{run.allowedActions.includes("resume") ? <Button loading={control.isPending} onClick={() => control.mutate(() => api.resumeRun(tenantId, projectId, runId))}><Play />Resume</Button> : null}{run.allowedActions.includes("cancel") ? <Button variant="destructive" loading={control.isPending} onClick={() => { if (window.confirm("Cancel this Run? In-flight work will be stopped.")) control.mutate(() => api.cancelRun(tenantId, projectId, runId)); }}><Ban />Cancel run</Button> : null}</div></div></div>
    {control.isError ? <div role="alert" className="rounded-xl border border-error-500 bg-error-50 p-4 text-sm text-error-600 dark:bg-error-500/15">The command was not accepted. Existing Run state is unchanged; retry when ready.</div> : null}
    {lastCommand ? <CommandStatus command={commandQuery.data ?? lastCommand} loading={commandQuery.isFetching} /> : null}
    {stream?.connection === "STALE" ? <div role="alert" className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-warning-300 bg-warning-50 p-4 text-sm text-warning-700 dark:bg-warning-500/10"><span>The event cursor expired. The latest snapshot was loaded; reconnecting from the new cursor.</span><Button size="sm" variant="outline" onClick={() => { void historyQuery.refetch(); void runQuery.refetch(); }}>Reload history</Button></div> : null}
    <HumanRequests approvals={approvalsQuery.data?.items ?? []} inputs={inputsQuery.data?.items ?? []} loading={approvalsQuery.isPending || inputsQuery.isPending} busy={control.isPending} onApprove={(id, value) => { if (window.confirm("Approve this request and resume execution?")) control.mutate(() => api.approve(tenantId, projectId, id, value)); }} onReject={(id) => { if (window.confirm("Reject this approval? The waiting task will fail.")) control.mutate(() => api.reject(tenantId, projectId, id, {})); }} onInput={(id, value) => control.mutate(() => api.provideInput(tenantId, projectId, id, value))} />
    {failedTasks.length ? <Card><CardHeader><CardTitle className="text-error-600">Failed tasks</CardTitle></CardHeader><CardContent><ul className="space-y-3">{failedTasks.map((task) => <li key={task.taskId} className="rounded-xl border border-error-200 p-3 dark:border-error-500/30"><div className="flex flex-wrap items-center justify-between gap-3"><p className="font-medium">{task.nodeKey}</p>{task.allowedActions?.includes("retry_task") ? <Button size="sm" loading={control.isPending} onClick={() => { if (window.confirm(`Retry failed task ${task.nodeKey}?`)) control.mutate(() => api.retryTask(tenantId, projectId, runId, task.taskId)); }}><RotateCcw />Retry task</Button> : null}</div><pre className="mt-2 whitespace-pre-wrap break-words text-xs text-error-600">{JSON.stringify(task.error ?? { message: "No structured error was recorded." }, null, 2)}</pre></li>)}</ul></CardContent></Card> : null}
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

export function CommandStatus({ command, loading }: { command: CommandHandle; loading: boolean }) {
  const pending = ["ACCEPTED", "DELIVERING"].includes(command.status);
  const resultCode = command.result?.["code"];
  const code = typeof resultCode === "string" || typeof resultCode === "number" ? ` · ${resultCode}` : "";
  const tone = command.status === "APPLIED" ? "border-success-300 bg-success-50 text-success-700 dark:bg-success-500/10" : pending ? "border-warning-300 bg-warning-50 text-warning-700 dark:bg-warning-500/10" : "border-error-300 bg-error-50 text-error-700 dark:bg-error-500/10";
  return <div role="status" className={cn("flex min-w-0 flex-wrap items-center justify-between gap-2 rounded-xl border p-4 text-sm", tone)}><span className="min-w-0 break-words">Command #{command.commandSeq} · {command.status}{code}</span>{loading || pending ? <RefreshCw className="size-4 animate-spin" /> : null}</div>;
}

function HumanRequests({ approvals, inputs, loading, busy, onApprove, onReject, onInput }: { approvals: ApprovalRequest[]; inputs: ExternalInputRequest[]; loading: boolean; busy: boolean; onApprove: (id: string, value: Record<string, unknown>) => void; onReject: (id: string) => void; onInput: (id: string, value: Record<string, unknown>) => void }) {
  if (loading) return <Card><CardContent className="space-y-3 pt-5"><Skeleton className="h-24" /><Skeleton className="h-24" /></CardContent></Card>;
  if (!approvals.length && !inputs.length) return null;
  return <section aria-label="Human interaction requests" className="grid min-w-0 gap-4 lg:grid-cols-2">
    {approvals.map((request) => <Card key={request.approvalId}><CardHeader><div><CardTitle>Approval required</CardTitle><p className="mt-1 text-xs text-gray-500">{request.nodeKey}</p></div><StatusBadge status={request.status} /></CardHeader><CardContent><p className="mb-4 text-sm text-gray-700 dark:text-gray-300">{request.prompt}</p><SchemaForm schema={request.inputSchema} submitLabel="Approve" busy={busy} icon={<Check />} onSubmit={(value) => onApprove(request.approvalId, value)} />{request.allowedActions.includes("reject") ? <Button className="mt-3 w-full sm:w-auto" variant="destructive" disabled={busy} onClick={() => onReject(request.approvalId)}><X />Reject</Button> : null}</CardContent></Card>)}
    {inputs.map((request) => <Card key={request.inputRequestId}><CardHeader><div><CardTitle>External input required</CardTitle><p className="mt-1 text-xs text-gray-500">{request.nodeKey}</p></div><StatusBadge status={request.status} /></CardHeader><CardContent><p className="mb-4 text-sm text-gray-700 dark:text-gray-300">{request.prompt}</p><SchemaForm schema={request.inputSchema} submitLabel="Submit input" busy={busy} onSubmit={(value) => onInput(request.inputRequestId, value)} /></CardContent></Card>)}
  </section>;
}

export function validateSchemaValues(schema: Record<string, unknown>, values: Record<string, unknown>): string | null {
  const required = Array.isArray(schema["required"]) ? schema["required"].filter((item): item is string => typeof item === "string") : [];
  const missing = required.find((key) => values[key] === undefined || values[key] === "");
  return missing ? `${missing} is required.` : null;
}

export function SchemaForm({ schema, submitLabel, busy, icon, onSubmit }: { schema: Record<string, unknown>; submitLabel: string; busy: boolean; icon?: React.ReactNode; onSubmit: (value: Record<string, unknown>) => void }) {
  const properties = typeof schema["properties"] === "object" && schema["properties"] ? schema["properties"] as Record<string, Record<string, unknown>> : {};
  const required = new Set(Array.isArray(schema["required"]) ? schema["required"].filter((item): item is string => typeof item === "string") : []);
  const [values, setValues] = React.useState<Record<string, unknown>>({});
  const [error, setError] = React.useState<string | null>(null);
  const submit = (event: React.FormEvent) => { event.preventDefault(); const validationError = validateSchemaValues(schema, values); if (validationError) { setError(validationError); return; } setError(null); onSubmit(values); };
  return <form className="min-w-0 space-y-3" onSubmit={submit}>{Object.entries(properties).map(([key, definition]) => { const type = definition["type"]; const label = typeof definition["title"] === "string" ? definition["title"] : key; const currentValue = values[key]; const displayValue = typeof currentValue === "string" || typeof currentValue === "number" ? String(currentValue) : ""; if (type === "boolean") return <label key={key} className="flex items-center gap-2 text-sm"><input type="checkbox" checked={values[key] === true} onChange={(event) => setValues((current) => ({ ...current, [key]: event.target.checked }))} />{label}</label>; return <label key={key} className="block min-w-0 text-sm"><span className="mb-1 block font-medium text-gray-700 dark:text-gray-300">{label}{required.has(key) ? " *" : ""}</span><input className="h-11 w-full min-w-0 rounded-lg border border-gray-300 bg-transparent px-3 outline-none focus-visible:ring-3 focus-visible:ring-brand-500/20 dark:border-gray-700" type={type === "number" || type === "integer" ? "number" : "text"} value={displayValue} onChange={(event) => setValues((current) => ({ ...current, [key]: type === "number" || type === "integer" ? Number(event.target.value) : event.target.value }))} /></label>; })}{error ? <p role="alert" className="text-sm text-error-600">{error}</p> : null}<Button className="w-full sm:w-auto" type="submit" loading={busy}>{icon}{submitLabel}</Button></form>;
}
