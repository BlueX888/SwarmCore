import * as React from "react";

import { ScreenDataTable } from "../../../bi/screen/atoms/screen-data-table";
import { ScreenDonutChart } from "../../../bi/screen/atoms/screen-donut-chart";
import { ScreenGaugeRing } from "../../../bi/screen/atoms/screen-gauge-ring";
import { ScreenGroupedBarChart } from "../../../bi/screen/atoms/screen-grouped-bar-chart";
import { ScreenLineAreaChart } from "../../../bi/screen/atoms/screen-line-area-chart";
import { ScreenMapScene } from "../../../bi/screen/atoms/screen-map-scene";
import { ScreenPanel } from "../../../bi/screen/atoms/screen-panel";
import { ScreenRadarChart } from "../../../bi/screen/atoms/screen-radar-chart";
import { ScreenRankBarList } from "../../../bi/screen/atoms/screen-rank-bar-list";
import { L3MapBottomTableLayout } from "../../../bi/screen/layouts/l3-map-bottom-table";
import { ScreenShell, type RefreshStatus } from "../../../bi/screen/screen-shell";
import { screenTokens } from "../../../bi/screen/theme/screen-tokens";
import {
  ds04FacilityRanking,
  ds04GreeningProgress,
  ds04MapMarkers,
  ds04MonitorRows,
  ds04ParkingKpis,
  ds04PeopleFlowTrend,
  ds04SecurityRadar,
  ds04SmartDevices,
  ds04VehicleTraffic,
} from "./mock-data";

export type CommunitySmartPlatformScreenProps = {
  refreshStatus?: RefreshStatus;
  onRefreshClick?: () => void;
};

/**
 * DS-04 社区智慧化数据平台 — L3 地图主导 + 设施/车流/监控组合。
 * @see docs/spec/b-design-system-tailadmin-radix/prd/data-screens/pages.md#ds-04
 */
export function CommunitySmartPlatformScreen({
  refreshStatus,
  onRefreshClick,
}: CommunitySmartPlatformScreenProps) {
  const dark = "dark" as const;
  const [selectedMarkerId, setSelectedMarkerId] = React.useState<string | null>(null);

  return (
    <ScreenShell
      title="社区智慧化数据平台"
      showClock
      aspectRatio="16:9"
      theme={dark}
      refreshStatus={refreshStatus}
      onRefreshClick={onRefreshClick}
    >
      <L3MapBottomTableLayout
        left={
          <>
            <ScreenPanel title="设施评分排行" fullHeight className="flex-1">
              <ScreenRankBarList rows={[...ds04FacilityRanking]} />
            </ScreenPanel>
            <ScreenPanel title="人员流量趋势" fullHeight className="flex-[1.2]">
              <ScreenLineAreaChart
                categories={[...ds04PeopleFlowTrend.categories]}
                series={ds04PeopleFlowTrend.series.map((s) => ({ ...s, data: [...s.data] }))}
                area
              />
            </ScreenPanel>
          </>
        }
        centerMap={
          <ScreenPanel title="社区地图标注" fullHeight className="h-full">
            <ScreenMapScene
              markers={[...ds04MapMarkers]}
              fallback="mock"
              selectedMarkerId={selectedMarkerId}
              onMarkerClick={setSelectedMarkerId}
              height="100%"
              theme={dark}
              className="h-full min-h-[220px]"
            />
          </ScreenPanel>
        }
        right={
          <>
            <ScreenPanel title="智慧设备分布" fullHeight className="flex-1">
              <ScreenDonutChart series={[...ds04SmartDevices]} centerLabel="设备" height={140} />
            </ScreenPanel>
            <ScreenPanel title="安防能力雷达" fullHeight className="flex-1">
              <ScreenRadarChart
                categories={[...ds04SecurityRadar.categories]}
                series={ds04SecurityRadar.series.map((s) => ({ ...s, data: [...s.data] }))}
                theme={dark}
                height={160}
              />
            </ScreenPanel>
            <ScreenPanel title="停车场 KPI" fullHeight className="flex-1">
              <ScreenGaugeRing
                items={ds04ParkingKpis.map((k) => ({
                  label: k.label,
                  value: k.value,
                  unit: k.unit,
                  max: k.label === "周转率" ? 100 : k.label === "平均停留" ? 8 : 600,
                }))}
                theme={dark}
                height={140}
              />
            </ScreenPanel>
            <ScreenPanel title="车辆通行柱图" fullHeight className="flex-1">
              <ScreenGroupedBarChart
                categories={[...ds04VehicleTraffic.categories]}
                series={ds04VehicleTraffic.series.map((s) => ({ ...s, data: [...s.data] }))}
                theme={dark}
                height={140}
              />
            </ScreenPanel>
            <ScreenPanel title="绿化进度" fullHeight className="shrink-0">
              <ScreenGaugeRing
                items={[{ ...ds04GreeningProgress[0] }]}
                theme={dark}
                height={120}
              />
            </ScreenPanel>
          </>
        }
        bottomTable={
          <ScreenPanel title="监控点位实时状态" fullHeight className="h-full">
            <ScreenDataTable
              columns={[
                { key: "point", title: "监控点", width: "28%" },
                { key: "status", title: "状态", width: "16%" },
                { key: "lastEvent", title: "最近事件", width: "36%" },
                { key: "time", title: "时间", width: "20%" },
              ]}
              rows={ds04MonitorRows.map((row) => ({
                ...row,
                status: (
                  <span
                    className={
                      row.status === "告警"
                        ? "text-rose-400"
                        : row.status === "维护"
                          ? "text-amber-400"
                          : "text-emerald-400"
                    }
                  >
                    {row.status}
                  </span>
                ),
              }))}
              maxHeight={140}
            />
          </ScreenPanel>
        }
      />
    </ScreenShell>
  );
}

export default CommunitySmartPlatformScreen;
