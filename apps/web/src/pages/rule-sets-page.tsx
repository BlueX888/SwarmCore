import { useMutation } from "@tanstack/react-query";
import { FormEvent, useMemo, useState } from "react";
import { api } from "@/api/client";
import { Button } from "@/components/ui/button";
import { useWorkspaceScope } from "@/lib/demo-scope";

export interface RequirementRow { key: string; documentType: string; mediaTypes: string; required: boolean; severity: string; }
export function previewMissing(requirements: RequirementRow[], sampleTypes: string[]) { return requirements.filter((row) => row.required && !sampleTypes.includes(row.documentType)).map((row) => row.documentType); }

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
  return <section className="space-y-5"><header><h1 className="text-2xl font-semibold text-gray-900 dark:text-white">规则集</h1><p className="mt-1 text-sm text-gray-500">确定性资料清单规则；发布后版本不可修改。</p></header><form onSubmit={submit} className="space-y-4"><div className="overflow-x-auto rounded-xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-800"><table className="w-full min-w-180 text-left text-sm"><thead className="bg-gray-50 text-gray-500 dark:bg-gray-900"><tr><th className="p-3">规则键</th><th className="p-3">资料类型</th><th className="p-3">允许 MIME</th><th className="p-3">必需</th><th className="p-3">严重级别</th></tr></thead><tbody>{rows.map((row, index) => <tr key={row.key} className="border-t border-gray-100 dark:border-gray-700"><td className="p-2"><input aria-label={`规则键 ${index + 1}`} className="w-full rounded border border-gray-300 bg-transparent p-2" value={row.key} onChange={(event) => update(index, "key", event.target.value)} /></td><td className="p-2"><input aria-label={`资料类型 ${index + 1}`} className="w-full rounded border border-gray-300 bg-transparent p-2" value={row.documentType} onChange={(event) => update(index, "documentType", event.target.value)} /></td><td className="p-2"><input aria-label={`MIME ${index + 1}`} className="w-full rounded border border-gray-300 bg-transparent p-2" value={row.mediaTypes} onChange={(event) => update(index, "mediaTypes", event.target.value)} /></td><td className="p-2 text-center"><input aria-label={`必需 ${index + 1}`} checked={row.required} type="checkbox" onChange={(event) => update(index, "required", event.target.checked)} /></td><td className="p-2"><select aria-label={`严重级别 ${index + 1}`} className="rounded border border-gray-300 bg-transparent p-2" value={row.severity} onChange={(event) => update(index, "severity", event.target.value)}><option>LOW</option><option>MEDIUM</option><option>HIGH</option><option>CRITICAL</option></select></td></tr>)}</tbody></table></div><div className="grid gap-4 lg:grid-cols-[1fr_auto]"><label className="rounded-xl border border-gray-200 bg-white p-4 text-sm dark:border-gray-800 dark:bg-gray-800">样例附件类型（逗号分隔）<input aria-label="样例附件类型" className="mt-2 w-full rounded-lg border border-gray-300 bg-transparent px-3 py-2" value={sample} onChange={(event) => setSample(event.target.value)} /><p className="mt-3 text-sm">预览：{missing.length ? `缺少 ${missing.join("、")}` : "资料完整"}</p></label><Button className="self-end" disabled={save.isPending} type="submit">校验并发布规则</Button></div>{published ? <p role="status" className="text-sm text-success-600">已发布：{published.slice(0, 16)}</p> : null}</form></section>;
}
