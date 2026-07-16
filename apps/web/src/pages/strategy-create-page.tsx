import { useMutation, useQueryClient } from "@tanstack/react-query";
import * as React from "react";
import { Link, useNavigate, useParams } from "react-router";
import { api } from "@/api/client";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { parseSpec, serializeSpec, SpecEditor, type SpecFormat } from "@/components/strategy/spec-editor";
import { sampleStrategy } from "@/lib/sample-strategy";

export function StrategyCreatePage() {
  const { tenantId = "", projectId = "" } = useParams(); const navigate = useNavigate(); const client = useQueryClient();
  const [name, setName] = React.useState("phase1-demo"); const [format, setFormat] = React.useState<SpecFormat>("json"); const [source, setSource] = React.useState(serializeSpec(sampleStrategy, "json")); const [parseError, setParseError] = React.useState("");
  const create = useMutation({ mutationFn: () => { const spec = parseSpec(source, format); return api.createStrategy(tenantId, projectId, name.trim(), spec); }, onSuccess: async (value) => { await client.invalidateQueries({ queryKey: ["strategies", tenantId, projectId] }); void navigate(`../${value.strategyId}`); }, onError: (error) => setParseError(error.message) });
  const submit = () => { setParseError(""); try { parseSpec(source, format); create.mutate(); } catch (error) { setParseError(error instanceof Error ? error.message : "Invalid strategy document"); } };
  return <div className="space-y-6"><div><Link to=".." className="text-sm text-brand-500">← Strategies</Link><h1 className="mt-3 text-2xl font-semibold text-gray-900 dark:text-white">Create strategy</h1></div><Card><CardContent className="space-y-5 pt-5"><div><label htmlFor="strategy-name" className="text-sm font-medium text-gray-700 dark:text-gray-300">Name</label><input id="strategy-name" value={name} onChange={(event) => setName(event.target.value)} className="mt-2 h-11 w-full rounded-xl border border-gray-300 bg-transparent px-4 outline-none focus:border-brand-500 dark:border-gray-700" /></div><SpecEditor value={source} onChange={setSource} format={format} onFormatChange={setFormat} />{parseError ? <p role="alert" className="rounded-xl bg-error-50 p-3 text-sm text-error-600 dark:bg-error-500/15">{parseError}</p> : null}<div className="flex justify-end"><Button onClick={submit} loading={create.isPending} disabled={!name.trim()}>Create draft</Button></div></CardContent></Card></div>;
}
