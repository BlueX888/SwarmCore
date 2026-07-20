import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, RefreshCw, RotateCcw, ShieldCheck, TriangleAlert, Upload } from "lucide-react";
import { ChangeEvent, useState } from "react";
import { Link, useParams } from "react-router";
import { api } from "@/api/client";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusBadge } from "@/components/ui/status-badge";
import { useWorkspaceScope } from "@/lib/demo-scope";

async function digest(file: File) { return Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256", await file.arrayBuffer()))).map((value) => value.toString(16).padStart(2, "0")).join(""); }
async function base64(file: File) { return new Promise<string>((resolve, reject) => { const reader = new FileReader(); reader.onload = () => { if (typeof reader.result !== "string") { reject(new Error("FileReader returned no data")); return; } resolve(reader.result.split(",")[1] ?? ""); }; reader.onerror = () => reject(reader.error ?? new Error("FileReader failed")); reader.readAsDataURL(file); }); }
function itemTitle(payload: Record<string, unknown>) { return typeof payload.title === "string" ? payload.title : "工作项详情"; }

export function WorkItemDetailPage() {
  const { workItemId = "" } = useParams();
  const { tenantId, projectId, workspacePath } = useWorkspaceScope();
  const queryClient = useQueryClient();
  const [documentType, setDocumentType] = useState("authorization");
  const [evaluationId, setEvaluationId] = useState<string | null>(null);
  const item = useQuery({ queryKey: ["work-item", workItemId], queryFn: () => api.getWorkItem(tenantId, projectId, workItemId), enabled: Boolean(workItemId) });
  const findings = useQuery({ queryKey: ["findings", workItemId], queryFn: () => api.listFindings(tenantId, projectId, workItemId), enabled: Boolean(workItemId) });
  const reports = useQuery({ queryKey: ["reports", evaluationId], queryFn: () => api.listReports(tenantId, projectId, evaluationId ?? ""), enabled: Boolean(evaluationId) });
  const execute = useMutation({ mutationFn: () => api.executeWorkItem(tenantId, projectId, workItemId), onSuccess: (value) => { setEvaluationId(value.evaluationId); void queryClient.invalidateQueries({ queryKey: ["findings", workItemId] }); void queryClient.invalidateQueries({ queryKey: ["work-item", workItemId] }); } });
  const upload = useMutation({ mutationFn: async (file: File) => { const sha256 = await digest(file); const handle = await api.initiateAttachment(tenantId, projectId, workItemId, { documentType, filename: file.name, mediaType: file.type || "application/octet-stream", sizeBytes: file.size, sha256 }); await api.uploadBlob(handle, await base64(file)); return api.completeAttachment(tenantId, projectId, handle, sha256); }, onSuccess: () => queryClient.invalidateQueries({ queryKey: ["work-item", workItemId] }) });
  const act = useMutation({ mutationFn: ({ findingId, action }: { findingId: string; action: "ACKNOWLEDGE" | "WAIVE" | "RESOLVE" | "REOPEN" }) => api.actOnFinding(tenantId, projectId, findingId, action, action === "WAIVE" ? "控制台人工豁免" : undefined), onSuccess: () => queryClient.invalidateQueries({ queryKey: ["findings", workItemId] }) });
  const chooseFile = (event: ChangeEvent<HTMLInputElement>) => { const file = event.target.files?.[0]; if (file) upload.mutate(file); };
  const refresh = () => { void item.refetch(); void findings.refetch(); };

  if (item.isLoading) return <div className="space-y-5"><Skeleton className="h-20" /><div className="grid gap-4 lg:grid-cols-2"><Skeleton className="h-64" /><Skeleton className="h-64" /></div></div>;
  if (!item.data) return <Card><CardContent className="flex min-h-60 flex-col items-center justify-center gap-3 pt-5 text-center"><p className="font-medium text-error-600">工作项不存在或加载失败</p><p className="text-sm text-gray-500">{item.error?.message}</p><Button onClick={() => void item.refetch()}>重试</Button></CardContent></Card>;

  return <div className="min-w-0 space-y-6">
    <div>
      <Link to={`${workspacePath}/work-items`} className="text-sm text-brand-500 hover:text-brand-600">← 业务工作项</Link>
      <div className="mt-3 flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-2xl font-semibold text-gray-900 dark:text-white">{itemTitle(item.data.payload)}</h1>
            <StatusBadge status={item.data.status} />
          </div>
          <p className="mt-2 text-sm text-gray-500">{item.data.workItemType} · 修订 v{item.data.revision}</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={refresh} loading={item.isFetching || findings.isFetching}><RefreshCw />刷新</Button>
          <Button disabled={execute.isPending} loading={execute.isPending} onClick={() => execute.mutate()}><ShieldCheck />发起完整性校验</Button>
        </div>
      </div>
    </div>

    <div className="grid gap-5 lg:grid-cols-2">
      <Card>
        <CardHeader><CardTitle>输入与附件</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <pre className="overflow-auto rounded-xl bg-gray-950 p-4 text-xs leading-6 text-gray-100">{JSON.stringify(item.data.payload, null, 2)}</pre>
          <div className="flex flex-wrap items-end gap-4">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">资料类型
              <select className="mt-1 block h-11 rounded-lg border border-gray-300 bg-transparent px-3 text-sm outline-none focus:border-brand-500 dark:border-gray-700" value={documentType} onChange={(event) => setDocumentType(event.target.value)}>
                <option value="contract">合同正文</option>
                <option value="business-license">营业执照</option>
                <option value="authorization">授权书</option>
              </select>
            </label>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">上传文件
              <div className="mt-1 flex h-11 items-center">
                <input className="block max-w-64 text-sm file:mr-3 file:rounded-lg file:border-0 file:bg-brand-50 file:px-3 file:py-2 file:text-sm file:font-medium file:text-brand-600 hover:file:bg-brand-100 dark:file:bg-brand-500/15 dark:file:text-brand-400" type="file" onChange={chooseFile} />
              </div>
            </label>
          </div>
          {upload.isPending ? <p className="flex items-center gap-2 text-sm text-gray-500"><Upload className="size-4 animate-pulse" />正在上传并扫描…</p> : null}
          {upload.isError ? <p role="alert" className="rounded-xl bg-error-50 p-3 text-sm text-error-600 dark:bg-error-500/15">上传失败：{upload.error.message}</p> : null}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>问题</CardTitle>
          {findings.data?.items.length ? <Badge color="warning">{findings.data.items.length} 项</Badge> : null}
        </CardHeader>
        <CardContent>
          {findings.isPending ? <div className="space-y-3"><Skeleton className="h-20" /><Skeleton className="h-20" /></div> : null}
          {findings.isError ? <p className="text-sm text-error-600">问题列表加载失败。</p> : null}
          {findings.data?.items.length === 0 ? <div className="flex min-h-32 flex-col items-center justify-center gap-2 text-center"><span className="grid size-10 place-items-center rounded-xl bg-success-50 text-success-600 dark:bg-success-500/15"><Check /></span><p className="text-sm text-gray-500">当前没有问题。</p></div> : null}
          <div className="space-y-3">
            {findings.data?.items.map((finding) => <div key={finding.findingId} className="rounded-xl border border-gray-200 p-4 dark:border-gray-800">
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-center gap-2">
                  <TriangleAlert className="size-4 shrink-0 text-warning-500" />
                  <strong className="text-sm font-medium text-gray-900 dark:text-white">{finding.title}</strong>
                </div>
                <StatusBadge status={finding.status} />
              </div>
              <p className="mt-2 text-sm text-gray-500">{finding.detail}</p>
              <div className="mt-3 flex flex-wrap gap-2">
                {finding.status === "OPEN" ? <Button size="sm" variant="outline" disabled={act.isPending} onClick={() => act.mutate({ findingId: finding.findingId, action: "ACKNOWLEDGE" })}>确认</Button> : null}
                {finding.status === "OPEN" || finding.status === "ACKNOWLEDGED" ? <>
                  <Button size="sm" variant="outline" disabled={act.isPending} onClick={() => act.mutate({ findingId: finding.findingId, action: "RESOLVE" })}>解决</Button>
                  <Button size="sm" variant="outline" disabled={act.isPending} onClick={() => act.mutate({ findingId: finding.findingId, action: "WAIVE" })}>豁免</Button>
                </> : <Button size="sm" variant="outline" disabled={act.isPending} onClick={() => act.mutate({ findingId: finding.findingId, action: "REOPEN" })}><RotateCcw />重新打开</Button>}
              </div>
            </div>)}
          </div>
        </CardContent>
      </Card>
    </div>

    {evaluationId ? <Card>
      <CardHeader><CardTitle>本次报告</CardTitle></CardHeader>
      <CardContent>
        {reports.isPending ? <Skeleton className="h-10" /> : null}
        {reports.data?.items.length ? <div className="flex flex-wrap gap-3">{reports.data.items.map((report) => <Badge key={report.reportId} color="primary">{report.format} · {report.contentHash.slice(0, 10)}</Badge>)}</div> : null}
        {reports.data?.items.length === 0 ? <p className="text-sm text-gray-500">报告生成中…</p> : null}
      </CardContent>
    </Card> : null}
  </div>;
}
