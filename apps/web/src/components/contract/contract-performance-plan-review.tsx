import { AlertTriangle, CalendarRange, FileSearch, History } from "lucide-react";
import type { TaskSnapshot } from "@/api/types";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";

const PLAN_SCHEMA = "schema://contract-performance/plan@1";

export interface ContractPerformancePlanReview {
  plan: Record<string, unknown>;
  originalPlan: Record<string, unknown> | null;
  differences: Record<string, unknown>[];
  schedule: Record<string, unknown> | null;
  unapprovedChangeRisks: Record<string, unknown>[];
}

export function contractPerformancePlanReviewFromTasks(
  tasks: TaskSnapshot[],
): ContractPerformancePlanReview | null {
  const applied = contentOf(tasks.find((task) => task.nodeKey === "apply-changes"));
  const plan = recordField(applied, "currentBaseline");
  if (!plan || textField(plan, "schemaVersion") !== PLAN_SCHEMA) return null;
  return {
    plan,
    originalPlan: recordField(applied, "originalBaseline"),
    differences: recordItems(applied, "differences"),
    schedule: contentOf(tasks.find((task) => task.nodeKey === "build-schedule")),
    unapprovedChangeRisks: recordItems(applied, "unapprovedChangeRisks"),
  };
}

export function ContractPerformancePlanReviewView({
  review,
}: {
  review: ContractPerformancePlanReview;
}) {
  const { plan, originalPlan, differences, schedule, unapprovedChangeRisks } = review;
  const contract = recordField(plan, "contract");
  const originalContract = recordField(originalPlan, "contract");
  const milestones = recordItems(plan, "milestones");
  const originalMilestones = recordItems(originalPlan, "milestones");
  const payments = recordItems(plan, "paymentConditions");
  const conflicts = recordItems(plan, "conflicts");
  const gaps = recordItems(plan, "gaps");
  const evidenceCount = milestones.reduce(
    (total, milestone) => total + recordItems(milestone, "evidenceRefs").length,
    0,
  );
  const contractTotal = numberField(contract, "totalAmount");
  const paymentTotal = payments.reduce(
    (total, item) => total + paymentAmount(item, contractTotal),
    0,
  );
  const currency = textField(contract, "currency", "CNY");
  const alerts = [...conflicts, ...gaps, ...unapprovedChangeRisks];
  const scheduleQuality = recordField(schedule, "quality");
  const meaningfulDifferences = differences.filter(
    (item) => !sameValue(item["before"], item["after"]),
  );
  const approvedChanges = recordItems(plan, "changes").filter(
    (item) => textField(item, "status").toUpperCase() === "APPROVED",
  );

  return (
    <section aria-labelledby="contract-plan-review-title" className="space-y-4">
      <Card>
        <CardHeader>
          <div>
            <CardTitle id="contract-plan-review-title">发布前候选履约计划</CardTitle>
            <p className="mt-1 text-sm text-gray-500">
              核对合同基准、原文证据、批准变更和排期质量后再处理发布审批。
            </p>
          </div>
          <Badge color={alerts.length ? "warning" : "success"}>
            {textField(plan, "status", "CANDIDATE")}
          </Badge>
        </CardHeader>
        <CardContent className="space-y-5">
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <Metric label="合同总额" value={money(contractTotal, currency)} />
            <Metric
              label="付款计划合计"
              value={money(paymentTotal, currency)}
              warning={paymentTotal !== contractTotal}
            />
            <Metric label="里程碑 / 证据" value={`${milestones.length} / ${evidenceCount}`} />
            <Metric
              label="排期质量"
              value={textField(
                scheduleQuality,
                "status",
                textField(schedule, "quality", textField(schedule, "mode", "待生成")),
              )}
            />
          </div>

          {alerts.length ? (
            <div role="alert" className="rounded-xl border border-warning-300 bg-warning-50 p-4 dark:bg-warning-500/10">
              <div className="flex items-center gap-2 font-medium text-warning-700">
                <AlertTriangle className="size-4" />
                发布前需人工确认 {alerts.length} 项
              </div>
              <div className="mt-3 grid gap-2 md:grid-cols-2">
                {alerts.map((item, index) => (
                  <div key={`${textField(item, "code", "RISK")}-${index}`} className="rounded-lg bg-white/70 p-3 text-xs text-gray-700 dark:bg-black/10 dark:text-gray-200">
                    <p className="font-semibold">{textField(item, "code", "UNAPPROVED_CHANGE")}</p>
                    <p className="mt-1 break-words">{alertDetail(item)}</p>
                  </div>
                ))}
              </div>
            </div>
          ) : null}

          <div>
            <h3 className="flex items-center gap-2 font-medium text-gray-900 dark:text-white">
              <CalendarRange className="size-4 text-brand-500" />
              里程碑与证据定位
            </h3>
            <div className="mt-3 space-y-3">
              {milestones.length ? milestones.map((item, index) => {
                const milestoneId = textField(item, "id", `M${index + 1}`);
                const original = originalMilestones.find(
                  (candidate) => textField(candidate, "id") === milestoneId,
                );
                const evidence = recordItems(item, "evidenceRefs")[0];
                return (
                  <div key={milestoneId} className="rounded-xl border border-gray-200 p-4 dark:border-gray-800">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <p className="font-medium text-gray-900 dark:text-white">
                          {milestoneId} · {textField(item, "name", textField(item, "title", "未命名里程碑"))}
                        </p>
                        <p className="mt-1 text-xs text-gray-500">
                          截止 {textField(item, "dueDate", "待确认")}
                          {original && textField(original, "dueDate") !== textField(item, "dueDate")
                            ? `（原 ${textField(original, "dueDate")}）`
                            : ""}
                          {" · "}依赖 {stringItems(item, "dependencies").join("、") || "无"}
                        </p>
                      </div>
                      <Badge color={evidence ? "primary" : "warning"}>{evidence ? "有原文证据" : "待补证据"}</Badge>
                    </div>
                    {evidence ? (
                      <p className="mt-3 flex items-start gap-2 rounded-lg bg-gray-50 p-3 text-xs text-gray-600 dark:bg-white/[0.04] dark:text-gray-300">
                        <FileSearch className="mt-0.5 size-4 shrink-0" />
                        <span>{evidenceLocation(evidence)}</span>
                      </p>
                    ) : null}
                  </div>
                );
              }) : <EmptyState compact title="尚未生成里程碑" />}
            </div>
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            <div>
              <h3 className="font-medium text-gray-900 dark:text-white">付款条件</h3>
              <div className="mt-3 space-y-2">
                {payments.map((item, index) => (
                  <div key={textField(item, "id", `${index}`)} className="flex items-center justify-between rounded-xl border border-gray-200 p-3 text-sm dark:border-gray-800">
                    <span>{textField(item, "name", textField(item, "title", textField(item, "condition", `第 ${index + 1} 笔`)))}</span>
                    <span className="font-mono">{paymentDisplay(item, contractTotal, currency)}</span>
                  </div>
                ))}
              </div>
            </div>
            <div>
              <h3 className="flex items-center gap-2 font-medium text-gray-900 dark:text-white">
                <History className="size-4 text-brand-500" />
                已批准变更
              </h3>
              <div className="mt-3 space-y-2">
                {meaningfulDifferences.length ? meaningfulDifferences.map((item, index) => (
                  <div key={`${textField(item, "path", "change")}-${index}`} className="rounded-xl border border-gray-200 p-3 text-xs dark:border-gray-800">
                    <p className="font-mono font-semibold">{textField(item, "path", "变更")}</p>
                    <p className="mt-1 text-gray-500">
                      {display(item["before"])} → {display(item["after"])}
                    </p>
                  </div>
                )) : approvedChanges.length ? approvedChanges.map((item, index) => (
                  <div key={textField(item, "id", `${index}`)} className="rounded-xl border border-gray-200 p-3 text-xs dark:border-gray-800">
                    <p className="font-semibold">{textField(item, "title", textField(item, "id", "批准变更"))}</p>
                    <p className="mt-1 text-gray-500">已包含在候选基准 · 生效日 {textField(item, "effectiveAt", "未注明")}</p>
                  </div>
                )) : <EmptyState compact title="当前基准没有已批准变更" />}
              </div>
            </div>
          </div>

          <p className="text-xs text-gray-400">
            合同：{textField(contract, "contractNumber", "—")}
            {numberField(originalContract, "totalAmount")
              ? ` · 原合同总额 ${money(numberField(originalContract, "totalAmount"), currency)}`
              : ""}
          </p>
        </CardContent>
      </Card>
    </section>
  );
}

