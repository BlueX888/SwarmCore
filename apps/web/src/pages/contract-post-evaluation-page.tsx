import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Bot, Boxes, Check, Cpu, Files, Play, RefreshCw, Save, ShieldCheck, Workflow } from "lucide-react";
import { Link, useParams } from "react-router";
import { api } from "@/api/client";
import type { CapabilityPackSnapshot } from "@/api/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useWorkspaceScope } from "@/lib/demo-scope";

type DocumentRequirement = {
  category: string;
  required: boolean;
};

const categoryLabels: Record<string, string> = {
  CONTRACT: "合同文件",
  PERFORMANCE: "履约资料",
  DEVIATION: "偏差资料",
  INVOICE: "发票资料",
  SUPPLIER: "供应商资料",
  REPORT: "报告与成果",
};

export function CapabilityPackConfigurationPage() {
  const { packName = "contract-post-evaluation" } = useParams();
  const { tenantId, projectId, workspacePath } = useWorkspaceScope();
  const queryClient = useQueryClient();
  const [configurationSource, setConfigurationSource] = useState("{}");
  const [configurationError, setConfigurationError] = useState<string | null>(null);
  const packs = useQuery({ queryKey: ["capability-packs", tenantId, projectId], queryFn: () => api.listCapabilityPacks(tenantId, projectId) });
  const documents = useQuery({ queryKey: ["documents", tenantId, projectId], queryFn: () => api.listDocuments(tenantId, projectId) });
  const pack = useMemo(() => packs.data?.items
    .filter((item) => item.name === packName)
    .sort((left, right) => right.version.localeCompare(left.version, undefined, { numeric: true }))[0], [packName, packs.data]);
  useEffect(() => {
    if (pack) setConfigurationSource(JSON.stringify(pack.configuration ?? {}, null, 2));
  }, [pack]);

  const saveConfiguration = useMutation({
    mutationFn: async () => {
      if (!pack) throw new Error("能力包版本尚未载入。");
      const value: unknown = JSON.parse(configurationSource);
      if (!value || typeof value !== "object" || Array.isArray(value)) throw new Error("运行配置必须是 JSON 对象。");
      await api.enableCapabilityPack(tenantId, projectId, pack.versionId, value as Record<string, unknown>);
    },
    onSuccess: async () => {
      setConfigurationError(null);
      await queryClient.invalidateQueries({ queryKey: ["capability-packs", tenantId, projectId] });
    },
    onError: (error) => setConfigurationError(error instanceof SyntaxError ? "运行配置不是有效的 JSON。" : error.message),
  });
  if (packs.isPending) return <div className="space-y-4"><Skeleton className="h-24" /><Skeleton className="h-72" /></div>;
  if (packs.isError) return <LoadError message={packs.error.message} onRetry={() => void packs.refetch()} />;
  if (!pack) return <LoadError message={`未找到业务能力包：${packName}`} onRetry={() => void packs.refetch()} />;

  const spec = manifestSpec(pack);
  const requirements = documentRequirements(pack);
  const agents = stringList(spec.agents);
  const tools = stringList(spec.tools);
  const strategies = stringValues(spec.strategies);
  const policies = stringList(spec.permissions);
  const availableCategories = new Set((documents.data?.items ?? []).filter((item) => item.status === "AVAILABLE").map((item) => item.category));
  const requiredDocuments = requirements.filter((item) => item.required);
  const configuredRequired = requiredDocuments.filter((item) => availableCategories.has(item.category)).length;

  return <div className="min-w-0 space-y-6">
    <header className="flex flex-wrap items-end justify-between gap-4">
      <div>
        <Link to={`${workspacePath}/capability-packs`} className="mb-3 inline-flex items-center gap-1 text-xs text-gray-500 hover:text-brand-600"><ArrowLeft className="size-4" />返回业务能力包</Link>
        <p className="text-sm font-medium text-brand-500">业务能力包 · 项目配置</p>
        <h1 className="mt-1 text-2xl font-semibold text-gray-900 dark:text-white">{businessName(pack.name)}</h1>
        <p className="mt-1 text-sm text-gray-500">为具体业务组合平台底座能力，并配置当前项目使用的资料和运行参数。</p>
      </div>
      <div className="flex flex-wrap items-center gap-2"><StatusBadge pack={pack} />{pack.enabled && pack.bindingStatus !== "DEGRADED" && !pack.blockers.length ? <Button asChild><Link to={`${workspacePath}/capability-packs/${encodeURIComponent(pack.name)}/workbench`}><Play />进入工作台</Link></Button> : null}<Button variant="outline" onClick={() => void Promise.all([packs.refetch(), documents.refetch()])} loading={packs.isFetching || documents.isFetching}><RefreshCw />刷新</Button></div>
    </header>

    <section className="grid gap-3 md:grid-cols-4" aria-label="能力包配置进度">
      <SummaryCard label="能力包版本" value={`v${pack.version}`} detail="已发布的不可变版本" icon={Boxes} />
      <SummaryCard label="编排策略" value={`${strategies.length} 项`} detail={strategies[0] ? referenceLabel(strategies[0]) : "未声明"} icon={Workflow} />
      <SummaryCard label="Agent / 工具" value={`${agents.length} / ${tools.length}`} detail="由能力包版本锁定" icon={Bot} />
      <SummaryCard label="必需资料" value={`${configuredRequired} / ${requiredDocuments.length}`} detail={configuredRequired === requiredDocuments.length ? "资料已准备" : "仍有资料待上传"} icon={Files} />
    </section>

    <Card><CardContent className="space-y-5 p-5">
      <SectionTitle icon={Files} title="业务资料要求" description="系统会按文件分类和业务关联自动选择资料；无法匹配时会提示用户选择。" action={<Button asChild variant="outline" size="sm"><Link to={`${workspacePath}/documents`}>打开业务资料库</Link></Button>} />
      {documents.isError ? <p role="alert" className="text-sm text-error-600">资料加载失败：{documents.error.message}</p> : null}
      <div className="grid gap-3 lg:grid-cols-2">{requirements.map((requirement) => {
        const available = availableCategories.has(requirement.category);
        return <article key={requirement.category} className="min-w-0 rounded-xl border border-gray-200 p-4 dark:border-gray-800"><div className="flex items-start justify-between gap-3"><div><h3 className="font-medium text-gray-900 dark:text-white">{categoryLabels[requirement.category] ?? requirement.category}</h3><p className="mt-1 text-xs text-gray-500">{requirement.required ? "执行前需要" : "可选资料"} · 自动按分类和业务对象匹配</p></div>{available ? <span className="inline-flex items-center gap-1 rounded-full bg-success-50 px-2 py-1 text-xs text-success-700 dark:bg-success-500/10"><Check className="size-3.5" />已准备</span> : <span className="rounded-full bg-warning-50 px-2 py-1 text-xs text-warning-700 dark:bg-warning-500/10">待上传</span>}</div></article>;
      })}</div>
    </CardContent></Card>

    <div className="grid gap-4 xl:grid-cols-2">
      <Card><CardContent className="space-y-5 p-5"><SectionTitle icon={Workflow} title="底座能力编排" description="版本内依赖不可直接改写；需要调整时发布新的能力包版本。" />
        <DependencyGroup title="编排策略" values={strategies} empty="未声明编排策略" />
        <DependencyGroup title="Agent" values={agents} empty="未声明 Agent" managePath={`${workspacePath}/agents`} />
        <DependencyGroup title="工具" values={tools} empty="未声明工具" managePath={`${workspacePath}/tools`} />
        <DependencyGroup title="模型" values={[]} empty="模型由 Agent 配置解析" managePath={`${workspacePath}/models`} />
        <DependencyGroup title="权限策略" values={policies} empty="未声明权限" managePath={`${workspacePath}/policies`} />
      </CardContent></Card>

      <Card><CardContent className="space-y-5 p-5"><SectionTitle icon={ShieldCheck} title="项目运行配置" description="配置仅作用于当前项目，不改变已发布的能力包版本。请勿填写密码或 Token。" />
        <label className="block text-xs font-medium text-gray-700 dark:text-gray-300">运行参数 JSON<textarea aria-label="项目运行配置 JSON" spellCheck={false} value={configurationSource} onChange={(event) => { setConfigurationSource(event.target.value); setConfigurationError(null); }} className="mt-2 min-h-52 w-full resize-y rounded-xl border border-gray-300 bg-white p-3 font-mono text-xs leading-5 outline-none focus:border-brand-500 dark:border-gray-700 dark:bg-gray-900" /></label>
        {configurationError ? <p role="alert" className="text-sm text-error-600">{configurationError}</p> : null}
        <div className="flex justify-end"><Button loading={saveConfiguration.isPending} disabled={!pack.enabled && pack.blockers.length > 0} onClick={() => saveConfiguration.mutate()}><Save />{pack.enabled ? "保存配置" : "保存并启用"}</Button></div>
        {pack.blockers.length ? <div className="rounded-xl bg-warning-50 p-3 text-xs text-warning-700 dark:bg-warning-500/10"><p className="font-semibold">启用前需处理</p><ul className="mt-2 space-y-1">{pack.blockers.map((blocker) => <li key={blocker.ref}>{referenceLabel(blocker.ref)}：{blocker.reasons.join("、")}</li>)}</ul></div> : null}
      </CardContent></Card>
    </div>
  </div>;
}

