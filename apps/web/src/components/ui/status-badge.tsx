import { Badge, type BadgeProps } from "./badge";

const success = new Set(["SUCCEEDED", "APPLIED", "COMPLETED"]);
const error = new Set(["FAILED", "CANCELLED", "REJECTED", "TIMED_OUT", "DEAD"]);
const warning = new Set(["WAITING_INPUT", "WAITING_APPROVAL", "PAUSING", "CANCELLING", "PENDING"]);

export function statusColor(status: string): BadgeProps["color"] {
  if (success.has(status)) return "success";
  if (error.has(status)) return "error";
  if (warning.has(status)) return "warning";
  if (status === "RUNNING" || status === "QUEUED") return "primary";
  return "neutral";
}
export function StatusBadge({ status }: { status: string }) { return <Badge color={statusColor(status)}>{status.replaceAll("_", " ")}</Badge>; }
