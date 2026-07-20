import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowRight, ClipboardList, Plus, RefreshCw } from "lucide-react";
import { FormEvent, useState } from "react";
import { Link } from "react-router";
import { api } from "@/api/client";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusBadge } from "@/components/ui/status-badge";
import { useWorkspaceScope } from "@/lib/demo-scope";

function itemTitle(payload: Record<string, unknown>, fallback: string) {
  return typeof payload.title === "string" ? payload.title : fallback;
}

export function WorkItemsPage() {
  const { tenantId, projectId, workspacePath } = useWorkspaceScope();
  const queryClient = useQueryClient();
  const [title, setTitle] = useState("");
  const [owner, setOwner] = useState("");
  const items = useQuery({ queryKey: ["work-items", tenantId, projectId], queryFn: () => api.listWorkItems(tenantId, projectId) });
  const create = useMutation({
    mutationFn: () => api.createWorkItem(tenantId, projectId, { workItemType: "contract-case", payload: { title, contractType: "purchase" }, owner: owner || undefined }),
    onSuccess: () => { setTitle(""); void queryClient.invalidateQueries({ queryKey: ["work-items", tenantId, projectId] }); },
  });
  const submit = (event: FormEvent) => { event.preventDefault(); if (title.trim()) create.mutate(); };

  return <div className="min-w-0 space-y-6">
    <div className="flex flex-wrap items-end justify-between gap-4">
      <div>
        <p className="text-sm font-medium text-brand-500">业务工作</p>
        <h1 className="mt-1 text-2xl font-semibold text-gray-900 dark:text-white">业务工作项</h1>
        <p className="mt-1 text-sm text-gray-500">通用工作项、修订、评估、问题和报告。</p>
      </div>
      <div className="flex gap-2">
        <Button variant="outline" onClick={() => void items.refetch()} loading={items.isFetching}><RefreshCw />刷新</Button>
      </div>
    </div>

    <Card>
      <CardHeader><CardTitle>新建工作项</CardTitle></CardHeader>
      <CardContent>
        <form onSubmit={submit} className="grid gap-4 md:grid-cols-[1fr_1fr_auto]">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">标题
            <input aria-label="工作项标题" className="mt-1 h-11 w-full rounded-lg border border-gray-300 bg-transparent px-3 text-sm text-gray-900 outline-none focus:border-brand-500 dark:border-gray-700 dark:text-white" value={title} onChange={(event) => setTitle(event.target.value)} />
          </label>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">负责人
            <input aria-label="负责人" className="mt-1 h-11 w-full rounded-lg border border-gray-300 bg-transparent px-3 text-sm text-gray-900 outline-none focus:border-brand-500 dark:border-gray-700 dark:text-white" value={owner} onChange={(event) => setOwner(event.target.value)} />
          </label>
          <Button className="self-end" disabled={!title.trim() || create.isPending} type="submit"><Plus />创建采购合同工作项</Button>
        </form>
      </CardContent>
    </Card>

    {items.isPending ? <Card><CardContent className="space-y-4 pt-5"><Skeleton className="h-14" /><Skeleton className="h-14" /><Skeleton className="h-14" /></CardContent></Card> : null}
    {items.isError ? <Card><CardContent className="flex min-h-60 flex-col items-center justify-center gap-3 pt-5 text-center"><p className="font-medium text-error-600">工作项加载失败</p><p className="text-sm text-gray-500">{items.error.message}</p><Button onClick={() => void items.refetch()}>重试</Button></CardContent></Card> : null}
    {items.data?.total === 0 ? <Card><CardContent className="flex min-h-72 flex-col items-center justify-center gap-3 pt-5 text-center"><span className="grid size-14 place-items-center rounded-2xl bg-brand-50 text-brand-500 dark:bg-brand-500/15"><ClipboardList /></span><p className="font-medium text-gray-900 dark:text-white">暂无工作项</p><p className="text-sm text-gray-500">创建第一个工作项开始业务流程。</p></CardContent></Card> : null}
    {items.data?.items.length ? <Card className="overflow-hidden">
      <CardHeader><CardTitle>全部工作项</CardTitle><span className="text-sm text-gray-500">共 {items.data.total} 条</span></CardHeader>
      <CardContent className="overflow-x-auto px-0">
        <table className="w-full min-w-[640px] text-left text-sm">
          <thead className="border-y border-gray-100 bg-gray-50 text-xs text-gray-500 dark:border-gray-800 dark:bg-gray-800/50">
            <tr><th className="px-5 py-3 font-medium">标题</th><th className="px-5 py-3 font-medium">类型</th><th className="px-5 py-3 font-medium">状态</th><th className="px-5 py-3 font-medium">修订</th><th className="px-5 py-3"><span className="sr-only">操作</span></th></tr>
          </thead>
          <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
            {items.data.items.map((item) => <tr key={item.workItemId} className="hover:bg-gray-50 dark:hover:bg-white/[0.03]">
              <td className="px-5 py-4 font-medium text-gray-900 dark:text-white">{itemTitle(item.payload, item.workItemId)}</td>
              <td className="px-5 py-4 text-gray-500">{item.workItemType}</td>
              <td className="px-5 py-4"><StatusBadge status={item.status} /></td>
              <td className="px-5 py-4 text-gray-500">v{item.revision}</td>
              <td className="px-5 py-4 text-right"><Button asChild variant="ghost" size="sm"><Link to={`${workspacePath}/work-items/${item.workItemId}`}>查看 <ArrowRight /></Link></Button></td>
            </tr>)}
          </tbody>
        </table>
      </CardContent>
    </Card> : null}
  </div>;
}
