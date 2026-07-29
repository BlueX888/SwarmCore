import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Background, Controls, type Edge, type Node, Position, ReactFlow } from "@xyflow/react";
import { Ban, CircleDollarSign, Clock3, ExternalLink, Hash, Pause, Play, RefreshCw, RotateCcw } from "lucide-react";
import * as React from "react";
import { useParams } from "react-router";
import { api } from "@/api/client";
import type { ApprovalRequest, CommandHandle, EvaluationSnapshot, ExternalInputRequest, PostEvaluationResult, RunEvent, TaskSnapshot } from "@/api/types";
import { HumanApprovalCard, HumanInputCard } from "@/components/operations/human-action-card";
import { BackLink } from "@/components/ui/back-link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusBadge } from "@/components/ui/status-badge";
import { useRunEvents } from "@/hooks/use-run-events";
import { useWorkspaceScope } from "@/lib/demo-scope";
import { eventTypeLabel, statusLabel } from "@/lib/display-text";
import { cn } from "@/lib/utils";
import { useRunEventStore } from "@/stores/run-event-store";

export function graph(tasks: TaskSnapshot[]): { nodes: Node[]; edges: Edge[]; height: number } {
  const byKey = new Map(tasks.map((task) => [task.nodeKey, task]));
  const depths = new Map<string, number>();
  const visiting = new Set<string>();
  const depthOf = (key: string): number => {
    const cached = depths.get(key);
    if (cached !== undefined) return cached;
    if (visiting.has(key)) return 0;
    visiting.add(key);
    const task = byKey.get(key);
    const depth = task?.dependencies.length ? Math.max(...task.dependencies.map((dependency) => depthOf(dependency))) + 1 : 0;
    visiting.delete(key);
    depths.set(key, depth);
    return depth;
  };
  tasks.forEach((task) => depthOf(task.nodeKey));
  const layers = new Map<number, TaskSnapshot[]>();
  tasks.forEach((task) => layers.set(depthOf(task.nodeKey), [...(layers.get(depthOf(task.nodeKey)) ?? []), task]));
  const widestLayer = Math.max(1, ...[...layers.values()].map((layer) => layer.length));
  const nodes = [...layers.entries()].flatMap(([depth, layer]) => layer.map((task, row) => {
    const offset = (widestLayer - layer.length) * 105;
    return { id: task.nodeKey, position: { x: offset + row * 210, y: depth * 110 }, sourcePosition: Position.Bottom, targetPosition: Position.Top, data: { label: <div className="flex min-w-0 items-center justify-between gap-2"><span className="truncate font-medium" title={task.nodeKey}>{task.nodeKey}</span><span className="shrink-0 text-[10px] opacity-70">{statusLabel(task.status)}</span></div> }, className: cn("run-node", `run-node-${task.status.toLowerCase()}`), style: { width: 190 } };
  }));
  const edges = tasks.flatMap((task) => task.dependencies.map((source) => ({ id: `${source}-${task.nodeKey}`, source, target: task.nodeKey, type: "smoothstep", animated: task.status === "RUNNING", style: { strokeWidth: 1.5 } })));
  const deepest = Math.max(0, ...depths.values());
  return { nodes, edges, height: Math.min(760, Math.max(420, deepest * 110 + 100)) };
}

