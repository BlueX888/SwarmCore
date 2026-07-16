import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, Save } from "lucide-react";
import * as React from "react";
import { Link, useNavigate, useParams } from "react-router";
import { api } from "@/api/client";
import type { Diagnostic } from "@/api/types";
import { StrategyEditor } from "@/components/strategy/strategy-editor";
import { EMPTY_EDITOR_STATE, cloneSpec, createBlankSpec, type EditorState } from "@/components/strategy/strategy-editor-model";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

export function StrategyCreatePage() {
  const { tenantId = "", projectId = "" } = useParams();
  const navigate = useNavigate();
  const client = useQueryClient();
  const [name, setName] = React.useState("untitled-strategy");
  const [spec, setSpec] = React.useState(() => createBlankSpec("untitled-strategy"));
  const [editorState, setEditorState] = React.useState<EditorState>(() => structuredClone(EMPTY_EDITOR_STATE));
  const [diagnostics, setDiagnostics] = React.useState<Diagnostic[]>([]);
  const [message, setMessage] = React.useState("");
  const capabilities = useQuery({ queryKey: ["capabilities", tenantId, projectId], queryFn: () => api.getCapabilities(tenantId, projectId) });
  const compile = useMutation({
    mutationFn: () => api.compileStrategy(tenantId, projectId, spec),
    onSuccess: (result) => {
      setDiagnostics(result.diagnostics);
      const hash = result.plan?.["plan_hash"];
      setMessage(result.valid ? `Valid plan · ${typeof hash === "string" ? hash : ""}` : "Compilation found errors.");
    },
    onError: (error) => setMessage(error.message),
  });
  const create = useMutation({
    mutationFn: async () => {
      const result = await api.compileStrategy(tenantId, projectId, spec);
      setDiagnostics(result.diagnostics);
      if (!result.valid) throw new Error("Fix compiler diagnostics before creating the draft.");
      return api.createStrategy(tenantId, projectId, name.trim(), spec, editorState);
    },
    onSuccess: async (value) => {
      await client.invalidateQueries({ queryKey: ["strategies", tenantId, projectId] });
      void navigate(`../${value.strategyId}`);
    },
    onError: (error) => setMessage(error.message),
  });
  const rename = (value: string) => {
    setName(value);
    const next = cloneSpec(spec);
    next.metadata.name = value.trim() || "untitled-strategy";
    setSpec(next);
  };
  return <div className="min-w-0 space-y-6">
    <div><Link to=".." className="text-sm text-brand-500">← Strategies</Link><h1 className="mt-3 text-2xl font-semibold text-gray-900 dark:text-white">Create strategy</h1><p className="mt-1 text-sm text-gray-500">Start with an empty canvas, then validate and create a durable draft.</p></div>
    <Card><CardContent className="space-y-5 pt-5">
      <div><label htmlFor="strategy-name" className="text-sm font-medium text-gray-700 dark:text-gray-300">Name</label><input id="strategy-name" value={name} onChange={(event) => rename(event.target.value)} className="mt-2 h-11 w-full rounded-xl border border-gray-300 bg-transparent px-4 outline-none focus:border-brand-500 dark:border-gray-700" /></div>
      <StrategyEditor spec={spec} editorState={editorState} nodeTypes={capabilities.data?.nodeTypes.map((item) => item.type) ?? []} diagnostics={diagnostics} onSpecChange={(value) => { setSpec(value); setMessage(""); }} onEditorStateChange={setEditorState} onError={setMessage} />
      <div className="flex flex-wrap justify-end gap-2"><Button variant="outline" onClick={() => compile.mutate()} loading={compile.isPending}><CheckCircle2 />Validate</Button><Button onClick={() => create.mutate()} loading={create.isPending} disabled={!name.trim()}><Save />Create draft</Button></div>
      {message ? <p role="status" className="break-all rounded-xl bg-gray-50 p-3 text-sm text-gray-600 dark:bg-gray-800">{message}</p> : null}
      {diagnostics.length ? <DiagnosticList diagnostics={diagnostics} /> : null}
    </CardContent></Card>
  </div>;
}

function DiagnosticList({ diagnostics }: { diagnostics: Diagnostic[] }) {
  return <ul className="space-y-2" aria-label="Compiler diagnostics">{diagnostics.map((item, index) => <li key={`${item.code}-${index}`} className="rounded-lg border border-error-200 p-3 text-sm dark:border-error-500/30"><strong className="text-error-600">{item.code}</strong> <code className="break-all text-xs text-gray-500">{item.path}</code><p className="mt-1 text-gray-600 dark:text-gray-300">{item.message}</p></li>)}</ul>;
}
