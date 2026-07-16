import * as React from "react";
import { cn } from "@/lib/utils";
import { Alert } from "@/components/ui/alert";
import { Cloud, CloudOff, HardDrive, Lock, Server } from "lucide-react";

export type DeploymentMode = "connected" | "airgap" | "local" | "cloud" | "private";

export type DeploymentModeOption = {
  id: DeploymentMode;
  label: string;
  description: string;
  icon?: React.ReactNode;
};

export type DeploymentModeMatrixProps = {
  modes?: DeploymentModeOption[];
  value: DeploymentMode;
  onChange?: (mode: DeploymentMode) => void;
  readOnly?: boolean;
  showBanner?: boolean;
  className?: string;
};

const defaultModes: DeploymentModeOption[] = [
  {
    id: "connected",
    label: "联网模式",
    description: "与集中控制面同步配额、报表与心跳。",
    icon: <Cloud className="size-4" />,
  },
  {
    id: "airgap",
    label: "离线隔离",
    description: "零出站流量，仅支持本地 License 验签。",
    icon: <CloudOff className="size-4" />,
  },
  {
    id: "local",
    label: "本地部署",
    description: "单机或边缘节点，端点本地托管。",
    icon: <HardDrive className="size-4" />,
  },
  {
    id: "cloud",
    label: "公有云",
    description: "控制面托管于公有云环境。",
    icon: <Server className="size-4" />,
  },
  {
    id: "private",
    label: "私有云",
    description: "控制面位于私有 VPC，出站受限。",
    icon: <Lock className="size-4" />,
  },
];

const bannerCopy: Record<DeploymentMode, { variant: "info" | "warning"; text: string } | null> = {
  connected: {
    variant: "info",
    text: "余额与配额由集中控制面同步；用量报表将按计划出网上报。",
  },
  airgap: {
    variant: "info",
    text: "零出站模式，用量不出内网；License 须离线续期。",
  },
  local: null,
  cloud: null,
  private: null,
};

/**
 * Deployment mode chip matrix — connected/airgap/local/cloud/private.
 * @see references/deployment-mode-matrix.md
 */
export function DeploymentModeMatrix({
  modes = defaultModes,
  value,
  onChange,
  readOnly = false,
  showBanner = true,
  className,
}: DeploymentModeMatrixProps) {
  const banner = showBanner ? bannerCopy[value] : null;

  return (
    <div className={cn("space-y-4", className)}>
      <div
        className="flex flex-wrap gap-2"
        role="radiogroup"
        aria-label="部署模式"
      >
        {modes.map((mode) => {
          const active = mode.id === value;
          return (
            <button
              key={mode.id}
              type="button"
              role="radio"
              aria-checked={active}
              disabled={readOnly}
              onClick={() => onChange?.(mode.id)}
              className={cn(
                "inline-flex min-w-[120px] flex-1 items-center gap-2 rounded-xl border px-3 py-2 text-left transition-colors",
                active
                  ? "border-brand-500/40 bg-brand-50 text-brand-600 dark:border-brand-500/30 dark:bg-brand-500/10 dark:text-brand-400"
                  : "border-gray-200 bg-white text-gray-700 hover:bg-gray-50 dark:border-white/[0.05] dark:bg-white/[0.03] dark:text-gray-300 dark:hover:bg-white/[0.05]",
                readOnly && "cursor-default opacity-90",
              )}
            >
              <span className="shrink-0 text-gray-500">{mode.icon}</span>
              <span className="min-w-0">
                <span className="block truncate text-theme-sm font-medium">{mode.label}</span>
                <span className="block truncate text-theme-xs text-gray-500 dark:text-gray-400">
                  {mode.description}
                </span>
              </span>
            </button>
          );
        })}
      </div>
      {banner ? (
        <Alert variant={banner.variant} title="部署提示">
          {banner.text}
        </Alert>
      ) : null}
    </div>
  );
}
