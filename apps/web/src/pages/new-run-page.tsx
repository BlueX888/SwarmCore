import { useMutation, useQuery } from "@tanstack/react-query";
import { ArrowLeft, Braces, ListChecks, Play, Sparkles } from "lucide-react";
import * as React from "react";
import { Link, useNavigate } from "react-router";
import { api } from "@/api/client";
import type { StrategyVersionSummary } from "@/api/types";
import { SchemaForm, schemaInitialValues } from "@/components/operations/schema-form";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { Skeleton } from "@/components/ui/skeleton";
import { useWorkspaceScope } from "@/lib/demo-scope";

type InputMode = "form" | "json";

function validateInput(schema: Record<string, unknown>, value: Record<string, unknown>) {
  const errors: string[] = [];
  const required = Array.isArray(schema["required"]) ? schema["required"].filter((item): item is string => typeof item === "string") : [];
  for (const key of required) if (!(key in value) || value[key] === "") errors.push(`$.${key}：缺少必填属性`);
  const properties = schema["properties"] && typeof schema["properties"] === "object" ? schema["properties"] as Record<string, Record<string, unknown>> : {};
  for (const [key, property] of Object.entries(properties)) {
    const current = value[key];
    if (current === undefined) continue;
    const type = property["type"];
    if (type === "string" && typeof current !== "string") errors.push(`$.${key}：应为字符串`);
    if (type === "number" && typeof current !== "number") errors.push(`$.${key}：应为数字`);
    if (type === "integer" && (!Number.isInteger(current))) errors.push(`$.${key}：应为整数`);
    if (type === "boolean" && typeof current !== "boolean") errors.push(`$.${key}：应为布尔值`);
    if (type === "array" && !Array.isArray(current)) errors.push(`$.${key}：应为数组`);
    if (type === "object" && (!current || typeof current !== "object" || Array.isArray(current))) errors.push(`$.${key}：应为对象`);
  }
  return errors;
}

function getInputSchema(plan: Record<string, unknown> | undefined): Record<string, unknown> {
  const schema = plan?.["input_schema"];
  return schema && typeof schema === "object" && !Array.isArray(schema) ? schema as Record<string, unknown> : {};
}

function supportsFormInput(schema: Record<string, unknown>) {
  const properties = schema["properties"] && typeof schema["properties"] === "object" ? schema["properties"] as Record<string, Record<string, unknown>> : {};
  return Object.values(properties).every((property) => {
    const type = property["type"];
    return type === undefined || typeof type === "string" && ["string", "number", "integer", "boolean"].includes(type);
  });
}

