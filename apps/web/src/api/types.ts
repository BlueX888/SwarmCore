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
  role?: string | null;
  instructions?: string | null;
  model?: string | null;
  tools?: string[];
  inputSchema?: Record<string, unknown>;
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
  capabilityPacks?: Array<{ name: string; version: string; workItemType: string; inputSchema: string; outputSchema: string; viewDefinition: string }>;
}
export type CapabilityKind = "agent" | "tool" | "model" | "policy";
export type ReadinessReasonCode =
  | "EXECUTOR_MISSING" | "ADAPTER_MISSING" | "MODEL_ROUTE_MISSING"
  | "SECRET_MISSING" | "DEPENDENCY_NOT_READY" | "DEPENDENCY_CYCLE"
  | "HEALTH_CHECK_FAILED" | "ENVIRONMENT_NOT_ALLOWED"
  | "CAPABILITY_PACK_DISABLED" | "SCHEMA_INVALID" | "POLICY_DENIED";
export interface ReadinessReason { code: ReadinessReasonCode; message: string; dependencyRef?: string | null; }
export interface CapabilityReadiness { status: "READY" | "NOT_READY"; reasons: ReadinessReason[]; }
export interface CapabilitySummary {
  ref: string;
  kind: CapabilityKind;
  name: string;
  description: string;
  source: string;
  readiness: CapabilityReadiness;
  risk?: string | null;
  inputSchema?: Record<string, unknown> | null;
  outputSchema?: Record<string, unknown> | null;
}
export interface CapabilityCenterResponse { registrySnapshot: string; items: CapabilitySummary[]; }
export interface ModelProviderConfiguration {
  logicalModel: string; providerUrl: string; modelName: string; apiKeyConfigured: boolean; displayName?: string;
}
export interface ModelProviderConfigurationRequest {
  logicalModel: string; providerUrl: string; modelName: string; apiKey?: string; displayName?: string;
}
export interface ModelProviderTestResult { connected: boolean; modelName: string; latencyMs: number; }
export interface CapabilityPreset {
  presetId: string; kind: "agent" | "tool" | "model"; name: string; capabilityRef: string;
  parameters: Record<string, unknown>; revision: number; readiness: CapabilityReadiness | null;
  createdBy: string; updatedBy: string; createdAt: string; updatedAt: string;
}
export interface CapabilityPresetListResponse { items: CapabilityPreset[]; total: number; }
export interface CapabilityPresetRequest { name: string; capabilityRef: string; parameters: Record<string, unknown>; }
export interface CanvasCapabilitySelection { capability: CapabilitySummary; input: Record<string, unknown>; }
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
export interface StrategyDeleteBlocker {
  code: string;
  count: number;
  message: string;
}
export interface StrategyDeleteImpact {
  strategyId: string;
  deletable: boolean;
  blockers: StrategyDeleteBlocker[];
}
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

export interface CapabilityPackSnapshot {
  packId: string; name: string; versionId: string; version: string; contentHash: string;
  manifest: Record<string, unknown>; enabled: boolean; bindingStatus: string | null;
  configuration: Record<string, unknown>;
  blockers: Array<{ ref: string; reasons: string[] }>;
  deleteBlockedReason?: string | null;
}
export interface CapabilityPackListResponse { items: CapabilityPackSnapshot[]; }
export interface CreateCapabilityPackRequest {
  manifest: Record<string, unknown>;
  strategyVersionId: string;
}

export interface WorkItemSnapshot {
  workItemId: string;
  workItemType: string;
  status: string;
  revisionId: string;
  revision: number;
}

export interface PackBindings {
  decisions: Array<{ slot: string; decisionVersionId: string; contentHash: string }>;
  resources: Array<{ slot: string; resourceId: string; accessMode: string }>;
}

export interface DocumentVersionSnapshot {
  documentVersionId: string;
  blobId: string;
  version: number;
  filename: string;
  mediaType: string;
  sizeBytes: number;
  sha256: string;
  processingStatus: string;
  createdAt: string;
}

export interface DocumentSnapshot {
  documentId: string;
  name: string;
  category: string;
  tags: string[];
  status: "UPLOADING" | "PROCESSING" | "AVAILABLE" | "REVIEW_REQUIRED" | "FAILED";
  currentVersion: number;
  updatedAt: string;
  current: DocumentVersionSnapshot | null;
  businessObjectIds: string[];
  businessWorkKeys: string[];
  versions: DocumentVersionSnapshot[];
}

