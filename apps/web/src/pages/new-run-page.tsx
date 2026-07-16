import { useMutation, useQuery } from "@tanstack/react-query";
import * as React from "react";
import { Link, useNavigate, useParams } from "react-router";
import { api } from "@/api/client";
import type { StrategyVersionSummary } from "@/api/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

function validateInput(schema: Record<string, unknown>, value: Record<string, unknown>) {
  const errors: string[] = []; const required = Array.isArray(schema["required"]) ? schema["required"] as string[] : [];
  for (const key of required) if (!(key in value)) errors.push(`$.${key}: required property is missing`);
  const properties = schema["properties"] && typeof schema["properties"] === "object" ? schema["properties"] as Record<string, Record<string, unknown>> : {};
  for (const [key, property] of Object.entries(properties)) { const current = value[key]; if (current === undefined) continue; const type = property["type"]; if (type === "string" && typeof current !== "string") errors.push(`$.${key}: expected string`); if (type === "number" && typeof current !== "number") errors.push(`$.${key}: expected number`); if (type === "boolean" && typeof current !== "boolean") errors.push(`$.${key}: expected boolean`); }
  return errors;
}

export function NewRunPage() {
  const { tenantId = "", projectId = "" } = useParams(); const navigate = useNavigate();
  const workspace = `/t/${tenantId}/p/${projectId}`;
  const strategies = useQuery({ queryKey: ["strategies", tenantId, projectId], queryFn: () => api.listStrategies(tenantId, projectId) });
  const versions = useQuery({ queryKey: ["all-versions", tenantId, projectId, strategies.data?.items], enabled: Boolean(strategies.data), queryFn: async () => (await Promise.all((strategies.data?.items ?? []).map(async (strategy) => (await api.listVersions(tenantId, projectId, strategy.strategyId)).items.map((version) => ({ ...version, strategyName: strategy.name }))))).flat() });
  const [selected, setSelected] = React.useState(""); const [source, setSource] = React.useState("{}"); const [errors, setErrors] = React.useState<string[]>([]); const key = React.useRef(crypto.randomUUID());
  const selectedVersion = versions.data?.find((item) => item.strategyVersionId === selected) as (StrategyVersionSummary & { strategyName: string }) | undefined;
  const detail = useQuery({ queryKey: ["version", tenantId, projectId, selected], enabled: Boolean(selectedVersion), queryFn: () => api.getVersion(tenantId, projectId, selectedVersion?.strategyId ?? "", selected) });
  const create = useMutation({ mutationFn: (input: Record<string, unknown>) => api.createRun(tenantId, projectId, selected, input, key.current), onSuccess: (run) => void navigate(`${workspace}/runs/${run.runId}`), onError: (error) => setErrors([error.message]) });
  const submit = () => { try { const value: unknown = JSON.parse(source); if (!value || typeof value !== "object" || Array.isArray(value)) throw new Error("Input must be a JSON object."); const input = value as Record<string, unknown>; const schema = detail.data?.plan["input_schema"]; const validation = validateInput(schema && typeof schema === "object" ? schema as Record<string, unknown> : {}, input); setErrors(validation); if (!validation.length) create.mutate(input); } catch (error) { setErrors([error instanceof Error ? error.message : "Invalid JSON input"]); } };
  const loading = strategies.isPending || versions.isPending;
  return <div className="space-y-6"><div><Link to=".." className="text-sm text-brand-500">← Runs</Link><h1 className="mt-3 text-2xl font-semibold text-gray-900 dark:text-white">New Run</h1><p className="mt-1 text-sm text-gray-500">Start an immutable published strategy version.</p></div><Card><CardContent className="space-y-5 pt-5">{loading ? <p className="text-sm text-gray-500">Loading published versions…</p> : versions.isError || strategies.isError ? <div className="flex items-center justify-between"><p className="text-sm text-error-600">Published versions could not be loaded.</p><Button size="sm" onClick={() => void versions.refetch()}>Retry</Button></div> : versions.data?.length ? <><div><label htmlFor="version" className="text-sm font-medium">Strategy version</label><select id="version" value={selected} onChange={(event) => { setSelected(event.target.value); setErrors([]); }} className="mt-2 h-11 w-full rounded-xl border border-gray-300 bg-white px-3 dark:border-gray-700 dark:bg-gray-900"><option value="">Select a published version</option>{versions.data.map((version) => <option key={version.strategyVersionId} value={version.strategyVersionId}>{version.strategyName} · v{version.version}</option>)}</select></div><div><label htmlFor="run-input" className="text-sm font-medium">JSON input</label><textarea id="run-input" value={source} onChange={(event) => setSource(event.target.value)} className="mt-2 min-h-72 w-full rounded-xl border border-gray-300 bg-gray-950 p-4 font-mono text-xs text-white outline-none focus:border-brand-500 dark:border-gray-700" /></div>{errors.length ? <ul role="alert" className="space-y-1 rounded-xl bg-error-50 p-3 text-sm text-error-600 dark:bg-error-500/15">{errors.map((error) => <li key={error}>{error}</li>)}</ul> : null}<div className="flex justify-end"><Button onClick={submit} loading={create.isPending} disabled={!selected || detail.isPending}>Create Run</Button></div></> : <div className="py-12 text-center"><p className="font-medium">No published strategy versions</p><p className="mt-1 text-sm text-gray-500">Publish a strategy before creating a Run.</p><Button asChild className="mt-4"><Link to="../../strategies">Open Strategies</Link></Button></div>}</CardContent></Card></div>;
}
