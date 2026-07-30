import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { BellRing, ClipboardCheck, History, Play } from "lucide-react";
import { api } from "@/api/client";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { Skeleton } from "@/components/ui/skeleton";

export function SupplierRiskOperations({
  tenantId,
  projectId,
  monitorId,
}: {
  tenantId: string;
  projectId: string;
  monitorId: string;
}) {
  const queryClient = useQueryClient();
  const alerts = useQuery({
    queryKey: ["supplier-risk-alerts", tenantId, projectId, monitorId],
    queryFn: () => api.listSupplierRiskAlerts(tenantId, projectId, monitorId),
  });
  const history = useQuery({
    queryKey: ["supplier-risk-history", tenantId, projectId, monitorId],
    queryFn: () => api.listSupplierRiskHistory(tenantId, projectId, monitorId),
  });
  const workOrders = useQuery({
    queryKey: ["supplier-risk-work-orders", tenantId, projectId, monitorId],
    queryFn: () => api.listSupplierRiskWorkOrders(tenantId, projectId, monitorId),
  });
  const refresh = useMutation({
    mutationFn: () => api.refreshSupplierRiskMonitor(tenantId, projectId, monitorId),
  });
  const invalidateOperations = async () => {
    await queryClient.invalidateQueries({
      queryKey: ["supplier-risk-work-orders", tenantId, projectId, monitorId],
    });
    await queryClient.invalidateQueries({
      queryKey: ["supplier-risk-alerts", tenantId, projectId, monitorId],
    });
  };
  const create = useMutation({
    mutationFn: (alertId: string) =>
      api.createSupplierRiskWorkOrder(tenantId, projectId, alertId, {
        priority: "HIGH",
      }),
    onSuccess: invalidateOperations,
  });
  const transition = useMutation({
    mutationFn: ({
      workOrderId,
      status,
    }: {
      workOrderId: string;
      status: "IN_PROGRESS" | "CLOSED";
    }) =>
      api.updateSupplierRiskWorkOrder(tenantId, projectId, workOrderId, {
        status,
        resolution:
          status === "CLOSED"
            ? { outcome: "handled", source: "assessment-ui" }
            : undefined,
        comment: status === "CLOSED" ? "风险处置完成" : "开始风险处置",
      }),
    onSuccess: invalidateOperations,
  });
  const ordersByAlert = new Map(
    (workOrders.data?.items ?? []).map((item) => [item.alertId, item]),
  );
  const error =
    create.error?.message ??
    transition.error?.message ??
    refresh.error?.message ??
    null;

  return (
    <Card>
      <CardContent className="space-y-5 p-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="flex items-start gap-3">
            <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-brand-50 text-brand-600 dark:bg-brand-500/10">
              <BellRing className="size-5" />
            </span>
            <div>
              <h2 className="font-semibold text-gray-900 dark:text-white">
                实时预警与风控工单
              </h2>
              <p className="mt-1 text-xs text-gray-500">
                监控 {monitorId}；刷新会重新获取真实来源并生成不可变历史快照。
              </p>
            </div>
          </div>
          <Button
            size="sm"
            variant="outline"
            loading={refresh.isPending}
            onClick={() => refresh.mutate()}
          >
            <Play />
            立即刷新
          </Button>
        </div>

        {refresh.data ? (
          <p className="rounded-xl bg-brand-50 px-3 py-2 text-xs text-brand-700 dark:bg-brand-500/10 dark:text-brand-300">
            已发起新评估：{refresh.data.evaluationId} · {refresh.data.status}
          </p>
        ) : null}
        {error ? (
          <ErrorState compact title="操作失败" message={error} />
        ) : null}

        <div className="grid gap-4 xl:grid-cols-[1.4fr_1fr]">
          <div>
            <div className="mb-3 flex items-center gap-2">
              <ClipboardCheck className="size-4 text-gray-400" />
              <h3 className="text-sm font-semibold">预警与处置</h3>
            </div>
            {alerts.isPending || workOrders.isPending ? (
              <Skeleton className="h-32" />
            ) : alerts.data?.items.length ? (
              <div className="space-y-2">
                {alerts.data.items.map((alert) => {
                  const order = ordersByAlert.get(alert.alertId);
                  return (
                    <div
                      key={alert.alertId}
                      className="rounded-xl border border-gray-200 p-3 dark:border-gray-800"
                    >
                      <div className="flex flex-wrap items-start justify-between gap-3">
                        <div>
                          <div className="flex flex-wrap items-center gap-2">
                            <Badge color={alert.severity === "CRITICAL" ? "error" : "warning"}>
                              {alert.severity}
                            </Badge>
                            <Badge color="neutral">{alert.alertType}</Badge>
                            <Badge color={alert.status === "CLOSED" ? "success" : "warning"}>
                              {alert.status}
                            </Badge>
                          </div>
                          <p className="mt-2 text-sm font-medium text-gray-900 dark:text-white">
                            {alert.title}
                          </p>
                          <p className="mt-1 text-xs text-gray-500">
                            依据 {alert.evidence.length} 条 · {formatTime(alert.createdAt)}
                          </p>
                        </div>
                        {!order ? (
                          <Button
                            size="sm"
                            variant="outline"
                            loading={create.isPending}
                            onClick={() => create.mutate(alert.alertId)}
                          >
                            创建工单
                          </Button>
                        ) : order.status === "OPEN" ? (
                          <Button
                            size="sm"
                            onClick={() =>
                              transition.mutate({
                                workOrderId: order.workOrderId,
                                status: "IN_PROGRESS",
                              })
                            }
                          >
                            开始处理
                          </Button>
                        ) : order.status === "IN_PROGRESS" ||
                          order.status === "RESOLVED" ? (
                          <Button
                            size="sm"
                            onClick={() =>
                              transition.mutate({
                                workOrderId: order.workOrderId,
                                status: "CLOSED",
                              })
                            }
                          >
                            关闭工单
                          </Button>
                        ) : (
                          <Badge color="success">工单 {order.status}</Badge>
                        )}
                      </div>
                      {order ? (
                        <p className="mt-2 text-[11px] text-gray-400">
                          工单 {order.workOrderId} · 动作记录 {order.actions.length}
                        </p>
                      ) : null}
                    </div>
                  );
                })}
              </div>
            ) : (
              <EmptyState compact tone="neutral" title="当前没有预警" />
            )}
          </div>

          <div>
            <div className="mb-3 flex items-center gap-2">
              <History className="size-4 text-gray-400" />
              <h3 className="text-sm font-semibold">历史快照</h3>
            </div>
            {history.isPending ? (
              <Skeleton className="h-32" />
            ) : history.data?.items.length ? (
              <ol className="space-y-2">
                {history.data.items.slice(0, 10).map((item) => (
                  <li
                    key={item.snapshotId}
                    className="rounded-xl border border-gray-200 p-3 dark:border-gray-800"
                  >
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <p className="text-sm font-medium">
                          {item.riskLevel} · {item.decision}
                        </p>
                        <p className="mt-1 text-xs text-gray-500">
                          {formatTime(item.asOf)}
                        </p>
                      </div>
                      <Badge
                        color={
                          item.changeSummary.hasMaterialChange === true
                            ? "warning"
                            : "neutral"
                        }
                      >
                        {item.changeSummary.hasMaterialChange === true
                          ? "有变化"
                          : "无变化"}
                      </Badge>
                    </div>
                  </li>
                ))}
              </ol>
            ) : (
              <EmptyState compact tone="neutral" title="尚无历史快照" />
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function formatTime(value: string) {
  return new Intl.DateTimeFormat("zh-CN", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}