export interface DocumentListResponse { items: DocumentSnapshot[]; }

export interface InitiateDocumentRequest {
  documentId?: string;
  name: string;
  category: string;
  tags: string[];
  filename: string;
  mediaType: string;
  sizeBytes: number;
  sha256: string;
  businessObjectIds: string[];
  businessWorkKeys: string[];
  retentionDays?: number;
}

export interface DocumentUploadHandle {
  documentId: string;
  uploadId: string;
  blobId: string;
  version: number;
  uploadRef: string;
  capabilityToken: string | null;
  status: string;
  uploadBatchId?: string | null;
}

export interface UploadBatchSnapshot {
  batchId: string;
  source: string;
  context: Record<string, unknown>;
  status: string;
  fileCount: number;
  succeededCount: number;
  failedCount: number;
  createdBy: string;
  createdAt: string;
  completedAt: string | null;
}

export interface DocumentProcessingRunSnapshot {
  processingRunId: string;
  businessDocumentVersionId: string;
  profileRef: string;
  status: string;
  currentStage: string;
  stageLabel: string;
  attempt: number;
  parserRef: string | null;
  classifierRef: string | null;
  extractorRefs: string[];
  errorCode: string | null;
  errorDetail: string | null;
  startedAt: string;
  completedAt: string | null;
}

export interface DocumentProcessingResultSnapshot {
  resultId: string;
  resultType: string;
  resultVersion: number;
  status: string;
  schemaRef: string | null;
  producerRef: string | null;
  result: {
    schemaVersion?: string;
    status?: string;
    documentType?: {
      label?: string;
      displayName?: string;
      confidence?: number;
      confirmedLabel?: string;
      alternatives?: Array<{ label: string; displayName?: string; confidence?: number }>;
      evidence?: Array<Record<string, unknown>>;
    };
    content?: {
      textExcerpt?: string;
      pages?: Array<Record<string, unknown>>;
      warnings?: string[];
    };
    extractions?: Array<{
      fieldPath: string;
      displayName: string;
      value: unknown;
      valueType: string;
      confidence: number;
      reviewStatus: string;
      evidenceRefs: Array<Record<string, unknown>>;
      machineValue: unknown;
      confirmedValue: unknown;
    }>;
    evidence?: Array<Record<string, unknown>>;
    qualityFlags?: string[];
    warnings?: string[];
    provenance?: Record<string, unknown>;
  };
  evidence: Array<Record<string, unknown>>;
  confirmedBy: string | null;
  confirmedAt: string | null;
  createdAt: string;
}

export interface DocumentRequirementSnapshot {
  key: string;
  displayName: string;
  description: string;
  required: boolean;
  minCount: number;
  maxCount: number | null;
  acceptedMediaTypes: string[];
  classificationLabels: string[];
  processingProfileRef: string | null;
  extractionSchemaRef: string | null;
  category: string | null;
  satisfiedCount: number;
  satisfied: boolean;
}

export interface DocumentRequirementListResponse {
  processingProfileRef: string | null;
  items: DocumentRequirementSnapshot[];
}

