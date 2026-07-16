import * as React from "react";

import { ScreenAlertTicker } from "../../../bi/screen/atoms/screen-alert-ticker";
import { ScreenDonutChart } from "../../../bi/screen/atoms/screen-donut-chart";
import { ScreenKpiStrip } from "../../../bi/screen/atoms/screen-kpi-strip";
import { ScreenLineAreaChart } from "../../../bi/screen/atoms/screen-line-area-chart";
import { ScreenPanel } from "../../../bi/screen/atoms/screen-panel";
import { ScreenRankBarList } from "../../../bi/screen/atoms/screen-rank-bar-list";
import { L1ClassicThreeColumnLayout } from "../../../bi/screen/layouts/l1-classic-three-column";
import { ScreenShell, type RefreshStatus } from "../../../bi/screen/screen-shell";
import {
  ds07AlertRows,
  ds07ApiCallTrend,
  ds07EndpointFailTop,
  ds07EndpointProbePie,
  ds07Kpis,
  ds07QuotaConsumeTrend,
  ds07SyncTrackSuccess,
} from "./mock-data";

export type GatewayControlPlaneSituationScreenProps = {
  refreshStatus?: RefreshStatus;
  onRefreshClick?: () => void;
};

/**
 * DS-07 Gateway 控制面态势 — L1 三栏 + 同步/端点/配额/API 趋势 + 告警 ticker。
 * 语义拆分自 ControlPlaneHub 子面板，专用于大屏态势总览。
 * @see docs/spec/b-design-system-tailadmin-radix/prd/data-screens/pages.md#ds-07
 */
export function GatewayControlPlaneSituationScreen({
  refreshStatus,
  onRefreshClick,
}: GatewayControlPlaneSituationScreenProps) {
  const syncRankRows = ds07SyncTrackSuccess.map((row) => ({
    rank: row.rank,
    label: `${row.label}（${row.value}%）`,
    value: row.value,
    max: 100,
  }));

  return (
    <ScreenShell
      title="Gateway 控制面态势"
      showClock
      aspectRatio="16:9"
      theme="dark"
      refreshStatus={refreshStatus}
      onRefreshClick={onRefreshClick}
    >
      <L1ClassicThreeColumnLayout
        kpi={<ScreenKpiStrip items={ds07Kpis} columns={4} />}
        left={
          <>
            <ScreenPanel title="端点探测分布" fullHeight className="flex-1">
              <ScreenDonutChart series={ds07EndpointProbePie} centerLabel="探测" />
            </ScreenPanel>
            <ScreenPanel title="四轨同步成功率" fullHeight className="flex-1">
              <ScreenRankBarList rows={syncRankRows} />
            </ScreenPanel>
          </>
        }
        center={
          <>
            <ScreenPanel title="API 调用量趋势（24 小时）" fullHeight className="row-span-3 flex-[1.4]">
              <ScreenLineAreaChart
                categories={ds07ApiCallTrend.categories}
                series={ds07ApiCallTrend.series}
              />
            </ScreenPanel>
            <ScreenPanel title="配额消耗趋势（近 7 日 · 元/分）" fullHeight className="flex-1">
              <ScreenLineAreaChart
                categories={ds07QuotaConsumeTrend.categories}
                series={ds07QuotaConsumeTrend.series}
              />
            </ScreenPanel>
          </>
        }
        right={
          <>
            <ScreenPanel title="探测失败 TOP5" fullHeight className="flex-1">
              <ScreenRankBarList rows={ds07EndpointFailTop} />
            </ScreenPanel>
            <ScreenPanel title="控制面实时告警" fullHeight className="flex-[1.2]">
              <ScreenAlertTicker rows={ds07AlertRows} mode="scroll" theme="dark" maxHeight={180} />
            </ScreenPanel>
          </>
        }
        footer={
          <ScreenAlertTicker rows={ds07AlertRows} mode="scroll" theme="dark" maxHeight={48} />
        }
      />
    </ScreenShell>
  );
}

export default GatewayControlPlaneSituationScreen;
