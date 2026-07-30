import { Check, ClipboardCheck, ExternalLink, MessageSquareText, ShieldAlert, X } from "lucide-react";
import { Link } from "react-router";
import type { ApprovalRequest, ExternalInputRequest } from "@/api/types";
import { SchemaForm } from "@/components/operations/schema-form";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { StatusBadge } from "@/components/ui/status-badge";

interface ApprovalGuide {
  title: string;
  summary: string;
  steps: string[];
  checklist: string[];
  approveLabel: string;
}

const APPROVAL_GUIDES: Record<string, ApprovalGuide> = {
  "publish-review": {
    title: "合同履约计划 · 发布审批",
    summary: "系统已生成候选履约计划。你需要核对材料后决定是否发布；批准后流程会继续，拒绝会使当前运行失败。",
    steps: [
      "打开运行详情，查看候选计划、证据定位、冲突和甘特基准",
      "确认没有明显错误或不可接受的冲突",
      "可选填写意见，然后批准发布或拒绝",
    ],
    checklist: ["候选履约计划", "证据定位与来源", "冲突与缺口", "甘特基准时间线"],
    approveLabel: "批准并发布",
  },
};

const DEFAULT_APPROVAL_GUIDE: ApprovalGuide = {
  title: "需要你审批",
  summary: "当前运行停在人工审批节点。请先查看运行详情中的上下文，再决定批准或拒绝。",
  steps: [
    "打开运行详情，了解为什么需要你审批",
    "核对相关结果或材料",
    "可选填写意见，然后批准继续或拒绝终止",
  ],
  checklist: [],
  approveLabel: "批准并继续",
};

export function resolveApprovalGuide(nodeKey: string, prompt: string): ApprovalGuide {
  const known = APPROVAL_GUIDES[nodeKey];
  if (known) return known;
  return {
    ...DEFAULT_APPROVAL_GUIDE,
    summary: prompt.trim() || DEFAULT_APPROVAL_GUIDE.summary,
  };
}

export function HumanApprovalCard({
  request,
  runPath,
  busy,
  onApprove,
  onReject,
  showRunLink = true,
}: {
  request: ApprovalRequest;
  runPath: string;
  busy: boolean;
  onApprove: (value: Record<string, unknown>) => void;
  onReject: () => void;
  showRunLink?: boolean;
}) {
  const guide = resolveApprovalGuide(request.nodeKey, request.prompt);
  const canReject = request.allowedActions.includes("reject");
  const commandPending = request.status === "PENDING" && Boolean(request.handledBy);

  return <Card className="min-w-0 overflow-hidden">
    <div className="h-1.5 bg-linear-to-r from-warning-400 via-brand-400 to-brand-600" aria-hidden />
    <CardHeader className="items-start">
      <div className="min-w-0 space-y-2">
        <div className="flex flex-wrap items-center gap-2">
          <span className="grid size-9 place-items-center rounded-xl bg-warning-50 text-warning-600 dark:bg-warning-500/15">
            <ShieldAlert aria-hidden className="size-4.5" />
          </span>
          <div className="min-w-0">
            <CardTitle className="text-lg">{guide.title}</CardTitle>
            <p className="mt-0.5 text-xs text-gray-500">
              节点 <span className="font-mono">{request.nodeKey}</span>
              <span className="mx-1.5 text-gray-300">·</span>
              运行 <span className="font-mono">{shortId(request.runId)}</span>
            </p>
          </div>
        </div>
      </div>
      <div className="flex shrink-0 items-center gap-2">
        <StatusBadge status={request.status} />
      </div>
    </CardHeader>
    <CardContent className="space-y-5">
      <p className="text-sm leading-6 text-gray-700 dark:text-gray-300">{guide.summary}</p>

      {commandPending ? (
        <div role="status" className="rounded-2xl border border-warning-200 bg-warning-50/80 px-4 py-3 text-sm text-warning-800 dark:border-warning-500/30 dark:bg-warning-500/10 dark:text-warning-200">
          批准/拒绝命令已受理，正在等待执行引擎落地。请稍候，列表会自动刷新。
        </div>
      ) : null}

      <section aria-labelledby={`approval-steps-${request.approvalId}`} className="rounded-2xl border border-brand-100 bg-brand-50/60 p-4 dark:border-brand-500/20 dark:bg-brand-500/10">
        <h3 id={`approval-steps-${request.approvalId}`} className="text-sm font-semibold text-brand-700 dark:text-brand-300">你需要做什么</h3>
        <ol className="mt-3 space-y-2">
          {guide.steps.map((step, index) => (
            <li key={step} className="flex gap-3 text-sm text-gray-700 dark:text-gray-300">
              <span className="mt-0.5 grid size-5 shrink-0 place-items-center rounded-full bg-white text-[11px] font-semibold text-brand-600 shadow-theme-xs dark:bg-gray-900 dark:text-brand-300">{index + 1}</span>
              <span className="leading-5">{step}</span>
            </li>
          ))}
        </ol>
      </section>

      {guide.checklist.length ? (
        <section aria-labelledby={`approval-check-${request.approvalId}`} className="rounded-2xl border border-gray-200 bg-gray-50/80 p-4 dark:border-gray-800 dark:bg-white/[0.03]">
          <h3 id={`approval-check-${request.approvalId}`} className="flex items-center gap-2 text-sm font-semibold text-gray-900 dark:text-white">
            <ClipboardCheck aria-hidden className="size-4 text-gray-500" />
            发布前请核对
          </h3>
          <ul className="mt-3 grid gap-2 sm:grid-cols-2">
            {guide.checklist.map((item) => (
              <li key={item} className="flex items-start gap-2 rounded-xl bg-white px-3 py-2 text-sm text-gray-700 shadow-theme-xs dark:bg-gray-900 dark:text-gray-300">
                <span className="mt-1 size-1.5 shrink-0 rounded-full bg-brand-500" aria-hidden />
                {item}
              </li>
            ))}
          </ul>
          {request.prompt ? <p className="mt-3 text-xs leading-5 text-gray-500">{request.prompt}</p> : null}
        </section>
      ) : request.prompt && request.prompt !== guide.summary ? (
        <p className="rounded-xl border border-gray-200 bg-gray-50/80 px-3 py-2 text-sm text-gray-600 dark:border-gray-800 dark:bg-white/[0.03] dark:text-gray-300">{request.prompt}</p>
      ) : null}

      {showRunLink ? (
        <Button asChild variant="outline" className="w-full sm:w-auto">
          <Link to={runPath}>
            <ExternalLink />
            打开运行详情核对
          </Link>
        </Button>
      ) : null}

      <div className="border-t border-gray-100 pt-4 dark:border-gray-800">
        <p className="mb-3 text-sm font-medium text-gray-900 dark:text-white">做出决定</p>
        <SchemaForm
          schema={request.inputSchema}
          omitKeys={["approved"]}
          submitLabel={guide.approveLabel}
          busy={busy || commandPending}
          icon={<Check />}
          onSubmit={(value) => onApprove({ ...value, approved: true })}
          footer={canReject ? (
            <Button type="button" variant="destructive" disabled={busy || commandPending} onClick={onReject}>
              <X />
              拒绝
            </Button>
          ) : null}
        />
        <p className="mt-3 text-xs leading-5 text-gray-500">
          点「{guide.approveLabel}」即表示你已核对并同意继续；点「拒绝」会使等待中的任务失败。
        </p>
      </div>
    </CardContent>
  </Card>;
}

