import * as React from "react";
import { Badge } from "@/components/ui/badge";
import { Timeline, type TimelineItem } from "@/components/ui/timeline";

export type ApprovalStatus = "pending" | "approved" | "rejected";

export type ApprovalEvent = {
  id: string;
  actor: string;
  role?: string;
  status: ApprovalStatus;
  timestamp?: string;
  reason?: string;
};

export type ApprovalTimelineProps = {
  events: ApprovalEvent[];
  className?: string;
};

const statusColor: Record<ApprovalStatus, "warning" | "success" | "error"> = {
  pending: "warning",
  approved: "success",
  rejected: "error",
};

const statusToTimeline: Record<
  ApprovalStatus,
  NonNullable<TimelineItem["status"]>
> = {
  approved: "success",
  rejected: "error",
  pending: "pending",
};

/**
 * Release approval timeline — pending/approved/rejected with actor, time, reason.
 * @see references/layout-patterns/cicd-release.md
 */
export function ApprovalTimeline({ events, className }: ApprovalTimelineProps) {
  const items: TimelineItem[] = events.map((event) => ({
    id: event.id,
    title: (
      <div className="flex flex-wrap items-center gap-2">
        <span>{event.actor}</span>
        {event.role ? (
          <span className="text-theme-xs font-normal text-gray-500">{event.role}</span>
        ) : null}
        <Badge variant="light" color={statusColor[event.status]} size="sm">
          {event.status}
        </Badge>
      </div>
    ),
    description: event.reason ? (
      <p className="rounded-lg bg-gray-50 px-3 py-2 text-theme-sm text-gray-600 dark:bg-white/[0.03] dark:text-gray-400">
        {event.reason}
      </p>
    ) : undefined,
    timestamp: event.timestamp,
    status: statusToTimeline[event.status],
  }));

  return (
    <Timeline items={items} size="sm" className={className} ariaLabel="审批时间线" />
  );
}
