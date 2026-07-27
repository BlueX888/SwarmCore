const statusLabels: Record<string, string> = {
  ACCEPTED: "已受理",
  ALLOWED: "已允许",
  APPLIED: "已执行",
  AVAILABLE: "可用",
  CANCELLING: "取消中",
  CANCELLED: "已取消",
  CLOSED: "已关闭",
  COMPENSATING: "补偿中",
  COMPLETED: "已完成",
  CONNECTING: "连接中",
  CREATED: "已创建",
  DEAD: "已失效",
  DELIVERING: "投递中",
  DENIED: "已拒绝",
  ERROR: "错误",
  FAILED: "失败",
  OPEN: "已连接",
  PAUSED: "已暂停",
  PAUSING: "暂停中",
  PENDING: "待处理",
  QUEUED: "排队中",
  RECONNECTING: "重连中",
  REJECTED: "已拒绝",
  RUNNING: "运行中",
  STALE: "已过期",
  SUCCEEDED: "成功",
  TIMED_OUT: "已超时",
  VALIDATING: "校验中",
  WAITING_APPROVAL: "等待审批",
  WAITING_INPUT: "等待输入",
};

const nodeTypeLabels: Record<string, string> = {
  agent: "智能体",
  approval: "审批",
  input: "外部输入",
  join: "汇合",
  parallel: "并行",
  reducer: "归并",
  tool: "工具",
};

const auditActionLabels: Record<string, string> = {
  "artifact.download.issue": "签发产物下载授权",
  "artifact.read": "读取产物",
  "artifact.upload": "上传产物",
  "model.invoke": "调用模型",
  "policy.deny": "策略拒绝",
  "run.create": "创建运行",
  "sandbox.execute": "执行沙箱",
  "sandbox.reconcile": "协调沙箱",
  "secret.read": "读取密钥",
  "strategy.create": "创建策略",
  "strategy.publish": "发布策略",
  "strategy.update": "更新策略",
  "tool.compensate": "补偿工具调用",
  "tool.execute": "执行工具",
  "webhook.create": "创建 Webhook",
  "webhook.deliver": "投递 Webhook",
};

const resourceTypeLabels: Record<string, string> = {
  api_route: "API 路由",
  artifact: "产物",
  mcp_tool: "MCP 工具",
  model: "模型",
  run: "运行",
  sandbox_execution: "沙箱执行",
  strategy: "策略",
  webhook_endpoint: "Webhook 端点",
};

const eventTypeLabels: Record<string, string> = {
  "approval.approved": "审批已通过",
  "approval.rejected": "审批已拒绝",
  "input.received": "已收到外部输入",
  "run.accepted": "运行已受理",
  "run.cancelled": "运行已取消",
  "run.cancelling": "运行取消中",
  "run.completed": "运行已完成",
  "run.failed": "运行失败",
  "run.pause_requested": "已请求暂停运行",
  "run.pausing": "运行暂停中",
  "run.queued": "运行已排队",
  "run.resume_requested": "已请求继续运行",
  "run.resumed": "运行已继续",
  "run.started": "运行已开始",
  "run.validating": "正在校验运行",
  "run.waiting_approval": "运行等待审批",
  "run.waiting_input": "运行等待输入",
  "task.cancelled": "任务已取消",
  "task.completed": "任务已完成",
  "task.failed": "任务失败",
  "task.retry_requested": "已请求重试任务",
  "task.retry_started": "任务重试已开始",
  "task.skipped": "任务已跳过",
  "task.started": "任务已开始",
};

export function statusLabel(status: string): string {
  return statusLabels[status] ?? status.replaceAll("_", " ");
}

export function nodeTypeLabel(type: string): string {
  return nodeTypeLabels[type] ?? type.replaceAll("_", " ");
}

export function auditActionLabel(action: string): string {
  return auditActionLabels[action] ?? action;
}

export function resourceTypeLabel(type: string): string {
  return resourceTypeLabels[type] ?? type;
}

export function eventTypeLabel(type: string): string {
  return eventTypeLabels[type] ?? type;
}
