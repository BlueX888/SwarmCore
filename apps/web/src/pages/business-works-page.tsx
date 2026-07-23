import { useMemo, useState } from "react";
import {
  ArrowRight, Bot, BrainCircuit, BriefcaseBusiness, CheckCircle2, Files,
  FileCheck2, FileOutput, FileScan, Gauge, Network, ReceiptText, Search, ShieldCheck,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { Link, useParams } from "react-router";
import { Badge } from "@/components/ui/badge";
import { BackLink } from "@/components/ui/back-link";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  BUSINESS_WORK_CATEGORIES, BUSINESS_WORKS, getBusinessWork,
  type BusinessWorkCategory, type BusinessWorkDefinition,
} from "@/lib/business-works";
import { useWorkspaceScope } from "@/lib/demo-scope";
import { cn } from "@/lib/utils";

const WORK_ICONS: Record<string, LucideIcon> = {
  "ai-foundation-quality": BrainCircuit,
  "document-structuring": FileScan,
  "document-integrity": FileCheck2,
  "performance-plan-collection": BriefcaseBusiness,
  "invoice-assurance": ReceiptText,
  "deviation-analysis": Gauge,
  "report-generation": FileOutput,
  "swarm-calibration": Network,
  "procurement-supplier-risk": ShieldCheck,
};

const CATEGORY_LABELS: Record<BusinessWorkCategory, string> = {
  foundation: "基础能力",
  business: "业务处理",
  governance: "调度治理",
};

export function BusinessWorksPage() {
  const { workKey } = useParams();
  return workKey ? <BusinessWorkDetail workKey={workKey} /> : <BusinessWorkCatalog />;
}

function BusinessWorkCatalog() {
  const { workspacePath } = useWorkspaceScope();
  const [category, setCategory] = useState<"all" | BusinessWorkCategory>("all");
  const [search, setSearch] = useState("");
  const visibleWorks = useMemo(() => {
    const keyword = search.trim().toLocaleLowerCase();
    return BUSINESS_WORKS.filter((work) => {
      if (category !== "all" && work.category !== category) return false;
      if (!keyword) return true;
      return [work.name, work.shortName, work.summary, ...work.functions.flatMap((item) => [item.name, item.description])]
        .some((value) => value.toLocaleLowerCase().includes(keyword));
    });
  }, [category, search]);

  return <div className="min-w-0 space-y-6">
    <header className="flex flex-wrap items-end justify-between gap-4">
      <div>
        <p className="text-sm font-medium text-brand-500">AI 智能体蜂群</p>
        <h1 className="mt-1 text-2xl font-semibold text-gray-900 dark:text-white">业务工作</h1>
        <p className="mt-1 max-w-3xl text-sm text-gray-500">按业务目标组织工作，每项工作独立组合 Agent、工具、模型、规则、业务资料和人工复核。</p>
      </div>
      <Button asChild><Link to={`${workspacePath}/canvas`}><Network />编排新工作</Link></Button>
    </header>

    <section aria-label="业务工作概况" className="grid gap-3 sm:grid-cols-3">
      <SummaryCard label="业务工作" value={BUSINESS_WORKS.length} detail="独立工作入口" />
      <SummaryCard label="功能模块" value={BUSINESS_WORKS.reduce((total, work) => total + work.functions.length, 0)} detail="按需组合扩展" />
      <SummaryCard label="统一底座" value={5} detail="Agent · 工具 · 模型 · 规则 · 资料" />
    </section>

    <section className="space-y-4">
      <div className="flex flex-col gap-3 rounded-2xl border border-gray-200/80 bg-white/80 p-3 shadow-theme-xs backdrop-blur sm:flex-row sm:items-center sm:justify-between dark:border-gray-800 dark:bg-gray-900/70">
        <div className="flex gap-1 overflow-x-auto" role="group" aria-label="业务工作分类">
          {BUSINESS_WORK_CATEGORIES.map((item) => <button
            key={item.value}
            type="button"
            aria-pressed={category === item.value}
            onClick={() => setCategory(item.value)}
            className={cn("shrink-0 rounded-xl px-3 py-2 text-sm font-semibold transition", category === item.value ? "bg-brand-50 text-brand-600 dark:bg-brand-500/15 dark:text-brand-400" : "text-gray-500 hover:bg-gray-50 hover:text-gray-900 dark:hover:bg-gray-800 dark:hover:text-white")}
          >{item.label}</button>)}
        </div>
        <label className="relative block sm:w-72">
          <span className="sr-only">搜索业务工作或功能</span>
          <Search aria-hidden className="pointer-events-none absolute left-3.5 top-1/2 size-4 -translate-y-1/2 text-gray-400" />
          <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="搜索工作或功能" className="h-11 w-full rounded-xl border border-gray-200 bg-white pl-10 pr-3 text-sm text-gray-800 outline-none transition focus:border-brand-500 focus:ring-3 focus:ring-brand-500/10 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-200" />
        </label>
      </div>

      {visibleWorks.length ? <div className="grid gap-4 lg:grid-cols-2 xl:grid-cols-3">
        {visibleWorks.map((work) => <BusinessWorkCard key={work.key} work={work} href={`${workspacePath}/business-works/${work.key}`} />)}
      </div> : <Card><CardContent className="flex min-h-56 flex-col items-center justify-center gap-2 p-6 text-center"><Search className="size-8 text-gray-300" /><p className="font-semibold text-gray-900 dark:text-white">没有匹配的业务工作</p><p className="text-sm text-gray-500">尝试更换分类或搜索词。</p></CardContent></Card>}
    </section>
  </div>;
}