function manifestSpec(pack: CapabilityPackSnapshot) {
  return pack.manifest.spec && typeof pack.manifest.spec === "object" ? pack.manifest.spec as Record<string, unknown> : {};
}

function documentRequirements(pack: CapabilityPackSnapshot): DocumentRequirement[] {
  const value = manifestSpec(pack).documents;
  if (!Array.isArray(value)) return [];
  return value.flatMap((item) => {
    if (!item || typeof item !== "object") return [];
    const requirement = item as Record<string, unknown>;
    if (typeof requirement.category !== "string") return [];
    return [{ category: requirement.category, required: requirement.required === true }];
  });
}

function stringList(value: unknown) {
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === "string") : [];
}

function stringValues(value: unknown) {
  return value && typeof value === "object" && !Array.isArray(value) ? Object.values(value).filter((item): item is string => typeof item === "string") : [];
}

function businessName(value: string) {
  return value === "contract-post-evaluation" ? "合同后评价" : value;
}

function referenceLabel(value: string) {
  const tail = value.includes("://") ? value.slice(value.indexOf("://") + 3) : value;
  return tail.replace(/@[^@/]+$/, "");
}

function StatusBadge({ pack }: { pack: CapabilityPackSnapshot }) {
  const active = pack.enabled && pack.bindingStatus !== "DEGRADED";
  return <span className={`rounded-full px-3 py-1 text-xs font-medium ${active ? "bg-success-50 text-success-700 dark:bg-success-500/10" : "bg-warning-50 text-warning-700 dark:bg-warning-500/10"}`}>{active ? "已启用" : pack.bindingStatus === "DEGRADED" ? "配置不完整" : "未启用"}</span>;
}

