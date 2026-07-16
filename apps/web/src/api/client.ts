import type {
  ApprovalListResponse, CommandHandle, CompileResponse, DraftSnapshot, EventHistory,
  ExternalInputListResponse, RunHandle, RunListResponse, RunSnapshot, StrategyHandle,
  StrategyListResponse, StrategyVersionDetail,
  StrategyVersionListResponse,
} from "./types";

const configuredApiUrl: unknown = import.meta.env["VITE_API_URL"];
const baseUrl = typeof configuredApiUrl === "string" ? configuredApiUrl : "/api";
const temporalUi: unknown = import.meta.env["VITE_TEMPORAL_UI_URL"];
const phoenixUi: unknown = import.meta.env["VITE_PHOENIX_URL"];

export class ApiError extends Error {
  constructor(public status: number, message: string, public code?: string) { super(message); }
}

async function request<T>(path: string, tenantId: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  headers.set("Content-Type", "application/json");
  headers.set("X-Tenant-ID", tenantId);
  const response = await fetch(`${baseUrl}${path}`, {
    ...init,
    headers,
  });
  if (!response.ok) {
    const body = await response.text();
    try {
      const problem = JSON.parse(body) as { detail?: string; code?: string };
      throw new ApiError(response.status, problem.detail ?? body, problem.code);
    } catch (error) {
      if (error instanceof ApiError) throw error;
      throw new ApiError(response.status, body || response.statusText);
    }
  }
  return response.json() as Promise<T>;
}

export const api = {
  listStrategies: (tenantId: string, projectId: string) => request<StrategyListResponse>(`/v1/projects/${projectId}/strategies`, tenantId),
  createStrategy: (tenantId: string, projectId: string, name: string, spec: Record<string, unknown>) => request<StrategyHandle>(`/v1/projects/${projectId}/strategies`, tenantId, { method: "POST", body: JSON.stringify({ name, spec }) }),
  getDraft: (tenantId: string, projectId: string, strategyId: string, draftId: string) => request<DraftSnapshot>(`/v1/projects/${projectId}/strategies/${strategyId}/drafts/${draftId}`, tenantId),
  updateDraft: (tenantId: string, projectId: string, strategyId: string, draftId: string, revision: number, spec: Record<string, unknown>) => request<StrategyHandle>(`/v1/projects/${projectId}/strategies/${strategyId}/drafts/${draftId}`, tenantId, { method: "PUT", headers: { "If-Match": `"${revision}"` }, body: JSON.stringify({ spec }) }),
  compileStrategy: (tenantId: string, projectId: string, spec: Record<string, unknown>) => request<CompileResponse>(`/v1/projects/${projectId}/strategies/compile`, tenantId, { method: "POST", body: JSON.stringify({ spec }) }),
  listVersions: (tenantId: string, projectId: string, strategyId: string) => request<StrategyVersionListResponse>(`/v1/projects/${projectId}/strategies/${strategyId}/versions`, tenantId),
  getVersion: (tenantId: string, projectId: string, strategyId: string, versionId: string) => request<StrategyVersionDetail>(`/v1/projects/${projectId}/strategies/${strategyId}/versions/${versionId}`, tenantId),
  publishStrategy: (tenantId: string, projectId: string, strategyId: string, draftId: string) => request<StrategyVersionDetail | { strategyVersionId: string; version: number; planHash: string }>(`/v1/projects/${projectId}/strategies/${strategyId}/publish`, tenantId, { method: "POST", body: JSON.stringify({ draftId }) }),
  listRuns: (tenantId: string, projectId: string) => request<RunListResponse>(`/v1/projects/${projectId}/runs`, tenantId),
  createRun: (tenantId: string, projectId: string, strategyVersionId: string, input: Record<string, unknown>, idempotencyKey: string) => request<RunHandle>(`/v1/projects/${projectId}/runs`, tenantId, { method: "POST", headers: { "Idempotency-Key": idempotencyKey }, body: JSON.stringify({ strategyVersionId, input }) }),
  getRun: (tenantId: string, projectId: string, runId: string) => request<RunSnapshot>(`/v1/projects/${projectId}/runs/${runId}`, tenantId),
  history: (tenantId: string, projectId: string, runId: string, after: number) => request<EventHistory>(`/v1/projects/${projectId}/runs/${runId}/event-history?after=${after}&limit=1000`, tenantId),
  cancelRun: (tenantId: string, projectId: string, runId: string) => request<CommandHandle>(`/v1/projects/${projectId}/runs/${runId}:cancel`, tenantId, { method: "POST", headers: { "Idempotency-Key": crypto.randomUUID() } }),
  pauseRun: (tenantId: string, projectId: string, runId: string) => request<CommandHandle>(`/v1/projects/${projectId}/runs/${runId}:pause`, tenantId, { method: "POST", headers: { "Idempotency-Key": crypto.randomUUID() } }),
  resumeRun: (tenantId: string, projectId: string, runId: string) => request<CommandHandle>(`/v1/projects/${projectId}/runs/${runId}:resume`, tenantId, { method: "POST", headers: { "Idempotency-Key": crypto.randomUUID() } }),
  getCommand: (tenantId: string, projectId: string, commandId: string) => request<CommandHandle>(`/v1/projects/${projectId}/commands/${commandId}`, tenantId),
  listApprovals: (tenantId: string, projectId: string, runId: string) => request<ApprovalListResponse>(`/v1/projects/${projectId}/approvals?runId=${runId}`, tenantId),
  approve: (tenantId: string, projectId: string, approvalId: string, value: Record<string, unknown>) => request<CommandHandle>(`/v1/projects/${projectId}/approvals/${approvalId}:approve`, tenantId, { method: "POST", headers: { "Idempotency-Key": crypto.randomUUID() }, body: JSON.stringify({ value }) }),
  reject: (tenantId: string, projectId: string, approvalId: string, value: Record<string, unknown>) => request<CommandHandle>(`/v1/projects/${projectId}/approvals/${approvalId}:reject`, tenantId, { method: "POST", headers: { "Idempotency-Key": crypto.randomUUID() }, body: JSON.stringify({ value }) }),
  listInputs: (tenantId: string, projectId: string, runId: string) => request<ExternalInputListResponse>(`/v1/projects/${projectId}/inputs?runId=${runId}`, tenantId),
  provideInput: (tenantId: string, projectId: string, inputRequestId: string, value: Record<string, unknown>) => request<CommandHandle>(`/v1/projects/${projectId}/inputs/${inputRequestId}:provide`, tenantId, { method: "POST", headers: { "Idempotency-Key": crypto.randomUUID() }, body: JSON.stringify({ value }) }),
  retryTask: (tenantId: string, projectId: string, runId: string, taskId: string) => request<CommandHandle>(`/v1/projects/${projectId}/runs/${runId}/tasks/${taskId}:retry`, tenantId, { method: "POST", headers: { "Idempotency-Key": crypto.randomUUID() } }),
  eventUrl: (projectId: string, runId: string, after: number) => `${baseUrl}/v1/projects/${projectId}/runs/${runId}/events?after=${after}`,
  temporalUrl: (tenantId: string, runId: string) => `${typeof temporalUi === "string" ? temporalUi : "http://localhost:8088"}/namespaces/default/workflows/${encodeURIComponent(`swarm:${tenantId}:${runId}`)}`,
  phoenixUrl: typeof phoenixUi === "string" ? phoenixUi : "http://localhost:6006",
};
