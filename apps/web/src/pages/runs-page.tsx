import { useQuery } from "@tanstack/react-query";
import { ArrowRight, Plus, RefreshCw } from "lucide-react";
import { Link } from "react-router";
import { api } from "@/api/client";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusBadge } from "@/components/ui/status-badge";
import { useWorkspaceScope } from "@/lib/demo-scope";

export function RunsPage() {
  const { tenantId, projectId } = useWorkspaceScope();
  const query = useQuery({
    queryKey: ["runs", tenantId, projectId],
    queryFn: () => api.listRuns(tenantId, projectId),
    refetchInterval: 5000,
  });
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
        <Card className="min-w-0 overflow-hidden">
          <CardHeader><CardTitle>最近运行</CardTitle><span className="text-sm text-gray-500">共 {query.data.total} 条</span></CardHeader>
          <CardContent className="w-full max-w-full overflow-x-auto px-0">
            <div className="divide-y divide-gray-100 px-5 md:hidden dark:divide-gray-800">
              {query.data.items.map((run) => (
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
                {query.data.items.map((run) => (
                  <tr key={run.runId} className="hover:bg-gray-50 dark:hover:bg-white/[0.03]"><td className="px-5 py-4 font-mono text-xs text-gray-700 dark:text-gray-300">{run.runId}</td><td className="px-5 py-4"><StatusBadge status={run.status} /></td><td className="px-5 py-4 text-gray-500">{Object.values(run.taskCounts).reduce((a, b) => a + b, 0)}</td><td className="px-5 py-4 text-gray-500">{run.snapshotSeq}</td><td className="px-5 py-4 text-right"><Button asChild variant="ghost" size="sm"><Link to={run.runId}>查看 <ArrowRight /></Link></Button></td></tr>
                ))}
              </tbody>
            </table>
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}

function ActivityIcon() {
  return <span className="grid size-12 place-items-center rounded-full bg-brand-50 text-brand-500 dark:bg-brand-500/15">●</span>;
}
