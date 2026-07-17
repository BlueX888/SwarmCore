import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Boxes, CheckCircle2 } from "lucide-react";
import { api } from "@/api/client";
import { Button } from "@/components/ui/button";
import { useWorkspaceScope } from "@/lib/demo-scope";

function packWorkItemType(manifest: Record<string, unknown>) {
  const spec = manifest.spec;
  if (!spec || typeof spec !== "object") return "-";
  const value = (spec as Record<string, unknown>).workItemType;
  return typeof value === "string" ? value : "-";
}

export function CapabilityPacksPage() {
  const { tenantId, projectId } = useWorkspaceScope();
  const queryClient = useQueryClient();
  const packs = useQuery({ queryKey: ["capability-packs", tenantId, projectId], queryFn: () => api.listCapabilityPacks(tenantId, projectId) });
  const enable = useMutation({
    mutationFn: (versionId: string) => api.enableCapabilityPack(tenantId, projectId, versionId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["capability-packs", tenantId, projectId] }),
  });
  return <section className="space-y-5">
    <header><h1 className="text-2xl font-semibold text-gray-900 dark:text-white">业务能力包</h1><p className="mt-1 text-sm text-gray-500">按项目启用不可变版本，历史评估继续绑定原版本。</p></header>
    {packs.isLoading ? <p className="text-sm text-gray-500">正在加载能力包…</p> : null}
    {packs.isError ? <p role="alert" className="text-sm text-error-600">能力包加载失败，请重试。</p> : null}
    <div className="grid gap-4 lg:grid-cols-2">
      {packs.data?.items.map((pack) => <article key={pack.versionId} className="rounded-xl border border-gray-200 bg-white p-5 shadow-theme-xs dark:border-gray-800 dark:bg-gray-800">
        <div className="flex items-start justify-between gap-4"><div className="flex gap-3"><span className="grid size-10 place-items-center rounded-lg bg-brand-50 text-brand-600 dark:bg-brand-500/15"><Boxes /></span><div><h2 className="font-semibold text-gray-900 dark:text-white">{pack.name}</h2><p className="mt-1 text-xs text-gray-500">v{pack.version} · {pack.contentHash.slice(0, 12)}</p></div></div>{pack.enabled ? <span className="inline-flex items-center gap-1 text-sm text-success-600"><CheckCircle2 className="size-4" />已启用</span> : <Button size="sm" disabled={enable.isPending} onClick={() => enable.mutate(pack.versionId)}>启用</Button>}</div>
        <p className="mt-4 text-sm text-gray-600 dark:text-gray-300">工作项类型：{packWorkItemType(pack.manifest)}</p>
      </article>)}
    </div>
    {packs.data?.items.length === 0 ? <p className="rounded-xl border border-dashed border-gray-300 p-8 text-center text-sm text-gray-500">暂无可信能力包。</p> : null}
  </section>;
}
