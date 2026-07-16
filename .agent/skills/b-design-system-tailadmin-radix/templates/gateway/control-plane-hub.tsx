import * as React from "react";
import { cn } from "@/lib/utils";
import {
  DeploymentModeMatrix,
  type DeploymentMode,
} from "./deployment-mode-matrix";
import { BalanceQuotaSummary } from "./balance-quota-summary";
import { SyncHealthPanel, type SyncTrack } from "./sync-health-panel";
import { EndpointProbeTable, type EndpointProbeRow } from "./endpoint-probe-table";
import { LicenseIssuePanel } from "./license-issue-panel";
import { ApiKeyRevealPanel } from "./api-key-reveal-panel";

export type ControlPlaneHubProps = {
  deploymentMode?: DeploymentMode;
  onDeploymentModeChange?: (mode: DeploymentMode) => void;
  balanceCents?: number;
  quotaPercent?: number;
  quotaUsed?: string;
  quotaLimit?: string;
  licenseEdition?: string;
  licenseExpiresAt?: string;
  instanceCount?: number;
  degradedCount?: number;
  syncTracks?: SyncTrack[];
  endpoints?: EndpointProbeRow[];
  issuedLicense?: string | null;
  rawApiKey?: string | null;
  showSync?: boolean;
  showBalance?: boolean;
  onProbe?: (rowId: string) => void;
  onSyncRetry?: (trackId: string) => void;
  className?: string;
};

/**
 * Control plane hub page composition — deployment mode + KPI + sync + probes + license + API key.
 * @see references/layout-patterns/control-plane.md
 * @see references/deployment-mode-matrix.md
 */
export function ControlPlaneHub({
  deploymentMode = "connected",
  onDeploymentModeChange,
  balanceCents = 1248000,
  quotaPercent = 84,
  quotaUsed = "840K",
  quotaLimit = "1M",
  licenseEdition = "企业版",
  licenseExpiresAt = "Dec 2026",
  instanceCount = 6,
  degradedCount = 1,
  syncTracks = [
    { id: "quota", label: "Quota sync", status: "ok", lastSuccess: "12s ago" },
    { id: "report", label: "Report sync", status: "ok", lastSuccess: "45s ago" },
    { id: "hmac", label: "HMAC heartbeat", status: "stale", lastSuccess: "8m ago", hint: "Check network egress" },
    { id: "license", label: "License check", status: "ok", lastSuccess: "2m ago" },
  ],
  endpoints = [
    {
      id: "ep-1",
      endpoint: "https://api.prod.internal/v1",
      instanceId: "gw-prod-01",
      status: "ready",
      latency: "42ms",
    },
    {
      id: "ep-2",
      endpoint: "https://api.staging.internal/v1",
      instanceId: "gw-stg-02",
      status: "unknown",
      hint: "过去 24 小时无探测记录",
    },
    {
      id: "ep-3",
      endpoint: "https://edge.airgap.local/v1",
      instanceId: "gw-edge-01",
      status: "failed",
      latency: "timeout",
      hint: "Connection refused — check local listener",
    },
  ],
  issuedLicense,
  rawApiKey,
  showSync,
  showBalance,
  onProbe,
  onSyncRetry,
  className,
}: ControlPlaneHubProps) {
  const isAirgap = deploymentMode === "airgap";
  const displaySync = showSync ?? !isAirgap;
  const displayBalance = showBalance ?? !isAirgap;

  return (
    <div className={cn("flex flex-col gap-6", className)}>
      <section>
        <h2 className="mb-3 text-theme-sm font-semibold text-gray-800 dark:text-white/90">
          Deployment mode
        </h2>
        <DeploymentModeMatrix
          value={deploymentMode}
          onChange={onDeploymentModeChange}
        />
      </section>

      {displayBalance ? (
        <section>
          <h2 className="mb-3 text-theme-sm font-semibold text-gray-800 dark:text-white/90">
            Balance & quota
          </h2>
          <BalanceQuotaSummary
            balanceCents={balanceCents}
            quotaPercent={quotaPercent}
            quotaUsed={quotaUsed}
            quotaLimit={quotaLimit}
            licenseEdition={licenseEdition}
            licenseExpiresAt={licenseExpiresAt}
            instanceCount={instanceCount}
            degradedCount={degradedCount}
          />
        </section>
      ) : null}

      {displaySync ? (
        <SyncHealthPanel tracks={syncTracks} onRetry={onSyncRetry} />
      ) : null}

      <EndpointProbeTable rows={endpoints} onProbe={onProbe} />

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <LicenseIssuePanel
          mode="issue"
          edition={licenseEdition}
          expiresAt={licenseExpiresAt}
          issuedLicense={issuedLicense}
        />
        <ApiKeyRevealPanel rawKey={rawApiKey} onDismiss={() => undefined} />
      </div>
    </div>
  );
}
