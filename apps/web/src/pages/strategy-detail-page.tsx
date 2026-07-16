import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, RefreshCw, Rocket, Save } from "lucide-react";
import * as React from "react";
import { Link, useParams } from "react-router";
import { api, ApiError } from "@/api/client";
import type { Diagnostic, DraftSnapshot } from "@/api/types";
import { StrategyEditor } from "@/components/strategy/strategy-editor";
import { EMPTY_EDITOR_STATE, isSwarmSpecDocument, type EditorState, type SwarmSpecDocument } from "@/components/strategy/strategy-editor-model";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

export function StrategyDetailPage() {
  const { tenantId = "", projectId = "", strategyId = "" } = useParams();
  const client = useQueryClient();
  const strategies = useQuery({ queryKey: ["strategies", tenantId, projectId], queryFn: () => api.listStrategies(tenantId, projectId) });
  const strategy = strategies.data?.items.find((item) => item.strategyId === strategyId);
  const draft = useQuery({ queryKey: ["draft", tenantId, projectId, strategyId, strategy?.draftId], queryFn: () => api.getDraft(tenantId, projectId, strategyId, strategy?.draftId ?? ""), enabled: Boolean(strategy?.draftId) });
  const versions = useQuery({ queryKey: ["versions", tenantId, projectId, strategyId], queryFn: () => api.listVersions(tenantId, projectId, strategyId) });
  const capabilities = useQuery({ queryKey: ["capabilities", tenantId, projectId], queryFn: () => api.getCapabilities(tenantId, projectId) });
  const [spec, setSpec] = React.useState<SwarmSpecDocument | null>(null);
  const [editorState, setEditorState] = React.useState<EditorState>(() => structuredClone(EMPTY_EDITOR_STATE));
  const [revision, setRevision] = React.useState(0);
  const [dirty, setDirty] = React.useState(false);
  const [diagnostics, setDiagnostics] = React.useState<Diagnostic[]>([]);
  const [message, setMessage] = React.useState("");
  const [conflict, setConflict] = React.useState(false);
  const initializedDraft = React.useRef<string | null>(null);

  const loadSnapshot = React.useCallback((snapshot: DraftSnapshot) => {
    if (!isSwarmSpecDocument(snapshot.spec)) {
      setMessage("Draft is not a SwarmSpec document.");
      return;
    }
    setSpec(snapshot.spec);
    setEditorState(snapshot.editorState ?? structuredClone(EMPTY_EDITOR_STATE));
    setRevision(snapshot.revision);
    setDiagnostics(snapshot.diagnostics);
    setDirty(false);
    setConflict(false);
    initializedDraft.current = snapshot.draftId;
  }, []);

  React.useEffect(() => {
    if (draft.data && initializedDraft.current !== draft.data.draftId) loadSnapshot(draft.data);
  }, [draft.data, loadSnapshot]);

  React.useEffect(() => {
    const beforeUnload = (event: BeforeUnloadEvent) => { if (dirty) event.preventDefault(); };
    window.addEventListener("beforeunload", beforeUnload);
    return () => window.removeEventListener("beforeunload", beforeUnload);
  }, [dirty]);

  React.useEffect(() => {
    if (!spec || !initializedDraft.current) return;
    let cancelled = false;
    const timer = window.setTimeout(() => {
      void api.compileStrategy(tenantId, projectId, spec).then((result) => {
        if (!cancelled) setDiagnostics(result.diagnostics);
      }).catch(() => undefined);
    }, 700);
    return () => { cancelled = true; window.clearTimeout(timer); };
  }, [projectId, spec, tenantId]);

  const handleError = (error: unknown) => {
    const apiConflict = error instanceof ApiError && error.status === 409;
    setConflict(apiConflict);
    setMessage(apiConflict ? "Draft revision conflict. Reload the server draft before saving again." : error instanceof Error ? error.message : "Operation failed.");
  };

  const save = useMutation({
    mutationFn: async () => {
      if (!spec || !draft.data) throw new Error("Draft is not ready.");
      return api.updateDraft(tenantId, projectId, strategyId, draft.data.draftId, revision, spec, editorState);
    },
    onSuccess: async (snapshot) => {
      setRevision(snapshot.revision);
      setDirty(false);
      setConflict(false);
      setMessage("Draft saved.");
      client.setQueryData(["draft", tenantId, projectId, strategyId, draft.data?.draftId], snapshot);
      await client.invalidateQueries({ queryKey: ["strategies", tenantId, projectId] });
    },
    onError: handleError,
  });

  const compile = useMutation({
    mutationFn: async () => {
      if (!spec) throw new Error("Draft is not ready.");
      return api.compileStrategy(tenantId, projectId, spec);
    },
    onSuccess: (result) => {
      setDiagnostics(result.diagnostics);
      const hash = result.plan?.["plan_hash"];
      setMessage(result.valid ? `Valid plan · ${typeof hash === "string" ? hash : ""}` : "Compilation found errors.");
    },
    onError: handleError,
  });

  const publish = useMutation({
    mutationFn: async () => {
      if (!spec || !draft.data) throw new Error("Draft is not ready.");
      const compiled = await api.compileStrategy(tenantId, projectId, spec);
      setDiagnostics(compiled.diagnostics);
      if (!compiled.valid) throw new Error("Publish stopped: fix compiler diagnostics first.");
      const saved = await api.updateDraft(tenantId, projectId, strategyId, draft.data.draftId, revision, spec, editorState);
      const published = await api.publishStrategy(tenantId, projectId, strategyId, draft.data.draftId);
      return { saved, published };
    },
    onSuccess: async ({ saved, published }) => {
      setRevision(saved.revision);
      setDirty(false);
      setConflict(false);
      setMessage(`Published version ${published.version} · ${published.planHash}`);
      client.setQueryData(["draft", tenantId, projectId, strategyId, draft.data?.draftId], saved);
      await Promise.all([
        client.invalidateQueries({ queryKey: ["versions", tenantId, projectId, strategyId] }),
        client.invalidateQueries({ queryKey: ["strategies", tenantId, projectId] }),
      ]);
    },
    onError: handleError,
  });

  const reload = async () => {
    if (dirty && !window.confirm("Discard unsaved Spec and canvas layout changes?")) return;
    const result = await draft.refetch();
    if (result.data) loadSnapshot(result.data);
  };

  if (strategies.isPending || draft.isPending) return <div className="space-y-5"><Skeleton className="h-20" /><Skeleton className="h-96" /></div>;
  if (strategies.isError || !strategy || draft.isError || !draft.data) return <Card><CardContent className="flex min-h-60 flex-col items-center justify-center gap-3 pt-5"><p className="font-medium text-error-600">Strategy could not be loaded</p><Button onClick={() => void strategies.refetch()}>Retry</Button></CardContent></Card>;
  if (!spec) return <Card><CardContent className="flex min-h-60 items-center justify-center pt-5"><p className="font-medium text-error-600">Draft is not a valid SwarmSpec document.</p></CardContent></Card>;
  return <div className="min-w-0 space-y-6">
    <div><Link to=".." className="text-sm text-brand-500">← Strategies</Link><div className="mt-3 flex flex-wrap items-end justify-between gap-4"><div><h1 className="text-2xl font-semibold text-gray-900 dark:text-white">{strategy.name}</h1><p className="mt-1 text-sm text-gray-500">Draft revision {revision}{dirty ? " · unsaved" : ""}</p></div><Button variant="outline" onClick={() => void reload()}><RefreshCw />Reload</Button></div></div>
    <Card><CardContent className="space-y-4 pt-5">
      <StrategyEditor spec={spec} editorState={editorState} nodeTypes={capabilities.data?.nodeTypes.map((item) => item.type) ?? []} diagnostics={diagnostics} onSpecChange={(value) => { setSpec(value); setDirty(true); setMessage(""); }} onEditorStateChange={(value) => { setEditorState(value); setDirty(true); }} onError={setMessage} />
      <div className="flex flex-wrap justify-end gap-2"><Button variant="outline" onClick={() => compile.mutate()} loading={compile.isPending}><CheckCircle2 />Validate</Button><Button variant="outline" onClick={() => save.mutate()} loading={save.isPending} disabled={conflict}><Save />Save draft</Button><Button onClick={() => publish.mutate()} loading={publish.isPending} disabled={conflict}><Rocket />Save & publish</Button></div>
      {message ? <p role="status" className="break-all rounded-xl bg-gray-50 p-3 text-sm text-gray-600 dark:bg-gray-800">{message}</p> : null}
    </CardContent></Card>
    {diagnostics.length ? <Card><CardHeader><CardTitle>Diagnostics</CardTitle></CardHeader><CardContent><ul className="space-y-3">{diagnostics.map((item, index) => <li key={`${item.code}-${index}`} className="rounded-xl border border-error-200 p-3 dark:border-error-500/30"><div className="flex flex-wrap gap-2 text-sm"><strong className="text-error-600">{item.code}</strong><code className="break-all text-gray-500">{item.path}</code></div><p className="mt-1 text-sm text-gray-600 dark:text-gray-300">{item.message}</p></li>)}</ul></CardContent></Card> : null}
    <Card><CardHeader><CardTitle>Published versions</CardTitle><span className="text-sm text-gray-500">{versions.data?.total ?? 0}</span></CardHeader><CardContent>{versions.isError ? <div className="flex items-center justify-between gap-3"><p className="text-sm text-error-600">Versions could not be loaded.</p><Button size="sm" onClick={() => void versions.refetch()}>Retry</Button></div> : versions.data?.items.length ? <ul className="space-y-3">{versions.data.items.map((version) => <li key={version.strategyVersionId} className="rounded-xl border border-gray-200 p-4 dark:border-gray-800"><p className="font-medium">Version {version.version}</p><p className="mt-1 break-all font-mono text-xs text-gray-500">{version.planHash}</p></li>)}</ul> : <p className="py-8 text-center text-sm text-gray-500">No published versions.</p>}</CardContent></Card>
  </div>;
}
