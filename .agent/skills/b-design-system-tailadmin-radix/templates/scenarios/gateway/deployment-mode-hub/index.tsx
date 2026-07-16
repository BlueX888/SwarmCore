import * as React from "react";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  DeploymentModeMatrix,
  type DeploymentMode,
} from "../../../gateway/deployment-mode-matrix";
import {
  connectivityRules,
  defaultDeploymentMode,
  deploymentModeHubTabs,
  deploymentModeOptions,
  syncPolicyRows,
  type DeploymentModeHubTabId,
} from "./mock-data";

export type DeploymentModeHubPageProps = {
  deploymentMode?: DeploymentMode;
  activeTab?: DeploymentModeHubTabId;
  defaultTab?: DeploymentModeHubTabId;
  onDeploymentModeChange?: (mode: DeploymentMode) => void;
  onTabChange?: (tabId: DeploymentModeHubTabId) => void;
  readOnly?: boolean;
  className?: string;
};

function isPolicyEnabled(mode: DeploymentMode, enabledModes: DeploymentMode[]) {
  return enabledModes.includes(mode);
}

/**
 * S02-G02 部署模式 Hub — Hub Tabs + 部署矩阵 + 同步策略 + 连通性说明。
 * @see docs/spec/b-design-system-tailadmin-radix/prd/scenarios/S02-gateway.md#s02-g02
 * @see references/layout-patterns/hub-tabs.md
 */
export function DeploymentModeHubPage({
  deploymentMode = defaultDeploymentMode,
  activeTab: activeTabProp,
  defaultTab = "mode",
  onDeploymentModeChange,
  onTabChange,
  readOnly = false,
  className,
}: DeploymentModeHubPageProps) {
  const [internalTab, setInternalTab] = React.useState<DeploymentModeHubTabId>(defaultTab);
  const activeTab = activeTabProp ?? internalTab;

  const handleTabChange = (next: string) => {
    const tabId = next as DeploymentModeHubTabId;
    if (activeTabProp === undefined) {
      setInternalTab(tabId);
    }
    onTabChange?.(tabId);
  };

  const isAirgap = deploymentMode === "airgap";

  return (
    <div className={cn("space-y-6", className)} data-scenario-page="deployment-mode-hub">
      <header className="space-y-1">
        <h1 className="text-lg font-semibold text-gray-900 dark:text-white/90">部署模式 Hub</h1>
        <p className="text-theme-sm text-gray-500">
          配置联网/离线部署矩阵、同步策略与出口连通性要求；切换模式将联动同步与配额露出规则。
        </p>
      </header>

      <Tabs value={activeTab} onValueChange={handleTabChange}>
        <TabsList
          className={cn(
            "h-auto w-full justify-start gap-0 overflow-x-auto rounded-none border-b border-gray-200 bg-transparent p-0 dark:border-gray-800",
          )}
        >
          {deploymentModeHubTabs.map((tab) => (
            <TabsTrigger
              key={tab.id}
              value={tab.id}
              className={cn(
                "rounded-none border-b-2 border-transparent px-4 py-3 text-theme-sm font-medium text-gray-500 shadow-none",
                "data-[state=active]:border-brand-500 data-[state=active]:bg-transparent data-[state=active]:text-brand-500",
                "dark:text-gray-400 dark:data-[state=active]:text-brand-400",
              )}
            >
              {tab.label}
            </TabsTrigger>
          ))}
        </TabsList>

        <TabsContent value="mode" className="mt-4 min-h-[320px] space-y-4 focus-visible:outline-none">
          <DeploymentModeMatrix
            modes={deploymentModeOptions}
            value={deploymentMode}
            onChange={onDeploymentModeChange}
            readOnly={readOnly}
            showBanner
          />
          {isAirgap ? (
            <p className="text-theme-xs text-gray-500">
              离线模式下将隐藏余额/企业池与四轨同步面板；License 须通过离线文件续期。
            </p>
          ) : null}
        </TabsContent>

        <TabsContent value="sync" className="mt-4 min-h-[320px] focus-visible:outline-none">
          <div className="overflow-hidden rounded-xl border border-gray-200 dark:border-white/[0.05]">
            <table className="w-full text-left text-theme-sm">
              <thead className="border-b border-gray-200 bg-gray-50 text-theme-xs text-gray-500 dark:border-white/[0.05] dark:bg-white/[0.03]">
                <tr>
                  <th className="px-4 py-3 font-medium">同步项</th>
                  <th className="px-4 py-3 font-medium">说明</th>
                  <th className="px-4 py-3 font-medium">当前模式</th>
                  <th className="px-4 py-3 font-medium">频率</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-white/[0.05]">
                {syncPolicyRows.map((row) => {
                  const enabled = isPolicyEnabled(deploymentMode, row.enabledModes);
                  return (
                    <tr key={row.id} className="bg-white dark:bg-transparent">
                      <td className="px-4 py-3 font-medium text-gray-800 dark:text-white/90">{row.label}</td>
                      <td className="px-4 py-3 text-gray-500">{row.description}</td>
                      <td className="px-4 py-3">
                        <Badge variant="light" color={enabled ? "success" : "light"} size="sm">
                          {enabled ? "已启用" : "不适用"}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 tabular-nums text-gray-500">{enabled ? row.interval : "—"}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          {isAirgap ? (
            <p className="mt-3 text-theme-xs text-warning-600 dark:text-warning-500">
              离线隔离模式下仅保留本地许可校验；配额与报表同步项将自动停用。
            </p>
          ) : null}
        </TabsContent>

        <TabsContent value="connectivity" className="mt-4 min-h-[320px] focus-visible:outline-none">
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            {connectivityRules.map((rule) => (
              <div
                key={rule.id}
                className="rounded-xl border border-gray-200 bg-white p-4 dark:border-white/[0.05] dark:bg-white/[0.03]"
              >
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <p className="text-theme-sm font-medium text-gray-800 dark:text-white/90">{rule.target}</p>
                    <p className="mt-1 text-theme-xs text-gray-500">
                      {rule.direction} · 端口 {rule.port}
                    </p>
                  </div>
                  <Badge variant="light" color={rule.required ? "warning" : "info"} size="sm">
                    {rule.required ? "必需" : "建议"}
                  </Badge>
                </div>
                {rule.note ? <p className="mt-2 text-theme-xs text-gray-500">{rule.note}</p> : null}
              </div>
            ))}
          </div>
          <p className="mt-4 text-theme-xs text-gray-500">
            切换至离线隔离后，除本地端点外的出站规则将标记为可关闭；保存前请确认防火墙白名单已更新。
          </p>
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default DeploymentModeHubPage;
