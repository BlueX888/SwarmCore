import * as React from "react";
import { Check, ChevronLeft, ChevronRight, Copy, Globe } from "lucide-react";

import { cn } from "@/lib/utils";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { AsyncField, type AsyncFieldState } from "@/components/ui/async-field";
import {
  activationSuccessResult,
  activationWizardSteps,
  defaultActivationFormValues,
  probeSuccessPayload,
  type ActivationFormValues,
  type ActivationWizardStepId,
} from "./mock-data";

export type ActivationWizardConnectedPageProps = {
  steps?: typeof activationWizardSteps;
  currentStep?: ActivationWizardStepId;
  onStepChange?: (stepId: ActivationWizardStepId) => void;
  formValues?: ActivationFormValues;
  onFormChange?: (field: keyof ActivationFormValues, value: string) => void;
  probeState?: AsyncFieldState;
  onProbe?: () => void;
  onCopyInstanceId?: () => void;
  onComplete?: () => void;
  readOnly?: boolean;
  className?: string;
};

function stepIndex(steps: typeof activationWizardSteps, stepId: ActivationWizardStepId) {
  return steps.findIndex((step) => step.id === stepId);
}

/**
 * S02-G03 激活向导（联网）— 填写网关地址 → 验证连通 → 完成激活。
 * @see docs/spec/b-design-system-tailadmin-radix/prd/scenarios/S02-gateway.md#s02-g03
 * @see references/layout-patterns/activation-wizard.md
 */