export function RunDetailPage() {
  const { runId = "" } = useParams();
  const { tenantId, projectId, workspacePath } = useWorkspaceScope();
  const queryClient = useQueryClient();
  const runQuery = useQuery({ queryKey: ["run", tenantId, projectId, runId], queryFn: () => api.getRun(tenantId, projectId, runId), refetchInterval: (query) => query.state.data?.allowedActions.length ? 3000 : false });
  const evaluationId = evaluationIdFromInput(runQuery.data?.input);
  const evaluationQuery = useQuery({ queryKey: ["evaluation", tenantId, projectId, evaluationId], queryFn: () => api.getEvaluation(tenantId, projectId, evaluationId ?? ""), enabled: Boolean(evaluationId && runQuery.data?.status === "SUCCEEDED") });
  const historyQuery = useQuery({ queryKey: ["events", tenantId, projectId, runId], queryFn: () => api.history(tenantId, projectId, runId, 0) });
  const approvalsQuery = useQuery({ queryKey: ["approvals", tenantId, projectId, runId], queryFn: () => api.listApprovals(tenantId, projectId, runId), refetchInterval: 3000 });
  const inputsQuery = useQuery({ queryKey: ["inputs", tenantId, projectId, runId], queryFn: () => api.listInputs(tenantId, projectId, runId), refetchInterval: 3000 });
  useRunEvents(tenantId, projectId, runQuery.data);
  const stream = useRunEventStore((state) => state.runs[runId]);
  const [lastCommand, setLastCommand] = React.useState<CommandHandle | null>(null);
  const [refreshing, setRefreshing] = React.useState(false);
  const commandQuery = useQuery({ queryKey: ["command", tenantId, projectId, lastCommand?.commandId], queryFn: () => api.getCommand(tenantId, projectId, lastCommand?.commandId ?? ""), enabled: Boolean(lastCommand), refetchInterval: (query) => ["ACCEPTED", "DELIVERING"].includes(query.state.data?.status ?? "ACCEPTED") ? 1000 : false });
  const control = useMutation({ mutationFn: (operation: () => Promise<CommandHandle>) => operation(), onSuccess: (command) => { setLastCommand(command); void queryClient.invalidateQueries({ queryKey: ["run", tenantId, projectId, runId] }); void queryClient.invalidateQueries({ queryKey: ["approvals", tenantId, projectId, runId] }); void queryClient.invalidateQueries({ queryKey: ["inputs", tenantId, projectId, runId] }); } });
  const events = React.useMemo(() => mergeEvents(historyQuery.data?.items ?? [], stream?.events ?? []), [historyQuery.data?.items, stream?.events]);
  const refreshDetails = async () => {
    setRefreshing(true);
    try {
      await refreshRunDetails([
        runQuery.refetch,
        historyQuery.refetch,
        approvalsQuery.refetch,
        inputsQuery.refetch,
        ...(evaluationId && runQuery.data?.status === "SUCCEEDED" ? [evaluationQuery.refetch] : []),
      ]);
    } finally {
      setRefreshing(false);
    }
  };
  if (runQuery.isPending) return <div className="space-y-5"><Skeleton className="h-20" /><Skeleton className="h-96" /></div>;
  if (runQuery.isError) return <Card><CardContent className="flex min-h-60 flex-col items-center justify-center gap-3 pt-5"><p className="font-medium text-error-600">无法加载运行详情</p><Button onClick={() => void runQuery.refetch()}>重试</Button></CardContent></Card>;
  const run = runQuery.data;
  const flow = graph(run.tasks);
  const failedTasks = run.tasks.filter((task) => task.status === "FAILED");
  return <div className="space-y-6">
    <div><BackLink to="..">运行记录</BackLink><div className="mt-4 flex flex-wrap items-start justify-between gap-4"><div><div className="flex flex-wrap items-center gap-3"><h1 className="text-2xl font-semibold text-gray-900 dark:text-white">运行详情</h1><StatusBadge status={run.status} /><StatusBadge status={stream?.connection ?? "CONNECTING"} /></div><p className="mt-2 break-all font-mono text-xs text-gray-500">{run.runId}</p></div><div className="flex w-full flex-wrap gap-2 sm:w-auto"><Button asChild variant="outline"><a href={api.temporalUrl(tenantId, runId)} target="_blank" rel="noreferrer">Temporal <ExternalLink /></a></Button><Button asChild variant="outline"><a href={api.phoenixUrl} target="_blank" rel="noreferrer">Phoenix <ExternalLink /></a></Button><Button variant="outline" loading={refreshing} disabled={refreshing} onClick={() => void refreshDetails()}><RefreshCw />刷新</Button>{run.allowedActions.includes("pause") ? <Button variant="outline" loading={control.isPending} onClick={() => control.mutate(() => api.pauseRun(tenantId, projectId, runId))}><Pause />暂停</Button> : null}{run.allowedActions.includes("resume") ? <Button loading={control.isPending} onClick={() => control.mutate(() => api.resumeRun(tenantId, projectId, runId))}><Play />继续</Button> : null}{run.allowedActions.includes("cancel") ? <Button variant="destructive" loading={control.isPending} onClick={() => { if (window.confirm("确定取消此运行吗？正在执行的工作将停止。")) control.mutate(() => api.cancelRun(tenantId, projectId, runId)); }}><Ban />取消运行</Button> : null}</div></div></div>
    {control.isError ? <div role="alert" className="rounded-xl border border-error-500 bg-error-50 p-4 text-sm text-error-600 dark:bg-error-500/15">命令未被受理，现有运行状态保持不变，请稍后重试。</div> : null}
    {lastCommand ? <CommandStatus command={commandQuery.data ?? lastCommand} loading={commandQuery.isFetching} /> : null}
    {stream?.connection === "STALE" ? <div role="alert" className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-warning-300 bg-warning-50 p-4 text-sm text-warning-700 dark:bg-warning-500/10"><span>事件游标已过期。已加载最新快照，正在从新游标重新连接。</span><Button size="sm" variant="outline" onClick={() => { void historyQuery.refetch(); void runQuery.refetch(); }}>重新加载历史</Button></div> : null}
    <HumanRequests workspacePath={workspacePath} approvals={approvalsQuery.data?.items ?? []} inputs={inputsQuery.data?.items ?? []} loading={approvalsQuery.isPending || inputsQuery.isPending} busy={control.isPending} onApprove={(id, value) => control.mutate(() => api.approve(tenantId, projectId, id, value))} onReject={(id) => control.mutate(() => api.reject(tenantId, projectId, id, {}))} onInput={(id, value) => control.mutate(() => api.provideInput(tenantId, projectId, id, value))} />
    {failedTasks.length ? <Card><CardHeader><CardTitle className="text-error-600">失败任务</CardTitle></CardHeader><CardContent><ul className="space-y-3">{failedTasks.map((task) => <li key={task.taskId} className="rounded-xl border border-error-200 p-3 dark:border-error-500/30"><div className="flex flex-wrap items-center justify-between gap-3"><p className="font-medium">{task.nodeKey}</p>{task.allowedActions?.includes("retry_task") ? <Button size="sm" loading={control.isPending} onClick={() => { if (window.confirm(`重试失败任务 ${task.nodeKey} 吗？`)) control.mutate(() => api.retryTask(tenantId, projectId, runId, task.taskId)); }}><RotateCcw />重试任务</Button> : null}</div><pre className="mt-2 whitespace-pre-wrap break-words text-xs text-error-600">{JSON.stringify(task.error ?? { message: "未记录结构化错误。" }, null, 2)}</pre></li>)}</ul></CardContent></Card> : null}
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4"><Metric icon={<Clock3 />} label="时长" value={formatDuration(run.startedAt, run.completedAt)} /><Metric icon={<Hash />} label="Token 用量" value={formatTokens(run.usage)} /><Metric icon={<CircleDollarSign />} label="费用" value={formatCost(run.usage)} /><Metric icon={<Hash />} label="计划" value={run.planHash.slice(0, 10)} mono /></div>
    <div className="grid gap-4 sm:grid-cols-2"><Metric icon={<Clock3 />} label="开始时间" value={formatTime(run.startedAt)} /><Metric icon={<Clock3 />} label="完成时间" value={formatTime(run.completedAt)} /></div>
    {run.status === "SUCCEEDED" && evaluationId ? <EvaluationResult evaluation={evaluationQuery.data} loading={evaluationQuery.isPending} /> : null}
    <Card><CardHeader><CardTitle>执行图</CardTitle><span className="text-xs text-gray-500">{run.tasks.length} 个任务节点</span></CardHeader><CardContent><div style={{ height: flow.height }} className="overflow-hidden rounded-xl border border-gray-200 dark:border-gray-800">{run.tasks.length ? <ReactFlow nodes={flow.nodes} edges={flow.edges} fitView minZoom={0.25} maxZoom={1.5}><Background /><Controls /></ReactFlow> : <div className="grid h-full place-items-center text-sm text-gray-500">工作进程开始执行后，任务将显示在这里。</div>}</div></CardContent></Card>
    <div className="grid gap-6 xl:grid-cols-[minmax(0,1.4fr)_minmax(320px,.6fr)]"><Timeline events={events} loading={historyQuery.isPending} /><Card><CardHeader><CardTitle>结构化结果</CardTitle></CardHeader><CardContent><pre className="max-h-[480px] overflow-auto rounded-xl bg-gray-900 p-4 text-xs text-white">{JSON.stringify(run.output ?? { status: "结果待生成" }, null, 2)}</pre></CardContent></Card></div>
  </div>;
}

export function evaluationIdFromInput(input: Record<string, unknown> | undefined): string | null {
  return typeof input?.["evaluationId"] === "string" ? input["evaluationId"] : null;
}

export async function refreshRunDetails(refetchers: Array<() => Promise<unknown>>): Promise<void> {
  await Promise.all(refetchers.map((refetch) => refetch()));
}

function isPostEvaluationResult(value: EvaluationSnapshot["result"]): value is PostEvaluationResult {
  return Boolean(value && typeof value === "object" && "overallScore" in value && "dimensions" in value);
}

export function EvaluationResult({ evaluation, loading }: { evaluation?: EvaluationSnapshot; loading: boolean }) {
  if (loading) return <Card><CardHeader><CardTitle>最终评估结果</CardTitle></CardHeader><CardContent><Skeleton className="h-40" /></CardContent></Card>;
  if (!evaluation || !isPostEvaluationResult(evaluation.result)) return null;
  const result = evaluation.result;
  return <Card><CardHeader><div><CardTitle>最终评估结果</CardTitle><p className="mt-1 text-sm text-gray-500">{result.executiveSummary}</p></div><StatusBadge status={result.passed ? "SUCCEEDED" : "FAILED"} /></CardHeader><CardContent className="space-y-5"><div className="grid gap-3 sm:grid-cols-3"><ResultValue label="综合得分" value={`${result.overallScore.toFixed(1)} / 100`} /><ResultValue label="等级" value={result.grade} /><ResultValue label="风险" value={result.riskLevel} /></div><div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">{result.dimensions.map((dimension) => <div key={dimension.code} className="rounded-xl border border-gray-200 p-3 dark:border-gray-800"><div className="flex items-center justify-between gap-3"><p className="text-sm font-medium text-gray-900 dark:text-white">{dimension.name}</p><span className="font-mono text-sm font-semibold text-brand-600">{dimension.score === null ? "数据不足" : dimension.score.toFixed(1)}</span></div><p className="mt-1 text-xs text-gray-500">权重 {dimension.weight}% · {dimension.summary}</p></div>)}</div><p className="text-sm text-gray-600 dark:text-gray-300">{result.findings.length ? `发现 ${result.findings.length} 项需关注问题。` : "未发现需关注问题，无需人工复核。"}</p></CardContent></Card>;
}

function ResultValue({ label, value }: { label: string; value: string }) { return <div className="rounded-xl bg-gray-50 p-4 dark:bg-gray-800/60"><p className="text-xs text-gray-500">{label}</p><p className="mt-1 text-xl font-semibold text-gray-900 dark:text-white">{value}</p></div>; }

function Metric({ icon, label, value, mono }: { icon: React.ReactNode; label: string; value: string; mono?: boolean }) { return <Card><CardContent className="flex items-center gap-4 pt-5"><span className="grid size-11 place-items-center rounded-xl bg-brand-50 text-brand-500 dark:bg-brand-500/15">{icon}</span><div><p className="text-xs text-gray-500">{label}</p><p className={cn("mt-1 font-semibold text-gray-900 dark:text-white", mono && "font-mono text-sm")}>{value}</p></div></CardContent></Card>; }
function formatCost(usage: Record<string, unknown>) { const value = usage.costUsd; return typeof value === "number" ? `$${value.toFixed(4)}` : "—"; }
function formatTokens(usage: Record<string, unknown>) { const direct = usage.tokens; const input = usage.input_tokens; const output = usage.output_tokens; const value = typeof direct === "number" ? direct : (typeof input === "number" ? input : 0) + (typeof output === "number" ? output : 0); return value ? value.toLocaleString() : "—"; }
function formatTime(value?: string | null) { return value ? new Date(value).toLocaleString("zh-CN") : "—"; }
function formatDuration(start?: string | null, end?: string | null) { if (!start) return "—"; const milliseconds = new Date(end ?? Date.now()).getTime() - new Date(start).getTime(); if (milliseconds < 1000) return `${milliseconds} 毫秒`; return `${(milliseconds / 1000).toFixed(1)} 秒`; }
function mergeEvents(first: RunEvent[], second: RunEvent[]) { return [...new Map([...first, ...second].map((event) => [event.seq, event])).values()].sort((a,b) => b.seq-a.seq); }
function Timeline({ events, loading }: { events: RunEvent[]; loading: boolean }) { return <Card><CardHeader><CardTitle>事件时间线</CardTitle><span className="text-xs text-gray-500">最新事件优先</span></CardHeader><CardContent>{loading ? <div className="space-y-3"><Skeleton className="h-14" /><Skeleton className="h-14" /></div> : events.length ? <ol className="max-h-[480px] space-y-4 overflow-y-auto pr-2">{events.map((event) => <li key={event.id} className="relative border-l border-gray-200 pl-5 dark:border-gray-700"><span className="absolute -left-1.5 top-1 size-3 rounded-full border-2 border-white bg-brand-500 dark:border-gray-900" /><div className="flex flex-wrap items-center justify-between gap-2"><p className="text-sm font-medium text-gray-800 dark:text-white/90">{eventTypeLabel(event.type)}</p><time className="text-xs text-gray-500">#{event.seq} · {new Date(event.occurredAt).toLocaleTimeString("zh-CN")}</time></div><p className="mt-1 truncate font-mono text-xs text-gray-500">{JSON.stringify(event.data)}</p></li>)}</ol> : <div className="grid min-h-60 place-items-center text-sm text-gray-500">暂无耐久事件。</div>}</CardContent></Card>; }

export function CommandStatus({ command, loading }: { command: CommandHandle; loading: boolean }) {
  const pending = ["ACCEPTED", "DELIVERING"].includes(command.status);
  const resultCode = command.result?.["code"];
  const code = typeof resultCode === "string" || typeof resultCode === "number" ? ` · ${resultCode}` : "";
  const tone = command.status === "APPLIED" ? "border-success-300 bg-success-50 text-success-700 dark:bg-success-500/10" : pending ? "border-warning-300 bg-warning-50 text-warning-700 dark:bg-warning-500/10" : "border-error-300 bg-error-50 text-error-700 dark:bg-error-500/10";
  return <div role="status" className={cn("flex min-w-0 flex-wrap items-center justify-between gap-2 rounded-xl border p-4 text-sm", tone)}><span className="min-w-0 break-words">命令 #{command.commandSeq} · {statusLabel(command.status)}{code}</span>{loading || pending ? <RefreshCw className="size-4 animate-spin" /> : null}</div>;
}

function HumanRequests({ approvals, inputs, loading, busy, onApprove, onReject, onInput, workspacePath }: { approvals: ApprovalRequest[]; inputs: ExternalInputRequest[]; loading: boolean; busy: boolean; onApprove: (id: string, value: Record<string, unknown>) => void; onReject: (id: string) => void; onInput: (id: string, value: Record<string, unknown>) => void; workspacePath: string }) {
  if (loading) return <Card><CardContent className="space-y-3 pt-5"><Skeleton className="h-24" /><Skeleton className="h-24" /></CardContent></Card>;
  if (!approvals.length && !inputs.length) return null;
  return <section aria-label="人工交互请求" className="grid min-w-0 gap-4 lg:grid-cols-2">
    {approvals.map((request) => (
      <HumanApprovalCard
        key={request.approvalId}
        request={request}
        runPath={`${workspacePath}/runs/${request.runId}`}
        busy={busy}
        onApprove={(value) => onApprove(request.approvalId, value)}
        onReject={() => onReject(request.approvalId)}
      />
    ))}
    {inputs.map((request) => (
      <HumanInputCard
        key={request.inputRequestId}
        request={request}
        runPath={`${workspacePath}/runs/${request.runId}`}
        busy={busy}
        onSubmit={(value) => onInput(request.inputRequestId, value)}
      />
    ))}
  </section>;
}
