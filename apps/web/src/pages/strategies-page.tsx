import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowRight, Plus, RefreshCw, Trash2 } from "lucide-react";
import * as React from "react";
import { Link } from "react-router";
import { api, ApiError } from "@/api/client";
import type { StrategyDeleteImpact, StrategySummary } from "@/api/types";
import { StrategyDeleteDialog } from "@/components/strategy/strategy-delete-dialog";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useWorkspaceScope } from "@/lib/demo-scope";

function formatDeleteError(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 404) return "策略不存在或已被删除。";
    if (error.status === 409) {
      const blockers = (error.blockers ?? [])
        .map((item) => (typeof item.message === "string" ? item.message : null))
        .filter((item): item is string => Boolean(item));
      if (blockers.length) return blockers.join("；");
      return error.message || "策略无法删除。";
    }
    return error.message || "删除失败。";
  }
  return error instanceof Error ? error.message : "网络错误，删除失败。";
}

export function StrategiesPage() {
  const { tenantId, projectId } = useWorkspaceScope();
  const client = useQueryClient();
  const query = useQuery({ queryKey: ["strategies", tenantId, projectId], queryFn: () => api.listStrategies(tenantId, projectId) });
  const [target, setTarget] = React.useState<StrategySummary | null>(null);
  const [impact, setImpact] = React.useState<StrategyDeleteImpact | null>(null);
  const [impactError, setImpactError] = React.useState("");
  const [loadingImpact, setLoadingImpact] = React.useState(false);

  const remove = useMutation({
    mutationFn: (strategyId: string) => api.deleteStrategy(tenantId, projectId, strategyId),
    onSuccess: async () => {
      setTarget(null);
      setImpact(null);
      setImpactError("");
      await client.invalidateQueries({ queryKey: ["strategies", tenantId, projectId] });
    },
    onError: (error) => setImpactError(formatDeleteError(error)),
  });

  async function openDelete(strategy: StrategySummary, event: React.MouseEvent) {
    event.preventDefault();
    event.stopPropagation();
    setTarget(strategy);
    setImpact(null);
    setImpactError("");
    setLoadingImpact(true);
    try {
      const next = await api.getStrategyDeleteImpact(tenantId, projectId, strategy.strategyId);
      setImpact(next);
    } catch (error) {
      setImpactError(formatDeleteError(error));
    } finally {
      setLoadingImpact(false);
    }
  }

  return <div className="min-w-0 space-y-6">
    <div className="flex flex-wrap items-end justify-between gap-4"><div><p className="text-sm font-medium text-brand-500">策略注册</p><h1 className="mt-1 text-2xl font-semibold text-gray-900 dark:text-white">策略管理</h1><p className="mt-1 text-sm text-gray-500">编辑、校验并发布不可变的执行计划。</p></div><div className="flex gap-2"><Button variant="outline" onClick={() => void query.refetch()} loading={query.isFetching}><RefreshCw />刷新</Button><Button asChild><Link to="new"><Plus />新建策略</Link></Button></div></div>
    {query.isPending ? <Card><CardContent className="space-y-4 pt-5">{[1,2,3].map((item) => <Skeleton key={item} className="h-16" />)}</CardContent></Card> : null}
    {query.isError ? <Card><CardContent className="flex min-h-60 flex-col items-center justify-center gap-3 pt-5 text-center"><p className="font-medium text-error-600">无法加载策略</p><p className="text-sm text-gray-500">{query.error.message}</p><Button onClick={() => void query.refetch()}>重试</Button></CardContent></Card> : null}
    {query.data?.items.length === 0 ? <Card><CardContent className="flex min-h-60 flex-col items-center justify-center gap-3 pt-5 text-center"><p className="font-medium">暂无策略</p><p className="text-sm text-gray-500">请创建并校验草稿，然后发布第一个版本。</p><Button asChild><Link to="new">创建策略</Link></Button></CardContent></Card> : null}
    {query.data?.items.length ? <Card className="overflow-hidden"><CardHeader><CardTitle>项目策略</CardTitle><span className="text-sm text-gray-500">共 {query.data.total} 条</span></CardHeader><CardContent className="grid gap-3">{query.data.items.map((strategy) => (
      <div key={strategy.strategyId} className="flex min-w-0 flex-wrap items-center justify-between gap-3 rounded-xl border border-gray-200 p-4 hover:border-brand-300 dark:border-gray-800">
        <Link to={strategy.strategyId} className="flex min-w-0 flex-1 items-center justify-between gap-3">
          <div className="min-w-0">
            <p className="font-medium text-gray-900 dark:text-white">{strategy.name}</p>
            <p className="mt-1 text-xs text-gray-500">草稿修订 {strategy.draftRevision ?? "—"} · 最新版本 {strategy.latestVersion ?? "—"}</p>
          </div>
          <ArrowRight className="shrink-0 text-gray-400" />
        </Link>
        <Button
          type="button"
          variant="outline"
          size="sm"
          aria-label={`删除 ${strategy.name}`}
          disabled={remove.isPending}
          onClick={(event) => void openDelete(strategy, event)}
        >
          <Trash2 />删除
        </Button>
      </div>
    ))}</CardContent></Card> : null}
    {target ? (
      <StrategyDeleteDialog
        open={Boolean(target)}
        strategyName={target.name}
        impact={impact}
        loadingImpact={loadingImpact}
        deleting={remove.isPending}
        error={impactError}
        onOpenChange={(open) => {
          if (!open && !remove.isPending) {
            setTarget(null);
            setImpact(null);
            setImpactError("");
          }
        }}
        onConfirm={() => {
          if (!target || remove.isPending) return;
          remove.mutate(target.strategyId);
        }}
      />
    ) : null}
  </div>;
}
