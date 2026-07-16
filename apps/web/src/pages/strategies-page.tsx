import { useQuery } from "@tanstack/react-query";
import { ArrowRight, Plus, RefreshCw } from "lucide-react";
import { Link, useParams } from "react-router";
import { api } from "@/api/client";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

export function StrategiesPage() {
  const { tenantId = "", projectId = "" } = useParams();
  const query = useQuery({ queryKey: ["strategies", tenantId, projectId], queryFn: () => api.listStrategies(tenantId, projectId) });
  return <div className="min-w-0 space-y-6">
    <div className="flex flex-wrap items-end justify-between gap-4"><div><p className="text-sm font-medium text-brand-500">Registry</p><h1 className="mt-1 text-2xl font-semibold text-gray-900 dark:text-white">Strategies</h1><p className="mt-1 text-sm text-gray-500">Edit, validate, and publish immutable execution plans.</p></div><div className="flex gap-2"><Button variant="outline" onClick={() => void query.refetch()} loading={query.isFetching}><RefreshCw />Refresh</Button><Button asChild><Link to="new"><Plus />New strategy</Link></Button></div></div>
    {query.isPending ? <Card><CardContent className="space-y-4 pt-5">{[1,2,3].map((item) => <Skeleton key={item} className="h-16" />)}</CardContent></Card> : null}
    {query.isError ? <Card><CardContent className="flex min-h-60 flex-col items-center justify-center gap-3 pt-5 text-center"><p className="font-medium text-error-600">Strategies could not be loaded</p><p className="text-sm text-gray-500">{query.error.message}</p><Button onClick={() => void query.refetch()}>Retry</Button></CardContent></Card> : null}
    {query.data?.items.length === 0 ? <Card><CardContent className="flex min-h-60 flex-col items-center justify-center gap-3 pt-5 text-center"><p className="font-medium">No strategies yet</p><p className="text-sm text-gray-500">Create a draft, validate it, then publish the first version.</p><Button asChild><Link to="new">Create strategy</Link></Button></CardContent></Card> : null}
    {query.data?.items.length ? <Card className="overflow-hidden"><CardHeader><CardTitle>Project strategies</CardTitle><span className="text-sm text-gray-500">{query.data.total} total</span></CardHeader><CardContent className="grid gap-3">{query.data.items.map((strategy) => <Link key={strategy.strategyId} to={strategy.strategyId} className="flex min-w-0 flex-wrap items-center justify-between gap-3 rounded-xl border border-gray-200 p-4 hover:border-brand-300 dark:border-gray-800"><div className="min-w-0"><p className="font-medium text-gray-900 dark:text-white">{strategy.name}</p><p className="mt-1 text-xs text-gray-500">Draft r{strategy.draftRevision ?? "—"} · Latest version {strategy.latestVersion ?? "—"}</p></div><ArrowRight className="text-gray-400" /></Link>)}</CardContent></Card> : null}
  </div>;
}
