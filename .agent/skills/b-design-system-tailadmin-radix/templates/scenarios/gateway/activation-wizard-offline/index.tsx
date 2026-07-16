import * as React from "react";
import { Check, ChevronLeft, ChevronRight, Copy, ShieldOff } from "lucide-react";

import { cn } from "@/lib/utils";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { FileUpload } from "@/components/ui/file-upload";
import { AsyncField, type AsyncFieldState } from "@/components/ui/async-field";
import {
  defaultOfflineActivationFormValues,
  licenseValidationPayload,
  offlineActivationSteps,
  offlineActivationSuccessResult,
  type OfflineActivationFormValues,
  type OfflineActivationStepId,
} from "./mock-data";

export type ActivationWizardOfflinePageProps = {
  steps?: typeof offlineActivationSteps;
  currentStep?: OfflineActivationStepId;
  onStepChange?: (stepId: OfflineActivationStepId) => void;
  formValues?: OfflineActivationFormValues;
  onFormChange?: (field: keyof OfflineActivationFormValues, value: string) => void;
  licenseFileName?: string | null;
  onLicenseFileChange?: (file: File | null) => void;
  licenseValidationState?: AsyncFieldState;
  onValidateLicense?: () => void;
  onCopyInstanceId?: () => void;
  onComplete?: () => void;
  readOnly?: boolean;
  className?: string;
};

function stepIndex(steps: typeof offlineActivationSteps, stepId: OfflineActivationStepId) {
  return steps.findIndex((step) => step.id === stepId);
}

/**
 * S02-G04 激活向导（离线）— 确认 airgap 环境 → 上传 License → 完成本地激活。
 * @see docs/spec/b-design-system-tailadmin-radix/prd/scenarios/S02-gateway.md#s02-g04
 * @see references/layout-patterns/activation-wizard.md
 */