export interface DocumentDownloadHandle {
  documentId: string;
  documentVersionId: string;
  filename: string;
  mediaType: string;
  downloadRef: string;
  capabilityToken: string;
}
export interface BusinessObjectSnapshot {
  businessObjectId: string; versionId: string; objectType: string; canonicalKey: string;
  currentVersion: number; schemaRef: string; data: Record<string, unknown>;
}
export interface CaseSubjectInput {
  businessObjectId: string; businessObjectVersionId: string; role: "PRIMARY" | "COMPARISON" | "EVIDENCE" | "RELATED"; subjectKey: string;
}
export interface CaseSnapshot {
  caseId: string; scenarioType: string; caseRevisionId: string; revision: number;
  payload: Record<string, unknown>; status: string; owner: string | null;
  subjects: CaseSubjectInput[]; createdAt: string; updatedAt: string;
}
export interface PostEvaluationDimension {
  code: string; name: string; weight: number; score: number | null; status: string;
  summary: string; metrics: Record<string, string | number | boolean | null>; evidenceRefs: string[];
}
export interface PostEvaluationFinding {
  dimension: string; severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  code: string; title: string; detail: string; evidenceRefs: string[];
}
export interface PostEvaluationResult {
  schemaVersion: string; evaluationPeriod: { start: string; end: string }; contractId: string;
  overallScore: number; grade: string; riskLevel: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  passed: boolean; reviewRequired: boolean; executiveSummary: string;
  dimensions: PostEvaluationDimension[]; findings: PostEvaluationFinding[];
  readabilityGate?: {
    documentCount: number;
    readableDocumentCount: number;
    readabilityRate: number;
    formalThreshold: number;
    formalEligible: boolean;
    reportMode: "FORMAL_REPORT" | "PRE_REVIEW_REPORT";
    reasons: string[];
  };
  reportQuality?: {
    passed: boolean;
    blockingIssues: string[];
    warnings: string[];
    checks: Record<string, boolean>;
  };
  reportDocument?: {
    title: string;
    reportNumber: string;
    reportMode: "FORMAL_REPORT" | "PRE_REVIEW_REPORT";
    formalEligible: boolean;
  };
}
export interface EvaluationSnapshot {
  evaluationId: string; workItemId: string; workItemRevisionId: string; runId: string;
  status: string; result: PostEvaluationResult | Record<string, unknown> | null; capabilityPackVersionId: string;
  planHash: string; attachmentManifestHash: string; createdAt: string;
}
export interface AssessmentListResponse { items: EvaluationSnapshot[]; }
export interface ReportSnapshot {
  reportId: string; evaluationId: string; format: string; templateVersion: string;
  resultSchemaVersion: string; content: Record<string, unknown> | null; contentHash: string; createdAt: string;
}
export interface ReportListResponse { items: ReportSnapshot[]; }

export type BusinessWorkStatus = "planned" | "not_configured" | "incomplete" | "runnable" | "unavailable";

export interface BusinessWorkBlocker {
  code: string;
  message: string;
  ref: string | null;
}

export interface BusinessWorkFunctionSnapshot {
  name: string;
  description: string;
}

export interface BusinessWorkSnapshot {
  workKey: string;
  name: string;
  shortName: string;
  category: string;
  summary: string;
  status: BusinessWorkStatus;
  statusLabel: string;
  packName: string | null;
  packVersionId: string | null;
  packVersion: string | null;
  enabled: boolean;
  bindingStatus: string | null;
  blockers: BusinessWorkBlocker[];
  agents: string[];
  tools: string[];
  models: string[];
  documentRequirements: Array<{
    key?: string;
    category: string;
    displayName?: string;
    description?: string;
    required: boolean;
    minCount?: number;
    maxCount?: number | null;
    acceptedMediaTypes?: string[];
    classificationLabels?: string[];
    processingProfile?: string | null;
    extractionSchema?: string | null;
  }>;
  decisionSlots: Array<{ slot: string; required: boolean }>;
  functions: BusinessWorkFunctionSnapshot[];
  configuration: Record<string, unknown>;
  workItemType: string | null;
  caseBased: boolean;
  boundStrategyVersionId: string | null;
  boundStrategyName: string | null;
  boundStrategyVersion: number | null;
}

export interface BusinessWorkListResponse { items: BusinessWorkSnapshot[]; }

export interface AssessmentDetailSnapshot {
  assessmentId: string;
  evaluationId: string;
  caseId: string;
  workItemId: string;
  workItemRevisionId: string;
  runId: string;
  status: string;
  result: PostEvaluationResult | Record<string, unknown> | null;
  capabilityPackVersionId: string;
  planHash: string;
  attachmentManifestHash: string;
  registrySnapshot: Record<string, unknown>;
  createdAt: string;
  casePayload: Record<string, unknown> | null;
  caseStatus: string | null;
  scenarioType: string | null;
  owner: string | null;
}

export interface FindingSnapshot {
  findingId: string;
  workItemId: string;
  evaluationId: string;
  ruleKey: string;
  code: string;
  category: string;
  severity: string;
  status: string;
  title: string;
  detail: string;
  evidence: Record<string, unknown>;
}

export interface FindingListResponse { items: FindingSnapshot[]; }

export interface RuleSetDraftSnapshot {
  ruleSetId: string; draftId: string; revision: number; rules: Record<string, unknown>;
}
export interface RuleSetValidationResponse {
  valid: boolean; normalizedRules: Record<string, unknown>; preview: Record<string, unknown> | null;
}
export interface RuleSetVersionSnapshot {
  ruleSetId: string; ruleSetVersionId: string; version: number; schemaVersion: string;
  contentHash: string; rules: Record<string, unknown>;
}
