import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import {
  BarChart3, Boxes, Braces, ChevronDown, ChevronUp, Files, Play, Settings2, ShieldCheck, Workflow,
} from "lucide-react";
import { Link, useNavigate, useParams } from "react-router";
import { api } from "@/api/client";
import type { CapabilityPackSnapshot, CaseSubjectInput, InvoiceRuleTrendSnapshot } from "@/api/types";
import { BusinessWorkPageHeader } from "@/components/business-works/business-work-page-header";
import {
  DocumentRequirementChecklist,
  DocumentUploadPanel,
} from "@/components/documents/document-intake";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useWorkspaceScope } from "@/lib/demo-scope";

type SubjectRole = CaseSubjectInput["role"];
type SubjectContract = { key: string; objectType: string; role: SubjectRole; min: number };

const inputClass = "mt-2 h-11 w-full rounded-xl border border-gray-300 bg-white px-3 text-sm outline-none transition focus:border-brand-500 focus:ring-3 focus:ring-brand-500/10 dark:border-gray-700 dark:bg-gray-900";

const WORKBENCH_ERROR_MESSAGES: Record<string, string> = {
  DOCUMENT_SELECTION_REQUIRED: "请先在「业务资料」中提供并绑定所需文件，再开始办理。",
  CASE_SUBJECT_REQUIRED: "缺少必需的业务对象主体，请检查策略与工作台输入。",
  BUSINESS_WORK_NOT_READY: "业务工作尚未满足运行资格，请先完成项目配置。",
  BUSINESS_WORK_UNAVAILABLE: "业务工作当前不可用。",
  INPUT_SCHEMA_INVALID: "业务输入不完整，请补齐资料或检查高级 JSON。",
  BASELINE_SELECTION_REQUIRED: "检测到多个基线版本，请在高级 JSON 的 documentSelection.baselineVersionIds 中明确本次基线。",
  DOCUMENT_SELECTION_INVALID: "文件选择包含无效、已排除或不属于当前项目的版本。",
};

function workbenchErrorMessage(error: unknown): string {
  if (error instanceof SyntaxError) return "业务输入不是有效的 JSON。";
  if (error && typeof error === "object" && "code" in error) {
    const code = String((error as { code?: string }).code ?? "");
    if (code && WORKBENCH_ERROR_MESSAGES[code]) return WORKBENCH_ERROR_MESSAGES[code];
  }
  const message = error instanceof Error ? error.message : "提交失败，请稍后重试。";
  return WORKBENCH_ERROR_MESSAGES[message] ?? (
    message === "[] should be non-empty"
      ? (WORKBENCH_ERROR_MESSAGES.DOCUMENT_SELECTION_REQUIRED ?? message)
      : message
  );
}