export function HumanInputCard({
  request,
  runPath,
  busy,
  onSubmit,
}: {
  request: ExternalInputRequest;
  runPath: string;
  busy: boolean;
  onSubmit: (value: Record<string, unknown>) => void;
}) {
  return <Card className="min-w-0 overflow-hidden">
    <div className="h-1.5 bg-linear-to-r from-brand-400 to-brand-600" aria-hidden />
    <CardHeader className="items-start">
      <div className="min-w-0 space-y-2">
        <div className="flex flex-wrap items-center gap-2">
          <span className="grid size-9 place-items-center rounded-xl bg-brand-50 text-brand-600 dark:bg-brand-500/15">
            <MessageSquareText aria-hidden className="size-4.5" />
          </span>
          <div className="min-w-0">
            <CardTitle className="text-lg">需要你补充信息</CardTitle>
            <p className="mt-0.5 text-xs text-gray-500">
              节点 <span className="font-mono">{request.nodeKey}</span>
              <span className="mx-1.5 text-gray-300">·</span>
              运行 <span className="font-mono">{shortId(request.runId)}</span>
            </p>
          </div>
        </div>
      </div>
      <StatusBadge status={request.status} />
    </CardHeader>
    <CardContent className="space-y-5">
      <section className="rounded-2xl border border-brand-100 bg-brand-50/60 p-4 dark:border-brand-500/20 dark:bg-brand-500/10">
        <h3 className="text-sm font-semibold text-brand-700 dark:text-brand-300">你需要做什么</h3>
        <ol className="mt-3 space-y-2 text-sm text-gray-700 dark:text-gray-300">
          <li className="flex gap-3"><span className="mt-0.5 grid size-5 shrink-0 place-items-center rounded-full bg-white text-[11px] font-semibold text-brand-600 shadow-theme-xs dark:bg-gray-900">1</span><span>打开运行详情，了解系统在等什么信息</span></li>
          <li className="flex gap-3"><span className="mt-0.5 grid size-5 shrink-0 place-items-center rounded-full bg-white text-[11px] font-semibold text-brand-600 shadow-theme-xs dark:bg-gray-900">2</span><span>按下方表单补齐必填项</span></li>
          <li className="flex gap-3"><span className="mt-0.5 grid size-5 shrink-0 place-items-center rounded-full bg-white text-[11px] font-semibold text-brand-600 shadow-theme-xs dark:bg-gray-900">3</span><span>提交后运行会继续执行</span></li>
        </ol>
      </section>
      {request.prompt ? <p className="text-sm leading-6 text-gray-700 dark:text-gray-300">{request.prompt}</p> : null}
      <Button asChild variant="outline" className="w-full sm:w-auto">
        <Link to={runPath}><ExternalLink />打开运行详情</Link>
      </Button>
      <div className="border-t border-gray-100 pt-4 dark:border-gray-800">
        <SchemaForm schema={request.inputSchema} submitLabel="提交信息" busy={busy} icon={<MessageSquareText />} onSubmit={onSubmit} />
      </div>
    </CardContent>
  </Card>;
}

function shortId(value: string): string {
  return value.length > 12 ? `${value.slice(0, 8)}…` : value;
}