export function NewRunPage() {
  const { tenantId, projectId, workspacePath } = useWorkspaceScope();
  const navigate = useNavigate();
  const strategies = useQuery({ queryKey: ["strategies", tenantId, projectId], queryFn: () => api.listStrategies(tenantId, projectId) });
  const versions = useQuery({
    queryKey: ["all-versions", tenantId, projectId, strategies.data?.items],
    enabled: Boolean(strategies.data),
    queryFn: async () => (await Promise.all((strategies.data?.items ?? []).map(async (strategy) =>
      (await api.listVersions(tenantId, projectId, strategy.strategyId)).items.map((version) => ({ ...version, strategyName: strategy.name })),
    ))).flat(),
  });
  const [selected, setSelected] = React.useState("");
  const [mode, setMode] = React.useState<InputMode>("form");
  const [source, setSource] = React.useState("{}");
  const [formValues, setFormValues] = React.useState<Record<string, unknown>>({});
  const [formEdited, setFormEdited] = React.useState(false);
  const [errors, setErrors] = React.useState<string[]>([]);
  const key = React.useRef(crypto.randomUUID());
  const selectedVersion = versions.data?.find((item) => item.strategyVersionId === selected) as (StrategyVersionSummary & { strategyName: string }) | undefined;
  const detail = useQuery({ queryKey: ["version", tenantId, projectId, selected], enabled: Boolean(selectedVersion), queryFn: () => api.getVersion(tenantId, projectId, selectedVersion?.strategyId ?? "", selected) });
  const inputSchema = getInputSchema(detail.data?.plan);
  const properties = inputSchema["properties"] && typeof inputSchema["properties"] === "object" ? inputSchema["properties"] as Record<string, Record<string, unknown>> : {};
  const formSupported = supportsFormInput(inputSchema);
  const effectiveMode: InputMode = formSupported ? mode : "json";
  const effectiveFormValues = formEdited ? formValues : schemaInitialValues(inputSchema);
  const create = useMutation({
    mutationFn: (input: Record<string, unknown>) => api.createRun(tenantId, projectId, selected, input, key.current),
    onSuccess: (run) => void navigate(`${workspacePath}/runs/${run.runId}`),
    onError: (error) => setErrors([error.message]),
  });
  const submitInput = (input: Record<string, unknown>) => {
    const validation = validateInput(inputSchema, input);
    setErrors(validation);
    if (!validation.length) create.mutate(input);
  };
  const submitJson = () => {
    try {
      const value: unknown = JSON.parse(source);
      if (!value || typeof value !== "object" || Array.isArray(value)) throw new Error("输入必须是 JSON 对象。");
      submitInput(value as Record<string, unknown>);
    } catch (error) {
      setErrors([error instanceof Error ? error.message : "JSON 输入无效"]);
    }
  };
  const changeVersion = (versionId: string) => {
    setSelected(versionId);
    setMode("form");
    setSource("{}");
    setFormValues({});
    setFormEdited(false);
    setErrors([]);
  };
  const changeFormValues = (value: Record<string, unknown>) => {
    setFormValues(value);
    setFormEdited(true);
    setSource(JSON.stringify(value, null, 2));
  };
  const openJson = () => {
    setSource(JSON.stringify(effectiveFormValues, null, 2));
    setMode("json");
    setErrors([]);
  };
  const openForm = () => {
    try {
      const value: unknown = JSON.parse(source);
      if (!value || typeof value !== "object" || Array.isArray(value)) throw new Error("输入必须是 JSON 对象。");
      setFormValues(value as Record<string, unknown>);
      setFormEdited(true);
      setMode("form");
      setErrors([]);
    } catch (error) {
      setErrors([error instanceof Error ? error.message : "JSON 输入无效"]);
    }
  };
  // Disabled queries remain isPending in TanStack Query v5; isLoading requires an in-flight fetch.
  const loading = strategies.isPending || versions.isLoading;

  return <div className="space-y-6">
    <div>
      <Link to=".." className="inline-flex items-center gap-1.5 rounded-lg text-sm font-medium text-brand-500 transition-colors hover:text-brand-600 focus-visible:outline-hidden focus-visible:ring-3 focus-visible:ring-brand-500/20">
        <ArrowLeft className="size-4" aria-hidden />
        运行记录
      </Link>
      <h1 className="mt-3 text-2xl font-semibold text-gray-900 dark:text-white">新建运行</h1>
      <p className="mt-1 text-sm text-gray-500">选择已发布策略版本，通过表单填写输入并启动运行。</p>
    </div>
    <Card><CardContent className="space-y-5 pt-5">
      {loading ? <div className="space-y-4"><Skeleton className="h-11" /><Skeleton className="h-64" /></div> : versions.isError || strategies.isError ? <ErrorState compact title="无法加载已发布版本" onRetry={() => void versions.refetch()} /> : versions.data?.length ? <>
        <div><label htmlFor="version" className="text-sm font-medium">策略版本</label><select id="version" value={selected} onChange={(event) => changeVersion(event.target.value)} className="mt-2 h-11 w-full rounded-xl border border-gray-300 bg-white px-3 dark:border-gray-700 dark:bg-gray-900"><option value="">请选择已发布版本</option>{versions.data.map((version) => <option key={version.strategyVersionId} value={version.strategyVersionId}>{version.strategyName} · 版本 {version.version}</option>)}</select></div>

        {!selected ? <div className="rounded-xl border border-dashed border-gray-300 dark:border-gray-700"><EmptyState icon={Sparkles} title="选择策略后自动生成输入表单" description="系统会读取策略的输入定义，自动展示需要填写的字段和必填提示。" /></div> : detail.isPending ? <div className="space-y-4"><p className="text-sm text-gray-500">正在读取策略输入字段…</p><Skeleton className="h-52" /></div> : detail.isError ? <ErrorState compact title="无法读取该版本的输入定义" onRetry={() => void detail.refetch()} /> : <div className="space-y-5 rounded-xl border border-gray-200 p-4 md:p-5 dark:border-gray-800">
          <div className="flex flex-wrap items-start justify-between gap-3"><div><h2 className="font-semibold text-gray-900 dark:text-white">运行输入</h2><p className="mt-1 text-sm text-gray-500">优先使用表单填写；需要完整控制时可切换到 JSON。</p></div><div role="group" aria-label="输入方式" className="flex rounded-lg bg-gray-100 p-1 dark:bg-gray-800"><Button type="button" size="sm" variant={effectiveMode === "form" ? "primary" : "ghost"} aria-pressed={effectiveMode === "form"} disabled={!formSupported} onClick={openForm} className="h-9"><ListChecks />表单填写</Button><Button type="button" size="sm" variant={effectiveMode === "json" ? "primary" : "ghost"} aria-pressed={effectiveMode === "json"} onClick={openJson} className="h-9"><Braces />JSON 编辑</Button></div></div>

          {!formSupported ? <p className="rounded-xl bg-warning-50 p-3 text-sm text-warning-700 dark:bg-warning-500/10">该策略包含对象或数组等复杂字段，请使用 JSON 编辑。</p> : null}
          {effectiveMode === "form" && Object.keys(properties).length ? <SchemaForm schema={inputSchema} values={effectiveFormValues} onValuesChange={changeFormValues} submitLabel="创建运行" busy={create.isPending} icon={<Play />} onSubmit={submitInput} /> : null}
          {effectiveMode === "form" && !Object.keys(properties).length ? <div className="rounded-xl bg-gray-50 dark:bg-gray-800/50"><EmptyState compact title="该策略无需额外输入" description="确认后即可直接创建运行。" action={<Button onClick={() => submitInput({})} loading={create.isPending}><Play />创建运行</Button>} /></div> : null}
          {effectiveMode === "json" ? <div><label htmlFor="run-input" className="text-sm font-medium">JSON 输入</label><textarea id="run-input" value={source} onChange={(event) => setSource(event.target.value)} className="mt-2 min-h-64 w-full rounded-xl border border-gray-300 bg-gray-950 p-4 font-mono text-xs text-white outline-none focus:border-brand-500 dark:border-gray-700" /><div className="mt-4 flex justify-end"><Button onClick={submitJson} loading={create.isPending}><Play />创建运行</Button></div></div> : null}
          {errors.length ? <ul role="alert" className="space-y-1 rounded-xl bg-error-50 p-3 text-sm text-error-600 dark:bg-error-500/15">{errors.map((error) => <li key={error}>{error}</li>)}</ul> : null}
        </div>}
      </> : <EmptyState title="暂无已发布的策略版本" description="请先发布策略，再创建运行。" action={<Button asChild><Link to="../../strategies">打开策略管理</Link></Button>} />}
    </CardContent></Card>
  </div>;
}
