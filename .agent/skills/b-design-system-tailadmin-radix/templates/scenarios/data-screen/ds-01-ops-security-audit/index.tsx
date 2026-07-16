import * as React from "react";

import { ScreenDataTable } from "../../../bi/screen/atoms/screen-data-table";
import { ScreenDonutChart } from "../../../bi/screen/atoms/screen-donut-chart";
import { ScreenKpiStrip } from "../../../bi/screen/atoms/screen-kpi-strip";
import { ScreenLineAreaChart } from "../../../bi/screen/atoms/screen-line-area-chart";
import { ScreenPanel } from "../../../bi/screen/atoms/screen-panel";
import { ScreenRankBarList } from "../../../bi/screen/atoms/screen-rank-bar-list";
import { L1ClassicThreeColumnLayout } from "../../../bi/screen/layouts/l1-classic-three-column";
import { ScreenShell, type RefreshStatus } from "../../../bi/screen/screen-shell";
import {
  ds01ActiveTrend,
  ds01AssetActivityPie,
  ds01AssetGroupPie,
  ds01AssetTopDay,
  ds01AssetTopWeek,
  ds01DangerCommands,
  ds01Kpis,
  ds01UserLoginDay,
  ds01UserLoginWeek,
} from "./mock-data";

export type OpsSecurityAuditScreenProps = {
  refreshStatus?: RefreshStatus;
  onRefreshClick?: () => void;
};

/**
 * DS-01 运维安全审计大屏 — 仅组装 L1 layout + screen atoms + mock。
 * @see docs/spec/b-design-system-tailadmin-radix/prd/data-screens/pages.md#ds-01
 */
export function OpsSecurityAuditScreen({
  refreshStatus,
  onRefreshClick,
}: OpsSecurityAuditScreenProps) {
  return (
    <ScreenShell
      title="运维安全审计大屏"
      showClock
      aspectRatio="16:9"
      theme="dark"
      refreshStatus={refreshStatus}
      onRefreshClick={onRefreshClick}
    >
      <L1ClassicThreeColumnLayout
        kpi={<ScreenKpiStrip items={ds01Kpis} columns={3} />}
        left={
          <>
            <ScreenPanel title="资产活跃度（近30天）" fullHeight className="flex-1">
              <ScreenDonutChart series={ds01AssetActivityPie} centerLabel="资产" />
            </ScreenPanel>
            <ScreenPanel title="最近一天用户登录" fullHeight className="flex-1">
              <ScreenRankBarList rows={ds01UserLoginDay} />
            </ScreenPanel>
            <ScreenPanel title="最近一周用户登录排名" fullHeight className="flex-1">
              <ScreenRankBarList rows={ds01UserLoginWeek} />
            </ScreenPanel>
          </>
        }
        center={
          <>
            <ScreenPanel title="用户/资产活跃趋势" fullHeight className="row-span-4 flex-[2]">
              <ScreenLineAreaChart
                categories={ds01ActiveTrend.categories}
                series={ds01ActiveTrend.series}
              />
            </ScreenPanel>
            <ScreenPanel title="高危命令统计" fullHeight className="flex-1">
              <ScreenDataTable
                columns={[
                  { key: "user", title: "用户", width: "28%" },
                  { key: "asset", title: "资产", width: "22%" },
                  { key: "input", title: "输入命令", width: "32%" },
                  { key: "time", title: "时间", width: "18%" },
                ]}
                rows={ds01DangerCommands.map((row) => ({ ...row }))}
                maxHeight={180}
              />
            </ScreenPanel>
          </>
        }
        right={
          <>
            <ScreenPanel title="各组资产占比" fullHeight className="flex-1">
              <ScreenDonutChart series={ds01AssetGroupPie} centerLabel="占比" />
            </ScreenPanel>
            <ScreenPanel title="最近一天资产登录 TOP5" fullHeight className="flex-1">
              <ScreenRankBarList rows={ds01AssetTopDay} />
            </ScreenPanel>
            <ScreenPanel title="最近一周资产登录排名" fullHeight className="flex-1">
              <ScreenRankBarList rows={ds01AssetTopWeek} />
            </ScreenPanel>
          </>
        }
      />
    </ScreenShell>
  );
}

export default OpsSecurityAuditScreen;
