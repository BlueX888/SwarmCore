import type {
  ApprovalListResponse, AuditListResponse, CapabilityCatalog, CapabilityCenterResponse, CapabilityPreset, CapabilityPresetListResponse, CapabilityPresetRequest, CommandHandle, CompileResponse, ConfigurationKind, CreateSavedConfiguration,
  DraftSnapshot, EditorState, EventHistory, ExternalInputListResponse, RunHandle, RunListResponse, RunSnapshot, SavedConfiguration,
  CapabilityPackListResponse, CapabilityPackSnapshot, CreateCapabilityPackRequest,
  AssessmentDetailSnapshot, AssessmentListResponse, BusinessObjectSnapshot, BusinessWorkListResponse, BusinessWorkSnapshot, CaseSnapshot, CaseSubjectInput, DocumentDownloadHandle, DocumentListResponse, DocumentProcessingResultSnapshot, DocumentProcessingRunSnapshot, DocumentRequirementListResponse, DocumentSnapshot, DocumentUploadHandle, EvaluationSnapshot, FindingListResponse, InitiateDocumentRequest, PackBindings, ReportListResponse,
  SavedConfigurationListResponse, StrategyDeleteImpact, StrategyHandle,
  ModelProviderConfiguration, ModelProviderConfigurationRequest, ModelProviderTestResult,
  StrategyListResponse, StrategyVersionDetail,
  StrategyVersionListResponse, UploadBatchSnapshot, WorkItemSnapshot, RuleSetDraftSnapshot, RuleSetValidationResponse, RuleSetVersionSnapshot,
} from "./types";

const configuredApiUrl: unknown = import.meta.env["VITE_API_URL"];
const baseUrl = typeof configuredApiUrl === "string" ? configuredApiUrl : "/api";
const temporalUi: unknown = import.meta.env["VITE_TEMPORAL_UI_URL"];
const phoenixUi: unknown = import.meta.env["VITE_PHOENIX_URL"];
const temporalUiUrl = typeof temporalUi === "string" ? temporalUi : "http://localhost:8088";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public code?: string,
    public blockers?: Array<{
      ref?: string;
      reasons?: string[];
      code?: string;
      count?: number;
      message?: string;
    }>,
  ) { super(message); }
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
      const problem = JSON.parse(body) as {
        detail?: string;
        code?: string;
        blockers?: Array<{
          ref?: string;
          reasons?: string[];
          code?: string;
          count?: number;
          message?: string;
        }>;
      };
      throw new ApiError(response.status, problem.detail ?? body, problem.code, problem.blockers);
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

async function uploadBlob(uploadRef: string, capabilityToken: string, file: File): Promise<void> {
  const bytes = new Uint8Array(await file.arrayBuffer());
  let binary = "";
  const chunkSize = 0x8000;
  for (let offset = 0; offset < bytes.length; offset += chunkSize) {
    binary += String.fromCharCode(...bytes.subarray(offset, offset + chunkSize));
  }
  const response = await fetch(uploadRef, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ capabilityToken, contentBase64: btoa(binary) }),
  });
  if (!response.ok) {
    const body = await response.text();
    if (response.status === 404) {
      throw new ApiError(404, "文件存储服务不可用。请确认 Artifact Gateway 已启动（默认 8091）。");
    }
    throw new ApiError(response.status, body || response.statusText);
  }
}

async function downloadBlob(handle: DocumentDownloadHandle): Promise<Blob> {
  const query = new URLSearchParams({ capability_token: handle.capabilityToken });
  const response = await fetch(`${handle.downloadRef}?${query}`, { method: "POST" });
  if (!response.ok) throw new ApiError(response.status, await response.text());
  return response.blob();
}

