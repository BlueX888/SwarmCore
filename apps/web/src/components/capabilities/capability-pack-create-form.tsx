import { useEffect, useMemo, useState, type FormEvent, type ReactNode } from "react";
import * as Dialog from "@radix-ui/react-dialog";
import { Boxes, Bot, Gauge, Route, Wrench, X } from "lucide-react";
import type { CapabilityPackSnapshot, CreateCapabilityPackRequest, StrategyVersionDetail } from "@/api/types";
import { Button } from "@/components/ui/button";
import { StrategyGraphPreview } from "@/components/strategy/strategy-graph-preview";

export interface CapabilityPackStrategyOption {
  strategyName: string;
  version: StrategyVersionDetail;
}

interface CapabilityPackCreateFormProps {
  packs: CapabilityPackSnapshot[];
  strategies: CapabilityPackStrategyOption[];
  loadingStrategies: boolean;
  pending: boolean;
  error?: string;
  onCancel: () => void;
  onSubmit: (request: CreateCapabilityPackRequest) => void;
}

export function CapabilityPackCreateForm({ packs, strategies, loadingStrategies, pending, error, onCancel, onSubmit }: CapabilityPackCreateFormProps) {
  const [name, setName] = useState("custom-capability");
  const [version, setVersion] = useState("1.0.0");
  const [workItemType, setWorkItemType] = useState("custom-work-item");
  const [templateVersionId, setTemplateVersionId] = useState(packs[0]?.versionId ?? "");
  const [strategyVersionId, setStrategyVersionId] = useState("");
  const [formError, setFormError] = useState("");

  useEffect(() => {
    if (!templateVersionId && packs[0]) setTemplateVersionId(packs[0].versionId);
  }, [packs, templateVersionId]);
  useEffect(() => {
    if (!strategyVersionId && strategies[0]) setStrategyVersionId(strategies[0].version.strategyVersionId);
  }, [strategies, strategyVersionId]);

  const selectedStrategy = strategies.find((item) => item.version.strategyVersionId === strategyVersionId);
  const dependencies = useMemo(() => selectedStrategy ? strategyDependencies(selectedStrategy.version.plan) : { agents: [], agentDisplay: [], tools: [], budget: {} }, [selectedStrategy]);

  function submit(event: FormEvent) {
    event.preventDefault();
    const template = packs.find((item) => item.versionId === templateVersionId);
    if (!template) return setFormError("请选择业务资产模板。");
    if (!selectedStrategy) return setFormError("请选择策略管理中已发布的运行策略版本。");
    if (!/^[a-z][a-z0-9-]{0,62}$/.test(name)) return setFormError("名称需使用小写字母、数字和连字符。");
    if (!/^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$/.test(version)) return setFormError("版本需使用 major.minor.patch 格式。");
    if (!workItemType.trim()) return setFormError("请输入工作项类型。");
    setFormError("");
    onSubmit(buildCreateRequest({ template, selectedStrategy, name, version, workItemType: workItemType.trim(), dependencies }));
  }

  return <Dialog.Root open onOpenChange={(open) => { if (!open) onCancel(); }}><Dialog.Portal>
    <Dialog.Overlay className="fixed inset-0 z-40 bg-gray-950/50 backdrop-blur-[2px]" />
    <Dialog.Content className="fixed left-1/2 top-1/2 z-50 w-[calc(100vw-2rem)] max-w-6xl -translate-x-1/2 -translate-y-1/2 outline-none">
    <form onSubmit={submit} className="flex max-h-[92vh] flex-col overflow-hidden rounded-2xl border border-brand-200 bg-white shadow-theme-xl dark:border-brand-500/30 dark:bg-gray-900">
    <div className="flex shrink-0 items-start justify-between gap-4 border-b border-gray-100 p-5 dark:border-gray-800">
      <div className="flex gap-3"><span className="grid size-11 shrink-0 place-items-center rounded-xl bg-brand-50 text-brand-600 dark:bg-brand-500/15"><Boxes /></span><div><Dialog.Title asChild><h2 className="font-semibold text-gray-900 dark:text-white">新建业务能力包</h2></Dialog.Title><Dialog.Description className="mt-1 text-sm text-gray-500">绑定策略管理中已发布的运行策略版本，发布新的不可变能力包。</Dialog.Description></div></div>
      <Button type="button" variant="ghost" size="icon" aria-label="关闭新建能力包" onClick={onCancel}><X /></Button>
    </div>
    <div className="flex min-h-0 flex-1 flex-col gap-6 overflow-y-auto p-5">
      <section>
        <SectionTitle icon={<Boxes />} title="基本信息" description="名称与版本发布后不可修改；后续变更请发布新版本。" />
        <div className="mt-4 grid gap-4 sm:grid-cols-2">
          <Field label="能力包名称"><input aria-label="能力包名称" value={name} onChange={(event) => setName(event.target.value)} className={inputClass} /></Field>
          <Field label="版本"><input aria-label="能力包版本" value={version} onChange={(event) => setVersion(event.target.value)} className={inputClass} /></Field>
        </div>
        <div className="mt-4 grid gap-4 sm:grid-cols-2">
          <Field label="工作项类型"><input aria-label="工作项类型" value={workItemType} onChange={(event) => setWorkItemType(event.target.value)} className={inputClass} /></Field>
          <Field label="业务资产模板"><select aria-label="业务资产模板" value={templateVersionId} onChange={(event) => setTemplateVersionId(event.target.value)} className={inputClass}>{packs.map((pack) => <option key={pack.versionId} value={pack.versionId}>{pack.name} v{pack.version}</option>)}</select></Field>
        </div>
      </section>

      <section className="space-y-4 border-t border-gray-100 pt-6 dark:border-gray-800">
        <SectionTitle icon={<Route />} title="运行策略与策略图" description="选择已发布的不可变策略版本，下方只读流程图会同步更新；修改请前往策略管理。" />
        <Field label="已发布策略版本">
          <select aria-label="已发布策略版本" value={strategyVersionId} disabled={loadingStrategies || !strategies.length} onChange={(event) => setStrategyVersionId(event.target.value)} className={inputClass}>
            <option value="">{loadingStrategies ? "正在加载策略…" : strategies.length ? "选择运行策略" : "暂无已发布策略"}</option>
            {strategies.map((item) => <option key={item.version.strategyVersionId} value={item.version.strategyVersionId}>{item.strategyName} · v{item.version.version} · {item.version.planHash.slice(0, 8)}</option>)}
          </select>
        </Field>
        {selectedStrategy ? <>
          <div className="rounded-xl bg-gray-50 p-4 text-xs text-gray-500 dark:bg-gray-800">
            <p>计划哈希：<span className="break-all font-mono text-gray-700 dark:text-gray-300">{selectedStrategy.version.planHash}</span></p>
            <p className="mt-2">该版本的运行预算、Agent 和工具均来自已发布执行计划。需要调整时，请先在策略管理中修改并发布新版本。</p>
          </div>
          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-gray-900 dark:text-white">策略图设计</h3>
            <StrategyGraphPreview spec={selectedStrategy.version.spec} />
          </div>
        </> : <p className="rounded-xl border border-dashed border-gray-200 px-4 py-10 text-center text-sm text-gray-400 dark:border-gray-700">选择策略后显示策略图设计预览。</p>}
      </section>

      <div className="grid gap-5 border-t border-gray-100 pt-6 md:grid-cols-3 dark:border-gray-800">
        <DependencyList icon={<Gauge />} title="冻结的运行预算" items={budgetItems(dependencies.budget)} empty="选择策略后显示预算。" />
        <DependencyList icon={<Bot />} title="Agent 依赖" items={dependencies.agentDisplay} empty="该策略未包含 Agent。" mono />
        <DependencyList icon={<Wrench />} title="工具依赖" items={dependencies.tools} empty="该策略未引用工具。" mono />
      </div>
    </div>
    {(formError || error) ? <p role="alert" className="mx-5 mb-4 rounded-xl bg-error-50 p-3 text-sm text-error-600 dark:bg-error-500/10">{formError || `创建失败：${error}`}</p> : null}
    <div className="flex shrink-0 justify-end gap-2 border-t border-gray-100 px-5 py-4 dark:border-gray-800"><Button type="button" variant="outline" onClick={onCancel}>取消</Button><Button type="submit" loading={pending} disabled={!packs.length || loadingStrategies || !strategies.length}>发布能力包</Button></div>
    </form>
    </Dialog.Content>
  </Dialog.Portal></Dialog.Root>;
}

