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
import { useWorkspaceScope } from "@/lib/demo-scope";

export function StrategyDetailPage() {
  const { strategyId = "" } = useParams();
  const { tenantId, projectId } = useWorkspaceScope();
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
      setMessage("草稿不是有效的 SwarmSpec 文档。");
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
    setMessage(apiConflict ? "草稿修订版本冲突，请重新加载服务端草稿后再保存。" : error instanceof Error ? error.message : "操作失败。");
  };

  const save = useMutation({
    mutationFn: async () => {
      if (!spec || !draft.data) throw new Error("草稿尚未就绪。");
      return api.updateDraft(tenantId, projectId, strategyId, draft.data.draftId, revision, spec, editorState);
    },
    onSuccess: async (snapshot) => {
      setRevision(snapshot.revision);
      setDirty(false);
      setConflict(false);
      setMessage("草稿已保存。");
      client.setQueryData(["draft", tenantId, projectId, strategyId, draft.data?.draftId], snapshot);
      await client.invalidateQueries({ queryKey: ["strategies", tenantId, projectId] });
    },
    onError: handleError,
  });

  const compile = useMutation({
    mutationFn: async () => {
      if (!spec) throw new Error("草稿尚未就绪。");
      return api.compileStrategy(tenantId, projectId, spec);
    },
    onSuccess: (result) => {
      setDiagnostics(result.diagnostics);
      const hash = result.plan?.["plan_hash"];
      setMessage(result.valid ? `计划校验通过 · ${typeof hash === "string" ? hash : ""}` : "编译发现错误。");
    },
    onError: handleError,
  });

  const publish = useMutation({
    mutationFn: async () => {
      if (!spec || !draft.data) throw new Error("草稿尚未就绪。");
      const compiled = await api.compileStrategy(tenantId, projectId, spec);
      setDiagnostics(compiled.diagnostics);
      if (!compiled.valid) throw new Error("发布已停止：请先修复编译诊断。");
      const saved = await api.updateDraft(tenantId, projectId, strategyId, draft.data.draftId, revision, spec, editorState);
      const published = await api.publishStrategy(tenantId, projectId, strategyId, draft.data.draftId);
      return { saved, published };
    },
    onSuccess: async ({ saved, published }) => {
      setRevision(saved.revision);
      setDirty(false);
      setConflict(false);
      setMessage(`已发布版本 ${published.version} · ${published.planHash}`);
      client.setQueryData(["draft", tenantId, projectId, strategyId, draft.data?.draftId], saved);
      await Promise.all([
        client.invalidateQueries({ queryKey: ["versions", tenantId, projectId, strategyId] }),
        client.invalidateQueries({ queryKey: ["strategies", tenantId, projectId] }),
      ]);
    },
    onError: handleError,
  });

  const reload = async () => {
    if (dirty && !window.confirm("是否放弃尚未保存的规范和画布布局更改？")) return;
    const result = await draft.refetch();
    if (result.data) loadSnapshot(result.data);
  };

  if (strategies.isPending || draft.isPending) return <div className="space-y-5"><Skeleton className="h-20" /><Skeleton className="h-96" /></div>;
  if (strategies.isError || !strategy || draft.isError || !draft.data) return <Card><CardContent className="flex min-h-60 flex-col items-center justify-center gap-3 pt-5"><p className="font-medium text-error-600">无法加载策略</p><Button onClick={() => void strategies.refetch()}>重试</Button></CardContent></Card>;
  if (!spec) return <Card><CardContent className="flex min-h-60 items-center justify-center pt-5"><p className="font-medium text-error-600">草稿不是有效的 SwarmSpec 文档。</p></CardContent></Card>;
  return <div className="min-w-0 space-y-6">
    <div><Link to=".." className="text-sm text-brand-500">← 策略管理</Link><div className="mt-3 flex flex-wrap items-end justify-between gap-4"><div><h1 className="text-2xl font-semibold text-gray-900 dark:text-white">{strategy.name}</h1><p className="mt-1 text-sm text-gray-500">草稿修订 {revision}{dirty ? " · 未保存" : ""}</p></div><Button variant="outline" onClick={() => void reload()}><RefreshCw />重新加载</Button></div></div>
    <Card><CardContent className="space-y-4 pt-5">
      <StrategyEditor spec={spec} editorState={editorState} nodeTypes={capabilities.data?.nodeTypes.map((item) => item.type) ?? []} diagnostics={diagnostics} onSpecChange={(value) => { setSpec(value); setDirty(true); setMessage(""); }} onEditorStateChange={(value) => { setEditorState(value); setDirty(true); }} onError={setMessage} />
      <div className="flex flex-wrap justify-end gap-2"><Button variant="outline" onClick={() => compile.mutate()} loading={compile.isPending}><CheckCircle2 />校验</Button><Button variant="outline" onClick={() => save.mutate()} loading={save.isPending} disabled={conflict}><Save />保存草稿</Button><Button onClick={() => publish.mutate()} loading={publish.isPending} disabled={conflict}><Rocket />保存并发布</Button></div>
      {message ? <p role="status" className="break-all rounded-xl bg-gray-50 p-3 text-sm text-gray-600 dark:bg-gray-800">{message}</p> : null}
    </CardContent></Card>
    {diagnostics.length ? <Card><CardHeader><CardTitle>诊断信息</CardTitle></CardHeader><CardContent><ul className="space-y-3">{diagnostics.map((item, index) => <li key={`${item.code}-${index}`} className="rounded-xl border border-error-200 p-3 dark:border-error-500/30"><div className="flex flex-wrap gap-2 text-sm"><strong className="text-error-600">{item.code}</strong><code className="break-all text-gray-500">{item.path}</code></div><p className="mt-1 text-sm text-gray-600 dark:text-gray-300">{item.message}</p></li>)}</ul></CardContent></Card> : null}
    <Card><CardHeader><CardTitle>已发布版本</CardTitle><span className="text-sm text-gray-500">{versions.data?.total ?? 0}</span></CardHeader><CardContent>{versions.isError ? <div className="flex items-center justify-between gap-3"><p className="text-sm text-error-600">无法加载版本。</p><Button size="sm" onClick={() => void versions.refetch()}>重试</Button></div> : versions.data?.items.length ? <ul className="space-y-3">{versions.data.items.map((version) => <li key={version.strategyVersionId} className="rounded-xl border border-gray-200 p-4 dark:border-gray-800"><p className="font-medium">版本 {version.version}</p><p className="mt-1 break-all font-mono text-xs text-gray-500">{version.planHash}</p></li>)}</ul> : <p className="py-8 text-center text-sm text-gray-500">暂无已发布版本。</p>}</CardContent></Card>
  </div>;
}