export function BusinessWorkWorkbenchPage() {
  const { workKey = "" } = useParams();
  const { tenantId, projectId, workspacePath } = useWorkspaceScope();
  const navigate = useNavigate();
  const [owner, setOwner] = useState("");
  const [title, setTitle] = useState("");
  const [contractType, setContractType] = useState("purchase");
  const [contractId, setContractId] = useState("HT-2026-001");
  const [deviationSubjectId, setDeviationSubjectId] = useState("PROJECT-2026-001");
  const [deviationSubjectType, setDeviationSubjectType] = useState("project");
  const [procurementProjectNo, setProcurementProjectNo] = useState("ZC-2026-001");
  const [procurementLotNo, setProcurementLotNo] = useState("LOT-01");
  const [procurementType, setProcurementType] = useState("ENTERPRISE");
  const [supplierName, setSupplierName] = useState("");
  const [supplierCreditCode, setSupplierCreditCode] = useState("");
  const [periodStart, setPeriodStart] = useState("2026-01-01");
  const [periodEnd, setPeriodEnd] = useState("2026-06-30");
  const [asOf, setAsOf] = useState("2026-06-30");
  const [contractOperation, setContractOperation] = useState<"INITIALIZE" | "COLLECT">("INITIALIZE");
  const [contractCurrency, setContractCurrency] = useState("CNY");
  const [contractTimezone, setContractTimezone] = useState("Asia/Shanghai");
  const [contractSourcesSource, setContractSourcesSource] = useState("[]");
  const [contractPlanSource, setContractPlanSource] = useState("{}");
  const [calibrationIssueUrl, setCalibrationIssueUrl] = useState("");
  const [calibrationObjective, setCalibrationObjective] = useState("");
  const [calibrationCriteria, setCalibrationCriteria] = useState("");
  const [calibrationTestArgs, setCalibrationTestArgs] = useState("");
  const [payloadSource, setPayloadSource] = useState("{}");
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [inputError, setInputError] = useState<string | null>(null);

  const work = useQuery({
    queryKey: ["business-work", tenantId, projectId, workKey],
    queryFn: () => api.getBusinessWork(tenantId, projectId, workKey),
  });
  const packs = useQuery({
    queryKey: ["capability-packs", tenantId, projectId],
    queryFn: () => api.listCapabilityPacks(tenantId, projectId),
    enabled: Boolean(work.data?.packName),
  });
  const invoiceTrends = useQuery({
    queryKey: ["invoice-assurance-rule-trends", tenantId, projectId],
    queryFn: () => api.getInvoiceAssuranceRuleTrends(tenantId, projectId, "day"),
    enabled: workKey === "invoice-assurance",
  });
  const pack = useMemo(
    () => selectPack(packs.data?.items ?? [], work.data?.packName ?? ""),
    [packs.data, work.data?.packName],
  );

  useEffect(() => {
    if (!pack) return;
    const defaults = defaultPayload(workItemType(pack));
    setPayloadSource(JSON.stringify(defaults, null, 2));
    if (typeof defaults.title === "string") setTitle(defaults.title);
    if (typeof defaults.contractType === "string") setContractType(defaults.contractType);
    const subject = defaults.subject;
    if (subject && typeof subject === "object") {
      const value = subject as Record<string, unknown>;
      if (typeof value.subjectId === "string") setDeviationSubjectId(value.subjectId);
      if (typeof value.subjectType === "string") setDeviationSubjectType(value.subjectType);
    }
    const period = defaults.period;
    if (period && typeof period === "object") {
      const value = period as Record<string, unknown>;
      if (typeof value.start === "string") setPeriodStart(value.start);
      if (typeof value.end === "string") setPeriodEnd(value.end);
    }
    if (typeof defaults.asOf === "string") setAsOf(defaults.asOf);
    if (defaults.operation === "INITIALIZE" || defaults.operation === "COLLECT") {
      setContractOperation(defaults.operation);
    }
    if (typeof defaults.currency === "string") setContractCurrency(defaults.currency);
    if (typeof defaults.timezone === "string") setContractTimezone(defaults.timezone);
    if (Array.isArray(defaults.sources)) {
      setContractSourcesSource(JSON.stringify(defaults.sources, null, 2));
    }
    if (defaults.plan && typeof defaults.plan === "object" && !Array.isArray(defaults.plan)) {
      setContractPlanSource(JSON.stringify(defaults.plan, null, 2));
    }
    if (typeof defaults.projectNo === "string") setProcurementProjectNo(defaults.projectNo);
    if (typeof defaults.lotNo === "string") setProcurementLotNo(defaults.lotNo);
    if (typeof defaults.procurementType === "string") setProcurementType(defaults.procurementType);
    const supplier = defaults.supplier;
    if (supplier && typeof supplier === "object") {
      const value = supplier as Record<string, unknown>;
      if (typeof value.name === "string") setSupplierName(value.name);
      if (typeof value.creditCode === "string") setSupplierCreditCode(value.creditCode);
    }
    if (typeof defaults.issueUrl === "string") setCalibrationIssueUrl(defaults.issueUrl);
    if (typeof defaults.objective === "string") setCalibrationObjective(defaults.objective);
    if (Array.isArray(defaults.acceptanceCriteria)) {
      setCalibrationCriteria(defaults.acceptanceCriteria.map(String).join("\n"));
    }
    const sandbox = defaults.sandbox;
    if (sandbox && typeof sandbox === "object") {
      const command = (sandbox as Record<string, unknown>).testCommand;
      if (Array.isArray(command)) setCalibrationTestArgs(command.map(String).join("\n"));
    }
    const contract = defaults.contract;
    if (contract && typeof contract === "object" && typeof (contract as Record<string, unknown>).contractId === "string") {
      setContractId((contract as Record<string, unknown>).contractId as string);
    }
  }, [pack]);

  const ready = work.data?.status === "runnable" && Boolean(pack);
  const run = useMutation({
    mutationFn: async () => {
      if (!pack || !work.data) throw new Error("业务工作尚未载入。");
      const payload = buildPayload(pack, {
        title,
        contractType,
        contractId,
        deviationSubjectId,
        deviationSubjectType,
        procurementProjectNo,
        procurementLotNo,
        procurementType,
        supplierName,
        supplierCreditCode,
        periodStart,
        periodEnd,
        asOf,
        contractOperation,
        contractCurrency,
        contractTimezone,
        contractSourcesSource,
        contractPlanSource,
        calibrationIssueUrl,
        calibrationObjective,
        calibrationCriteria,
        calibrationTestArgs,
        advancedSource: showAdvanced ? payloadSource : null,
      });
      const type = workItemType(pack);
      const subjectContracts = requiredSubjects(pack);
      if (!subjectContracts.length) {
        const item = await api.createWorkItem(tenantId, projectId, {
          workItemType: type,
          payload,
          owner: owner.trim() || undefined,
        });
        return api.executeWorkItem(tenantId, projectId, item.workItemId);
      }
      const subjects = await Promise.all(subjectContracts.map(async (contract) => {
        const data = subjectData(payload, contract.objectType);
        const object = await api.createBusinessObject(tenantId, projectId, {
          objectType: contract.objectType,
          canonicalKey: canonicalKey(data, payload, contract.objectType),
          schemaRef: `schema://${contract.objectType}/facts@1`,
          data,
          provenance: { source: "business-work-workbench", workKey, capabilityPackVersionId: pack.versionId },
        });
        return {
          businessObjectId: object.businessObjectId,
          businessObjectVersionId: object.versionId,
          role: contract.role,
          subjectKey: contract.key,
        };
      }));
      const businessCase = await api.createCase(tenantId, projectId, {
        scenarioType: type,
        payload,
        subjects,
        owner: owner.trim() || undefined,
      });
      if (type === "procurement-supplier-risk-case") {
        const supplier = payload.supplier as Record<string, unknown>;
        const rawSources = Array.isArray(payload.riskSources)
          ? payload.riskSources.filter(
            (value): value is Record<string, unknown> =>
              Boolean(value) && typeof value === "object" && !Array.isArray(value),
          )
          : [];
        const monitor = await api.createSupplierRiskMonitor(tenantId, projectId, {
          caseId: businessCase.caseId,
          supplierName: typeof supplier.name === "string" ? supplier.name : "",
          supplierCreditCode:
            typeof supplier.creditCode === "string" ? supplier.creditCode : "",
          cadence: "DAILY",
          sources: rawSources,
        });
        return api.refreshSupplierRiskMonitor(
          tenantId,
          projectId,
          monitor.monitorId,
        );
      }
      return api.assessCase(tenantId, projectId, businessCase.caseId);
    },
    onSuccess: (evaluation) => navigate(`${workspacePath}/assessments/${evaluation.evaluationId}`),
    onError: (error) => setInputError(workbenchErrorMessage(error)),
  });

  if (work.isPending || (work.data?.packName && packs.isPending)) {
    return <div className="space-y-4"><Skeleton className="h-40" /><Skeleton className="h-80" /></div>;
  }
  if (work.isError || !work.data) {
    return <LoadError message={work.error?.message ?? `未找到业务工作：${workKey}`} onRetry={() => void work.refetch()} />;
  }
  if (work.data.status === "planned") {
    return <Card><CardContent className="flex min-h-72 flex-col items-center justify-center gap-3 p-6 text-center">
      <Boxes className="size-8 text-gray-400" />
      <h1 className="text-lg font-semibold text-gray-900 dark:text-white">该业务工作仍在规划中</h1>
      <p className="text-sm text-gray-500">尚未接入可执行定义，不能开始办理。</p>
      <Button asChild variant="outline"><Link to={`${workspacePath}/business-works/${workKey}`}>返回业务工作</Link></Button>
    </CardContent></Card>;
  }
  if (packs.isError || !pack) {
    return <LoadError message={packs.error?.message ?? "内部执行定义尚未配置"} onRetry={() => void packs.refetch()} />;
  }

  const type = workItemType(pack);
  const subjectContracts = requiredSubjects(pack);
  const blockers = work.data.blockers.map((item) => item.message);
  const strategyLabel = work.data.boundStrategyName && work.data.boundStrategyVersion != null
    ? `${work.data.boundStrategyName} · v${work.data.boundStrategyVersion}`
    : "尚未绑定";
  const requiredDocs = work.data.documentRequirements.filter((item) => item.required).length;

  return <div className="min-w-0 space-y-5">
    <BusinessWorkPageHeader
      backTo={`${workspacePath}/business-works/${workKey}`}
      icon={Play}
      meta={<>
        <p className="text-sm font-medium text-brand-500">工作台</p>
        <Badge color={ready ? "success" : "warning"}>{work.data.statusLabel}</Badge>
        {work.data.packVersion ? <Badge color="primary">v{work.data.packVersion}</Badge> : null}
      </>}
      title={work.data.name}
      description="填写本次办理信息后发起评估；成功后进入评估结果页。"
      actions={<>
        <Button asChild className="w-full justify-center" variant="outline"><Link to={`${workspacePath}/documents`}><Files />业务资料</Link></Button>
        <Button asChild className="w-full justify-center" variant="outline"><Link to={`${workspacePath}/business-works/${workKey}/settings`}><Settings2 />项目配置</Link></Button>
      </>}
    />

    <section className="grid gap-3 md:grid-cols-3" aria-label="运行资格">
      <SummaryCard
        label="运行资格"
        value={work.data.statusLabel}
        detail={ready ? "可立即开始办理" : "仍有配置待完成"}
        icon={ready ? ShieldCheck : Boxes}
        ok={ready}
      />
      <SummaryCard
        label="执行策略"
        value={strategyLabel}
        detail={work.data.enabled ? "当前项目绑定版本" : "绑定后生效"}
        icon={Workflow}
        ok={Boolean(work.data.boundStrategyVersionId)}
      />
      <SummaryCard
        label="资料要求"
        value={requiredDocs ? `${requiredDocs} 类必需` : "无强制要求"}
        detail={requiredDocs ? "按分类自动匹配已绑定文件" : "可直接发起办理"}
        icon={Files}
        ok
      />
    </section>

    <DocumentWorkbenchPanel workKey={workKey} tenantId={tenantId} projectId={projectId} />
    {workKey === "invoice-assurance" ? (
      <InvoiceRuleTrendPanel trend={invoiceTrends.data} loading={invoiceTrends.isPending} />
    ) : null}

    {!ready ? (
      <Card>
        <CardContent className="flex flex-wrap items-center justify-between gap-4 border border-warning-200 bg-warning-50 p-5 dark:border-warning-500/20 dark:bg-warning-500/10">
          <div>
            <p className="font-medium text-warning-800 dark:text-warning-300">运行前还需准备资料或配置</p>
            <ul className="mt-2 space-y-1 text-xs text-warning-700 dark:text-warning-400">
              {blockers.map((value) => <li key={value}>{value}</li>)}
            </ul>
          </div>
          <div className="flex gap-2">
            <Button asChild size="sm"><Link to={`${workspacePath}/documents`}>选择业务资料</Link></Button>
            <Button asChild size="sm" variant="outline"><Link to={`${workspacePath}/business-works/${workKey}/settings`}>项目配置</Link></Button>
          </div>
        </CardContent>
      </Card>
    ) : null}

    <Card>
      <CardContent className="space-y-5 p-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="flex items-start gap-3">
            <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-brand-50 text-brand-600 dark:bg-brand-500/10">
              <Braces className="size-5" />
            </span>
            <div>
              <h2 className="font-semibold text-gray-900 dark:text-white">本次业务输入</h2>
              <p className="mt-1 text-xs leading-5 text-gray-500">优先使用表单填写；需要自定义字段时再展开高级 JSON。</p>
            </div>
          </div>
          <Badge color="neutral">{type}</Badge>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <Field label="案件标题" htmlFor="workbench-title">
            <input id="workbench-title" aria-label="案件标题" value={title} onChange={(event) => setTitle(event.target.value)} className={inputClass} />
          </Field>
          <Field label="负责人（可选）" htmlFor="workbench-owner">
            <input id="workbench-owner" aria-label="负责人" value={owner} onChange={(event) => setOwner(event.target.value)} className={inputClass} placeholder="未填写则使用系统默认" />
          </Field>
          {type === "contract-case" ? (
            <Field label="合同类型" htmlFor="workbench-contract-type">
              <input id="workbench-contract-type" aria-label="合同类型" value={contractType} onChange={(event) => setContractType(event.target.value)} className={inputClass} />
            </Field>
          ) : null}
          {type === "contract-post-evaluation-case" ? (
            <Field label="合同编号" htmlFor="workbench-contract-id">
              <input id="workbench-contract-id" aria-label="合同编号" value={contractId} onChange={(event) => setContractId(event.target.value)} className={inputClass} />
            </Field>
          ) : null}
          {type === "deviation-analysis-case" ? <>
            <Field label="分析对象编号" htmlFor="workbench-deviation-subject-id">
              <input id="workbench-deviation-subject-id" value={deviationSubjectId} onChange={(event) => setDeviationSubjectId(event.target.value)} className={inputClass} />
            </Field>
            <Field label="分析对象类型" htmlFor="workbench-deviation-subject-type">
              <select id="workbench-deviation-subject-type" value={deviationSubjectType} onChange={(event) => setDeviationSubjectType(event.target.value)} className={inputClass}>
                <option value="project">项目</option>
                <option value="contract">合同</option>
                <option value="work-package">工作包</option>
              </select>
            </Field>
            <Field label="分析期开始" htmlFor="workbench-period-start">
              <input id="workbench-period-start" type="date" value={periodStart} onChange={(event) => setPeriodStart(event.target.value)} className={inputClass} />
            </Field>
            <Field label="分析期结束" htmlFor="workbench-period-end">
              <input id="workbench-period-end" type="date" value={periodEnd} onChange={(event) => setPeriodEnd(event.target.value)} className={inputClass} />
            </Field>
            <Field label="数据截止日" htmlFor="workbench-as-of">
              <input id="workbench-as-of" type="date" value={asOf} onChange={(event) => setAsOf(event.target.value)} className={inputClass} />
            </Field>
          </> : null}
          {type === "contract-performance-case" ? <>
            <Field label="办理类型" htmlFor="workbench-contract-performance-operation">
              <select
                id="workbench-contract-performance-operation"
                aria-label="办理类型"
                value={contractOperation}
                onChange={(event) => setContractOperation(event.target.value as "INITIALIZE" | "COLLECT")}
                className={inputClass}
              >
                <option value="INITIALIZE">生成并发布履约计划</option>
                <option value="COLLECT">采集执行资料并更新状态</option>
              </select>
            </Field>
            <Field label="数据截止日" htmlFor="workbench-contract-performance-as-of">
              <input
                id="workbench-contract-performance-as-of"
                aria-label="履约数据截止日"
                type="date"
                value={asOf}
                onChange={(event) => setAsOf(event.target.value)}
                className={inputClass}
              />
            </Field>
            <Field label="币种" htmlFor="workbench-contract-performance-currency">
              <input
                id="workbench-contract-performance-currency"
                aria-label="履约币种"
                value={contractCurrency}
                onChange={(event) => setContractCurrency(event.target.value.toUpperCase())}
                className={inputClass}
                maxLength={3}
              />
            </Field>
            <Field label="业务时区" htmlFor="workbench-contract-performance-timezone">
              <input
                id="workbench-contract-performance-timezone"
                aria-label="履约业务时区"
                value={contractTimezone}
                onChange={(event) => setContractTimezone(event.target.value)}
                className={inputClass}
                placeholder="Asia/Shanghai"
              />
            </Field>
            {contractOperation === "COLLECT" ? <>
              <div className="md:col-span-2">
                <Field label="只读采集源（JSON 数组，最多 5 个）" htmlFor="workbench-contract-performance-sources">
                  <textarea
                    id="workbench-contract-performance-sources"
                    aria-label="履约采集源"
                    value={contractSourcesSource}
                    onChange={(event) => setContractSourcesSource(event.target.value)}
                    className={`${inputClass} min-h-36 py-3 font-mono text-xs`}
                    spellCheck={false}
                  />
                </Field>
              </div>
              <div className="md:col-span-2">
                <Field label="已人工发布的计划（JSON 对象）" htmlFor="workbench-contract-performance-plan">
                  <textarea
                    id="workbench-contract-performance-plan"
                    aria-label="已发布履约计划"
                    value={contractPlanSource}
                    onChange={(event) => setContractPlanSource(event.target.value)}
                    className={`${inputClass} min-h-56 py-3 font-mono text-xs`}
                    spellCheck={false}
                  />
                </Field>
              </div>
              <p className="md:col-span-2 rounded-xl bg-warning-50 px-4 py-3 text-xs leading-5 text-warning-700 dark:bg-warning-500/10 dark:text-warning-300">
                采集运行只接受已人工发布的计划。采集源使用只读连接或公开 HTTPS 数据；凭据仅填写 secretRef，不能粘贴密钥。
              </p>
            </> : (
              <p className="md:col-span-2 rounded-xl bg-gray-50 px-4 py-3 text-xs leading-5 text-gray-500 dark:bg-gray-800/60">
                初始化会读取本次冻结的合同资料，调用计划提取 Agent、规范化和甘特工具，并在发布前暂停等待人工确认。
              </p>
            )}
          </> : null}
          {type === "procurement-supplier-risk-case" ? <>
            <Field label="采购项目编号" htmlFor="workbench-procurement-project-no">
              <input id="workbench-procurement-project-no" value={procurementProjectNo} onChange={(event) => setProcurementProjectNo(event.target.value)} className={inputClass} />
            </Field>
            <Field label="标包编号" htmlFor="workbench-procurement-lot-no">
              <input id="workbench-procurement-lot-no" value={procurementLotNo} onChange={(event) => setProcurementLotNo(event.target.value)} className={inputClass} />
            </Field>
            <Field label="采购类型" htmlFor="workbench-procurement-type">
              <select id="workbench-procurement-type" value={procurementType} onChange={(event) => setProcurementType(event.target.value)} className={inputClass}>
                <option value="ENTERPRISE">企业采购</option>
                <option value="GOVERNMENT_GOODS">政府采购货物</option>
                <option value="GOVERNMENT_SERVICES">政府采购服务</option>
                <option value="GOVERNMENT_WORKS">政府采购工程</option>
              </select>
            </Field>
            <Field label="数据截止日" htmlFor="workbench-procurement-as-of">
              <input id="workbench-procurement-as-of" type="date" value={asOf} onChange={(event) => setAsOf(event.target.value)} className={inputClass} />
            </Field>
            <Field label="供应商名称" htmlFor="workbench-supplier-name">
              <input id="workbench-supplier-name" value={supplierName} onChange={(event) => setSupplierName(event.target.value)} className={inputClass} />
            </Field>
            <Field label="统一社会信用代码" htmlFor="workbench-supplier-credit-code">
              <input id="workbench-supplier-credit-code" value={supplierCreditCode} onChange={(event) => setSupplierCreditCode(event.target.value.toUpperCase())} className={inputClass} maxLength={18} />
            </Field>
            <p className="md:col-span-2 rounded-xl bg-gray-50 px-4 py-3 text-xs leading-5 text-gray-500 dark:bg-gray-800/60">
              外部风控源和 ERP 绩效记录通过高级 JSON 的 riskSources、performance.records 配置；凭据只填写 secretRef，由工具网关运行时解析。
            </p>
          </> : null}
          {type === "swarm-calibration-case" ? <>
            <div className="md:col-span-2">
              <Field label="真实 GitHub Issue URL" htmlFor="workbench-calibration-issue">
                <input
                  id="workbench-calibration-issue"
                  type="url"
                  value={calibrationIssueUrl}
                  onChange={(event) => setCalibrationIssueUrl(event.target.value)}
                  className={inputClass}
                  placeholder="https://github.com/owner/repository/issues/123"
                />
              </Field>
            </div>
            <div className="md:col-span-2">
              <Field label="本次校准目标" htmlFor="workbench-calibration-objective">
                <textarea
                  id="workbench-calibration-objective"
                  value={calibrationObjective}
                  onChange={(event) => setCalibrationObjective(event.target.value)}
                  className={`${inputClass} min-h-24 py-3`}
                />
              </Field>
            </div>
            <Field label="验收标准（每行一项）" htmlFor="workbench-calibration-criteria">
              <textarea
                id="workbench-calibration-criteria"
                value={calibrationCriteria}
                onChange={(event) => setCalibrationCriteria(event.target.value)}
                className={`${inputClass} min-h-32 py-3`}
              />
            </Field>
            <Field label="沙箱测试命令参数（每行一个）" htmlFor="workbench-calibration-command">
              <textarea
                id="workbench-calibration-command"
                value={calibrationTestArgs}
                onChange={(event) => setCalibrationTestArgs(event.target.value)}
                className={`${inputClass} min-h-32 py-3 font-mono`}
              />
            </Field>
          </> : null}
        </div>

        <div className="rounded-xl border border-gray-200 dark:border-gray-800">
          <button
            type="button"
            className="flex w-full items-center justify-between gap-3 px-4 py-3 text-left text-sm font-medium text-gray-700 transition hover:bg-gray-50 dark:text-gray-200 dark:hover:bg-gray-900/60"
            onClick={() => setShowAdvanced((value) => !value)}
            aria-expanded={showAdvanced}
          >
            <span>{showAdvanced ? "收起高级 JSON 输入" : "展开高级 JSON 输入"}</span>
            {showAdvanced ? <ChevronUp className="size-4 text-gray-400" /> : <ChevronDown className="size-4 text-gray-400" />}
          </button>
          {showAdvanced ? (
            <div className="border-t border-gray-200 p-4 dark:border-gray-800">
              <label className="block text-xs font-medium text-gray-700 dark:text-gray-300">
                高级 JSON 输入
                <textarea
                  aria-label="业务输入 JSON"
                  spellCheck={false}
                  value={payloadSource}
                  onChange={(event) => { setPayloadSource(event.target.value); setInputError(null); }}
                  className="mt-2 min-h-64 w-full resize-y rounded-xl border border-gray-300 bg-gray-950 p-4 font-mono text-xs leading-5 text-gray-100 outline-none focus:border-brand-500 dark:border-gray-700"
                />
              </label>
            </div>
          ) : null}
        </div>

        {subjectContracts.length ? (
          <p className="rounded-xl bg-gray-50 px-4 py-3 text-xs leading-5 text-gray-500 dark:bg-gray-800/60">
            提交时会自动建立 {subjectContracts.map((subject) => `${subject.key}（${subject.objectType}）`).join("、")} 业务对象，并冻结到本次评估。
          </p>
        ) : null}

        {inputError ? (
          <p role="alert" className="rounded-xl bg-error-50 p-3 text-sm text-error-600 dark:bg-error-500/10">
            提交失败：{inputError}
          </p>
        ) : null}

        <div className="flex flex-wrap items-center justify-between gap-3 border-t border-gray-100 pt-4 dark:border-gray-800">
          <p className="text-xs text-gray-400">
            {ready ? "准备就绪，可开始办理。" : "完成资料与配置后即可开始办理。"}
          </p>
          <Button
            loading={run.isPending}
            disabled={!ready || run.isPending}
            onClick={() => { setInputError(null); run.mutate(); }}
          >
            <Play />开始办理
          </Button>
        </div>
      </CardContent>
    </Card>
  </div>;
}

