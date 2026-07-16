import * as React from "react";

import { ScreenDonutChart } from "../../../bi/screen/atoms/screen-donut-chart";
import { ScreenGroupedBarChart } from "../../../bi/screen/atoms/screen-grouped-bar-chart";
import { ScreenHeroCenter } from "../../../bi/screen/atoms/screen-hero-center";
import { ScreenLineAreaChart } from "../../../bi/screen/atoms/screen-line-area-chart";
import { ScreenPanel } from "../../../bi/screen/atoms/screen-panel";
import { ScreenWordCloud } from "../../../bi/screen/atoms/screen-word-cloud";
import { L2HeroOrbitLayout } from "../../../bi/screen/layouts/l2-hero-orbit";
import { ScreenShell, type RefreshStatus } from "../../../bi/screen/screen-shell";
import { screenTokens } from "../../../bi/screen/theme/screen-tokens";
import {
  ds02Applications,
  ds02DocumentDistribution,
  ds02HeroSubtitle,
  ds02HeroTitle,
  ds02ModelTokens,
  ds02OrbitItems,
  ds02SessionSummary,
  ds02SessionTrend,
  ds02TokenByApp,
  ds02TotalTokens,
  ds02WordCloud,
} from "./mock-data";

export type AiPlatformOverviewScreenProps = {
  refreshStatus?: RefreshStatus;
  onRefreshClick?: () => void;
};

/**
 * DS-02 AI 平台数据概览 — L2 Hero 环绕布局 + 词云/分组柱图原子。
 * @see docs/spec/b-design-system-tailadmin-radix/prd/data-screens/pages.md#ds-02
 */
export function AiPlatformOverviewScreen({
  refreshStatus,
  onRefreshClick,
}: AiPlatformOverviewScreenProps) {
  const dark = "dark" as const;

  return (
    <ScreenShell
      title="AI 平台数据概览"
      showClock
      aspectRatio="16:9"
      theme={dark}
      refreshStatus={refreshStatus}
      onRefreshClick={onRefreshClick}
    >
      <L2HeroOrbitLayout
        kpi={
          <div className="flex items-center justify-between rounded-lg border border-cyan-500/20 bg-slate-900/60 px-4 py-2">
            <span className={screenTokens.title}>累计 Token 消耗</span>
            <span className={screenTokens.kpiValue}>{ds02TotalTokens}</span>
          </div>
        }
        leftColumn={
          <>
            <ScreenPanel title="7 日会话摘要" fullHeight className="flex-1">
              <div className="grid grid-cols-2 gap-2">
                {ds02SessionSummary.map((item) => (
                  <div
                    key={item.label}
                    className="rounded-md border border-white/10 bg-white/5 px-2 py-2 text-center"
                  >
                    <p className={screenTokens.kpiLabel}>{item.label}</p>
                    <p className="text-sm font-semibold tabular-nums text-white">{item.value}</p>
                  </div>
                ))}
              </div>
            </ScreenPanel>
            <ScreenPanel title="应用占比" fullHeight className="flex-1">
              <ScreenDonutChart series={[...ds02Applications]} centerLabel="应用" height={160} />
            </ScreenPanel>
            <ScreenPanel title="应用 Token 分布" fullHeight className="flex-[1.2]">
              <ScreenGroupedBarChart
                categories={[...ds02TokenByApp.categories]}
                series={ds02TokenByApp.series.map((s) => ({ ...s, data: [...s.data] }))}
                theme={dark}
                height={180}
              />
            </ScreenPanel>
          </>
        }
        hero={
          <ScreenPanel title="平台核心指标" fullHeight className="h-full">
            <ScreenHeroCenter
              title={ds02HeroTitle}
              subtitle={ds02HeroSubtitle}
              orbitItems={[...ds02OrbitItems]}
              theme={dark}
              className="h-full"
            />
          </ScreenPanel>
        }
        rightColumn={
          <>
            <ScreenPanel title="热词云" fullHeight className="flex-1">
              <ScreenWordCloud
                words={[...ds02WordCloud]}
                theme={dark}
                fallback="tag-cloud"
              />
            </ScreenPanel>
            <ScreenPanel title="文档类型分布" fullHeight className="flex-1">
              <ScreenDonutChart
                series={[...ds02DocumentDistribution]}
                centerLabel="文档"
                height={160}
              />
            </ScreenPanel>
            <ScreenPanel title="模型 Token 排行" fullHeight className="flex-[1.2]">
              <ScreenGroupedBarChart
                categories={[...ds02ModelTokens.categories]}
                series={ds02ModelTokens.series.map((s) => ({ ...s, data: [...s.data] }))}
                theme={dark}
                horizontal
                height={180}
              />
            </ScreenPanel>
          </>
        }
        bottomTrend={
          <ScreenPanel title="7 日访问与 Token 趋势" fullHeight className="h-full">
            <ScreenLineAreaChart
              categories={[...ds02SessionTrend.categories]}
              series={ds02SessionTrend.series.map((s) => ({ ...s, data: [...s.data] }))}
              area
            />
          </ScreenPanel>
        }
      />
    </ScreenShell>
  );
}

export default AiPlatformOverviewScreen;
