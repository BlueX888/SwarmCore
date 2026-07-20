import type {
  ApprovalListResponse, AuditListResponse, CapabilityCatalog, CapabilityCenterResponse, CapabilityPreset, CapabilityPresetListResponse, CapabilityPresetRequest, CommandHandle, CompileResponse, ConfigurationKind, CreateSavedConfiguration,
  DraftSnapshot, EditorState, EventHistory, ExternalInputListResponse, RunHandle, RunListResponse, RunSnapshot, SavedConfiguration,
  AttachmentUploadHandle, CapabilityPackListResponse, CapabilityPackSnapshot, CreateCapabilityPackRequest, EvaluationSnapshot, FindingListResponse, ReportListResponse,
  RuleSetDraftSnapshot, RuleSetValidationResponse, RuleSetVersionSnapshot, WorkItemListResponse, WorkItemSnapshot,
  SavedConfigurationListResponse, StrategyHandle,
  StrategyListResponse, StrategyVersionDetail,
  StrategyVersionListResponse,
} from "./types";

const configuredApiUrl: unknown = import.meta.env["VITE_API_URL"];
const baseUrl = typeof configuredApiUrl === "string" ? configuredApiUrl : "/api";
const temporalUi: unknown = import.meta.env["VITE_TEMPORAL_UI_URL"];
const phoenixUi: unknown = import.meta.env["VITE_PHOENIX_URL"];
const temporalUiUrl = typeof temporalUi === "string" ? temporalUi : "http://localhost:8088";
const configuredArtifactGateway: unknown = import.meta.env["VITE_ARTIFACT_GATEWAY_URL"];
const artifactGatewayUrl = typeof configuredArtifactGateway === "string" ? configuredArtifactGateway : "http://localhost:8091";

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
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

async function requestFile(path: string, tenantId: string, init?: RequestInit): Promise<Blob> {
  const headers = new Headers(init?.headers);
  headers.set("X-Tenant-ID", tenantId);
  const response = await fetch(`${baseUrl}${path}`, { ...init, headers });
  if (!response.ok) throw new ApiError(response.status, await response.text());
  return response.blob();
}

