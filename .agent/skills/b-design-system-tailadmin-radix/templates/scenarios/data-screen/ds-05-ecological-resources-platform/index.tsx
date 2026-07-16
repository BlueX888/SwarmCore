import * as React from "react";

import { ScreenDonutChart } from "../../../bi/screen/atoms/screen-donut-chart";
import { ScreenGaugeRing } from "../../../bi/screen/atoms/screen-gauge-ring";
import { ScreenGroupedBarChart } from "../../../bi/screen/atoms/screen-grouped-bar-chart";
import { ScreenKpiStrip } from "../../../bi/screen/atoms/screen-kpi-strip";
import { ScreenLineAreaChart } from "../../../bi/screen/atoms/screen-line-area-chart";
import { ScreenMapScene } from "../../../bi/screen/atoms/screen-map-scene";
import { ScreenPanel } from "../../../bi/screen/atoms/screen-panel";
import { ScreenRankBarList } from "../../../bi/screen/atoms/screen-rank-bar-list";
import { ScreenTimeline } from "../../../bi/screen/atoms/screen-timeline";
import { L3MapBottomTableLayout } from "../../../bi/screen/layouts/l3-map-bottom-table";
import { ScreenShell, type RefreshStatus } from "../../../bi/screen/screen-shell";
import {
  ds05FacilityGauges,
  ds05IndustryDonut,
  ds05KpiStrip,
  ds05MapMarkers,
  ds05MineralRanking,
  ds05PublicHealthGauges,
  ds05Timeline,
  ds05TrafficBars,
  ds05WaterResources,
} from "./mock-data";

export type EcologicalResourcesPlatformScreenProps = {
  refreshStatus?: RefreshStatus;
  onRefreshClick?: () => void;
};

/**
 * DS-05 生态资源大数据平台 — L3 地图主导 + 设施仪表/交通/公共卫生/矿藏 + 底 Timeline。
 * @see docs/spec/b-design-system-tailadmin-radix/prd/data-screens/pages.md#ds-05
 */
export function EcologicalResourcesPlatformScreen({
  refreshStatus,
  onRefreshClick,
}: EcologicalResourcesPlatformScreenProps) {
  const dark = "dark" as const;
  const [selectedMarkerId, setSelectedMarkerId] = React.useState<string | null>(null);

  return (
    <ScreenShell
      title="生态资源大数据平台"
      showClock
      aspectRatio="16:9"
      theme={dark}
      refreshStatus={refreshStatus}
      onRefreshClick={onRefreshClick}
    >
      <L3MapBottomTableLayout
        kpi={<ScreenKpiStrip items={[...ds05KpiStrip]} columns={6} variant={dark} />}
        left={
          <>
            <ScreenPanel title="监测设施仪表" fullHeight className="flex-1">
              <ScreenGaugeRing
                items={ds05FacilityGauges.map((k) => ({ ...k }))}
                theme={dark}
                height={140}
              />
            </ScreenPanel>
            <ScreenPanel title="水资源趋势" fullHeight className="flex-[1.2]">
              <ScreenLineAreaChart
                categories={[...ds05WaterResources.categories]}
                series={ds05WaterResources.series.map((s) => ({ ...s, data: [...s.data] }))}
                area
              />
            </ScreenPanel>
            <ScreenPanel title="生态产业结构" fullHeight className="flex-1">
              <ScreenDonutChart series={[...ds05IndustryDonut]} centerLabel="产业" height={140} />
            </ScreenPanel>
          </>
        }
        centerMap={
          <ScreenPanel title="内蒙古生态地图" fullHeight className="h-full">
            <ScreenMapScene
              markers={[...ds05MapMarkers]}
              fallback="mock"
              selectedMarkerId={selectedMarkerId}
              onMarkerClick={setSelectedMarkerId}
              hintText="内蒙古生态底图 · 点击城市标注查看信息浮层"
              height="100%"
              theme={dark}
              className="h-full min-h-[220px]"
            />
          </ScreenPanel>
        }
        right={
          <>
            <ScreenPanel title="交通运量柱图" fullHeight className="flex-1">
              <ScreenGroupedBarChart
                categories={[...ds05TrafficBars.categories]}
                series={ds05TrafficBars.series.map((s) => ({ ...s, data: [...s.data] }))}
                theme={dark}
                height={140}
              />
            </ScreenPanel>
            <ScreenPanel title="公共卫生指标" fullHeight className="flex-1">
              <ScreenGaugeRing
                items={ds05PublicHealthGauges.map((k) => ({ ...k }))}
                theme={dark}
                height={140}
              />
            </ScreenPanel>
            <ScreenPanel title="矿产资源排行" fullHeight className="flex-1">
              <ScreenRankBarList rows={[...ds05MineralRanking]} />
            </ScreenPanel>
          </>
        }
        bottomTable={
          <ScreenPanel title="生态保护时间轴" fullHeight className="h-full">
            <ScreenTimeline nodes={[...ds05Timeline]} theme={dark} />
          </ScreenPanel>
        }
      />
    </ScreenShell>
  );
}

export default EcologicalResourcesPlatformScreen;