export function ActivationWizardOfflinePage({
  steps = offlineActivationSteps,
  currentStep = "airgap",
  onStepChange,
  formValues = defaultOfflineActivationFormValues,
  onFormChange,
  licenseFileName = null,
  onLicenseFileChange,
  licenseValidationState = "idle",
  onValidateLicense,
  onCopyInstanceId,
  onComplete,
  readOnly = false,
  className,
}: ActivationWizardOfflinePageProps) {
  const currentIndex = Math.max(0, stepIndex(steps, currentStep));
  const step = steps[currentIndex] ?? steps[0];
  const isFirst = currentIndex <= 0;
  const isLast = currentIndex >= steps.length - 1;

  const goBack = () => onStepChange?.(steps[Math.max(0, currentIndex - 1)].id);
  const goNext = () => onStepChange?.(steps[Math.min(steps.length - 1, currentIndex + 1)].id);

  const canContinueFromAirgap =
    formValues.orgName.trim().length > 0 &&
    formValues.adminEmail.trim().length > 0 &&
    formValues.instanceHost.trim().length > 0;

  const canContinueFromLicense =
    Boolean(licenseFileName) && licenseValidationState === "success";

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0] ?? null;
    onLicenseFileChange?.(file);
  };

  return (
    <div className={cn("mx-auto w-full max-w-2xl", className)} data-scenario-page="activation-wizard-offline">
      <header className="mb-6 space-y-1 text-center sm:text-left">
        <div className="inline-flex items-center gap-2 text-warning-600 dark:text-warning-400">
          <ShieldOff className="size-4" aria-hidden="true" />
          <span className="text-theme-xs font-medium uppercase tracking-wide">Gateway 离线激活</span>
        </div>
        <h1 className="text-lg font-semibold text-gray-900 dark:text-white/90">离线激活向导</h1>
        <p className="text-theme-sm text-gray-500">
          零出站网络环境下，通过本地 License 文件完成网关实例激活与验签。
        </p>
      </header>

      <section
        className="space-y-6 rounded-xl border border-gray-200 bg-white p-6 dark:border-white/[0.05] dark:bg-white/[0.03]"
        aria-label="离线激活向导"
      >
        <ol className="flex flex-wrap items-center gap-2" aria-label="向导步骤">
          {steps.map((item, index) => (
            <li key={item.id} className="flex items-center gap-2">
              <span
                className={cn(
                  "inline-flex size-7 items-center justify-center rounded-full text-xs font-semibold",
                  index < currentIndex && "bg-success-500 text-white",
                  index === currentIndex && "bg-brand-500 text-white",
                  index > currentIndex && "bg-gray-100 text-gray-500 dark:bg-white/5 dark:text-gray-400",
                )}
                aria-current={index === currentIndex ? "step" : undefined}
              >
                {index < currentIndex ? <Check className="size-3.5" /> : index + 1}
              </span>
              <span
                className={cn(
                  "text-theme-sm font-medium",
                  index === currentIndex ? "text-gray-900 dark:text-white" : "text-gray-500",
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
          ))}
        </ol>

        <div className="space-y-4" data-audit="activation-offline-step-content">
          {step.id === "airgap" ? (
            <div className="space-y-4">
              <Alert variant="warning" title="离线隔离模式">
                当前环境禁止出站流量；License 须通过本地文件验签，无法在线拉取同步策略。
              </Alert>
              <div className="space-y-1.5">
                <label className="text-theme-sm font-medium text-gray-700 dark:text-gray-300">
                  组织名称 <span className="text-error-500">*</span>
                </label>
                <Input
                  readOnly={readOnly}
                  value={formValues.orgName}
                  placeholder="西南离线数据中心"
                  onChange={(event) => onFormChange?.("orgName", event.target.value)}
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-theme-sm font-medium text-gray-700 dark:text-gray-300">
                  管理员邮箱 <span className="text-error-500">*</span>
                </label>
                <Input
                  readOnly={readOnly}
                  type="email"
                  value={formValues.adminEmail}
                  placeholder="airgap-admin@corp.example.com"
                  onChange={(event) => onFormChange?.("adminEmail", event.target.value)}
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-theme-sm font-medium text-gray-700 dark:text-gray-300">
                  实例主机名 <span className="text-error-500">*</span>
                </label>
                <Input
                  readOnly={readOnly}
                  value={formValues.instanceHost}
                  placeholder="edge.airgap.local"
                  className="font-mono text-xs"
                  onChange={(event) => onFormChange?.("instanceHost", event.target.value)}
                />
                <p className="text-theme-xs text-gray-500">用于本地实例标识，不与公网 DNS 解析关联。</p>
              </div>
              <Alert variant="info" title="联网激活">
                若环境可访问控制面，请使用 S02-G03 联网激活向导。
              </Alert>
            </div>
          ) : null}

          {step.id === "license" ? (
            <div className="space-y-4">
              <AsyncField
                label="License 文件验签"
                state={licenseValidationState}
                helper="上传由控制面签发的 .lic 离线 License 文件，本地验签通过后继续。"
                success="License 验签通过，版本与席位符合离线部署策略。"
                error="License 验签失败，请确认文件未损坏且与实例指纹匹配。"
                onRetry={onValidateLicense}
              >
                <FileUpload
                  accept=".lic,.txt"
                  disabled={readOnly || licenseValidationState === "validating"}
                  label="离线 License 文件"
                  hint="支持 .lic 或 .txt，单文件不超过 2 MB"
                  onChange={handleFileChange}
                />
              </AsyncField>
              {licenseFileName ? (
                <p className="text-theme-xs text-gray-500">
                  已选择文件：<span className="font-mono text-gray-700 dark:text-gray-300">{licenseFileName}</span>
                </p>
              ) : null}
              {licenseValidationState === "success" ? (
                <pre className="overflow-x-auto rounded-lg border border-gray-200 bg-gray-50 p-3 text-theme-xs text-gray-700 dark:border-gray-800 dark:bg-white/[0.03] dark:text-gray-300">
                  {JSON.stringify(licenseValidationPayload, null, 2)}
                </pre>
              ) : null}
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={onValidateLicense}
                disabled={readOnly || !licenseFileName || licenseValidationState === "validating"}
              >
                {licenseValidationState === "validating" ? "验签中…" : "验证 License 文件"}
              </Button>
            </div>
          ) : null}

          {step.id === "done" ? (
            <div className="space-y-4">
              <Alert variant="success" title="离线实例已激活">
                实例 {offlineActivationSuccessResult.instanceId} 已完成本地验签，写入权限已开启。
              </Alert>
              <div className="grid gap-3 sm:grid-cols-2">
                <div className="rounded-lg border border-dashed border-gray-200 p-4 dark:border-white/[0.05]">
                  <p className="text-theme-xs text-gray-500">实例 ID</p>
                  <div className="mt-1 flex items-center gap-2">
                    <p className="font-mono text-theme-sm text-gray-900 dark:text-white">
                      {offlineActivationSuccessResult.instanceId}
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
                  <p className="text-theme-xs text-gray-500">License 版本</p>
                  <p className="mt-1 text-theme-sm font-medium text-gray-900 dark:text-white">
                    {offlineActivationSuccessResult.licenseEdition}
                  </p>
                  <p className="mt-1 text-theme-xs text-gray-500">
                    有效期至 {offlineActivationSuccessResult.expiresAt}
                  </p>
                </div>
              </div>
              <p className="text-theme-xs text-gray-500">
                组织「{formValues.orgName}」· 主机 {formValues.instanceHost} · 指纹{" "}
                {offlineActivationSuccessResult.fingerprint} · 激活于 {offlineActivationSuccessResult.activatedAt}
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
                  (step.id === "airgap" && !canContinueFromAirgap) ||
                  (step.id === "license" && !canContinueFromLicense)
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

export default ActivationWizardOfflinePage;
