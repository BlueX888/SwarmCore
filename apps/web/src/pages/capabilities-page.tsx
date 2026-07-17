import { useQuery } from "@tanstack/react-query";
import { Bot, Boxes, Cpu, Network, RefreshCw, Wrench } from "lucide-react";
import { Link } from "react-router";
import { api } from "@/api/client";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useWorkspaceScope } from "@/lib/demo-scope";
import { nodeTypeLabel } from "@/lib/display-text";

export function CapabilitiesPage() {
  const { tenantId, projectId, workspacePath } = useWorkspaceScope();
  const query = useQuery({ queryKey: ["capabilities", tenantId, projectId], queryFn: () => api.getCapabilities(tenantId, projectId) });
  return <div className="min-w-0 space-y-6">
    <div className="flex flex-wrap items-end justify-between gap-4"><div><p className="text-sm font-medium text-brand-500">构建</p><h1 className="mt-1 text-2xl font-semibold text-gray-900 dark:text-white">能力目录</h1><p className="mt-1 text-sm text-gray-500">设计策略前，先查看当前注册表提供的可用能力。</p></div><div className="flex gap-2"><Button variant="outline" onClick={() => void query.refetch()} loading={query.isFetching}><RefreshCw />刷新</Button><Button asChild><Link to={`${workspacePath}/canvas`}><Network />打开画布</Link></Button></div></div>
    {query.isPending ? <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">{[1,2,3,4].map((item) => <Skeleton key={item} className="h-28" />)}</div> : null}
    {query.isError ? <Card><CardContent className="flex min-h-60 flex-col items-center justify-center gap-3 pt-5 text-center"><p className="font-medium text-error-600">无法加载能力目录</p><p className="text-sm text-gray-500">{query.error.message}</p><Button onClick={() => void query.refetch()}>重试</Button></CardContent></Card> : null}
    {query.data ? <><div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4"><CapabilityMetric icon={<Boxes />} label="节点类型" value={query.data.nodeTypes.length} /><CapabilityMetric icon={<Bot />} label="智能体" value={query.data.agents.length} /><CapabilityMetric icon={<Wrench />} label="工具" value={query.data.tools.length} /><CapabilityMetric icon={<Cpu />} label="模型" value={query.data.models.length} /></div><div className="grid gap-6 xl:grid-cols-2"><Card><CardHeader><CardTitle>画布节点</CardTitle><span className="text-xs text-gray-500">{query.data.registrySnapshot.slice(0, 10)}</span></CardHeader><CardContent className="flex flex-wrap gap-2">{query.data.nodeTypes.map((item) => <span key={item.type} className="rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm font-medium text-gray-700 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-200">{nodeTypeLabel(item.type)}</span>)}</CardContent></Card><Card><CardHeader><CardTitle>运行时目录</CardTitle></CardHeader><CardContent className="space-y-4"><CatalogList title="智能体" emptyLabel="暂无已注册智能体。" items={query.data.agents.map((item) => `${item.id} · ${item.runtime}`)} /><CatalogList title="模型" emptyLabel="暂无已注册模型。" items={query.data.models.map((item) => `${item.ref} · ${item.runtime}`)} /></CardContent></Card></div></> : null}
  </div>;
}

function CapabilityMetric({ icon, label, value }: { icon: React.ReactNode; label: string; value: number }) { return <Card><CardContent className="flex items-center gap-4 pt-5"><span className="grid size-11 place-items-center rounded-xl bg-brand-50 text-brand-500 dark:bg-brand-500/15">{icon}</span><div><p className="text-xs text-gray-500">{label}</p><p className="mt-1 text-2xl font-semibold text-gray-900 dark:text-white">{value}</p></div></CardContent></Card>; }
function CatalogList({ title, emptyLabel, items }: { title: string; emptyLabel: string; items: string[] }) { return <div><p className="mb-2 text-xs font-semibold uppercase tracking-wider text-gray-500">{title}</p>{items.length ? <ul className="space-y-2">{items.map((item) => <li key={item} className="rounded-lg bg-gray-50 px-3 py-2 font-mono text-xs text-gray-600 dark:bg-gray-800 dark:text-gray-300">{item}</li>)}</ul> : <p className="text-sm text-gray-500">{emptyLabel}</p>}</div>; }
