import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { ArrowLeft, Boxes, Braces, Play, Settings2, ShieldCheck } from "lucide-react";
import { Link, useNavigate, useParams } from "react-router";
import { api } from "@/api/client";
import type { CapabilityPackSnapshot, CaseSubjectInput } from "@/api/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { ErrorState } from "@/components/ui/error-state";
import { PageHeader } from "@/components/ui/page-header";
import { Skeleton } from "@/components/ui/skeleton";
import { useWorkspaceScope } from "@/lib/demo-scope";

type SubjectRole = CaseSubjectInput["role"];
type SubjectContract = { key: string; objectType: string; role: SubjectRole; min: number };
type BindingSlot = { slot: string; required: boolean };
type DocumentRequirement = { category: string; required: boolean };

const inputClass = "mt-2 h-11 w-full rounded-lg border border-gray-300 bg-white px-3 text-sm outline-none focus:border-brand-500 dark:border-gray-700 dark:bg-gray-900";

export function CapabilityPackWorkbenchPage() {
  const { packName = "" } = useParams();
  const { tenantId, projectId, workspacePath } = useWorkspaceScope();
  const navigate = useNavigate();
  const [owner, setOwner] = useState("");
  const [payloadSource, setPayloadSource] = useState("{}");
  const [inputError, setInputError] = useState<string | null>(null);
  const packs = useQuery({ queryKey: ["capability-packs", tenantId, projectId], queryFn: () => api.listCapabilityPacks(tenantId, projectId) });
  const pack = useMemo(() => selectPack(packs.data?.items ?? [], packName), [packName, packs.data]);
  const documentContracts = pack ? documentRequirements(pack) : [];
  const decisionContracts = pack ? decisionSlots(pack) : [];
  const documents = useQuery({ queryKey: ["documents", tenantId, projectId], queryFn: () => api.listDocuments(tenantId, projectId) });
  const bindings = useQuery({
    queryKey: ["capability-pack-bindings", tenantId, projectId, pack?.versionId],
    queryFn: () => {
      if (!pack) throw new Error("能力包版本尚未载入。");
      return api.getPackBindings(tenantId, projectId, pack.versionId);
    },
    enabled: Boolean(pack && decisionContracts.length),
  });

  useEffect(() => {
    if (pack) setPayloadSource(JSON.stringify(defaultPayload(workItemType(pack)), null, 2));
  }, [pack]);

  const availableCategories = new Set((documents.data?.items ?? []).filter((item) => item.status === "AVAILABLE").map((item) => item.category));
  const missingDocuments = documentContracts.filter((item) => item.required && !availableCategories.has(item.category));
  const missingDecisions = decisionContracts
    .filter((slot) => slot.required)
    .filter((slot) => !bindings.data?.decisions.some((binding) => binding.slot === slot.slot));
  const bindingStateRequired = decisionContracts.length > 0;
  const bindingsReady = !bindingStateRequired || (!bindings.isPending && !bindings.isError);
  const ready = Boolean(pack?.enabled && pack.bindingStatus !== "DEGRADED" && !pack.blockers.length && !missingDocuments.length && !missingDecisions.length && bindingsReady && !documents.isPending && !documents.isError);
  const run = useMutation({
    mutationFn: async () => {
      if (!pack) throw new Error("能力包版本尚未载入。");
      const payload = parseObject(payloadSource, "业务输入必须是 JSON 对象。");
      const type = workItemType(pack);
      const subjectContracts = requiredSubjects(pack);
      if (!subjectContracts.length) {
        const item = await api.createWorkItem(tenantId, projectId, { workItemType: type, payload, owner: owner.trim() || undefined });
        return api.executeWorkItem(tenantId, projectId, item.workItemId);
      }
      const subjects = await Promise.all(subjectContracts.map(async (contract) => {
        const data = subjectData(payload, contract.objectType);
        const object = await api.createBusinessObject(tenantId, projectId, {
          objectType: contract.objectType,
          canonicalKey: canonicalKey(data, payload, contract.objectType),
          schemaRef: `schema://${contract.objectType}/facts@1`,
          data,
          provenance: { source: "capability-pack-workbench", capabilityPackVersionId: pack.versionId },
        });
        return { businessObjectId: object.businessObjectId, businessObjectVersionId: object.versionId, role: contract.role, subjectKey: contract.key };
      }));
      const businessCase = await api.createCase(tenantId, projectId, { scenarioType: type, payload, subjects, owner: owner.trim() || undefined });
      return api.assessCase(tenantId, projectId, businessCase.caseId);
    },
    onSuccess: (evaluation) => navigate(`${workspacePath}/runs/${evaluation.runId}`),
    onError: (error) => setInputError(error instanceof SyntaxError ? "业务输入不是有效的 JSON。" : error.message),
  });

  if (packs.isPending) return <div className="space-y-4"><Skeleton className="h-24" /><Skeleton className="h-80" /></div>;
  if (packs.isError || !pack) return <LoadError message={packs.error?.message ?? `未找到业务能力包：${packName}`} onRetry={() => void packs.refetch()} />;

  const type = workItemType(pack);
  const subjectContracts = requiredSubjects(pack);
  const blockers = [
    ...pack.blockers.map((blocker) => `${blocker.ref}：${blocker.reasons.join("、")}`),
    ...missingDecisions.map((slot) => `决策槽位 ${slot.slot} 尚未绑定`),
    ...missingDocuments.map((item) => `${item.category} 类资料尚未准备`),
    ...(bindings.isError ? [`决策配置状态加载失败：${bindings.error.message}`] : []),
    ...(documents.isError ? [`业务资料加载失败：${documents.error.message}`] : []),
  ];

  return <div className="min-w-0 space-y-6">
    <div>
      <Link to={`${workspacePath}/capability-packs`} className="mb-3 inline-flex items-center gap-1 text-xs text-gray-500 hover:text-brand-600"><ArrowLeft className="size-4" />返回业务能力包</Link>
      <PageHeader
        eyebrow="业务能力包 · 工作台"
        title={businessName(pack.name)}
        description="填写本次业务输入，一次完成业务对象创建、能力包评估和耐久运行提交。"
        actions={<Button asChild variant="outline"><Link to={`${workspacePath}/capability-packs/${encodeURIComponent(pack.name)}`}><Settings2 />项目配置</Link></Button>}
      />
    </div>

    <section className="grid gap-3 sm:grid-cols-3" aria-label="运行资格">
      <Summary label="能力包版本" value={`v${pack.version}`} ok={pack.enabled} />
      <Summary label="启用状态" value={pack.enabled ? "已启用" : "未启用"} ok={pack.enabled && pack.bindingStatus !== "DEGRADED"} />
      <Summary label="运行类型" value={type} ok />
    </section>

    {!ready ? <Card><CardContent className="flex flex-wrap items-center justify-between gap-4 border border-warning-200 bg-warning-50 p-5 dark:border-warning-500/20 dark:bg-warning-500/10"><div><p className="font-medium text-warning-800 dark:text-warning-300">运行前还需准备资料或配置</p><ul className="mt-2 space-y-1 text-xs text-warning-700 dark:text-warning-400">{!pack.enabled ? <li>能力包尚未启用</li> : null}{pack.bindingStatus === "DEGRADED" ? <li>能力包当前处于退化状态</li> : null}{blockers.map((value) => <li key={value}>{value}</li>)}</ul></div><div className="flex gap-2"><Button asChild size="sm"><Link to={`${workspacePath}/documents`}>选择业务资料</Link></Button><Button asChild size="sm" variant="outline"><Link to={`${workspacePath}/capability-packs/${encodeURIComponent(pack.name)}`}>项目配置</Link></Button></div></CardContent></Card> : null}

    <Card><CardContent className="space-y-5 p-5">
      <div className="flex items-start gap-3"><span className="grid size-10 shrink-0 place-items-center rounded-xl bg-brand-50 text-brand-600 dark:bg-brand-500/10"><Braces className="size-5" /></span><div><h2 className="font-semibold text-gray-900 dark:text-white">本次运行输入</h2><p className="mt-1 text-xs leading-5 text-gray-500">输入会按能力包冻结的业务 Schema 校验；提交后可在运行详情查看 Temporal 执行进度。</p></div></div>
      <label className="block text-xs font-medium text-gray-700 dark:text-gray-300">负责人（可选）<input aria-label="负责人" value={owner} onChange={(event) => setOwner(event.target.value)} className={inputClass} /></label>
      <label className="block text-xs font-medium text-gray-700 dark:text-gray-300">业务输入 JSON<textarea aria-label="业务输入 JSON" spellCheck={false} value={payloadSource} onChange={(event) => { setPayloadSource(event.target.value); setInputError(null); }} className="mt-2 min-h-80 w-full resize-y rounded-xl border border-gray-300 bg-gray-950 p-4 font-mono text-xs leading-5 text-gray-100 outline-none focus:border-brand-500 dark:border-gray-700" /></label>
      {subjectContracts.length ? <p className="rounded-xl bg-gray-50 p-3 text-xs text-gray-500 dark:bg-gray-800/60">工作台会自动建立 {subjectContracts.map((subject) => `${subject.key}（${subject.objectType}）`).join("、")} 业务对象，并冻结到本次评估。</p> : null}
      {inputError ? <p role="alert" className="rounded-xl bg-error-50 p-3 text-sm text-error-600 dark:bg-error-500/10">运行提交失败：{inputError}</p> : null}
      <div className="flex justify-end"><Button loading={run.isPending} disabled={!ready || run.isPending} onClick={() => { setInputError(null); run.mutate(); }}><Play />开始运行</Button></div>
    </CardContent></Card>
  </div>;
}