function DependencyList({ icon, title, items, empty, mono = false }: { icon: ReactNode; title: string; items: string[]; empty: string; mono?: boolean }) {
  return <section><SectionTitle icon={icon} title={title} description="来自所选 StrategyVersion 的冻结执行计划。" />{items.length ? <ul className="mt-3 space-y-2">{items.map((item) => <li key={item} className={`break-all rounded-xl border border-gray-200 p-3 text-xs text-gray-700 dark:border-gray-800 dark:text-gray-300 ${mono ? "font-mono" : ""}`}>{item}</li>)}</ul> : <p className="mt-3 text-sm text-gray-400">{empty}</p>}</section>;
}

function SectionTitle({ icon, title, description }: { icon: ReactNode; title: string; description: string }) {
  return <div className="flex gap-3"><span className="mt-0.5 text-brand-500 [&_svg]:size-5">{icon}</span><div><h3 className="text-sm font-semibold text-gray-900 dark:text-white">{title}</h3><p className="mt-1 text-xs text-gray-500">{description}</p></div></div>;
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return <label className="text-xs font-medium text-gray-700 dark:text-gray-300">{label}{children}</label>;
}

const inputClass = "mt-2 h-10 w-full rounded-lg border border-gray-300 bg-transparent px-3 text-sm text-gray-800 outline-none focus:border-brand-500 disabled:opacity-60 dark:border-gray-700 dark:text-gray-200";

