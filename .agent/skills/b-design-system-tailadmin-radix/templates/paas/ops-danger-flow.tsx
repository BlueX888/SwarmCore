import * as React from "react";
import { cn } from "@/lib/utils";
import { AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export type PaasDangerAction = "scale" | "restart" | "failover";

export type PaasOpsDangerFlowProps = {
  resourceName: string;
  namespace?: string;
  environment?: string;
  currentReplicas?: number;
  onAction?: (action: PaasDangerAction) => void;
  className?: string;
};

type DialogState =
  | { type: "scale"; targetReplicas: number }
  | { type: "restart" }
  | { type: "failover" }
  | null;

/**
 * PaaS 危险操作流 — 伸缩/重启/故障转移，含权限影响范围与二次确认。
 * @see references/component-styles/paas-template.md
 */
export function PaasOpsDangerFlow({
  resourceName,
  namespace = "prod-data",
  environment = "生产环境",
  currentReplicas = 3,
  onAction,
  className,
}: PaasOpsDangerFlowProps) {
  const [dialog, setDialog] = React.useState<DialogState>(null);
  const [confirmText, setConfirmText] = React.useState("");
  const [targetReplicas, setTargetReplicas] = React.useState(String(currentReplicas));

  const close = () => {
    setDialog(null);
    setConfirmText("");
    setTargetReplicas(String(currentReplicas));
  };

  const requiredConfirm = resourceName;
  const canConfirm = confirmText === requiredConfirm;

  return (
    <>
      <section
        className={cn(
          "rounded-xl border border-error-200 bg-error-50/30 p-4 dark:border-error-500/30 dark:bg-error-500/5",
          className,
        )}
        aria-label="PaaS 危险操作"
      >
        <div className="mb-4 flex items-start gap-2">
          <AlertTriangle className="mt-0.5 size-4 shrink-0 text-error-600 dark:text-error-500" />
          <div>
            <h3 className="text-theme-sm font-semibold text-error-700 dark:text-error-400">运维危险操作</h3>
            <p className="mt-1 text-theme-sm text-error-600/80 dark:text-error-400/80">
              以下操作可能影响 {environment} 中 <span className="font-mono">{namespace}/{resourceName}</span> 的可用性，执行前请确认权限与影响范围。
            </p>
          </div>
        </div>

        <div className="space-y-3">
          <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-error-200/60 bg-white px-4 py-3 dark:border-error-500/20 dark:bg-gray-900">
            <div className="min-w-0">
              <p className="text-theme-sm font-medium text-gray-900 dark:text-white/90">水平伸缩</p>
              <p className="text-theme-xs text-gray-500">当前副本 {currentReplicas}，调整后将触发滚动更新。</p>
            </div>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setDialog({ type: "scale", targetReplicas: currentReplicas })}
            >
              调整副本
            </Button>
          </div>

          <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-error-200/60 bg-white px-4 py-3 dark:border-error-500/20 dark:bg-gray-900">
            <div className="min-w-0">
              <p className="text-theme-sm font-medium text-gray-900 dark:text-white/90">重启实例</p>
              <p className="text-theme-xs text-gray-500">将中断当前连接，建议在低峰期执行。</p>
            </div>
            <Button type="button" variant="destructive" size="sm" onClick={() => setDialog({ type: "restart" })}>
              重启
            </Button>
          </div>

          <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-error-200/60 bg-white px-4 py-3 dark:border-error-500/20 dark:bg-gray-900">
            <div className="min-w-0">
              <p className="text-theme-sm font-medium text-gray-900 dark:text-white/90">强制故障转移</p>
              <p className="text-theme-xs text-gray-500">将主节点切换至备节点，可能导致短暂写入中断。</p>
            </div>
            <Button type="button" variant="destructive" size="sm" onClick={() => setDialog({ type: "failover" })}>
              故障转移
            </Button>
          </div>
        </div>
      </section>

      {dialog ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-gray-900/50 p-4 backdrop-blur-sm">
          <div
            role="dialog"
            aria-modal="true"
            className="w-full max-w-lg rounded-2xl border border-error-200 bg-white p-6 shadow-xl dark:border-error-500/30 dark:bg-gray-900"
          >
            <h4 className="text-base font-semibold text-error-700 dark:text-error-400">
              {dialog.type === "scale"
                ? "确认水平伸缩"
                : dialog.type === "restart"
                  ? "确认重启实例"
                  : "确认强制故障转移"}
            </h4>
            <p className="mt-2 text-theme-sm text-gray-600 dark:text-gray-400">
              目标资源：<strong className="font-mono">{namespace}/{resourceName}</strong>
              {dialog.type === "scale" ? (
                <>
                  {" "}
                  · 当前副本 {currentReplicas}
                </>
              ) : null}
            </p>

            {dialog.type === "scale" ? (
              <div className="mt-4 space-y-2">
                <label className="text-theme-xs font-medium text-gray-700 dark:text-gray-300">目标副本数</label>
                <Input
                  type="number"
                  min={0}
                  value={targetReplicas}
                  onChange={(e) => setTargetReplicas(e.target.value)}
                  className="tabular-nums"
                />
              </div>
            ) : null}

            <div className="mt-4 space-y-2">
              <label className="text-theme-xs font-medium text-gray-700 dark:text-gray-300">
                输入 <code className="rounded bg-gray-100 px-1 dark:bg-gray-800">{requiredConfirm}</code> 以确认
              </label>
              <Input
                value={confirmText}
                onChange={(e) => setConfirmText(e.target.value)}
                placeholder={requiredConfirm}
                className="font-mono"
              />
            </div>

            <div className="mt-6 flex justify-end gap-2">
              <Button type="button" variant="outline" onClick={close}>
                取消
              </Button>
              <Button
                type="button"
                variant="destructive"
                disabled={!canConfirm}
                onClick={() => {
                  onAction?.(dialog.type);
                  close();
                }}
              >
                确认执行
              </Button>
            </div>
          </div>
        </div>
      ) : null}
    </>
  );
}
