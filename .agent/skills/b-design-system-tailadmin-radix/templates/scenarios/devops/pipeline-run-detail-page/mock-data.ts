import type { ApprovalEvent } from "../../../devops/approval-timeline";
import type { ArtifactRow } from "../../../devops/artifact-table";
import type { LogLine } from "../../../devops/log-stream-panel";
import type { PipelineStage } from "../../../devops/pipeline-stage-bar";

export type PipelineRunStatus = "running" | "success" | "failed" | "canceled";

export type PipelineRunDetailMock = {
  pipelineName: string;
  runId: string;
  status: PipelineRunStatus;
  branch: string;
  triggerBy: string;
  startedAt: string;
  duration: string;
  environment: string;
  currentVersion: string;
  targetRollbackVersion: string;
  stages: PipelineStage[];
  logsByStage: Record<string, LogLine[]>;
  artifacts: ArtifactRow[];
  approvals: ApprovalEvent[];
};

export const pipelineRunDetailMock: PipelineRunDetailMock = {
  pipelineName: "网关生产发布流水线",
  runId: "RUN-2026-06128-0042",
  status: "failed",
  branch: "release/2.8.4",
  triggerBy: "周敏",
  startedAt: "2026-06-28 14:32:08",
  duration: "18 分 42 秒",
  environment: "生产环境",
  currentVersion: "v2.8.4-build-1842",
  targetRollbackVersion: "v2.8.3-build-1836",
  stages: [
    { id: "checkout", label: "拉取代码", status: "success", duration: "42 秒" },
    { id: "test", label: "单元测试", status: "success", duration: "3 分 12 秒" },
    { id: "build", label: "构建镜像", status: "success", duration: "6 分 05 秒" },
    { id: "scan", label: "安全扫描", status: "success", duration: "2 分 18 秒" },
    { id: "canary", label: "灰度发布", status: "failed", duration: "4 分 11 秒" },
    { id: "approve", label: "生产审批", status: "skipped", duration: "—" },
    { id: "prod", label: "全量发布", status: "skipped", duration: "—" },
  ],
  logsByStage: {
    checkout: [
      { id: "c1", timestamp: "14:32:09", severity: "info", message: "检出分支 release/2.8.4（提交 a3f91c2）" },
      { id: "c2", timestamp: "14:32:18", severity: "info", message: "依赖缓存命中，跳过 npm install" },
      { id: "c3", timestamp: "14:32:42", severity: "info", message: "代码检出完成" },
    ],
    test: [
      { id: "t1", timestamp: "14:32:45", severity: "info", message: "执行单元测试套件 gateway-api / gateway-web" },
      { id: "t2", timestamp: "14:34:12", severity: "info", message: "覆盖率 87.2%，门禁通过" },
      { id: "t3", timestamp: "14:35:57", severity: "info", message: "全部 1,284 项测试通过" },
    ],
    build: [
      { id: "b1", timestamp: "14:36:01", severity: "info", message: "构建镜像 gateway-web:2.8.4-rc.42" },
      { id: "b2", timestamp: "14:39:44", severity: "info", message: "推送镜像至华东镜像仓库" },
      { id: "b3", timestamp: "14:42:06", severity: "info", message: "镜像构建完成，digest sha256:9f3a…c21d" },
    ],
    scan: [
      { id: "s1", timestamp: "14:42:10", severity: "info", message: "启动容器漏洞扫描" },
      { id: "s2", timestamp: "14:43:55", severity: "warn", message: "发现 2 个中危依赖，已记录在制品报告" },
      { id: "s3", timestamp: "14:44:28", severity: "info", message: "安全扫描通过，允许进入灰度" },
    ],
    canary: [
      { id: "y1", timestamp: "14:44:32", severity: "info", message: "灰度切流 15% → gateway-prod-cn" },
      { id: "y2", timestamp: "14:46:18", severity: "warn", message: "P95 延迟升至 820ms，超过阈值 600ms" },
      { id: "y3", timestamp: "14:47:41", severity: "error", message: "健康检查连续 3 次失败，自动中止灰度" },
      { id: "y4", timestamp: "14:48:43", severity: "error", message: "阶段失败：灰度发布回滚至上一稳定版本" },
    ],
    approve: [],
    prod: [],
  },
  artifacts: [
    {
      id: "art-1",
      name: "gateway-web.tar",
      digest: "sha256:9f3a21dc",
      size: "128 MB",
      expiresAt: "2026-07-28",
      status: "available",
      scanReportUrl: "#",
    },
    {
      id: "art-2",
      name: "api-schema.json",
      digest: "sha256:b71e44aa",
      size: "2.4 MB",
      expiresAt: "2026-07-28",
      status: "available",
    },
    {
      id: "art-3",
      name: "rollback-plan.md",
      digest: "sha256:c02d88fe",
      size: "18 KB",
      status: "scanning",
    },
  ],
  approvals: [
    {
      id: "ap-1",
      actor: "林越",
      role: "研发负责人",
      status: "approved",
      timestamp: "14:30:12",
      reason: "变更单 CHG-2026-0628 已关联，允许进入发布窗口。",
    },
    {
      id: "ap-2",
      actor: "王敏",
      role: "SRE 值班",
      status: "pending",
      timestamp: "等待中",
      reason: "灰度失败后需确认是否继续重试或执行回滚。",
    },
    {
      id: "ap-3",
      actor: "系统自动",
      role: "生产切流",
      status: "rejected",
      timestamp: "14:48:50",
      reason: "灰度健康检查未通过，全量发布已阻断。",
    },
  ],
};