function Field({
  label,
  htmlFor,
  children,
}: {
  label: string;
  htmlFor: string;
  children: React.ReactNode;
}) {
  return (
    <label htmlFor={htmlFor} className="block text-xs font-medium text-gray-700 dark:text-gray-300">
      {label}
      {children}
    </label>
  );
}

function InvoiceRuleTrendPanel({
  trend,
  loading,
}: {
  trend: InvoiceRuleTrendSnapshot | undefined;
  loading: boolean;
}) {
  return (
    <Card>
      <CardContent className="space-y-4 p-5">
        <div className="flex items-start gap-3">
          <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-brand-50 text-brand-600 dark:bg-brand-500/10">
            <BarChart3 className="size-5" />
          </span>
          <div>
            <h2 className="font-semibold text-gray-900 dark:text-white">规则命中趋势</h2>
            <p className="mt-1 text-xs text-gray-500">按历史发票 Assessment 聚合，只统计 FAIL、WARN 和 UNKNOWN。</p>
          </div>
        </div>
        {loading ? <Skeleton className="h-24" /> : (
          <>
            <div className="grid gap-3 sm:grid-cols-3">
              <div className="rounded-xl bg-gray-50 p-3 dark:bg-gray-800/60">
                <p className="text-xs text-gray-500">历史评估</p>
                <p className="mt-1 text-xl font-semibold text-gray-900 dark:text-white">{trend?.totalAssessments ?? 0}</p>
              </div>
              <div className="rounded-xl bg-gray-50 p-3 dark:bg-gray-800/60">
                <p className="text-xs text-gray-500">付款阻断</p>
                <p className="mt-1 text-xl font-semibold text-error-600">{trend?.outcomes.PAYMENT_BLOCKED ?? 0}</p>
              </div>
              <div className="rounded-xl bg-gray-50 p-3 dark:bg-gray-800/60">
                <p className="text-xs text-gray-500">需人工复核</p>
                <p className="mt-1 text-xl font-semibold text-warning-600">{trend?.outcomes.REVIEW_REQUIRED ?? 0}</p>
              </div>
            </div>
            <div className="space-y-2">
              {(trend?.topRules ?? []).slice(0, 5).map((item) => (
                <div key={`${item.ruleId}-${item.status}`} className="flex items-center justify-between gap-3 rounded-lg border border-gray-200 px-3 py-2 text-sm dark:border-gray-800">
                  <span className="min-w-0 truncate text-gray-700 dark:text-gray-200">{item.ruleId}</span>
                  <span className="flex shrink-0 items-center gap-2">
                    <Badge color={item.status === "FAIL" ? "error" : item.status === "WARN" ? "warning" : "neutral"}>{item.status}</Badge>
                    <span className="text-gray-500">{item.count} 次</span>
                  </span>
                </div>
              ))}
              {!trend?.topRules.length ? <p className="text-sm text-gray-500">暂无规则命中历史。</p> : null}
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}

function SummaryCard({
  label,
  value,
  detail,
  icon: Icon,
  ok,
}: {
  label: string;
  value: string;
  detail: string;
  icon: typeof Boxes;
  ok: boolean;
}) {
  return (
    <Card className="min-w-0">
      <CardContent className="flex min-w-0 items-start gap-3 p-4">
        <span className={`grid size-10 shrink-0 place-items-center rounded-xl ${ok ? "bg-success-50 text-success-600 dark:bg-success-500/10" : "bg-warning-50 text-warning-600 dark:bg-warning-500/10"}`}>
          <Icon className="size-5" />
        </span>
        <div className="min-w-0">
          <p className="text-xs text-gray-500">{label}</p>
          <p className="mt-1 truncate font-semibold text-gray-900 dark:text-white" title={value}>{value}</p>
          <p className="mt-1 truncate text-xs text-gray-400" title={detail}>{detail}</p>
        </div>
      </CardContent>
    </Card>
  );
}

function buildPayload(
  pack: CapabilityPackSnapshot,
  values: {
    title: string;
    contractType: string;
    contractId: string;
    deviationSubjectId: string;
    deviationSubjectType: string;
    procurementProjectNo: string;
    procurementLotNo: string;
    procurementType: string;
    supplierName: string;
    supplierCreditCode: string;
    periodStart: string;
    periodEnd: string;
    asOf: string;
    contractOperation: "INITIALIZE" | "COLLECT";
    contractCurrency: string;
    contractTimezone: string;
    contractSourcesSource: string;
    contractPlanSource: string;
    calibrationIssueUrl: string;
    calibrationObjective: string;
    calibrationCriteria: string;
    calibrationTestArgs: string;
    advancedSource: string | null;
  },
) {
  if (values.advancedSource) return parseObject(values.advancedSource, "业务输入必须是 JSON 对象。");
  const type = workItemType(pack);
  const base = defaultPayload(type);
  if (type === "contract-case") return { ...base, title: values.title || base.title, contractType: values.contractType };
  if (type === "contract-post-evaluation-case") {
    const contract = base.contract && typeof base.contract === "object" ? { ...(base.contract as Record<string, unknown>) } : {};
    return { ...base, title: values.title || base.title, contract: { ...contract, contractId: values.contractId } };
  }
  if (type === "deviation-analysis-case") {
    return {
      ...base,
      title: values.title || base.title,
      subject: {
        subjectId: values.deviationSubjectId,
        subjectType: values.deviationSubjectType,
      },
      period: { start: values.periodStart, end: values.periodEnd },
      asOf: values.asOf,
    };
  }
  if (type === "contract-performance-case") {
    const currency = values.contractCurrency.trim().toUpperCase();
    if (!/^[A-Z]{3}$/.test(currency)) throw new Error("币种必须是 3 位大写字母代码。");
    const payload: Record<string, unknown> = {
      ...base,
      title: values.title || base.title,
      operation: values.contractOperation,
      asOf: values.asOf,
      currency,
      timezone: values.contractTimezone.trim() || "Asia/Shanghai",
      manualDocuments: [],
    };
    if (values.contractOperation === "COLLECT") {
      const sources = parseArray(values.contractSourcesSource, "采集源必须是 JSON 数组。");
      if (sources.length > 5 || sources.some((item) => !item || typeof item !== "object" || Array.isArray(item))) {
        throw new Error("采集源必须是最多 5 个 JSON 对象。");
      }
      const plan = parseObject(values.contractPlanSource, "已发布计划必须是 JSON 对象。");
      if (Object.keys(plan).length === 0) throw new Error("采集前必须提供已人工发布的履约计划。");
      payload.sources = sources;
      payload.plan = plan;
    } else {
      payload.sources = [];
    }
    return payload;
  }
  if (type === "procurement-supplier-risk-case") {
    return {
      ...base,
      title: values.title || base.title,
      projectNo: values.procurementProjectNo,
      lotNo: values.procurementLotNo,
      procurementType: values.procurementType,
      asOf: values.asOf,
      supplier: {
        name: values.supplierName.trim(),
        creditCode: values.supplierCreditCode.trim().toUpperCase(),
      },
    };
  }
  if (type === "swarm-calibration-case") {
    return {
      ...base,
      title: values.title || base.title,
      issueUrl: values.calibrationIssueUrl.trim(),
      objective: values.calibrationObjective.trim(),
      acceptanceCriteria: nonEmptyLines(values.calibrationCriteria),
      sandbox: {
        enabled: true,
        testCommand: nonEmptyLines(values.calibrationTestArgs),
      },
    };
  }
  return { ...base, title: values.title || base.title };
}

function nonEmptyLines(value: string) {
  return value.split(/\r?\n/).map((item) => item.trim()).filter(Boolean);
}

function parseArray(source: string, message: string) {
  const value: unknown = JSON.parse(source);
  if (!Array.isArray(value)) throw new Error(message);
  return value as unknown[];
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
  if (caseContract && typeof caseContract === "object" && typeof (caseContract as Record<string, unknown>).type === "string") {
    return (caseContract as Record<string, unknown>).type as string;
  }
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

function isSubjectRole(value: unknown): value is SubjectRole {
  return value === "PRIMARY" || value === "COMPARISON" || value === "EVIDENCE" || value === "RELATED";
}

function DocumentWorkbenchPanel({
  workKey,
  tenantId,
  projectId,
}: {
  workKey: string;
  tenantId: string;
  projectId: string;
}) {
  const requirements = useQuery({
    queryKey: ["document-requirements", tenantId, projectId, workKey],
    queryFn: () => api.listWorkDocumentRequirements(tenantId, projectId, workKey),
  });
  const [showUpload, setShowUpload] = useState(false);
  const [uploadCategory, setUploadCategory] = useState("");
  const items = requirements.data?.items ?? [];
  const selectedRequirement = items.find((item) => item.category === uploadCategory) ?? items[0];
  const labels = (selectedRequirement?.classificationLabels ?? []).map((label) => ({
    label,
    displayName: selectedRequirement?.displayName,
  }));
  return (
    <Card>
      <CardContent className="space-y-4 p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="font-semibold text-gray-900 dark:text-white">业务资料准备</h2>
            <p className="mt-1 text-sm text-gray-500">按资料要求上传并确认；组件不绑定具体业务名称。</p>
          </div>
          <Button size="sm" variant="outline" onClick={() => setShowUpload((value) => !value)}>
            {showUpload ? "收起上传" : "上下文上传"}
          </Button>
        </div>
        {requirements.isPending ? <Skeleton className="h-24" /> : <DocumentRequirementChecklist items={items} />}
        {showUpload ? (
          <div className="space-y-3">
            {items.length ? <label className="block text-xs font-medium text-gray-700 dark:text-gray-300">
              本批资料分类
              <select
                aria-label="本批资料分类"
                value={selectedRequirement?.category ?? ""}
                onChange={(event) => setUploadCategory(event.target.value)}
                className={inputClass}
              >
                {items.map((item) => <option key={item.key} value={item.category ?? "OTHER"}>{item.displayName}{item.required ? "（必需）" : ""}</option>)}
              </select>
            </label> : null}
            <DocumentUploadPanel
              tenantId={tenantId}
              projectId={projectId}
              context={{
                businessWorkKey: workKey,
                businessWorkKeys: [workKey],
                processingProfileRef: requirements.data?.processingProfileRef ?? undefined,
                extractionSchemaRef: selectedRequirement?.extractionSchemaRef ?? undefined,
                classificationLabels: labels,
                category: selectedRequirement?.category ?? "OTHER",
              }}
              onCompleted={async () => {
                setShowUpload(false);
                await requirements.refetch();
              }}
            />
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
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
  if (type === "swarm-calibration-case") return {
    title: "Temporal Python SDK 调度问题校准",
    issueUrl: "https://github.com/temporalio/sdk-python/issues/782",
    objective: "基于真实 Issue、讨论和合并代码，校验任务调度、主备切换与结论质量。",
    acceptanceCriteria: [
      "所有关键结论都引用冻结证据",
      "使用完整合并提交 SHA 执行隔离验证",
      "主 Agent 失败时由 Runtime 选择备用 Agent 并保留原因",
    ],
    budget: {
      maxDurationSeconds: 720,
      maxCostUsd: 1,
      maxTokens: 120000,
    },
    sandbox: {
      enabled: true,
      testCommand: ["python", "-m", "pytest", "-q"],
    },
  };
  if (type === "contract-performance-case") return {
    title: "合同履约计划与采集",
    operation: "INITIALIZE",
    asOf: "2026-07-27",
    currency: "CNY",
    timezone: "Asia/Shanghai",
    sources: [],
    manualDocuments: [],
  };
  if (type === "procurement-supplier-risk-case") return {
    title: "招采一致性与供应商风控评估",
    projectNo: "ZC-2026-001",
    lotNo: "LOT-01",
    procurementType: "ENTERPRISE",
    asOf: "2026-07-28",
    supplier: {
      name: "",
      creditCode: "",
      aliases: [],
    },
    riskSources: [
      {
        kind: "CCGP_SERIOUS_ILLEGAL",
        sourceRef: "official://ccgp/serious-illegal",
        endpoint: "https://www.ccgp.gov.cn/cr/list",
      },
    ],
    performance: {
      periodStart: "2026-01-01",
      periodEnd: "2026-06-30",
      minimumSampleSize: 3,
      records: [],
    },
    clauses: {},
    semanticProposals: [],
    approvedExceptionKeys: [],
    previousSnapshot: null,
  };
  if (type === "invoice-assurance-case") return {
    title: "发票一致性校验",
    asOf: "2026-07-27",
    currency: "CNY",
    timezone: "Asia/Shanghai",
    verificationMode: "HUMAN_ASSISTED",
    businessSnapshot: {},
  };
  if (type === "deviation-analysis-case") return {
    title: "项目偏差分析",
    subject: { subjectId: "PROJECT-2026-001", subjectType: "project", name: "示例项目" },
    period: { start: "2026-01-01", end: "2026-06-30" },
    asOf: "2026-06-30",
    dimensions: ["TIME", "CONTENT", "COST"],
    currency: "CNY",
    timezone: "Asia/Shanghai",
    trendWindow: "P6M",
    evidenceTopK: 8,
    thresholds: {
      delayDaysHigh: 15,
      contentVarianceRateHigh: 0.1,
      forecastOverrunRateHigh: 0.05,
    },
    approval: {
      requireResponsibilityConfirmation: true,
      requireHighImpactReview: true,
    },
    documentSelection: {
      includeVersionIds: [],
      excludeVersionIds: [],
      baselineVersionIds: [],
    },
    time: { milestones: [] },
    content: { items: [] },
    cost: { originalBAC: null, approvedChanges: [], eac: null, ac: null, commitments: null },
  };
  if (type === "contract-post-evaluation-case") return {
    title: "合同后评价",
    evaluationPeriod: { start: "2026-01-01", end: "2026-06-30" },
    contract: { contractId: "HT-2026-001", contractName: "采购合同", contractAmount: 100000, currency: "CNY" },
    documents: [], obligations: [], deviations: [], invoices: [], risks: [],
  };
  if (type === "contract-case") return { title: "采购合同检查", contractType: "purchase" };
  return {};
}

function LoadError({ message, onRetry }: { message: string; onRetry: () => void }) {
  return <Card><CardContent className="flex min-h-60 flex-col items-center justify-center gap-3 p-5 text-center"><Boxes className="size-8 text-gray-400" /><p className="font-medium text-gray-900 dark:text-white">业务工作台无法加载</p><p className="text-sm text-gray-500">{message}</p><Button onClick={onRetry}>重试</Button></CardContent></Card>;
}
