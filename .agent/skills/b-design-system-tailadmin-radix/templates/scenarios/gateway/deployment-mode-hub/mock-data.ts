import type { DeploymentMode, DeploymentModeOption } from "../../../gateway/deployment-mode-matrix";
import { Cloud, CloudOff, HardDrive, Lock, Server } from "lucide-react";
import * as React from "react";

export const deploymentModeHubTabs = [
  { id: "mode", label: "部署模式" },
  { id: "sync", label: "同步策略" },
  { id: "connectivity", label: "连通性说明" },
] as const;

export type DeploymentModeHubTabId = (typeof deploymentModeHubTabs)[number]["id"];

export const deploymentModeOptions: DeploymentModeOption[] = [
  {
    id: "connected",
    label: "联网模式",
    description: "与集中控制面同步配额、报表与心跳。",
    icon: React.createElement(Cloud, { className: "size-4" }),
  },
  {
    id: "airgap",
    label: "离线隔离",
    description: "零出站流量，仅支持本地 License 验签。",
    icon: React.createElement(CloudOff, { className: "size-4" }),
  },
  {
    id: "local",
    label: "本地部署",
    description: "单机或边缘节点，端点本地托管。",
    icon: React.createElement(HardDrive, { className: "size-4" }),
  },
  {
    id: "cloud",
    label: "公有云",
    description: "控制面托管于公有云环境。",
    icon: React.createElement(Server, { className: "size-4" }),
  },
  {
    id: "private",
    label: "私有云",
    description: "控制面位于私有 VPC，出站受限。",
    icon: React.createElement(Lock, { className: "size-4" }),
  },
];

export type SyncPolicyRow = {
  id: string;
  label: string;
  description: string;
  enabledModes: DeploymentMode[];
  interval: string;
};

export const syncPolicyRows: SyncPolicyRow[] = [
  {
    id: "quota",
    label: "配额同步",
    description: "从集中端拉取企业池配额与余量。",
    enabledModes: ["connected", "cloud", "private"],
    interval: "每 30 秒",
  },
  {
    id: "report",
    label: "报表同步",
    description: "上报调用量与计费明细至集中端。",
    enabledModes: ["connected", "cloud"],
    interval: "每小时",
  },
  {
    id: "hmac",
    label: "HMAC 心跳",
    description: "维持与控制面的双向认证心跳。",
    enabledModes: ["connected", "cloud", "private"],
    interval: "每 60 秒",
  },
  {
    id: "license",
    label: "许可校验",
    description: "在线或离线校验 License 有效期。",
    enabledModes: ["connected", "airgap", "local", "cloud", "private"],
    interval: "每日",
  },
];

export type ConnectivityRule = {
  id: string;
  direction: "出站" | "入站" | "双向";
  target: string;
  port: string;
  required: boolean;
  note?: string;
};

export const connectivityRules: ConnectivityRule[] = [
  {
    id: "cp-api",
    direction: "出站",
    target: "control.prod.internal",
    port: "443",
    required: true,
    note: "联网模式必需；离线模式可关闭",
  },
  {
    id: "ntp",
    direction: "出站",
    target: "ntp.corp.internal",
    port: "123",
    required: false,
    note: "建议配置以保证心跳时间一致",
  },
  {
    id: "gateway-api",
    direction: "入站",
    target: "业务子网",
    port: "8443",
    required: true,
    note: "业务系统调用网关 API",
  },
  {
    id: "probe",
    direction: "双向",
    target: "已注册端点",
    port: "443",
    required: true,
    note: "端点探测 debounce 300ms",
  },
];

export const defaultDeploymentMode: DeploymentMode = "connected";