function contentOf(task: TaskSnapshot | undefined): Record<string, unknown> | null {
  return recordField(task?.output ?? null, "content");
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value && typeof value === "object" && !Array.isArray(value));
}

function recordField(value: unknown, key: string): Record<string, unknown> | null {
  if (!isRecord(value)) return null;
  const field = value[key];
  return isRecord(field) ? field : null;
}

function recordItems(value: unknown, key: string): Record<string, unknown>[] {
  if (!isRecord(value) || !Array.isArray(value[key])) return [];
  return value[key].filter(isRecord);
}

function stringItems(value: unknown, key: string): string[] {
  if (!isRecord(value) || !Array.isArray(value[key])) return [];
  return value[key].filter((item): item is string => typeof item === "string");
}

function textField(value: unknown, key: string, fallback = ""): string {
  if (!isRecord(value)) return fallback;
  const field = value[key];
  return typeof field === "string" && field ? field : fallback;
}

function numberField(value: unknown, key: string): number {
  if (!isRecord(value)) return 0;
  const field = value[key];
  return typeof field === "number" && Number.isFinite(field) ? field : 0;
}

function money(value: number, currency: string): string {
  return `${currency} ${value.toLocaleString("zh-CN", { maximumFractionDigits: 2 })}`;
}

function optionalNumberField(value: unknown, key: string): number | null {
  if (!isRecord(value)) return null;
  const field = value[key];
  return typeof field === "number" && Number.isFinite(field) ? field : null;
}

