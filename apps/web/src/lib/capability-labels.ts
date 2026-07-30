/** Logical capability refs (without @version) → Chinese display names. */
export const CAPABILITY_LABELS: Record<string, string> = {
  "agent://builtin/researcher": "通用研究智能体",
  "agent://calibration/primary-diagnostician": "主诊断智能体",
  "agent://calibration/quality-supervisor": "质量监督智能体",
  "agent://calibration/scheduler": "调度决策智能体",
  "agent://calibration/standby-diagnostician": "备用诊断智能体",
  "agent://contract-performance/execution-evidence-analyst": "履约证据分析智能体",
  "agent://contract-performance/plan-extractor": "履约计划提取智能体",
  "agent://contract/baseline-analyst": "合同基准分析智能体",
  "agent://contract/document-classifier": "合同文件分类智能体",
  "agent://contract/performance-quality-analyst": "履约质量分析智能体",
  "agent://contract/finance-invoice-analyst": "财务与发票分析智能体",
  "agent://contract/deviation-risk-analyst": "偏差与风险分析智能体",
  "agent://contract/evidence-reviewer": "证据复核智能体",
  "agent://contract/field-extractor": "合同字段提取智能体",
  "agent://contract/post-evaluation-analyst": "合同后评价分析智能体",
  "agent://contract/performance-report-writer": "履约报告撰写智能体",
  "agent://contract/governance-report-writer": "治理报告撰写智能体",
  "agent://contract/report-narrator": "合同后评价报告统稿智能体",
  "agent://contract/report-quality-reviewer": "报告质量复核智能体",
  "agent://deviation/cost-change-fact-analyst": "成本与变更事实分析智能体",
  "agent://deviation/evidence-reviewer": "偏差证据复核智能体",
  "agent://deviation/report-narrator": "偏差报告撰写智能体",
  "agent://deviation/responsibility-analyst": "偏差责任分析智能体",
  "agent://deviation/root-cause-analyst": "偏差根因分析智能体",
  "agent://deviation/schedule-scope-fact-analyst": "进度与范围事实分析智能体",
  "agent://document/structurer": "文件结构化智能体",
  "agent://invoice/commercial-match-analyst": "发票商务匹配智能体",
  "agent://invoice/evidence-risk-reviewer": "发票证据风险复核智能体",
  "agent://invoice/fact-normalizer": "发票事实整理智能体",
  "agent://procurement/clause-evidence-analyst": "招采条款证据分析智能体",
  "agent://procurement/evidence-quality-reviewer": "招采证据质量复核智能体",
  "agent://supplier/risk-analyst": "供应商风险分析智能体",
};

export function logicalCapabilityRef(ref: string): string {
  return ref.replace(/@[^@/]+$/, "");
}

const PROJECT_UUID_RE =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

/**
 * Short label for a capability URI in selects (value stays the full ref).
 * `model://general@1` → `general`; `tool://document/read@1` → `document/read`;
 * `model://project/<uuid>@1` → `项目模型 · <uuid8>`.
 */
export function capabilityRefDisplayName(ref: string): string {
  const trimmed = ref.trim();
  const match = /^(agent|tool|model|policy):\/\/(.+)$/.exec(trimmed);
  if (!match) return trimmed;
  const scheme = match[1];
  const rest = match[2];
  const at = rest.lastIndexOf("@");
  const path = at >= 0 && !rest.slice(at + 1).includes("/") ? rest.slice(0, at) : rest;
  const projectMatch = /^project\/([^/]+)$/.exec(path);
  if (projectMatch) {
    const id = projectMatch[1];
    const short = PROJECT_UUID_RE.test(id) ? id.slice(0, 8) : id;
    const kindLabel =
      scheme === "model" ? "项目模型"
        : scheme === "tool" ? "项目工具"
          : scheme === "agent" ? "项目智能体"
            : "项目能力";
    return `${kindLabel} · ${short}`;
  }
  return path;
}

export function capabilityLabel(ref: string): string | null {
  return CAPABILITY_LABELS[logicalCapabilityRef(ref)] ?? null;
}

/** Prefer mapped Chinese label; keep project/custom names; soften raw role slugs. */
export function capabilityDisplayName(item: { ref: string; name: string }): string {
  const mapped = capabilityLabel(item.ref);
  if (mapped) return mapped;
  if (!looksLikeCapabilityRef(item.name) && !looksLikeRoleSlug(item.name)) return item.name;
  const fromName = capabilityLabel(item.name);
  if (fromName) return fromName;
  return humanizeRoleSlug(item.name);
}

/** If the query is a capability URI, show the Chinese label in the search box. */
export function normalizeCapabilitySearch(query: string): string {
  const trimmed = query.trim();
  if (!trimmed) return "";
  return capabilityLabel(trimmed) ?? trimmed;
}

export function capabilitySearchHaystack(item: { ref: string; name: string; description: string }): string {
  return `${capabilityDisplayName(item)} ${item.name} ${item.description} ${item.ref}`.toLowerCase();
}

function looksLikeCapabilityRef(value: string): boolean {
  return /^(agent|tool|model|policy):\/\//.test(value);
}

function looksLikeRoleSlug(value: string): boolean {
  return /^[a-z0-9]+(?:-[a-z0-9]+)+$/.test(value);
}

function humanizeRoleSlug(value: string): string {
  if (!looksLikeRoleSlug(value)) return value;
  return value
    .split("-")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}