function SummaryCard({ label, value, detail, icon: Icon }: { label: string; value: string; detail: string; icon: typeof Boxes }) {
  return <Card className="min-w-0"><CardContent className="flex min-w-0 items-start gap-3 p-4"><span className="grid size-10 shrink-0 place-items-center rounded-xl bg-brand-50 text-brand-600 dark:bg-brand-500/10"><Icon className="size-5" /></span><div className="min-w-0"><p className="text-xs text-gray-500">{label}</p><p className="mt-1 font-semibold text-gray-900 dark:text-white">{value}</p><p className="mt-1 truncate text-xs text-gray-400" title={detail}>{detail}</p></div></CardContent></Card>;
}

function SectionTitle({ icon: Icon, title, description, action }: { icon: typeof Files; title: string; description: string; action?: React.ReactNode }) {
  return <div className="flex flex-wrap items-start justify-between gap-3"><div className="flex items-start gap-3"><span className="grid size-10 shrink-0 place-items-center rounded-xl bg-brand-50 text-brand-600 dark:bg-brand-500/10"><Icon className="size-5" /></span><div><h2 className="font-semibold text-gray-900 dark:text-white">{title}</h2><p className="mt-1 text-xs leading-5 text-gray-500">{description}</p></div></div>{action}</div>;
}

function DependencyGroup({ title, values, empty, managePath }: { title: string; values: string[]; empty: string; managePath?: string }) {
  return <section className="border-t border-gray-100 pt-4 first:border-0 first:pt-0 dark:border-gray-800"><div className="flex items-center justify-between gap-3"><h3 className="text-xs font-semibold text-gray-500">{title}</h3>{managePath ? <Link to={managePath} className="text-xs text-brand-600 hover:underline">底座管理</Link> : null}</div>{values.length ? <div className="mt-2 flex flex-wrap gap-2">{values.map((value) => <span key={value} title={value} className="rounded-lg bg-gray-50 px-2.5 py-1.5 text-xs text-gray-700 dark:bg-gray-800 dark:text-gray-300">{referenceLabel(value)}</span>)}</div> : <p className="mt-2 text-xs text-gray-400">{empty}</p>}</section>;
}

function LoadError({ message, onRetry }: { message: string; onRetry: () => void }) {
  return <Card><CardContent className="flex min-h-60 flex-col items-center justify-center gap-3 p-5 text-center"><Cpu className="size-8 text-gray-400" /><p className="font-medium text-gray-900 dark:text-white">能力包配置无法加载</p><p className="text-sm text-gray-500">{message}</p><Button onClick={onRetry}>重试</Button></CardContent></Card>;
}

// Keep the previous export name for imports outside the web router.
export const ContractPostEvaluationPage = CapabilityPackConfigurationPage;
