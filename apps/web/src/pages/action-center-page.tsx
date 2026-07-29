import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Inbox, RefreshCw } from "lucide-react";
import * as React from "react";
import { Link } from "react-router";
import { api } from "@/api/client";
import type { CommandHandle } from "@/api/types";
import { HumanApprovalCard, HumanInputCard } from "@/components/operations/human-action-card";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
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
  const approvalItems = approvals.data?.items ?? [];
  const inputItems = inputs.data?.items ?? [];
  const total = (approvals.data?.total ?? 0) + (inputs.data?.total ?? 0);
  const noticeTone = control.isError ? "error" : "ok";

  return <div className="min-w-0 space-y-6">
    <div className="flex flex-wrap items-end justify-between gap-4">
      <div>
        <p className="text-sm font-medium text-brand-500">运行管理</p>
        <h1 className="mt-1 text-2xl font-semibold text-gray-900 dark:text-white">待办中心</h1>
        <p className="mt-1 max-w-2xl text-sm text-gray-500">
          这里汇集需要你拍板的审批和需要你补充的信息。先打开运行详情核对材料，再在卡片里批准、拒绝或提交。
        </p>
      </div>
      <Button variant="outline" onClick={refresh} loading={approvals.isFetching || inputs.isFetching}><RefreshCw />刷新</Button>
    </div>

    {!loading && !error && total > 0 ? (
      <div className="flex flex-wrap gap-3 text-sm">
        <span className="rounded-full bg-warning-50 px-3 py-1 font-medium text-warning-700 dark:bg-warning-500/15 dark:text-warning-300">
          {approvalItems.length} 项待审批
        </span>
        <span className="rounded-full bg-brand-50 px-3 py-1 font-medium text-brand-700 dark:bg-brand-500/15 dark:text-brand-300">
          {inputItems.length} 项待输入
        </span>
      </div>
    ) : null}

    {notice ? <p role="status" className={noticeTone === "error" ? "rounded-xl border border-error-200 bg-error-50 p-3 text-sm text-error-700 dark:border-error-500/30 dark:bg-error-500/10 dark:text-error-300" : "rounded-xl border border-gray-200 bg-white p-3 text-sm text-gray-600 dark:border-gray-800 dark:bg-gray-900 dark:text-gray-300"}>{notice}</p> : null}
    {loading ? <div className="grid gap-4 xl:grid-cols-2"><Skeleton className="h-80" /><Skeleton className="h-80" /></div> : null}
    {error ? <Card><CardContent className="flex min-h-60 flex-col items-center justify-center gap-3 pt-5 text-center"><p className="font-medium text-error-600">无法加载待办事项</p><p className="text-sm text-gray-500">{error.message}</p><Button onClick={refresh}>重试</Button></CardContent></Card> : null}
    {!loading && !error && total === 0 ? <Card><CardContent className="flex min-h-72 flex-col items-center justify-center gap-3 pt-5 text-center"><span className="grid size-14 place-items-center rounded-2xl bg-success-50 text-success-600 dark:bg-success-500/15"><Inbox /></span><p className="font-medium text-gray-900 dark:text-white">待办已清空</p><p className="max-w-md text-sm text-gray-500">当前没有待审批事项或外部输入请求。</p><Button asChild variant="outline"><Link to={`${workspacePath}/runs`}>打开运行记录</Link></Button></CardContent></Card> : null}
    {total ? <div className="grid min-w-0 gap-5 xl:grid-cols-2">
      {approvalItems.map((request) => (
        <HumanApprovalCard
          key={request.approvalId}
          request={request}
          runPath={`${workspacePath}/runs/${request.runId}`}
          busy={control.isPending}
          onApprove={(value) => {
            control.mutate(() => api.approve(tenantId, projectId, request.approvalId, value));
          }}
          onReject={() => {
            control.mutate(() => api.reject(tenantId, projectId, request.approvalId, {}));
          }}
        />
      ))}
      {inputItems.map((request) => (
        <HumanInputCard
          key={request.inputRequestId}
          request={request}
          runPath={`${workspacePath}/runs/${request.runId}`}
          busy={control.isPending}
          onSubmit={(value) => control.mutate(() => api.provideInput(tenantId, projectId, request.inputRequestId, value))}
        />
      ))}
    </div> : null}
  </div>;
}