export const api = {
  listStrategies: (tenantId: string, projectId: string, limit = 50) => request<StrategyListResponse>(`/v1/projects/${projectId}/strategies?limit=${limit}`, tenantId),
  getCapabilities: (tenantId: string, projectId: string) => request<CapabilityCatalog>(`/v1/projects/${projectId}/capabilities`, tenantId),
  getCapabilityCenter: (tenantId: string, projectId: string) => request<CapabilityCenterResponse>(`/v1/projects/${projectId}/capability-center`, tenantId),
  runCapability: (tenantId: string, projectId: string, capabilityRef: string, input: Record<string, unknown>, presetId?: string) => request<RunHandle>(`/v1/projects/${projectId}/capability-runs`, tenantId, { method: "POST", headers: { "Idempotency-Key": crypto.randomUUID() }, body: JSON.stringify({ capabilityRef, input, presetId }) }),
  listPresets: (tenantId: string, projectId: string) => request<CapabilityPresetListResponse>(`/v1/projects/${projectId}/presets`, tenantId),
  createPreset: (tenantId: string, projectId: string, body: CapabilityPresetRequest) => request<CapabilityPreset>(`/v1/projects/${projectId}/presets`, tenantId, { method: "POST", body: JSON.stringify(body) }),
  updatePreset: (tenantId: string, projectId: string, presetId: string, body: CapabilityPresetRequest) => request<CapabilityPreset>(`/v1/projects/${projectId}/presets/${presetId}`, tenantId, { method: "PUT", body: JSON.stringify(body) }),
  copyPreset: (tenantId: string, projectId: string, presetId: string, name: string) => request<CapabilityPreset>(`/v1/projects/${projectId}/presets/${presetId}:copy`, tenantId, { method: "POST", body: JSON.stringify({ name }) }),
  deletePreset: (tenantId: string, projectId: string, presetId: string) => request<undefined>(`/v1/projects/${projectId}/presets/${presetId}`, tenantId, { method: "DELETE" }),
  listConfigurations: (tenantId: string, projectId: string, kind: ConfigurationKind) => request<SavedConfigurationListResponse>(`/v1/projects/${projectId}/configurations/${kind}`, tenantId),
  createConfiguration: (tenantId: string, projectId: string, kind: ConfigurationKind, body: CreateSavedConfiguration) => request<SavedConfiguration>(`/v1/projects/${projectId}/configurations/${kind}`, tenantId, { method: "POST", body: JSON.stringify(body) }),
  updateConfiguration: (tenantId: string, projectId: string, kind: ConfigurationKind, configurationId: string, body: CreateSavedConfiguration) => request<SavedConfiguration>(`/v1/projects/${projectId}/configurations/${kind}/${configurationId}`, tenantId, { method: "PUT", body: JSON.stringify(body) }),
  deleteConfiguration: (tenantId: string, projectId: string, kind: ConfigurationKind, configurationId: string) => request<undefined>(`/v1/projects/${projectId}/configurations/${kind}/${configurationId}`, tenantId, { method: "DELETE" }),
  createStrategy: (tenantId: string, projectId: string, name: string, spec: Record<string, unknown>, editorState: EditorState) => request<StrategyHandle>(`/v1/projects/${projectId}/strategies`, tenantId, { method: "POST", body: JSON.stringify({ name, spec, editorState }) }),
  getDraft: (tenantId: string, projectId: string, strategyId: string, draftId: string) => request<DraftSnapshot>(`/v1/projects/${projectId}/strategies/${strategyId}/drafts/${draftId}`, tenantId),
  updateDraft: (tenantId: string, projectId: string, strategyId: string, draftId: string, revision: number, spec: Record<string, unknown>, editorState: EditorState) => request<DraftSnapshot>(`/v1/projects/${projectId}/strategies/${strategyId}/drafts/${draftId}`, tenantId, { method: "PUT", headers: { "If-Match": `"${revision}"` }, body: JSON.stringify({ spec, editorState }) }),
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
  listApprovals: (tenantId: string, projectId: string, runId?: string) => request<ApprovalListResponse>(`/v1/projects/${projectId}/approvals${runId ? `?runId=${runId}` : ""}`, tenantId),
  approve: (tenantId: string, projectId: string, approvalId: string, value: Record<string, unknown>) => request<CommandHandle>(`/v1/projects/${projectId}/approvals/${approvalId}:approve`, tenantId, { method: "POST", headers: { "Idempotency-Key": crypto.randomUUID() }, body: JSON.stringify({ value }) }),
  reject: (tenantId: string, projectId: string, approvalId: string, value: Record<string, unknown>) => request<CommandHandle>(`/v1/projects/${projectId}/approvals/${approvalId}:reject`, tenantId, { method: "POST", headers: { "Idempotency-Key": crypto.randomUUID() }, body: JSON.stringify({ value }) }),
  listInputs: (tenantId: string, projectId: string, runId?: string) => request<ExternalInputListResponse>(`/v1/projects/${projectId}/inputs${runId ? `?runId=${runId}` : ""}`, tenantId),
  provideInput: (tenantId: string, projectId: string, inputRequestId: string, value: Record<string, unknown>) => request<CommandHandle>(`/v1/projects/${projectId}/inputs/${inputRequestId}:provide`, tenantId, { method: "POST", headers: { "Idempotency-Key": crypto.randomUUID() }, body: JSON.stringify({ value }) }),
  listAuditLogs: (tenantId: string, projectId: string, limit = 100) => request<AuditListResponse>(`/v1/projects/${projectId}/audit-logs?limit=${limit}`, tenantId),
  exportAuditLogs: (tenantId: string, projectId: string) => requestFile(`/v1/projects/${projectId}/audit-logs:export`, tenantId, { method: "POST" }),
  retryTask: (tenantId: string, projectId: string, runId: string, taskId: string) => request<CommandHandle>(`/v1/projects/${projectId}/runs/${runId}/tasks/${taskId}:retry`, tenantId, { method: "POST", headers: { "Idempotency-Key": crypto.randomUUID() } }),
  listCapabilityPacks: (tenantId: string, projectId: string) => request<CapabilityPackListResponse>(`/v1/projects/${projectId}/capability-packs`, tenantId),
  createCapabilityPack: (tenantId: string, projectId: string, body: CreateCapabilityPackRequest) => request<CapabilityPackSnapshot>(`/v1/projects/${projectId}/capability-packs`, tenantId, { method: "POST", body: JSON.stringify(body) }),
  enableCapabilityPack: (tenantId: string, projectId: string, versionId: string, configuration: Record<string, unknown> = {}) => request(`/v1/projects/${projectId}/capability-packs/${versionId}:enable`, tenantId, { method: "POST", headers: { "Idempotency-Key": crypto.randomUUID() }, body: JSON.stringify({ configuration }) }),
  listWorkItems: (tenantId: string, projectId: string) => request<WorkItemListResponse>(`/v1/projects/${projectId}/work-items`, tenantId),
  getWorkItem: (tenantId: string, projectId: string, workItemId: string) => request<WorkItemSnapshot>(`/v1/projects/${projectId}/work-items/${workItemId}`, tenantId),
  createWorkItem: (tenantId: string, projectId: string, body: { workItemType: string; payload: Record<string, unknown>; owner?: string }) => request<WorkItemSnapshot>(`/v1/projects/${projectId}/work-items`, tenantId, { method: "POST", headers: { "Idempotency-Key": crypto.randomUUID() }, body: JSON.stringify(body) }),
  executeWorkItem: (tenantId: string, projectId: string, workItemId: string) => request<EvaluationSnapshot>(`/v1/projects/${projectId}/work-items/${workItemId}:execute`, tenantId, { method: "POST", headers: { "Idempotency-Key": crypto.randomUUID() } }),
  listFindings: (tenantId: string, projectId: string, workItemId: string) => request<FindingListResponse>(`/v1/projects/${projectId}/work-items/${workItemId}/findings`, tenantId),
  actOnFinding: (tenantId: string, projectId: string, findingId: string, action: "ACKNOWLEDGE" | "WAIVE" | "RESOLVE" | "REOPEN", reason?: string) => request(`/v1/projects/${projectId}/findings/${findingId}:act`, tenantId, { method: "POST", headers: { "Idempotency-Key": crypto.randomUUID() }, body: JSON.stringify({ action, reason }) }),
  listReports: (tenantId: string, projectId: string, evaluationId: string) => request<ReportListResponse>(`/v1/projects/${projectId}/evaluations/${evaluationId}/reports`, tenantId),
  initiateAttachment: (tenantId: string, projectId: string, workItemId: string, body: { documentType: string; filename: string; mediaType: string; sizeBytes: number; sha256: string }) => request<AttachmentUploadHandle>(`/v1/projects/${projectId}/work-items/${workItemId}/attachments:initiate`, tenantId, { method: "POST", headers: { "Idempotency-Key": crypto.randomUUID() }, body: JSON.stringify(body) }),
  uploadBlob: async (handle: AttachmentUploadHandle, contentBase64: string) => {
    const response = await fetch(`${artifactGatewayUrl}${handle.uploadRef}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ capabilityToken: handle.capabilityToken, contentBase64 }) });
    if (!response.ok) throw new ApiError(response.status, await response.text());
  },
  completeAttachment: (tenantId: string, projectId: string, handle: AttachmentUploadHandle, sha256: string) => request<AttachmentUploadHandle>(`/v1/projects/${projectId}/attachments/${handle.attachmentId}:complete`, tenantId, { method: "POST", headers: { "Idempotency-Key": crypto.randomUUID() }, body: JSON.stringify({ sha256, scanStatus: "CLEAN" }) }),
  createRuleSet: (tenantId: string, projectId: string, body: { name: string; purpose: string; rules: Record<string, unknown> }) => request<RuleSetDraftSnapshot>(`/v1/projects/${projectId}/rule-sets`, tenantId, { method: "POST", headers: { "Idempotency-Key": crypto.randomUUID() }, body: JSON.stringify(body) }),
  validateRuleSet: (tenantId: string, projectId: string, draftId: string, attachments: Array<Record<string, unknown>>) => request<RuleSetValidationResponse>(`/v1/projects/${projectId}/rule-set-drafts/${draftId}:validate`, tenantId, { method: "POST", headers: { "Idempotency-Key": crypto.randomUUID() }, body: JSON.stringify({ attachments }) }),
  publishRuleSet: (tenantId: string, projectId: string, draftId: string) => request<RuleSetVersionSnapshot>(`/v1/projects/${projectId}/rule-set-drafts/${draftId}:publish`, tenantId, { method: "POST", headers: { "Idempotency-Key": crypto.randomUUID() } }),
  eventUrl: (projectId: string, runId: string, after: number) => `${baseUrl}/v1/projects/${projectId}/runs/${runId}/events?after=${after}`,
  temporalUiUrl,
  temporalUrl: (tenantId: string, runId: string) => `${temporalUiUrl}/namespaces/default/workflows/${encodeURIComponent(`swarm:${tenantId}:${runId}`)}`,
  phoenixUrl: typeof phoenixUi === "string" ? phoenixUi : "http://localhost:6006",
};
