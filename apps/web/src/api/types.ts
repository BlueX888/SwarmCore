export interface TaskSnapshot {
  taskId: string;
  nodeKey: string;
  nodeType: string;
  status: string;
  dependencies: string[];
  error?: Record<string, unknown> | null;
  output?: Record<string, unknown> | null;
}

export interface Diagnostic { severity: "error" | "warning"; code: string; path: string; message: string; }
export interface CompileResponse { valid: boolean; plan: Record<string, unknown> | null; diagnostics: Diagnostic[]; }
export interface StrategySummary {
  strategyId: string; name: string; lifecycle: string; createdAt: string; updatedAt: string;
  draftId: string | null; draftRevision: number | null; latestVersion: number | null;
}
export interface StrategyListResponse { items: StrategySummary[]; total: number; }
export interface DraftSnapshot {
  draftId: string; strategyId: string; revision: number; spec: Record<string, unknown>;
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
export interface RunHandle { runId: string; status: string; commandId: string; commandStatus: string; }

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
export interface CommandHandle { commandId: string; requestId: string; commandSeq: number; status: string; }
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
