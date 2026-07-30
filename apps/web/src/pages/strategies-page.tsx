import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowRight, Plus, RefreshCw, Trash2 } from "lucide-react";
import * as React from "react";
import { Link } from "react-router";
import { api, ApiError } from "@/api/client";
import type { StrategyDeleteImpact, StrategySummary } from "@/api/types";
import { StrategyDeleteDialog } from "@/components/strategy/strategy-delete-dialog";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { PageHeader } from "@/components/ui/page-header";
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

function strategyDescription(strategy: StrategySummary): string {
  const name = strategy.name.toLowerCase();
  if (name.includes("invoice") || name.includes("发票")) return "核验发票、业务凭证与付款条件，输出一致性结论。";
  if (name.includes("deviation") || name.includes("偏差")) return "分析合同履约偏差及风险，形成可追溯的处置结论。";
  if (name.includes("post-evaluation") || name.includes("后评价")) return "汇总合同履约证据，生成结构化合同后评价结果。";
  if (name.includes("integrity") || name.includes("完整性")) return "校验合同材料的完整性、一致性与关键风险。";
  if (name.startsWith("inline-") || strategy.lifecycle === "EPHEMERAL") return "由运行任务临时生成，用于执行一次性内联流程。";
  if (/phase\d+-demo/.test(name)) return "用于验证阶段能力与端到端执行链路的演示策略。";
  if (name === "untitled-strategy") return "待补充名称和流程配置的策略草稿。";
  if (strategy.lifecycle === "TRUSTED") return "平台托管的可信执行策略，可直接用于稳定运行。";
  return "项目自定义执行策略，用于编排智能体、工具与业务流程。";
}

export function sortStrategiesByUpdatedAtDesc(items: StrategySummary[]): StrategySummary[] {
  return [...items].sort((left, right) => {
    const delta = Date.parse(right.updatedAt) - Date.parse(left.updatedAt);
    if (delta !== 0) return delta;
    return left.strategyId.localeCompare(right.strategyId);
  });
}

function formatUpdatedAt(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleString("zh-CN", {
    month: "numeric",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function StrategiesPage() {
  const { tenantId, projectId } = useWorkspaceScope();
  const client = useQueryClient();
  const query = useQuery({ queryKey: ["strategies", tenantId, projectId], queryFn: () => api.listStrategies(tenantId, projectId) });
  const items = React.useMemo(
    () => sortStrategiesByUpdatedAtDesc(query.data?.items ?? []),
    [query.data?.items],
  );
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
    <PageHeader
      eyebrow="策略注册"
      title="策略管理"
      description="编辑、校验并发布不可变的执行计划。"
      actions={<><Button variant="outline" onClick={() => void query.refetch()} loading={query.isFetching}><RefreshCw />刷新</Button><Button asChild><Link to="new"><Plus />新建策略</Link></Button></>}
    />
    {query.isPending ? <Card><CardContent className="space-y-4 pt-5">{[1,2,3].map((item) => <Skeleton key={item} className="h-16" />)}</CardContent></Card> : null}
    {query.isError ? <Card><CardContent className="pt-5"><ErrorState title="无法加载策略" message={query.error.message} onRetry={() => void query.refetch()} /></CardContent></Card> : null}
    {query.data?.items.length === 0 ? <Card><CardContent className="pt-5"><EmptyState title="暂无策略" description="请创建并校验草稿，然后发布第一个版本。" action={<Button asChild><Link to="new">创建策略</Link></Button>} /></CardContent></Card> : null}
    {items.length ? <Card className="overflow-hidden"><CardHeader><CardTitle>项目策略</CardTitle><span className="text-sm text-gray-500">共 {query.data?.total ?? items.length} 条</span></CardHeader><CardContent className="grid gap-3">{items.map((strategy) => (
      <div key={strategy.strategyId} className="flex min-w-0 flex-wrap items-center justify-between gap-3 rounded-xl border border-gray-200 p-4 hover:border-brand-300 dark:border-gray-800">
        <Link to={strategy.strategyId} className="flex min-w-0 flex-1 items-center justify-between gap-3">
          <div className="min-w-0">
            <p className="font-medium text-gray-900 dark:text-white">{strategy.name}</p>
            <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">{strategyDescription(strategy)}</p>
            <p className="mt-1 text-xs text-gray-500">草稿修订 {strategy.draftRevision ?? "—"} · 最新版本 {strategy.latestVersion ?? "—"} · 更新于 {formatUpdatedAt(strategy.updatedAt)}</p>
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
