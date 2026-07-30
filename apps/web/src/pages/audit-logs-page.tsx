import { useMutation, useQuery } from "@tanstack/react-query";
import { Download, RefreshCw, ScrollText } from "lucide-react";
import { api } from "@/api/client";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { PageHeader } from "@/components/ui/page-header";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusBadge } from "@/components/ui/status-badge";
import { useWorkspaceScope } from "@/lib/demo-scope";
import { auditActionLabel, resourceTypeLabel } from "@/lib/display-text";

export function AuditLogsPage() {
  const { tenantId, projectId } = useWorkspaceScope();
  const query = useQuery({ queryKey: ["audit-logs", tenantId, projectId], queryFn: () => api.listAuditLogs(tenantId, projectId) });
  const download = useMutation({
    mutationFn: () => api.exportAuditLogs(tenantId, projectId),
    onSuccess: (blob) => {
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = "swarmcore-audit.ndjson";
      anchor.click();
      URL.revokeObjectURL(url);
    },
  });
  return <div className="min-w-0 space-y-6">
    <PageHeader
      eyebrow="治理"
      title="审计日志"
      description="查看只追加的项目活动记录，并将审计证据导出为 NDJSON。"
      actions={<><Button variant="outline" onClick={() => void query.refetch()} loading={query.isFetching}><RefreshCw />刷新</Button><Button onClick={() => download.mutate()} loading={download.isPending}><Download />导出</Button></>}
    />
    {download.isError ? <p role="alert" className="rounded-xl bg-error-50 p-3 text-sm text-error-600 dark:bg-error-500/15">审计日志导出失败：{download.error.message}</p> : null}
    {query.isPending ? <Card><CardContent className="space-y-4 pt-5"><Skeleton className="h-14" /><Skeleton className="h-14" /><Skeleton className="h-14" /></CardContent></Card> : null}
    {query.isError ? <Card><CardContent className="pt-5"><ErrorState title="无法加载审计日志" message={query.error.message} onRetry={() => void query.refetch()} /></CardContent></Card> : null}
    {query.data?.items.length === 0 ? <Card><CardContent className="pt-5"><EmptyState icon={ScrollText} title="暂无审计事件" description="受治理的操作将显示在这里。" /></CardContent></Card> : null}
    {query.data?.items.length ? <Card className="overflow-hidden"><CardHeader><CardTitle>项目活动</CardTitle><span className="text-sm text-gray-500">最近 {query.data.total} 条</span></CardHeader><CardContent className="overflow-x-auto px-0"><table className="w-full min-w-[880px] text-left text-sm"><thead className="border-y border-gray-100 bg-gray-50 text-xs text-gray-500 dark:border-gray-800 dark:bg-gray-800/50"><tr><th className="px-5 py-3 font-medium">时间</th><th className="px-5 py-3 font-medium">操作</th><th className="px-5 py-3 font-medium">资源</th><th className="px-5 py-3 font-medium">操作者</th><th className="px-5 py-3 font-medium">结果</th></tr></thead><tbody className="divide-y divide-gray-100 dark:divide-gray-800">{query.data.items.map((item) => <tr key={item.auditId} className="hover:bg-gray-50 dark:hover:bg-white/[0.03]"><td className="whitespace-nowrap px-5 py-4 text-xs text-gray-500">{new Date(item.occurredAt).toLocaleString("zh-CN")}</td><td className="px-5 py-4 font-medium text-gray-900 dark:text-white">{auditActionLabel(item.action)}</td><td className="px-5 py-4"><p>{resourceTypeLabel(item.resourceType)}</p><p className="max-w-64 truncate font-mono text-xs text-gray-500">{item.resourceId}</p></td><td className="px-5 py-4 text-gray-500">{item.actorId}</td><td className="px-5 py-4"><StatusBadge status={item.outcome} /></td></tr>)}</tbody></table></CardContent></Card> : null}
  </div>;
}