function normalizedRate(item: Record<string, unknown>): number | null {
  const rate = optionalNumberField(item, "rate");
  if (rate === null) return null;
  return rate > 1 ? rate / 100 : rate;
}

function paymentAmount(item: Record<string, unknown>, contractTotal: number): number {
  const amount = optionalNumberField(item, "amount");
  if (amount !== null) return amount;
  const rate = normalizedRate(item);
  return rate === null ? 0 : contractTotal * rate;
}

function paymentDisplay(
  item: Record<string, unknown>,
  contractTotal: number,
  currency: string,
): string {
  const rate = normalizedRate(item);
  const amount = money(paymentAmount(item, contractTotal), currency);
  return rate === null ? amount : `${amount} · ${(rate * 100).toLocaleString("zh-CN")}%`;
}

function sameValue(left: unknown, right: unknown): boolean {
  if (Object.is(left, right)) return true;
  if (typeof left === "object" && left !== null && typeof right === "object" && right !== null) {
    return JSON.stringify(left) === JSON.stringify(right);
  }
  return false;
}

function display(value: unknown): string {
  if (value === null || value === undefined || value === "") return "—";
  if (typeof value === "string") return value;
  if (typeof value === "number" || typeof value === "boolean" || typeof value === "bigint") {
    return `${value}`;
  }
  if (typeof value === "object") return JSON.stringify(value);
  return "—";
}

function alertDetail(item: Record<string, unknown>): string {
  if (textField(item, "code") === "PAYMENT_TOTAL_MISMATCH") {
    return `合同总额 ${display(item["contractTotal"])}，付款计划 ${display(item["paymentTotal"])}，差额 ${display(item["difference"])}。`;
  }
  return textField(item, "message", display(item));
}

function evidenceLocation(item: Record<string, unknown>): string {
  const location = recordField(item, "location");
  const page = numberField(item, "page") || numberField(location, "page");
  const excerpt = textField(item, "text", textField(item, "excerpt"));
  return [
    textField(item, "documentVersionId", textField(item, "sourceId", "合同原文")),
    page ? `第 ${page} 页` : "",
    excerpt,
  ].filter(Boolean).join(" · ");
}

function Metric({
  label,
  value,
  warning = false,
}: {
  label: string;
  value: string;
  warning?: boolean;
}) {
  return (
    <div className="rounded-xl bg-gray-50 p-4 dark:bg-white/[0.04]">
      <p className="text-xs text-gray-500">{label}</p>
      <p className={`mt-1 font-semibold ${warning ? "text-warning-600" : "text-gray-900 dark:text-white"}`}>
        {value}
      </p>
    </div>
  );
}