export function ActivationWizardConnectedPage({
  steps = activationWizardSteps,
  currentStep = "form",
  onStepChange,
  formValues = defaultActivationFormValues,
  onFormChange,
  probeState = "idle",
  onProbe,
  onCopyInstanceId,
  onComplete,
  readOnly = false,
  className,
}: ActivationWizardConnectedPageProps) {
  const currentIndex = Math.max(0, stepIndex(steps, currentStep));
  const step = steps[currentIndex] ?? steps[0];
  const isFirst = currentIndex <= 0;
  const isLast = currentIndex >= steps.length - 1;

  const goBack = () => onStepChange?.(steps[Math.max(0, currentIndex - 1)].id);
  const goNext = () => onStepChange?.(steps[Math.min(steps.length - 1, currentIndex + 1)].id);

  const canContinueFromForm =
    formValues.gatewayUrl.trim().length > 0 &&
    formValues.adminEmail.trim().length > 0 &&
    formValues.orgName.trim().length > 0;

  const canContinueFromVerify = probeState === "success";

  return (
    <div className={cn("mx-auto w-full max-w-2xl", className)} data-scenario-page="activation-wizard-connected">
      <header className="mb-6 space-y-1 text-center sm:text-left">
        <div className="inline-flex items-center gap-2 text-brand-600 dark:text-brand-400">
          <Globe className="size-4" aria-hidden="true" />
          <span className="text-theme-xs font-medium uppercase tracking-wide">Gateway 激活</span>
        </div>
        <h1 className="text-lg font-semibold text-gray-900 dark:text-white/90">联网激活向导</h1>
        <p className="text-theme-sm text-gray-500">
          填写网关地址与组织信息，完成连通性验证后即可接入控制面。
        </p>
      </header>

      <section
        className="space-y-6 rounded-xl border border-gray-200 bg-white p-6 dark:border-white/[0.05] dark:bg-white/[0.03]"
        aria-label="联网激活向导"
      >
        <ol className="flex flex-wrap items-center gap-2" aria-label="向导步骤">
          {steps.map((item, index) => {
            const done = index < currentIndex;
            const active = index === currentIndex;
            return (
              <li key={item.id} className="flex items-center gap-2">
                <span
                  className={cn(
                    "inline-flex size-7 items-center justify-center rounded-full text-xs font-semibold",
                    done && "bg-success-500 text-white",
                    active && !done && "bg-brand-500 text-white",
                    !done && !active && "bg-gray-100 text-gray-500 dark:bg-white/5 dark:text-gray-400",
                  )}
                  aria-current={active ? "step" : undefined}
                >
                  {done ? <Check className="size-3.5" /> : index + 1}
                </span>
                <span
                  className={cn(
                    "text-theme-sm font-medium",
                    active ? "text-gray-900 dark:text-white" : "text-gray-500",
                  )}
                >
                  {item.title}
                </span>
                {index < steps.length - 1 ? (
                  <span className="hidden text-gray-300 sm:inline dark:text-gray-700" aria-hidden="true">
                    /
                  </span>
                ) : null}
              </li>
            );
          })}
        </ol>

        <div className="space-y-4" data-audit="activation-wizard-step-content">
          {step.id === "form" ? (
            <div className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-theme-sm font-medium text-gray-700 dark:text-gray-300">
                  网关 URL <span className="text-error-500">*</span>
                </label>
                <Input
                  readOnly={readOnly}
                  value={formValues.gatewayUrl}
                  placeholder="https://gateway.corp.example.com"
                  className="font-mono text-xs"
                  onChange={(event) => onFormChange?.("gatewayUrl", event.target.value)}
                />
                <p className="text-theme-xs text-gray-500">须为 HTTPS 公网或专线可达地址，端口默认 443。</p>
              </div>
              <div className="space-y-1.5">
                <label className="text-theme-sm font-medium text-gray-700 dark:text-gray-300">
                  管理员邮箱 <span className="text-error-500">*</span>
                </label>
                <Input
                  readOnly={readOnly}
                  type="email"
                  value={formValues.adminEmail}
                  placeholder="ops-admin@corp.example.com"
                  onChange={(event) => onFormChange?.("adminEmail", event.target.value)}
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-theme-sm font-medium text-gray-700 dark:text-gray-300">
                  组织名称 <span className="text-error-500">*</span>
                </label>
                <Input
                  readOnly={readOnly}
                  value={formValues.orgName}
                  placeholder="华东研发中心"
                  onChange={(event) => onFormChange?.("orgName", event.target.value)}
                />
              </div>
              <Alert variant="info" title="联网模式">
                激活后将自动注册实例并拉取 License 与同步策略；离线激活请使用 S02-G04 向导。
              </Alert>
            </div>
          ) : null}

          {step.id === "verify" ? (
            <div className="space-y-4">
              <AsyncField
                label="连通性测试"
                state={probeState}
                helper="向网关 /health 端点发起探测，验证 TLS 与响应时延。"
                success="连通性测试通过，可继续完成激活。"
                error="连通性测试失败，请检查 URL、防火墙与证书配置。"
                onRetry={onProbe}
              >
                <Input readOnly value={formValues.gatewayUrl} className="font-mono text-xs" />
              </AsyncField>
              {probeState === "success" ? (
                <pre className="overflow-x-auto rounded-lg border border-gray-200 bg-gray-50 p-3 text-theme-xs text-gray-700 dark:border-gray-800 dark:bg-white/[0.03] dark:text-gray-300">
                  {JSON.stringify(probeSuccessPayload, null, 2)}
                </pre>
              ) : null}
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={onProbe}
                disabled={readOnly || probeState === "validating"}
              >
                {probeState === "validating" ? "测试中…" : "运行连通性测试"}
              </Button>
            </div>
          ) : null}

          {step.id === "done" ? (
            <div className="space-y-4">
              <Alert variant="success" title="网关已激活">
                实例 {activationSuccessResult.instanceId} 已注册，控制面同步将在 2 分钟内完成。
              </Alert>
              <div className="grid gap-3 sm:grid-cols-2">
                <div className="rounded-lg border border-dashed border-gray-200 p-4 dark:border-white/[0.05]">
                  <p className="text-theme-xs text-gray-500">实例 ID</p>
                  <div className="mt-1 flex items-center gap-2">
                    <p className="font-mono text-theme-sm text-gray-900 dark:text-white">
                      {activationSuccessResult.instanceId}
                    </p>
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="h-7 px-2"
                      onClick={onCopyInstanceId}
                      disabled={readOnly}
                      aria-label="复制实例 ID"
                    >
                      <Copy className="size-3.5" />
                    </Button>
                  </div>
                </div>
                <div className="rounded-lg border border-dashed border-gray-200 p-4 dark:border-white/[0.05]">
                  <p className="text-theme-xs text-gray-500">连接 ID</p>
                  <p className="mt-1 font-mono text-theme-sm text-gray-900 dark:text-white">
                    {activationSuccessResult.connectionId}
                  </p>
                </div>
              </div>
              <p className="text-theme-xs text-gray-500">
                组织「{formValues.orgName}」· {activationSuccessResult.region} · 激活于{" "}
                {activationSuccessResult.activatedAt}
              </p>
            </div>
          ) : null}
        </div>

        <div className="sticky bottom-0 flex flex-wrap items-center gap-2 border-t border-gray-100 pt-4 dark:border-gray-800">
          {!isFirst ? (
            <Button type="button" variant="outline" size="sm" onClick={goBack} disabled={readOnly}>
              <ChevronLeft className="size-4" />
              上一步
            </Button>
          ) : null}
          <div className="ml-auto flex gap-2">
            {!isLast ? (
              <Button
                type="button"
                size="sm"
                onClick={goNext}
                disabled={
                  readOnly ||
                  (step.id === "form" && !canContinueFromForm) ||
                  (step.id === "verify" && !canContinueFromVerify)
                }
              >
                继续
                <ChevronRight className="size-4" />
              </Button>
            ) : (
              <Button type="button" size="sm" onClick={onComplete} disabled={readOnly}>
                进入控制面
              </Button>
            )}
          </div>
        </div>
      </section>
    </div>
  );
}

export default ActivationWizardConnectedPage;