function BusinessWorkCard({ work, href }: { work: BusinessWorkDefinition; href: string }) {
  const Icon = WORK_ICONS[work.key] ?? BriefcaseBusiness;
  return <Card className="group transition hover:-translate-y-0.5 hover:border-brand-300 hover:shadow-theme-float dark:hover:border-brand-500/50">
    <CardContent className="flex h-full flex-col p-5">
      <div className="flex items-start justify-between gap-3">
        <span className="grid size-11 shrink-0 place-items-center rounded-2xl bg-brand-50 text-brand-600 dark:bg-brand-500/15 dark:text-brand-400"><Icon className="size-5" /></span>
        <div className="flex flex-wrap justify-end gap-1.5"><Badge color="neutral">规划中</Badge><Badge color={work.category === "business" ? "primary" : "neutral"}>{CATEGORY_LABELS[work.category]}</Badge></div>
      </div>
      <h2 className="mt-4 text-base font-semibold text-gray-900 dark:text-white">{work.name}</h2>
      <p className="mt-2 flex-1 text-sm leading-6 text-gray-500">{work.summary}</p>
      <div className="mt-4 flex flex-wrap gap-1.5">{work.functions.slice(0, 3).map((item) => <span key={item.name} className="rounded-lg bg-gray-50 px-2 py-1 text-xs text-gray-600 dark:bg-gray-800 dark:text-gray-300">{item.name}</span>)}{work.functions.length > 3 ? <span className="rounded-lg bg-gray-50 px-2 py-1 text-xs text-gray-500 dark:bg-gray-800">+{work.functions.length - 3}</span> : null}</div>
      <Link to={href} aria-label={`查看${work.name}的 ${work.functions.length} 项功能`} className="mt-5 inline-flex items-center gap-1.5 text-sm font-semibold text-brand-600 outline-none transition group-hover:gap-2.5 focus-visible:rounded-lg focus-visible:ring-3 focus-visible:ring-brand-500/20 dark:text-brand-400">查看 {work.functions.length} 项功能<ArrowRight className="size-4" /></Link>
    </CardContent>
  </Card>;
}

