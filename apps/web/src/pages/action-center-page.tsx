import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, ExternalLink, Inbox, MessageSquareText, RefreshCw, X } from "lucide-react";
import * as React from "react";
import { Link } from "react-router";
import { api } from "@/api/client";
import type { ApprovalRequest, CommandHandle, ExternalInputRequest } from "@/api/types";
import { SchemaForm } from "@/components/operations/schema-form";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusBadge } from "@/components/ui/status-badge";
import { useWorkspaceScope } from "@/lib/demo-scope";
import { statusLabel } from "@/lib/display-text";

export function ActionCenterPage() {
  const { tenantId, projectId, workspacePath } = useWorkspaceScope();
  const queryClient = useQueryClient();
  const [notice, setNotice] = React.useState("");
  const approvals = useQuery({
    queryKey: ["approvals", tenantId, projectId, "all"],
    queryFn: () => api.listApprovals(tenantId, projectId),
    refetchInterval: 5000,
  });
  const inputs = useQuery({
    queryKey: ["inputs", tenantId, projectId, "all"],
    queryFn: () => api.listInputs(tenantId, projectId),
    refetchInterval: 5000,
  });
  const control = useMutation({
    mutationFn: (operation: () => Promise<CommandHandle>) => operation(),
    onSuccess: async (command) => {
      setNotice(`命令 #${command.commandSeq} 已受理 · ${statusLabel(command.status)}`);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["approvals", tenantId, projectId] }),
        queryClient.invalidateQueries({ queryKey: ["inputs", tenantId, projectId] }),
      ]);
    },
    onError: (error) => setNotice(error.message),
  });
  const refresh = () => {
    void approvals.refetch();
    void inputs.refetch();
  };
  const loading = approvals.isPending || inputs.isPending;
  const error = approvals.error ?? inputs.error;
  const total = (approvals.data?.total ?? 0) + (inputs.data?.total ?? 0);

  return <div className="min-w-0 space-y-6">
    <div className="flex flex-wrap items-end justify-between gap-4">
      <div>
        <p className="text-sm font-medium text-brand-500">运行管理</p>
        <h1 className="mt-1 text-2xl font-semibold text-gray-900 dark:text-white">待办中心</h1>
        <p className="mt-1 text-sm text-gray-500">集中处理待审批事项和外部输入，无需逐个查找运行。</p>
      </div>
      <Button variant="outline" onClick={refresh} loading={approvals.isFetching || inputs.isFetching}><RefreshCw />刷新</Button>
    </div>
    {notice ? <p role="status" className="rounded-xl border border-gray-200 bg-white p-3 text-sm text-gray-600 dark:border-gray-800 dark:bg-gray-900 dark:text-gray-300">{notice}</p> : null}
    {loading ? <div className="grid gap-4 lg:grid-cols-2"><Skeleton className="h-64" /><Skeleton className="h-64" /></div> : null}
    {error ? <Card><CardContent className="flex min-h-60 flex-col items-center justify-center gap-3 pt-5 text-center"><p className="font-medium text-error-600">无法加载待办事项</p><p className="text-sm text-gray-500">{error.message}</p><Button onClick={refresh}>重试</Button></CardContent></Card> : null}
    {!loading && !error && total === 0 ? <Card><CardContent className="flex min-h-72 flex-col items-center justify-center gap-3 pt-5 text-center"><span className="grid size-14 place-items-center rounded-2xl bg-success-50 text-success-600 dark:bg-success-500/15"><Inbox /></span><p className="font-medium text-gray-900 dark:text-white">待办已清空</p><p className="max-w-md text-sm text-gray-500">当前没有待审批事项或外部输入请求。</p><Button asChild variant="outline"><Link to={`${workspacePath}/runs`}>打开运行记录</Link></Button></CardContent></Card> : null}
    {total ? <div className="grid min-w-0 gap-5 xl:grid-cols-2">
      {(approvals.data?.items ?? []).map((request) => <ApprovalCard key={request.approvalId} request={request} runPath={`${workspacePath}/runs/${request.runId}`} busy={control.isPending} onApprove={(value) => control.mutate(() => api.approve(tenantId, projectId, request.approvalId, value))} onReject={() => { if (window.confirm("拒绝此审批吗？等待中的任务将失败。")) control.mutate(() => api.reject(tenantId, projectId, request.approvalId, {})); }} />)}
      {(inputs.data?.items ?? []).map((request) => <InputCard key={request.inputRequestId} request={request} runPath={`${workspacePath}/runs/${request.runId}`} busy={control.isPending} onSubmit={(value) => control.mutate(() => api.provideInput(tenantId, projectId, request.inputRequestId, value))} />)}
    </div> : null}
  </div>;
}

function RequestHeader({ title, nodeKey, status, runPath }: { title: string; nodeKey: string; status: string; runPath: string }) {
  return <CardHeader><div className="min-w-0"><CardTitle>{title}</CardTitle><p className="mt-1 truncate text-xs text-gray-500">{nodeKey}</p></div><div className="flex items-center gap-2"><StatusBadge status={status} /><Button asChild size="sm" variant="ghost"><Link to={runPath} aria-label={`打开 ${nodeKey} 所在运行`}><ExternalLink /></Link></Button></div></CardHeader>;
}

function ApprovalCard({ request, runPath, busy, onApprove, onReject }: { request: ApprovalRequest; runPath: string; busy: boolean; onApprove: (value: Record<string, unknown>) => void; onReject: () => void }) {
  return <Card className="min-w-0"><RequestHeader title="需要审批" nodeKey={request.nodeKey} status={request.status} runPath={runPath} /><CardContent><p className="mb-4 text-sm text-gray-700 dark:text-gray-300">{request.prompt}</p><SchemaForm schema={request.inputSchema} submitLabel="批准" busy={busy} icon={<Check />} onSubmit={onApprove} />{request.allowedActions.includes("reject") ? <Button className="mt-3" variant="destructive" disabled={busy} onClick={onReject}><X />拒绝</Button> : null}</CardContent></Card>;
}

function InputCard({ request, runPath, busy, onSubmit }: { request: ExternalInputRequest; runPath: string; busy: boolean; onSubmit: (value: Record<string, unknown>) => void }) {
  return <Card className="min-w-0"><RequestHeader title="需要外部输入" nodeKey={request.nodeKey} status={request.status} runPath={runPath} /><CardContent><p className="mb-4 text-sm text-gray-700 dark:text-gray-300">{request.prompt}</p><SchemaForm schema={request.inputSchema} submitLabel="提交输入" busy={busy} icon={<MessageSquareText />} onSubmit={onSubmit} /></CardContent></Card>;
}