export const api = {
  listStrategies: (tenantId: string, projectId: string, limit = 50) => request<StrategyListResponse>(`/v1/projects/${projectId}/strategies?limit=${limit}`, tenantId),
  getCapabilities: (tenantId: string, projectId: string) => request<CapabilityCatalog>(`/v1/projects/${projectId}/capabilities`, tenantId),
  getCapabilityCenter: (tenantId: string, projectId: string) => request<CapabilityCenterResponse>(`/v1/projects/${projectId}/capability-center`, tenantId),
  getModelProvider: (tenantId: string, projectId: string, logicalModel: string) => request<ModelProviderConfiguration>(`/v1/projects/${projectId}/model-provider?logicalModel=${encodeURIComponent(logicalModel)}`, tenantId),
  saveModelProvider: (tenantId: string, projectId: string, body: ModelProviderConfigurationRequest) => request<ModelProviderConfiguration>(`/v1/projects/${projectId}/model-provider`, tenantId, { method: "PUT", body: JSON.stringify(body) }),
  testModelProvider: (tenantId: string, projectId: string, body: ModelProviderConfigurationRequest) => request<ModelProviderTestResult>(`/v1/projects/${projectId}/model-provider:test`, tenantId, { method: "POST", body: JSON.stringify(body) }),
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
  getStrategyDeleteImpact: (tenantId: string, projectId: string, strategyId: string) => request<StrategyDeleteImpact>(`/v1/projects/${projectId}/strategies/${strategyId}/delete-impact`, tenantId),
  deleteStrategy: (tenantId: string, projectId: string, strategyId: string) => request<undefined>(`/v1/projects/${projectId}/strategies/${strategyId}`, tenantId, { method: "DELETE" }),
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
  listBusinessWorks: (tenantId: string, projectId: string) => request<BusinessWorkListResponse>(`/v1/projects/${projectId}/business-works`, tenantId),
  getBusinessWork: (tenantId: string, projectId: string, workKey: string) => request<BusinessWorkSnapshot>(`/v1/projects/${projectId}/business-works/${encodeURIComponent(workKey)}`, tenantId),
  bindBusinessWorkStrategy: (tenantId: string, projectId: string, workKey: string, strategyVersionId: string) => request<BusinessWorkSnapshot>(`/v1/projects/${projectId}/business-works/${encodeURIComponent(workKey)}:bind-strategy`, tenantId, { method: "POST", headers: { "Idempotency-Key": crypto.randomUUID() }, body: JSON.stringify({ strategyVersionId }) }),
  getAssessment: (tenantId: string, projectId: string, assessmentId: string) => request<AssessmentDetailSnapshot>(`/v1/projects/${projectId}/assessments/${assessmentId}`, tenantId),
  listAssessmentDocumentSnapshots: (tenantId: string, projectId: string, assessmentId: string) => request<{ items: Array<Record<string, unknown>> }>(`/v1/projects/${projectId}/assessments/${assessmentId}/document-snapshots`, tenantId),
  createCapabilityPack: (tenantId: string, projectId: string, body: CreateCapabilityPackRequest) => request<CapabilityPackSnapshot>(`/v1/projects/${projectId}/capability-packs`, tenantId, { method: "POST", body: JSON.stringify(body) }),
  createRuleSet: (tenantId: string, projectId: string, body: { name: string; purpose: string; rules: Record<string, unknown> }) => request<RuleSetDraftSnapshot>(`/v1/projects/${projectId}/rule-sets`, tenantId, { method: "POST", headers: { "Idempotency-Key": crypto.randomUUID() }, body: JSON.stringify(body) }),
  validateRuleSet: (tenantId: string, projectId: string, draftId: string) => request<RuleSetValidationResponse>(`/v1/projects/${projectId}/rule-set-drafts/${draftId}:validate`, tenantId, { method: "POST", headers: { "Idempotency-Key": crypto.randomUUID() }, body: JSON.stringify({ attachments: null }) }),
  publishRuleSet: (tenantId: string, projectId: string, draftId: string) => request<RuleSetVersionSnapshot>(`/v1/projects/${projectId}/rule-set-drafts/${draftId}:publish`, tenantId, { method: "POST", headers: { "Idempotency-Key": crypto.randomUUID() } }),
  enableCapabilityPack: (tenantId: string, projectId: string, versionId: string, configuration: Record<string, unknown> = {}) => request(`/v1/projects/${projectId}/capability-packs/${versionId}:enable`, tenantId, { method: "POST", headers: { "Idempotency-Key": crypto.randomUUID() }, body: JSON.stringify({ configuration }) }),
  disableCapabilityPack: (tenantId: string, projectId: string, versionId: string) => request<CapabilityPackSnapshot>(`/v1/projects/${projectId}/capability-packs/${versionId}:disable`, tenantId, { method: "POST", headers: { "Idempotency-Key": crypto.randomUUID() } }),
  deleteCapabilityPack: (tenantId: string, projectId: string, versionId: string) => request<undefined>(`/v1/projects/${projectId}/capability-packs/${versionId}`, tenantId, { method: "DELETE" }),
  createWorkItem: (tenantId: string, projectId: string, body: { workItemType: string; payload: Record<string, unknown>; owner?: string }) => request<WorkItemSnapshot>(`/v1/projects/${projectId}/work-items`, tenantId, { method: "POST", headers: { "Idempotency-Key": crypto.randomUUID() }, body: JSON.stringify(body) }),
  executeWorkItem: (tenantId: string, projectId: string, workItemId: string) => request<EvaluationSnapshot>(`/v1/projects/${projectId}/work-items/${workItemId}:execute`, tenantId, { method: "POST", headers: { "Idempotency-Key": crypto.randomUUID() } }),
  getEvaluation: (tenantId: string, projectId: string, evaluationId: string) => request<EvaluationSnapshot>(`/v1/projects/${projectId}/evaluations/${evaluationId}`, tenantId),
  listDocuments: (tenantId: string, projectId: string, search = "", category = "", status = "") => {
    const query = new URLSearchParams();
    if (search) query.set("search", search);
    if (category) query.set("category", category);
    if (status) query.set("status", status);
    const suffix = query.size ? `?${query.toString()}` : "";
    return request<DocumentListResponse>(`/v1/projects/${projectId}/documents${suffix}`, tenantId);
  },
  initiateDocument: (tenantId: string, projectId: string, body: InitiateDocumentRequest) => request<DocumentUploadHandle>(`/v1/projects/${projectId}/documents:initiate`, tenantId, { method: "POST", headers: { "Idempotency-Key": crypto.randomUUID() }, body: JSON.stringify(body) }),
  uploadDocumentContent: (handle: DocumentUploadHandle, file: File) => {
    if (!handle.capabilityToken) throw new ApiError(409, "文件上传凭证不可用");
    return uploadBlob(handle.uploadRef, handle.capabilityToken, file);
  },
  completeDocument: (
    tenantId: string,
    projectId: string,
    uploadId: string,
    sha256: string,
    options: {
      uploadBatchId?: string;
      profileRef?: string;
      extractionSchemaRef?: string;
      classificationLabels?: Array<{ label: string; displayName?: string }>;
    } = {},
  ) => request<DocumentSnapshot>(`/v1/projects/${projectId}/document-uploads/${uploadId}:complete`, tenantId, {
    method: "POST",
    headers: { "Idempotency-Key": crypto.randomUUID() },
    body: JSON.stringify({
      sha256,
      uploadBatchId: options.uploadBatchId,
      profileRef: options.profileRef,
      extractionSchemaRef: options.extractionSchemaRef,
      classificationLabels: options.classificationLabels ?? [],
    }),
  }),
  createUploadBatch: (tenantId: string, projectId: string, body: { source?: string; context?: Record<string, unknown> }) =>
    request<UploadBatchSnapshot>(`/v1/projects/${projectId}/upload-batches`, tenantId, {
      method: "POST",
      headers: { "Idempotency-Key": crypto.randomUUID() },
      body: JSON.stringify({ source: body.source ?? "web", context: body.context ?? {} }),
    }),
  getUploadBatch: (tenantId: string, projectId: string, batchId: string) =>
    request<UploadBatchSnapshot>(`/v1/projects/${projectId}/upload-batches/${batchId}`, tenantId),
  getDocumentProcessing: (tenantId: string, projectId: string, documentId: string) =>
    request<DocumentProcessingRunSnapshot>(`/v1/projects/${projectId}/documents/${documentId}/processing`, tenantId),
  getDocumentProcessingResult: (tenantId: string, projectId: string, documentId: string) =>
    request<DocumentProcessingResultSnapshot>(`/v1/projects/${projectId}/documents/${documentId}/processing-result`, tenantId),
  confirmDocumentClassification: (tenantId: string, projectId: string, documentId: string, body: { label: string; displayName?: string; expectedResultVersion?: number }) =>
    request<DocumentProcessingResultSnapshot>(`/v1/projects/${projectId}/documents/${documentId}:confirm-classification`, tenantId, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  confirmDocumentFields: (tenantId: string, projectId: string, documentId: string, body: { fields: Array<Record<string, unknown>>; acceptHighConfidence?: boolean; expectedResultVersion?: number }) =>
    request<DocumentProcessingResultSnapshot>(`/v1/projects/${projectId}/documents/${documentId}:confirm-fields`, tenantId, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  reprocessDocument: (tenantId: string, projectId: string, documentId: string, body: Record<string, unknown> = {}) =>
    request<DocumentProcessingRunSnapshot>(`/v1/projects/${projectId}/documents/${documentId}:reprocess`, tenantId, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  updateDocumentBindings: (tenantId: string, projectId: string, documentId: string, body: { businessObjectIds: string[]; businessWorkKeys: string[] }) =>
    request<DocumentSnapshot>(`/v1/projects/${projectId}/documents/${documentId}/bindings`, tenantId, {
      method: "PUT",
      body: JSON.stringify(body),
    }),
  listWorkDocumentRequirements: (tenantId: string, projectId: string, workKey: string) =>
    request<DocumentRequirementListResponse>(`/v1/projects/${projectId}/business-works/${workKey}/document-requirements`, tenantId),
  getDocument: (tenantId: string, projectId: string, documentId: string) => request<DocumentSnapshot>(`/v1/projects/${projectId}/documents/${documentId}`, tenantId),
  resumeDocumentUpload: (tenantId: string, projectId: string, documentId: string) =>
    request<DocumentSnapshot>(`/v1/projects/${projectId}/documents/${documentId}:resume-upload`, tenantId, {
      method: "POST",
      headers: { "Idempotency-Key": crypto.randomUUID() },
      body: JSON.stringify({}),
    }),
  downloadDocumentVersion: async (tenantId: string, projectId: string, documentId: string, version: number) => {
    const handle = await request<DocumentDownloadHandle>(`/v1/projects/${projectId}/documents/${documentId}/versions/${version}:download`, tenantId, { method: "POST" });
    return { filename: handle.filename, content: await downloadBlob(handle) };
  },
  getPackBindings: (tenantId: string, projectId: string, versionId: string) => request<PackBindings>(`/v1/projects/${projectId}/capability-packs/${versionId}/bindings`, tenantId),
  createBusinessObject: (tenantId: string, projectId: string, body: { objectType: string; canonicalKey: string; schemaRef: string; data: Record<string, unknown>; provenance?: Record<string, unknown> }) => request<BusinessObjectSnapshot>(`/v1/projects/${projectId}/business-objects`, tenantId, { method: "POST", body: JSON.stringify(body) }),
  createCase: (tenantId: string, projectId: string, body: { scenarioType: string; payload: Record<string, unknown>; subjects: CaseSubjectInput[]; owner?: string }) => request<CaseSnapshot>(`/v1/projects/${projectId}/cases`, tenantId, { method: "POST", headers: { "Idempotency-Key": crypto.randomUUID() }, body: JSON.stringify(body) }),
  assessCase: (tenantId: string, projectId: string, caseId: string) => request<EvaluationSnapshot>(`/v1/projects/${projectId}/cases/${caseId}:assess`, tenantId, { method: "POST", headers: { "Idempotency-Key": crypto.randomUUID() } }),
  listCaseAssessments: (tenantId: string, projectId: string, caseId: string) => request<AssessmentListResponse>(`/v1/projects/${projectId}/cases/${caseId}/assessments`, tenantId),
  listCaseFindings: (tenantId: string, projectId: string, caseId: string) => request<FindingListResponse>(`/v1/projects/${projectId}/cases/${caseId}/findings`, tenantId),
  listEvaluationReports: (tenantId: string, projectId: string, evaluationId: string) => request<ReportListResponse>(`/v1/projects/${projectId}/evaluations/${evaluationId}/reports`, tenantId),
  eventUrl: (projectId: string, runId: string, after: number) => `${baseUrl}/v1/projects/${projectId}/runs/${runId}/events?after=${after}`,
  temporalUiUrl,
  temporalUrl: (tenantId: string, runId: string) => `${temporalUiUrl}/namespaces/default/workflows/${encodeURIComponent(`swarm:${tenantId}:${runId}`)}`,
  phoenixUrl: typeof phoenixUi === "string" ? phoenixUi : "http://localhost:6006",
};
