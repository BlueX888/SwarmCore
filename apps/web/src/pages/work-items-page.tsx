import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FormEvent, useState } from "react";
import { Link } from "react-router";
import { api } from "@/api/client";
import { Button } from "@/components/ui/button";
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
  return <section className="space-y-5">
    <header><h1 className="text-2xl font-semibold text-gray-900 dark:text-white">业务工作项</h1><p className="mt-1 text-sm text-gray-500">通用工作项、修订、评估、问题和报告。</p></header>
    <form onSubmit={submit} className="grid gap-3 rounded-xl border border-gray-200 bg-white p-4 md:grid-cols-[1fr_1fr_auto] dark:border-gray-800 dark:bg-gray-800">
      <label className="text-sm text-gray-600 dark:text-gray-300">标题<input aria-label="工作项标题" className="mt-1 w-full rounded-lg border border-gray-300 bg-transparent px-3 py-2 text-gray-900 dark:border-gray-700 dark:text-white" value={title} onChange={(event) => setTitle(event.target.value)} /></label>
      <label className="text-sm text-gray-600 dark:text-gray-300">负责人<input aria-label="负责人" className="mt-1 w-full rounded-lg border border-gray-300 bg-transparent px-3 py-2 text-gray-900 dark:border-gray-700 dark:text-white" value={owner} onChange={(event) => setOwner(event.target.value)} /></label>
      <Button className="self-end" disabled={!title.trim() || create.isPending} type="submit">创建采购合同工作项</Button>
    </form>
    {items.isLoading ? <p className="text-sm text-gray-500">正在加载工作项…</p> : null}
    {items.isError ? <p role="alert" className="text-sm text-error-600">工作项加载失败。</p> : null}
    <div className="overflow-hidden rounded-xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-800"><table className="w-full text-left text-sm"><thead className="bg-gray-50 text-gray-500 dark:bg-gray-900"><tr><th className="px-4 py-3">标题</th><th className="px-4 py-3">类型</th><th className="px-4 py-3">状态</th><th className="px-4 py-3">修订</th></tr></thead><tbody>{items.data?.items.map((item) => <tr key={item.workItemId} className="border-t border-gray-100 dark:border-gray-700"><td className="px-4 py-3"><Link className="font-medium text-brand-600" to={`${workspacePath}/work-items/${item.workItemId}`}>{itemTitle(item.payload, item.workItemId)}</Link></td><td className="px-4 py-3">{item.workItemType}</td><td className="px-4 py-3">{item.status}</td><td className="px-4 py-3">v{item.revision}</td></tr>)}</tbody></table>{items.data?.total === 0 ? <p className="p-8 text-center text-sm text-gray-500">暂无工作项。</p> : null}</div>
  </section>;
}
