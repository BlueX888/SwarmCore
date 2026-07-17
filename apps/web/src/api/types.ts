export interface TaskSnapshot {
  taskId: string;
  nodeKey: string;
  nodeType: string;
  status: string;
  dependencies: string[];
  error?: Record<string, unknown> | null;
  output?: Record<string, unknown> | null;
  retryGeneration: number;
  allowedActions: string[];
}

export interface Diagnostic { severity: "error" | "warning"; code: string; path: string; message: string; }
export interface CompileResponse { valid: boolean; plan: Record<string, unknown> | null; diagnostics: Diagnostic[]; }
export interface EditorState {
  positions: Record<string, { x: number; y: number }>;
  viewport: { x: number; y: number; zoom: number };
}
export interface AgentCapability {
  id: string;
  runtime: string;
  environments: string[];
  declarationSchema: Record<string, unknown>;
}
export interface ToolCapability {
  ref: string;
  risk: string;
  inputSchema: Record<string, unknown>;
  outputSchema: Record<string, unknown>;
}
export interface ModelCapability {
  ref: string;
  runtime: string;
  environments: string[];
}
export interface CapabilityCatalog {
  schemaVersion: string;
  registrySnapshot: string;
  nodeTypes: Array<{ type: string; schema: Record<string, unknown> }>;
  agents: AgentCapability[];
  tools: ToolCapability[];
  models: ModelCapability[];
  limits: Record<string, unknown>;
  swarmSpecSchema: Record<string, unknown>;
}
export type ConfigurationKind = "agent" | "tool" | "model";
export interface SavedConfiguration {
  configurationId: string;
  kind: ConfigurationKind;
  name: string;
  sourceRef: string;
  configuration: Record<string, unknown>;
  revision: number;
  createdBy: string;
  updatedBy: string;
  createdAt: string;
  updatedAt: string;
}
export interface SavedConfigurationListResponse { items: SavedConfiguration[]; total: number; }
export interface CreateSavedConfiguration {
  name: string;
  sourceRef: string;
  configuration: Record<string, unknown>;
}
export interface StrategySummary {
  strategyId: string; name: string; lifecycle: string; createdAt: string; updatedAt: string;
  draftId: string | null; draftRevision: number | null; latestVersion: number | null;
}
export interface StrategyListResponse { items: StrategySummary[]; total: number; }
export interface DraftSnapshot {
  draftId: string; strategyId: string; revision: number; spec: Record<string, unknown>;
  editorState: EditorState;
  diagnostics: Diagnostic[]; updatedBy: string; updatedAt: string;
}
export interface StrategyVersionSummary {
  strategyVersionId: string; strategyId: string; version: number; lifecycle: string;
  planHash: string; schemaVersion: string; runtimeVersion: string; createdAt: string;
}
export interface StrategyVersionListResponse { items: StrategyVersionSummary[]; total: number; }
export interface StrategyVersionDetail extends StrategyVersionSummary {
  spec: Record<string, unknown>; normalizedSpec: Record<string, unknown>; plan: Record<string, unknown>;
}
export interface StrategyHandle { strategyId: string; draftId: string; revision: number; }
export interface RunHandle { runId: string; status: string; commandId: string; commandStatus: string; planHash: string; }

export interface RunSnapshot {
  runId: string;
  status: string;
  input: Record<string, unknown>;
  output: Record<string, unknown> | null;
  outputRef: string | null;
  snapshotSeq: number;
  earliestAvailableSeq: number;
  planHash: string;
  usage: Record<string, unknown>;
  taskCounts: Record<string, number>;
  allowedActions: string[];
  tasks: TaskSnapshot[];
  startedAt?: string | null;
  completedAt?: string | null;
}

export interface RunListResponse { items: RunSnapshot[]; total: number; }
export interface CommandHandle {
  commandId: string; requestId: string; commandSeq: number; status: string;
  result?: Record<string, unknown> | null; error?: Record<string, unknown> | null;
  createdAt?: string | null; appliedAt?: string | null; rejectedAt?: string | null;
}
export interface ApprovalRequest {
  approvalId: string; runId: string; nodeKey: string; prompt: string;
  inputSchema: Record<string, unknown>; status: string; allowedActions: string[];
  requestedBy: string; handledBy: string | null; createdAt: string; handledAt: string | null;
}
export interface ApprovalListResponse { items: ApprovalRequest[]; total: number; }
export interface ExternalInputRequest {
  inputRequestId: string; runId: string; nodeKey: string; prompt: string;
  inputSchema: Record<string, unknown>; status: string; allowedActions: string[];
  requestedBy: string; handledBy: string | null; createdAt: string; handledAt: string | null;
}
export interface ExternalInputListResponse { items: ExternalInputRequest[]; total: number; }
export interface AuditSnapshot {
  auditId: string;
  actorId: string;
  action: string;
  resourceType: string;
  resourceId: string;
  outcome: string;
  policyRevision: string | null;
  runId: string | null;
  metadata: Record<string, unknown>;
  occurredAt: string;
}
export interface AuditListResponse { items: AuditSnapshot[]; total: number; }
export interface RunEvent {
  id: string;
  seq: number;
  type: string;
  schemaVersion: string;
  runId: string;
  taskId: string | null;
  attemptId: string | null;
  occurredAt: string;
  redacted: boolean;
  data: Record<string, unknown>;
}
export interface EventHistory { items: RunEvent[]; nextAfter: number; }
export type ConnectionState = "CONNECTING" | "OPEN" | "RECONNECTING" | "STALE" | "CLOSED" | "ERROR";