function selectPack(items: CapabilityPackSnapshot[], name: string) {
  return items.filter((item) => item.name === name).sort((left, right) => {
    if (left.enabled !== right.enabled) return left.enabled ? -1 : 1;
    return right.version.localeCompare(left.version, undefined, { numeric: true });
  })[0];
}

function manifestSpec(pack: CapabilityPackSnapshot) {
  return pack.manifest.spec && typeof pack.manifest.spec === "object" ? pack.manifest.spec as Record<string, unknown> : {};
}

function workItemType(pack: CapabilityPackSnapshot) {
  const spec = manifestSpec(pack);
  const caseContract = spec.case;
  if (caseContract && typeof caseContract === "object" && typeof (caseContract as Record<string, unknown>).type === "string") return (caseContract as Record<string, unknown>).type as string;
  return typeof spec.workItemType === "string" ? spec.workItemType : pack.name;
}

function requiredSubjects(pack: CapabilityPackSnapshot): SubjectContract[] {
  const value = manifestSpec(pack).case;
  if (!value || typeof value !== "object") return [];
  const caseContract = value as Record<string, unknown>;
  const roles = caseContract.subjectRoles;
  if (!Array.isArray(roles)) return [];
  const contracts = roles.flatMap((item): SubjectContract[] => {
    if (!item || typeof item !== "object") return [];
    const role = item as Record<string, unknown>;
    if (typeof role.key !== "string" || typeof role.objectType !== "string" || !isSubjectRole(role.role)) return [];
    return [{ key: role.key, objectType: role.objectType, role: role.role, min: typeof role.min === "number" ? role.min : 0 }];
  });
  const required = contracts.filter((contract) => contract.min > 0);
  if (required.length || caseContract.subjectsRequired !== true) return required;
  const primary = contracts.find((contract) => contract.role === "PRIMARY");
  return primary ? [primary] : [];
}