function BusinessWorkDetail({ workKey }: { workKey: string }) {
  const { workspacePath } = useWorkspaceScope();
  const work = getBusinessWork(workKey);
  if (!work) return <Card><CardContent className="flex min-h-72 flex-col items-center justify-center gap-3 p-6 text-center"><BriefcaseBusiness className="size-9 text-gray-300" /><h1 className="text-lg font-semibold text-gray-900 dark:text-white">业务工作不存在</h1><p className="text-sm text-gray-500">该工作可能尚未登记或地址有误。</p><Button asChild variant="outline"><Link to={`${workspacePath}/business-works`}>返回业务工作</Link></Button></CardContent></Card>;
  const Icon = WORK_ICONS[work.key] ?? BriefcaseBusiness;

  return <div className="min-w-0 space-y-6">
    <header>
      <BackLink to={`${workspacePath}/business-works`}>返回业务工作</BackLink>
      <div className="mt-5 flex flex-col gap-5 rounded-[24px] border border-gray-200/80 bg-white/90 p-6 shadow-theme-card md:flex-row md:items-start md:justify-between dark:border-gray-800 dark:bg-white/[0.035]">
        <div className="flex min-w-0 items-start gap-4">
          <span className="grid size-13 shrink-0 place-items-center rounded-2xl bg-brand-50 text-brand-600 dark:bg-brand-500/15 dark:text-brand-400"><Icon className="size-6" /></span>
          <div><div className="flex flex-wrap items-center gap-2"><p className="text-sm font-medium text-brand-500">业务工作</p><Badge color="neutral">规划中</Badge><Badge>{CATEGORY_LABELS[work.category]}</Badge></div><h1 className="mt-1 text-2xl font-semibold text-gray-900 dark:text-white">{work.name}</h1><p className="mt-2 max-w-3xl text-sm leading-6 text-gray-500">{work.summary}</p></div>
        </div>
        <Button asChild><Link to={`${workspacePath}/canvas`}><Network />编排此工作</Link></Button>
      </div>
    </header>

    <section aria-labelledby="work-functions-title">
      <div className="mb-4 flex flex-wrap items-end justify-between gap-2"><div><h2 id="work-functions-title" className="text-lg font-semibold text-gray-900 dark:text-white">工作功能</h2><p className="mt-1 text-sm text-gray-500">功能通过统一底座组合，后续可以继续添加和替换。</p></div><Badge color="primary">{work.functions.length} 项</Badge></div>
      <div className="grid gap-3 md:grid-cols-2">{work.functions.map((item, index) => <Card key={item.name}><CardContent className="flex gap-3 p-5"><span className="grid size-8 shrink-0 place-items-center rounded-xl bg-success-50 text-success-600 dark:bg-success-500/10 dark:text-success-500"><CheckCircle2 className="size-4" /></span><div><h3 className="font-semibold text-gray-900 dark:text-white"><span className="mr-1 text-gray-400">{String(index + 1).padStart(2, "0")}.</span>{item.name}</h3><p className="mt-1 text-sm leading-6 text-gray-500">{item.description}</p></div></CardContent></Card>)}</div>
    </section>

    <section aria-labelledby="work-foundation-title" className="rounded-[20px] border border-brand-100 bg-brand-50/50 p-5 dark:border-brand-500/20 dark:bg-brand-500/5">
      <h2 id="work-foundation-title" className="font-semibold text-gray-900 dark:text-white">配置工作所需能力</h2>
      <p className="mt-1 text-sm text-gray-500">从统一能力中心选择依赖，不在业务工作中复制底层实现。</p>
      <div className="mt-4 flex flex-wrap gap-2"><Button asChild size="sm"><Link to={`${workspacePath}/agents/configure`}><Bot />配置 Agent</Link></Button><Button asChild size="sm" variant="outline"><Link to={`${workspacePath}/tools/new`}><BrainCircuit />添加工具</Link></Button><Button asChild size="sm" variant="outline"><Link to={`${workspacePath}/documents`}><Files />准备业务资料</Link></Button></div>
    </section>
  </div>;
}

function SummaryCard({ label, value, detail }: { label: string; value: number; detail: string }) {
  return <Card><CardContent className="p-4"><p className="text-xs font-semibold text-gray-500">{label}</p><div className="mt-2 flex items-end justify-between gap-2"><strong className="text-2xl font-semibold text-gray-900 dark:text-white">{value}</strong><span className="text-xs text-gray-400">{detail}</span></div></CardContent></Card>;
}
