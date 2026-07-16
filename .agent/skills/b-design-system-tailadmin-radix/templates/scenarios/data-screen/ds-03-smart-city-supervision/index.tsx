import * as React from "react";

import { ScreenAlertTicker } from "../../../bi/screen/atoms/screen-alert-ticker";
import { ScreenDataTable } from "../../../bi/screen/atoms/screen-data-table";
import { ScreenGaugeRing } from "../../../bi/screen/atoms/screen-gauge-ring";
import { ScreenGlobeScene } from "../../../bi/screen/atoms/screen-globe-scene";
import { ScreenPanel } from "../../../bi/screen/atoms/screen-panel";
import { ScreenRankBarList } from "../../../bi/screen/atoms/screen-rank-bar-list";
import { ScreenWordCloud } from "../../../bi/screen/atoms/screen-word-cloud";
import { L3MapBottomTableLayout } from "../../../bi/screen/layouts/l3-map-bottom-table";
import { ScreenShell, type RefreshStatus } from "../../../bi/screen/screen-shell";
import {
  ds03AlertRows,
  ds03CityGauges,
  ds03DepartmentWords,
  ds03GlobeNodes,
  ds03IndustryStructure,
  ds03IssueRows,
} from "./mock-data";

export type SmartCitySupervisionScreenProps = {
  refreshStatus?: RefreshStatus;
  onRefreshClick?: () => void;
};

/**
 * DS-03 智慧城市综合监管 — L3 地球主导 + 仪表/产业/词云/告警 + 底整改宽表。
 * @see docs/spec/b-design-system-tailadmin-radix/prd/data-screens/pages.md#ds-03
 */
export function SmartCitySupervisionScreen({
  refreshStatus,
  onRefreshClick,
}: SmartCitySupervisionScreenProps) {
  const dark = "dark" as const;
  const [selectedNodeId, setSelectedNodeId] = React.useState<string | null>(null);

  return (
    <ScreenShell
      title="智慧城市综合监管"
      showClock
      aspectRatio="16:9"
      theme={dark}
      refreshStatus={refreshStatus}
      onRefreshClick={onRefreshClick}
    >
      <L3MapBottomTableLayout
        left={
          <>
            <ScreenPanel title="城市运行仪表" fullHeight className="flex-1">
              <ScreenGaugeRing
                items={ds03CityGauges.map((k) => ({ ...k, max: k.label === "城市安全指数" ? 100 : 100 }))}
                theme={dark}
                height={140}
              />
            </ScreenPanel>
            <ScreenPanel title="产业结构占比" fullHeight className="flex-[1.2]">
              <ScreenRankBarList rows={[...ds03IndustryStructure]} />
            </ScreenPanel>
          </>
        }
        centerMap={
          <ScreenPanel title="全球城市态势" fullHeight className="h-full">
            <ScreenGlobeScene
              nodes={[...ds03GlobeNodes]}
              selectedNodeId={selectedNodeId}
              onNodeClick={setSelectedNodeId}
              hintText="CSS/SVG 地球占位 · 点击节点查看城市态势浮层"
              height="100%"
              theme={dark}
              className="h-full min-h-[220px]"
            />
          </ScreenPanel>
        }
        right={
          <>
            <ScreenPanel title="部门热词" fullHeight className="flex-1">
              <ScreenWordCloud
                words={[...ds03DepartmentWords]}
                theme={dark}
                fallback="tag-cloud"
              />
            </ScreenPanel>
            <ScreenPanel title="实时告警" fullHeight className="flex-[1.2]">
              <ScreenAlertTicker rows={[...ds03AlertRows]} mode="scroll" theme={dark} maxHeight={160} />
            </ScreenPanel>
          </>
        }
        bottomTable={
          <ScreenPanel title="发现问题及整改数据" fullHeight className="h-full">
            <ScreenDataTable
              columns={[
                { key: "seq", title: "序号", width: "8%" },
                { key: "type", title: "问题类型", width: "14%" },
                { key: "location", title: "发现地点", width: "18%" },
                { key: "unit", title: "责任单位", width: "14%" },
                { key: "foundAt", title: "发现时间", width: "18%" },
                { key: "status", title: "整改状态", width: "14%" },
                { key: "progress", title: "整改进度", width: "14%" },
              ]}
              rows={ds03IssueRows.map((row) => ({
                ...row,
                status: (
                  <span
                    className={
                      row.status === "已完成" || row.status === "已闭环"
                        ? "text-emerald-400"
                        : row.status === "整改中"
                          ? "text-amber-400"
                          : "text-cyan-300"
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

export default SmartCitySupervisionScreen;