function documentRequirements(pack: CapabilityPackSnapshot): DocumentRequirement[] {
  const value = manifestSpec(pack).documents;
  if (!Array.isArray(value)) return [];
  return value.flatMap((item) => item && typeof item === "object" && typeof (item as Record<string, unknown>).category === "string"
    ? [{ category: (item as Record<string, unknown>).category as string, required: (item as Record<string, unknown>).required === true }]
    : []);
}

function decisionSlots(pack: CapabilityPackSnapshot): BindingSlot[] {
  const value = manifestSpec(pack).decisions;
  if (!Array.isArray(value)) return [];
  return value.flatMap((item) => item && typeof item === "object" && typeof (item as Record<string, unknown>).slot === "string"
    ? [{ slot: (item as Record<string, unknown>).slot as string, required: (item as Record<string, unknown>).required === true }]
    : []);
}

function isSubjectRole(value: unknown): value is SubjectRole {
  return value === "PRIMARY" || value === "COMPARISON" || value === "EVIDENCE" || value === "RELATED";
}

function parseObject(source: string, message: string) {
  const value: unknown = JSON.parse(source);
  if (!value || typeof value !== "object" || Array.isArray(value)) throw new Error(message);
  return value as Record<string, unknown>;
}

function subjectData(payload: Record<string, unknown>, objectType: string) {
  const value = payload[objectType];
  return value && typeof value === "object" && !Array.isArray(value) ? value as Record<string, unknown> : payload;
}

function canonicalKey(data: Record<string, unknown>, payload: Record<string, unknown>, objectType: string) {
  for (const key of [`${objectType}Id`, "id", "canonicalKey", "title"]) {
    const value = data[key] ?? payload[key];
    if (typeof value === "string" && value.trim()) return value.trim();
  }
  return `${objectType}-${crypto.randomUUID()}`;
}

function defaultPayload(type: string): Record<string, unknown> {
  if (type === "contract-post-evaluation-case") return {
    title: "合同后评价",
    evaluationPeriod: { start: "2026-01-01", end: "2026-06-30" },
    contract: { contractId: "HT-2026-001", contractName: "采购合同", contractAmount: 100000, currency: "CNY" },
    documents: [], obligations: [], deviations: [], invoices: [], risks: [],
  };
  if (type === "contract-case") return { title: "采购合同检查", contractType: "purchase" };
  return {};
}

function businessName(value: string) {
  return value === "contract-post-evaluation" ? "合同后评价工作台" : `${value} 工作台`;
}

function Summary({ label, value, ok }: { label: string; value: string; ok: boolean }) {
  return <Card><CardContent className="flex items-center gap-3 p-4"><span className={`grid size-9 shrink-0 place-items-center rounded-full ${ok ? "bg-success-50 text-success-600 dark:bg-success-500/10" : "bg-warning-50 text-warning-600 dark:bg-warning-500/10"}`}>{ok ? <ShieldCheck className="size-4" /> : <Boxes className="size-4" />}</span><div className="min-w-0"><p className="text-xs text-gray-500">{label}</p><p className="mt-1 truncate text-sm font-medium text-gray-900 dark:text-white" title={value}>{value}</p></div></CardContent></Card>;
}

function LoadError({ message, onRetry }: { message: string; onRetry: () => void }) {
  return <Card><CardContent className="pt-5"><ErrorState title="能力包工作台无法加载" message={message} onRetry={onRetry} /></CardContent></Card>;
}
