import { useMutation } from "@tanstack/react-query";
import { CheckCircle2 } from "lucide-react";
import { FormEvent, useMemo, useState } from "react";
import { api } from "@/api/client";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useWorkspaceScope } from "@/lib/demo-scope";

export interface RequirementRow { key: string; documentType: string; mediaTypes: string; required: boolean; severity: string; }
export function previewMissing(requirements: RequirementRow[], sampleTypes: string[]) { return requirements.filter((row) => row.required && !sampleTypes.includes(row.documentType)).map((row) => row.documentType); }

const fieldClass = "h-10 w-full rounded-lg border border-gray-300 bg-transparent px-3 text-sm outline-none focus:border-brand-500 dark:border-gray-700 dark:text-white";

const initialRows: RequirementRow[] = [
  { key: "contract", documentType: "contract", mediaTypes: "application/pdf", required: true, severity: "CRITICAL" },
  { key: "business-license", documentType: "business-license", mediaTypes: "application/pdf,image/png,image/jpeg", required: true, severity: "HIGH" },
  { key: "authorization", documentType: "authorization", mediaTypes: "application/pdf", required: true, severity: "HIGH" },
];

export function RuleSetsPage() {
  const { tenantId, projectId } = useWorkspaceScope();
  const [rows, setRows] = useState(initialRows);
  const [sample, setSample] = useState("contract,business-license");
  const [published, setPublished] = useState<string | null>(null);
  const missing = useMemo(() => previewMissing(rows, sample.split(",").map((value) => value.trim()).filter(Boolean)), [rows, sample]);
  const save = useMutation({ mutationFn: async () => { const rules = { schemaVersion: "schema://contract/checklist-rule@1", match: { contractType: "purchase" }, requirements: rows.map((row) => ({ key: row.key, documentType: row.documentType, required: row.required, mediaTypes: row.mediaTypes.split(",").map((value) => value.trim()).filter(Boolean), severity: row.severity })) }; const draft = await api.createRuleSet(tenantId, projectId, { name: `采购合同资料规则-${Date.now()}`, purpose: "采购合同资料完整性校验", rules }); const version = await api.publishRuleSet(tenantId, projectId, draft.draftId); setPublished(version.contentHash); return version; } });
  const submit = (event: FormEvent) => { event.preventDefault(); save.mutate(); };
  const update = (index: number, field: keyof RequirementRow, value: string | boolean) => setRows((current) => current.map((row, rowIndex) => rowIndex === index ? { ...row, [field]: value } : row));

  return <div className="min-w-0 space-y-6">
    <div className="flex flex-wrap items-end justify-between gap-4">
      <div>
        <p className="text-sm font-medium text-brand-500">治理</p>
        <h1 className="mt-1 text-2xl font-semibold text-gray-900 dark:text-white">规则集</h1>
        <p className="mt-1 text-sm text-gray-500">确定性资料清单规则；发布后版本不可修改。</p>
      </div>
    </div>

    <form onSubmit={submit} className="space-y-5">
      <Card className="overflow-hidden">
        <CardHeader><CardTitle>需求规则</CardTitle><span className="text-xs text-gray-500">编辑后校验并发布</span></CardHeader>
        <CardContent className="overflow-x-auto px-0">
          <table className="w-full min-w-[800px] text-left text-sm">
            <thead className="border-y border-gray-100 bg-gray-50 text-xs text-gray-500 dark:border-gray-800 dark:bg-gray-800/50">
              <tr><th className="px-5 py-3 font-medium">规则键</th><th className="px-5 py-3 font-medium">资料类型</th><th className="px-5 py-3 font-medium">允许 MIME</th><th className="px-5 py-3 font-medium text-center">必需</th><th className="px-5 py-3 font-medium">严重级别</th></tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
              {rows.map((row, index) => <tr key={row.key}>
                <td className="px-4 py-3"><input aria-label={`规则键 ${index + 1}`} className={fieldClass} value={row.key} onChange={(event) => update(index, "key", event.target.value)} /></td>
                <td className="px-4 py-3"><input aria-label={`资料类型 ${index + 1}`} className={fieldClass} value={row.documentType} onChange={(event) => update(index, "documentType", event.target.value)} /></td>
                <td className="px-4 py-3"><input aria-label={`MIME ${index + 1}`} className={fieldClass} value={row.mediaTypes} onChange={(event) => update(index, "mediaTypes", event.target.value)} /></td>
                <td className="px-4 py-3 text-center"><input aria-label={`必需 ${index + 1}`} checked={row.required} type="checkbox" className="size-4 rounded border-gray-300 text-brand-500 focus:ring-brand-500" onChange={(event) => update(index, "required", event.target.checked)} /></td>
                <td className="px-4 py-3"><select aria-label={`严重级别 ${index + 1}`} className={fieldClass} value={row.severity} onChange={(event) => update(index, "severity", event.target.value)}><option>LOW</option><option>MEDIUM</option><option>HIGH</option><option>CRITICAL</option></select></td>
              </tr>)}
            </tbody>
          </table>
        </CardContent>
      </Card>

      <div className="grid gap-5 lg:grid-cols-[1fr_auto]">
        <Card>
          <CardHeader><CardTitle>样例预览</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">样例附件类型（逗号分隔）
              <input aria-label="样例附件类型" className="mt-1 h-11 w-full rounded-lg border border-gray-300 bg-transparent px-3 text-sm outline-none focus:border-brand-500 dark:border-gray-700 dark:text-white" value={sample} onChange={(event) => setSample(event.target.value)} />
            </label>
            <div className="flex items-center gap-2">
              {missing.length
                ? <><Badge color="warning">缺少 {missing.length} 项</Badge><span className="text-sm text-gray-500">{missing.join("、")}</span></>
                : <Badge color="success">资料完整</Badge>}
            </div>
          </CardContent>
        </Card>
        <div className="flex flex-col items-end justify-end gap-3">
          <Button disabled={save.isPending} loading={save.isPending} type="submit"><CheckCircle2 />校验并发布规则</Button>
          {published ? <p role="status" className="text-sm text-success-600">已发布：{published.slice(0, 16)}</p> : null}
          {save.isError ? <p role="alert" className="text-sm text-error-600">发布失败：{save.error.message}</p> : null}
        </div>
      </div>
    </form>
  </div>;
}
