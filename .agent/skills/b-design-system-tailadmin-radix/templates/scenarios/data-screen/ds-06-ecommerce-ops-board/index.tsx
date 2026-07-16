import * as React from "react";

import { ScreenDonutChart } from "../../../bi/screen/atoms/screen-donut-chart";
import { ScreenFunnelChart } from "../../../bi/screen/atoms/screen-funnel-chart";
import { ScreenGroupedBarChart } from "../../../bi/screen/atoms/screen-grouped-bar-chart";
import { ScreenLineAreaChart } from "../../../bi/screen/atoms/screen-line-area-chart";
import { ScreenPanel } from "../../../bi/screen/atoms/screen-panel";
import { ScreenRadarChart } from "../../../bi/screen/atoms/screen-radar-chart";
import { ScreenRankBarList } from "../../../bi/screen/atoms/screen-rank-bar-list";
import { ScreenDataTable } from "../../../bi/screen/atoms/screen-data-table";
import { ScreenWordCloud } from "../../../bi/screen/atoms/screen-word-cloud";
import { L4LightAnalyticsBoardLayout } from "../../../bi/screen/layouts/l4-light-analytics-board";
import { ScreenShell, type RefreshStatus } from "../../../bi/screen/screen-shell";
import {
  ds06ChannelTraffic,
  ds06FunnelStages,
  ds06GoalCompletion,
  ds06HotWords,
  ds06MonthlyGrowth,
  ds06ProvinceActiveUsers,
  ds06RevenueTrend,
  ds06SpendingBars,
  ds06UserCategoryPie,
  ds06UserRadar,
} from "./mock-data";

export type EcommerceOpsBoardProps = {
  refreshStatus?: RefreshStatus;
  onRefreshClick?: () => void;
};

/**
 * DS-06 电商运营数据看板 — L4 浅色布局 + 漏斗/雷达/分组柱图等原子。
 * @see docs/spec/b-design-system-tailadmin-radix/prd/data-screens/pages.md#ds-06
 */
export function EcommerceOpsBoardScreen({
  refreshStatus,
  onRefreshClick,
}: EcommerceOpsBoardProps) {
  const light = "light" as const;

  return (
    <ScreenShell
      title="电商运营数据看板"
      showClock
      aspectRatio="16:9"
      theme={light}
      refreshStatus={refreshStatus}
      onRefreshClick={onRefreshClick}
    >
      <L4LightAnalyticsBoardLayout
        leftColumn={
          <>
            <ScreenPanel title="目标完成度" variant={light} fullHeight className="flex-1">
              <ScreenDonutChart
                theme={light}
                series={[
                  { name: "已完成", value: ds06GoalCompletion },
                  { name: "未完成", value: 100 - ds06GoalCompletion },
                ]}
                centerLabel={`${ds06GoalCompletion}%`}
                height={180}
              />
            </ScreenPanel>
            <ScreenPanel title="转化漏斗" variant={light} fullHeight className="flex-[1.4]">
              <ScreenFunnelChart stages={ds06FunnelStages} theme={light} />
            </ScreenPanel>
          </>
        }
        centerTop={
          <div className="grid h-full grid-cols-2 gap-3">
            <ScreenPanel title="热词气泡" variant={light} fullHeight>
              <ScreenWordCloud words={ds06HotWords} theme={light} fallback="tag-cloud" />
            </ScreenPanel>
            <ScreenPanel title="用户雷达（男/女）" variant={light} fullHeight>
              <ScreenRadarChart
                categories={ds06UserRadar.categories}
                series={ds06UserRadar.series}
                theme={light}
                height={180}
              />
            </ScreenPanel>
          </div>
        }
        centerMiddle={
          <ScreenPanel title="消费金额（男/女 × 产品 A–D）" variant={light} fullHeight>
            <ScreenGroupedBarChart
              categories={ds06SpendingBars.categories}
              series={ds06SpendingBars.series}
              horizontal
              theme={light}
              height={180}
            />
          </ScreenPanel>
        }
        centerBottom={
          <ScreenPanel title="用户分类" variant={light} fullHeight>
            <ScreenDonutChart theme={light} series={ds06UserCategoryPie} centerLabel="用户" height={180} />
          </ScreenPanel>
        }
        rightColumn={
          <>
            <ScreenPanel title="历年营收" variant={light} fullHeight className="flex-[1.2]">
              <ScreenLineAreaChart
                categories={ds06RevenueTrend.categories}
                series={ds06RevenueTrend.series}
                theme={light}
                height={200}
              />
            </ScreenPanel>
            <ScreenPanel title="各省活跃用户" variant={light} fullHeight className="flex-1">
              <ScreenRankBarList rows={ds06ProvinceActiveUsers} variant={light} />
            </ScreenPanel>
          </>
        }
        fullWidthBottom={
          <div className="grid grid-cols-2 gap-3">
            <ScreenPanel title="12 月增长（千人）" variant={light} fullHeight>
              <ScreenGroupedBarChart
                categories={ds06MonthlyGrowth.categories}
                series={ds06MonthlyGrowth.series}
                theme={light}
                height={180}
              />
            </ScreenPanel>
            <ScreenPanel title="渠道流量" variant={light} fullHeight>
              <div className="grid h-full grid-cols-2 gap-3">
                <ScreenDonutChart theme={light} series={ds06ChannelTraffic.pie} height={160} />
                <ScreenDataTable
                  variant={light}
                  columns={[
                    { key: "channel", title: "渠道", width: "28%" },
                    { key: "visits", title: "访问量", width: "28%" },
                    { key: "share", title: "占比", width: "22%" },
                    { key: "trend", title: "环比", width: "22%" },
                  ]}
                  rows={ds06ChannelTraffic.table.map((row) => ({ ...row }))}
                  maxHeight={160}
                />
              </div>
            </ScreenPanel>
          </div>
        }
      />
    </ScreenShell>
  );
}

export default EcommerceOpsBoardScreen;
