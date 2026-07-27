import { useMutation } from "@tanstack/react-query";
import { CheckCircle2, Plus, Trash2 } from "lucide-react";
import { type FormEvent, useState } from "react";
import { api } from "@/api/client";
import { BackLink } from "@/components/ui/back-link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useWorkspaceScope } from "@/lib/demo-scope";

export interface PolicyRequirement {
  id: number; key: string; documentType: string; mediaTypes: string; required: boolean; severity: string;
}

const fieldClass = "h-10 w-full rounded-lg border border-gray-300 bg-transparent px-3 text-sm outline-none focus:border-brand-500 dark:border-gray-700 dark:text-white";
const initialRequirements: PolicyRequirement[] = [
  { id: 1, key: "contract", documentType: "contract", mediaTypes: "application/pdf", required: true, severity: "CRITICAL" },
];

export function buildPolicyRules(requirements: PolicyRequirement[]): Record<string, unknown> {
  return {
    schemaVersion: "schema://contract/checklist-rule@1",
    match: {},
    requirements: requirements.map((row) => ({
      key: row.key.trim(), documentType: row.documentType.trim(), required: row.required,
      mediaTypes: row.mediaTypes.split(",").map((value) => value.trim()).filter(Boolean), severity: row.severity,
    })),
  };
}

export function PolicyCreatePage() {
  const { tenantId, projectId, workspacePath } = useWorkspaceScope();
  const [name, setName] = useState("");
  const [purpose, setPurpose] = useState("");
  const [requirements, setRequirements] = useState(initialRequirements);
  const [published, setPublished] = useState<{ version: number; contentHash: string }>();
  const [formError, setFormError] = useState("");
  const create = useMutation({
    mutationFn: async () => {
      const draft = await api.createRuleSet(tenantId, projectId, { name: name.trim(), purpose: purpose.trim(), rules: buildPolicyRules(requirements) });
      await api.validateRuleSet(tenantId, projectId, draft.draftId);
      return api.publishRuleSet(tenantId, projectId, draft.draftId);
    },
    onSuccess: (version) => setPublished(version),
  });
  const canSubmit = Boolean(name.trim() && purpose.trim() && requirements.length && requirements.every((row) => row.key.trim() && row.documentType.trim() && row.mediaTypes.trim()));
  const update = (id: number, field: keyof Omit<PolicyRequirement, "id">, value: string | boolean) => setRequirements((current) => current.map((row) => row.id === id ? { ...row, [field]: value } : row));
  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (!canSubmit) {
      setFormError(!name.trim() || !purpose.trim() ? "请先填写策略名称和策略用途。" : "请完整填写至少一条资料要求。");
      return;
    }
    setFormError("");
    create.mutate();
  };

  return <div className="min-w-0 space-y-6">
    <div><BackLink to={`${workspacePath}/policies`}>策略能力</BackLink><h1 className="mt-4 text-2xl font-semibold text-gray-900 dark:text-white">新建策略</h1><p className="mt-1 text-sm text-gray-500">定义确定性的资料要求；系统会先校验草稿，再发布不可变版本。</p></div>
    <form className="space-y-5" onSubmit={submit}>
      <Card><CardHeader><CardTitle>基本信息</CardTitle></CardHeader><CardContent className="grid gap-4 md:grid-cols-2">
        <label className="text-sm font-medium">策略名称 <span className="text-error-500">*</span><input aria-label="策略名称" className={`mt-2 ${fieldClass}`} value={name} onChange={(event) => { setName(event.target.value); setFormError(""); }} placeholder="例如：采购合同资料策略" /></label>
        <label className="text-sm font-medium">策略用途 <span className="text-error-500">*</span><input aria-label="策略用途" className={`mt-2 ${fieldClass}`} value={purpose} onChange={(event) => { setPurpose(event.target.value); setFormError(""); }} placeholder="说明该策略用于什么场景" /></label>
      </CardContent></Card>
      <Card className="overflow-hidden"><CardHeader><div><CardTitle>资料要求</CardTitle><p className="mt-1 text-sm text-gray-500">每项要求包含稳定键、资料类型、允许格式和严重级别。</p></div><Button type="button" variant="outline" size="sm" onClick={() => setRequirements((current) => [...current, { id: Date.now(), key: "", documentType: "", mediaTypes: "application/pdf", required: true, severity: "HIGH" }])}><Plus />添加要求</Button></CardHeader><CardContent className="space-y-3">
        {requirements.map((row, index) => <section key={row.id} aria-label={`资料要求 ${index + 1}`} className="grid gap-3 rounded-xl border border-gray-200 p-4 md:grid-cols-2 xl:grid-cols-[1fr_1fr_1.4fr_auto_auto] dark:border-gray-800">
          <label className="text-xs font-medium text-gray-500">规则键<input aria-label={`规则键 ${index + 1}`} className={`mt-1 ${fieldClass}`} value={row.key} onChange={(event) => update(row.id, "key", event.target.value)} /></label>
          <label className="text-xs font-medium text-gray-500">资料类型<input aria-label={`资料类型 ${index + 1}`} className={`mt-1 ${fieldClass}`} value={row.documentType} onChange={(event) => update(row.id, "documentType", event.target.value)} /></label>
          <label className="text-xs font-medium text-gray-500">允许 MIME（逗号分隔）<input aria-label={`允许 MIME ${index + 1}`} className={`mt-1 ${fieldClass}`} value={row.mediaTypes} onChange={(event) => update(row.id, "mediaTypes", event.target.value)} /></label>
          <label className="text-xs font-medium text-gray-500">严重级别<select aria-label={`严重级别 ${index + 1}`} className={`mt-1 ${fieldClass}`} value={row.severity} onChange={(event) => update(row.id, "severity", event.target.value)}><option>LOW</option><option>MEDIUM</option><option>HIGH</option><option>CRITICAL</option></select></label>
          <div className="flex items-end gap-2 pb-1"><label className="flex h-10 items-center gap-2 text-sm"><input aria-label={`必需 ${index + 1}`} type="checkbox" checked={row.required} onChange={(event) => update(row.id, "required", event.target.checked)} />必需</label><Button type="button" variant="ghost" size="icon" aria-label={`删除要求 ${index + 1}`} disabled={requirements.length === 1} onClick={() => setRequirements((current) => current.filter((item) => item.id !== row.id))}><Trash2 /></Button></div>
        </section>)}
      </CardContent></Card>
      <div className="flex flex-wrap items-center justify-end gap-3">{formError ? <p role="alert" className="mr-auto text-sm text-error-600">{formError}</p> : null}{create.isError ? <p role="alert" className="mr-auto text-sm text-error-600">创建失败：{create.error.message}</p> : null}{published ? <p role="status" className="mr-auto text-sm text-success-600">策略版本 {published.version} 已发布（{published.contentHash.slice(0, 12)}）</p> : null}<Button type="submit" loading={create.isPending} disabled={Boolean(published)}><CheckCircle2 />校验并发布</Button></div>
    </form>
  </div>;
}