function buildCreateRequest({ template, selectedStrategy, name, version, workItemType, dependencies }: { template: CapabilityPackSnapshot; selectedStrategy: CapabilityPackStrategyOption; name: string; version: string; workItemType: string; dependencies: ReturnType<typeof strategyDependencies> }): CreateCapabilityPackRequest {
  const manifest = structuredClone(template.manifest);
  const spec = objectValue(manifest.spec);
  const strategyRef = `strategy://project/${selectedStrategy.version.strategyId}@${selectedStrategy.version.version}`;
  const apiVersion = manifest.apiVersion === "swarmcore.io/v2" ? "swarmcore.io/v2" : "swarmcore.io/v1";
  manifest.apiVersion = apiVersion;
  manifest.kind = "CapabilityPack";
  manifest.metadata = { name, version };
  const caseDefinition = objectValue(spec.case);
  manifest.spec = {
    ...spec,
    ...(apiVersion === "swarmcore.io/v2" ? { case: { ...caseDefinition, type: workItemType } } : { workItemType }),
    strategies: { execute: strategyRef },
    agents: dependencies.agents,
    tools: dependencies.tools,
    events: { namespace: `capability.${name}` },
  };
  return { manifest, strategyVersionId: selectedStrategy.version.strategyVersionId };
}

function strategyDependencies(plan: Record<string, unknown>) {
  const resolvedAgents = objectValue(plan.resolved_agents);
  const agents = Object.values(resolvedAgents).flatMap((value) => {
    const ref = objectValue(value).registryRef;
    return typeof ref === "string" ? [ref] : [];
  });
  const agentDisplay = Object.entries(resolvedAgents).map(([key, value]) => {
    const declaration = objectValue(value);
    const ref = declaration.registryRef;
    if (typeof ref === "string") return ref;
    const role = declaration.role;
    return typeof role === "string" ? `内联 Agent：${key} · ${role}` : `内联 Agent：${key}`;
  });
  const agentTools = Object.values(resolvedAgents).flatMap((value) => {
    const tools = objectValue(value).tools;
    return Array.isArray(tools) ? tools.filter((item): item is string => typeof item === "string") : [];
  });
  return {
    agents: [...new Set(agents)].sort(),
    agentDisplay: [...new Set(agentDisplay)].sort(),
    tools: [...new Set([...Object.keys(objectValue(plan.resolved_tools)), ...agentTools])].sort(),
    budget: objectValue(plan.budget),
  };
}

function budgetItems(budget: Record<string, unknown>) {
  const fields: Array<[string, string, string]> = [
    ["max_duration", "maxDuration", "最长运行时间"], ["max_tokens", "maxTokens", "最大 Token"],
    ["max_cost_usd", "maxCostUsd", "最大成本（USD）"], ["max_agents", "maxAgents", "最大 Agent 数"],
    ["max_parallelism", "maxParallelism", "最大并行数"], ["on_exhausted", "onExhausted", "预算耗尽策略"],
  ];
  return fields.flatMap(([snakeKey, camelKey, label]) => {
    const value = budget[snakeKey] ?? budget[camelKey];
    return value === undefined ? [] : [`${label}：${displayValue(value)}`];
  });
}

function displayValue(value: unknown) {
  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") return String(value);
  return JSON.stringify(value);
}

function objectValue(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value) ? value as Record<string, unknown> : {};
}
