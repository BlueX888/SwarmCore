import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import * as Dialog from "@radix-ui/react-dialog";
import { useNavigate, useParams, useSearchParams } from "react-router";
import {
  ArrowDown,
  ArrowUp,
  Check,
  ChevronDown,
  CircleAlert,
  Download,
  Eye,
  FileText,
  ListFilter,
  LoaderCircle,
  MoreHorizontal,
  RefreshCw,
  Search,
  Settings2,
  Tag,
  Upload,
  X,
} from "lucide-react";
import { api } from "@/api/client";
import type { DocumentSnapshot } from "@/api/types";
import {
  DocumentBindingEditor,
  DocumentClassificationReview,
  DocumentExtractionReviewForm,
  DocumentProcessingStatus,
  DocumentUploadPanel,
} from "@/components/documents/document-intake";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { BUSINESS_WORKS } from "@/lib/business-works";
import { useWorkspaceScope } from "@/lib/demo-scope";

const fieldClass = "h-10 w-full rounded-lg border border-gray-300 bg-white px-3 text-sm outline-none focus:border-brand-500 dark:border-gray-700 dark:bg-gray-900";

const categories = [
  { value: "CONTRACT", label: "合同文件" },
  { value: "SOURCE_DOCUMENT", label: "源文件" },
  { value: "MASTER_CONTRACT", label: "主合同" },
  { value: "AWARD_NOTICE", label: "中标公告" },
  { value: "WINNING_BID", label: "中标响应" },
  { value: "TENDER_DOCUMENT", label: "招标文件" },
  { value: "PROCUREMENT_CHANGE", label: "采购变更" },
  { value: "SUPPLIER_PERFORMANCE", label: "供应商绩效" },
  { value: "PERFORMANCE", label: "履约资料" },
  { value: "INVOICE", label: "发票资料" },
  { value: "DEVIATION", label: "偏差资料" },
  { value: "SUPPLIER", label: "供应商资料" },
  { value: "REPORT", label: "报告与成果" },
  { value: "OTHER", label: "其他资料" },
];

const statuses: Record<string, { label: string; tone: string }> = {
  UPLOADING: { label: "上传中", tone: "bg-blue-50 text-blue-700 dark:bg-blue-500/10 dark:text-blue-300" },
  PROCESSING: { label: "解析中", tone: "bg-blue-50 text-blue-700 dark:bg-blue-500/10 dark:text-blue-300" },
  REVIEW_REQUIRED: { label: "待确认", tone: "bg-warning-50 text-warning-700 dark:bg-warning-500/10 dark:text-warning-300" },
  AVAILABLE: { label: "可用", tone: "bg-success-50 text-success-700 dark:bg-success-500/10 dark:text-success-300" },
  FAILED: { label: "解析失败", tone: "bg-error-50 text-error-700 dark:bg-error-500/10 dark:text-error-300" },
  DISABLED: { label: "已停用", tone: "bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-300" },
  EXPIRED: { label: "已过期", tone: "bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-300" },
};

const views = [
  { value: "all", label: "全部资料" },
  { value: "mine", label: "我上传的" },
  { value: "recent", label: "最近更新" },
  { value: "unlinked", label: "未关联业务" },
  { value: "failed", label: "处理异常" },
] as const;

type ViewKey = (typeof views)[number]["value"];
type SortKey = "name" | "size" | "updatedAt";
type ColumnKey = "version" | "status" | "binding" | "usage" | "updatedAt";

const defaultColumns: Record<ColumnKey, boolean> = {
  version: true,
  status: true,
  binding: true,
  usage: true,
  updatedAt: true,
};

export function DocumentLibraryPage() {
  const { documentId } = useParams();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const { tenantId, projectId, workspacePath } = useWorkspaceScope();
  const queryClient = useQueryClient();
  const [showUpload, setShowUpload] = useState(false);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [status, setStatus] = useState("");
  const [updatedWithin, setUpdatedWithin] = useState("");
  const requestedView = searchParams.get("view");
  const view: ViewKey = views.some((item) => item.value === requestedView)
    ? requestedView as ViewKey
    : "all";
  const setView = (next: ViewKey) => {
    const params = new URLSearchParams(searchParams);
    if (next === "all") params.delete("view");
    else params.set("view", next);
    setSearchParams(params, { replace: true });
  };
  const [showMoreFilters, setShowMoreFilters] = useState(false);
  const [showColumnSettings, setShowColumnSettings] = useState(false);
  const [association, setAssociation] = useState<"" | "linked" | "unlinked">("");
  const [format, setFormat] = useState("");
  const [tagFilter, setTagFilter] = useState("");
  const [versionFilter, setVersionFilter] = useState("");
  const [columns, setColumns] = useState(defaultColumns);
  const [sort, setSort] = useState<{ key: SortKey; direction: "asc" | "desc" }>({ key: "updatedAt", direction: "desc" });
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [batchMessage, setBatchMessage] = useState<string | null>(null);
  const [uploadSummary, setUploadSummary] = useState<DocumentSnapshot[] | null>(null);

  const documents = useQuery({
    queryKey: ["documents", tenantId, projectId],
    queryFn: () => api.listDocuments(tenantId, projectId),
  });
  const selectedDocument = useQuery({
    queryKey: ["document", tenantId, projectId, documentId],
    queryFn: () => api.getDocument(tenantId, projectId, documentId ?? ""),
    enabled: Boolean(documentId),
  });
  const resumeUpload = useMutation({
    mutationFn: (id: string) => api.resumeDocumentUpload(tenantId, projectId, id),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["documents", tenantId, projectId] });
    },
  });
  const batchReprocess = useMutation({
    mutationFn: (ids: string[]) => Promise.all(ids.map((id) => api.reprocessDocument(tenantId, projectId, id))),
    onSuccess: async (_, ids) => {
      setSelectedIds((current) => current.filter((id) => !ids.includes(id)));
      setBatchMessage(`已提交 ${ids.length} 份资料重新解析。`);
      await queryClient.invalidateQueries({ queryKey: ["documents", tenantId, projectId] });
    },
  });

  const allItems = useMemo(() => documents.data?.items ?? [], [documents.data?.items]);
  const filteredItems = useMemo(() => {
    const needle = search.trim().toLowerCase();
    const tagNeedle = tagFilter.trim().toLowerCase();
    const now = Date.now();
    const days = updatedWithin ? Number(updatedWithin) : 0;
    return allItems.filter((item) => {
      const workLabels = item.businessWorkKeys.map((key) => BUSINESS_WORKS.find((work) => work.key === key)?.shortName ?? key).join(" ");
      const searchable = `${item.name} ${item.current?.filename ?? ""} ${item.tags.join(" ")} ${workLabels} ${item.businessObjectIds.join(" ")} ${categoryLabel(item.category)}`.toLowerCase();
      const matchesSearch = !needle || searchable.includes(needle);
      const matchesUpdated = !days || now - new Date(item.updatedAt).getTime() <= days * 24 * 60 * 60 * 1000;
      const matchesView = view === "all"
        || (view === "recent" && now - new Date(item.updatedAt).getTime() <= 30 * 24 * 60 * 60 * 1000)
        || (view === "unlinked" && !item.businessObjectIds.length)
        || (view === "failed" && ["FAILED", "REVIEW_REQUIRED"].includes(item.status))
        || view === "mine";
      const matchesFormat = !format || item.current?.filename.toLowerCase().endsWith(format);
      const matchesTag = !tagNeedle || item.tags.some((tag) => tag.toLowerCase().includes(tagNeedle));
      const matchesVersion = !versionFilter || String(item.currentVersion) === versionFilter;
      const matchesAssociation = !association
        || (association === "linked" && item.businessObjectIds.length > 0)
        || (association === "unlinked" && item.businessObjectIds.length === 0);
      return matchesSearch
        && matchesUpdated
        && matchesView
        && matchesFormat
        && matchesTag
        && matchesVersion
        && matchesAssociation
        && (!category || item.category === category)
        && (!status || item.status === status);
    });
  }, [allItems, association, category, format, search, status, tagFilter, updatedWithin, versionFilter, view]);

  const items = useMemo(() => [...filteredItems].sort((left, right) => {
    const leftValue = sort.key === "name" ? left.name : sort.key === "size" ? left.current?.sizeBytes ?? 0 : new Date(left.updatedAt).getTime();
    const rightValue = sort.key === "name" ? right.name : sort.key === "size" ? right.current?.sizeBytes ?? 0 : new Date(right.updatedAt).getTime();
    const comparison = typeof leftValue === "string" ? leftValue.localeCompare(rightValue as string, "zh-CN") : leftValue - (rightValue as number);
    return sort.direction === "asc" ? comparison : -comparison;
  }), [filteredItems, sort]);

  const stats = useMemo(() => ({
    all: allItems.length,
    available: allItems.filter((item) => item.status === "AVAILABLE").length,
    processing: allItems.filter((item) => ["UPLOADING", "PROCESSING"].includes(item.status)).length,
    failed: allItems.filter((item) => ["FAILED", "REVIEW_REQUIRED"].includes(item.status)).length,
    unlinked: allItems.filter((item) => !item.businessObjectIds.length).length,
  }), [allItems]);

  const visibleSelectedIds = selectedIds.filter((id) => items.some((item) => item.documentId === id));
  const allVisibleSelected = items.length > 0 && items.every((item) => visibleSelectedIds.includes(item.documentId));
  const activeFilter = Boolean(search || category || status || updatedWithin || association || format || tagFilter || versionFilter || view !== "all");
  const moreFilterCount = [category, status, updatedWithin, association, format, tagFilter, versionFilter].filter(Boolean).length;
  const selectDocument = (item: DocumentSnapshot) => {
    void navigate(`${workspacePath}/documents/${encodeURIComponent(item.documentId)}`);
  };
  const clearFilters = () => {
    setSearch("");
    setCategory("");
    setStatus("");
    setUpdatedWithin("");
    setAssociation("");
    setFormat("");
    setTagFilter("");
    setVersionFilter("");
    setView("all");
  };
  const toggleSort = (key: SortKey) => {
    setSort((current) => current.key === key
      ? { key, direction: current.direction === "asc" ? "desc" : "asc" }
      : { key, direction: key === "updatedAt" ? "desc" : "asc" });
  };
  const toggleSelected = (id: string) => {
    setSelectedIds((current) => current.includes(id) ? current.filter((value) => value !== id) : [...current, id]);
  };
  const toggleAll = () => {
    setSelectedIds((current) => allVisibleSelected
      ? current.filter((id) => !items.some((item) => item.documentId === id))
      : Array.from(new Set([...current, ...items.map((item) => item.documentId)])));
  };

  return <div className="min-w-0 space-y-4">
    <h1 className="sr-only">业务资料库</h1>
    <div className="flex flex-wrap items-center justify-between gap-3">
      <p className="text-sm text-gray-600 dark:text-gray-300">共 {stats.all} 份资料 <span className="mx-1 text-gray-300">｜</span> {stats.processing} 份处理中 <span className="mx-1 text-gray-300">｜</span> {stats.failed} 份异常</p>
      <div className="flex items-center gap-2">
        <Button variant="ghost" size="icon" aria-label="刷新资料库" onClick={() => void documents.refetch()} loading={documents.isFetching}><RefreshCw /></Button>
        <Button onClick={() => { setUploadSummary(null); setShowUpload(true); }}><Upload />上传文件</Button>
      </div>
    </div>

    <OverviewStats stats={stats} onSelect={(next) => {
      if (next === "all") { clearFilters(); return; }
      setView("all");
      setStatus(next === "available" ? "AVAILABLE" : next === "processing" ? "PROCESSING" : next === "failed" ? "FAILED" : "");
      if (next === "unlinked") setAssociation("unlinked");
    }} />

    {uploadSummary ? <UploadSuccessNotice documents={uploadSummary} onDismiss={() => setUploadSummary(null)} onContinue={() => { setUploadSummary(null); setShowUpload(true); }} onBind={() => { selectDocument(uploadSummary[0]); setUploadSummary(null); }} /> : null}
    {showUpload ? <UploadDrawer
      tenantId={tenantId}
      projectId={projectId}
      onClose={() => setShowUpload(false)}
      onCompleted={async (uploaded) => {
        setUploadSummary(uploaded);
        setShowUpload(false);
        await queryClient.invalidateQueries({ queryKey: ["documents", tenantId, projectId] });
      }}
    /> : null}

    <Card>
      <CardContent className="space-y-3 p-4 md:p-5">
        <div className="grid gap-2 xl:grid-cols-[minmax(18rem,1fr)_11rem_10rem_10rem_auto_auto]">
          <label className="relative"><span className="sr-only">搜索文件</span><Search className="pointer-events-none absolute left-3 top-2.5 size-5 text-gray-400" /><input aria-label="搜索文件" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="搜索文件名、原始文件名、标签或业务名称" className={`${fieldClass} pl-10`} /></label>
          <select aria-label="资料类型" value={category} onChange={(event) => setCategory(event.target.value)} className={fieldClass}><option value="">资料类型</option>{categories.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}</select>
          <select aria-label="状态" value={status} onChange={(event) => setStatus(event.target.value)} className={fieldClass}><option value="">状态</option>{Object.entries(statuses).map(([value, item]) => <option key={value} value={value}>{item.label}</option>)}</select>
          <select aria-label="更新时间" value={updatedWithin} onChange={(event) => setUpdatedWithin(event.target.value)} className={fieldClass}><option value="">更新时间</option><option value="1">今天</option><option value="7">近 7 天</option><option value="30">近 30 天</option><option value="90">近 90 天</option></select>
          <Button variant={showMoreFilters ? "outline" : "ghost"} size="sm" onClick={() => setShowMoreFilters((current) => !current)}><ListFilter />更多筛选{moreFilterCount ? <span className="grid size-5 place-items-center rounded-full bg-brand-500 text-[11px] text-white">{moreFilterCount}</span> : null}</Button>
          <Button variant={showColumnSettings ? "outline" : "ghost"} size="sm" onClick={() => setShowColumnSettings((current) => !current)}><Settings2 />列设置</Button>
        </div>

        {showMoreFilters ? <div className="grid gap-2 rounded-xl border border-gray-200 bg-gray-50/70 p-3 sm:grid-cols-2 lg:grid-cols-4 dark:border-gray-800 dark:bg-gray-900/60">
          <label className="text-xs text-gray-500">是否关联业务<select aria-label="是否关联业务" value={association} onChange={(event) => setAssociation(event.target.value as "" | "linked" | "unlinked")} className={`${fieldClass} mt-1`}><option value="">全部</option><option value="linked">已关联</option><option value="unlinked">未关联</option></select></label>
          <label className="text-xs text-gray-500">文件格式<select aria-label="文件格式" value={format} onChange={(event) => setFormat(event.target.value)} className={`${fieldClass} mt-1`}><option value="">全部格式</option>{[".pdf", ".docx", ".xlsx", ".txt", ".csv", ".json"].map((value) => <option key={value} value={value}>{value.toUpperCase()}</option>)}</select></label>
          <label className="text-xs text-gray-500">标签<input aria-label="按标签筛选" value={tagFilter} onChange={(event) => setTagFilter(event.target.value)} placeholder="输入标签" className={`${fieldClass} mt-1`} /></label>
          <label className="text-xs text-gray-500">版本<input aria-label="按版本筛选" value={versionFilter} onChange={(event) => setVersionFilter(event.target.value.replace(/\D/g, ""))} placeholder="例如 2" className={`${fieldClass} mt-1`} inputMode="numeric" /></label>
        </div> : null}

        {showColumnSettings ? <div className="flex flex-wrap items-center gap-3 rounded-xl border border-gray-200 bg-gray-50/70 p-3 text-sm dark:border-gray-800 dark:bg-gray-900/60">
          <span className="text-xs text-gray-500">显示列</span>
          {(Object.keys(defaultColumns) as ColumnKey[]).map((key) => <label key={key} className="inline-flex items-center gap-1.5"><input type="checkbox" checked={columns[key]} onChange={(event) => setColumns((current) => ({ ...current, [key]: event.target.checked }))} />{columnLabel(key)}</label>)}
        </div> : null}

        {activeFilter ? <div className="flex flex-wrap items-center gap-2 text-xs"><span className="font-medium text-gray-500">已选：</span>{search ? <FilterChip label={`搜索：${search}`} onRemove={() => setSearch("")} /> : null}{category ? <FilterChip label={categoryLabel(category)} onRemove={() => setCategory("")} /> : null}{status ? <FilterChip label={statuses[status]?.label ?? status} onRemove={() => setStatus("")} /> : null}{updatedWithin ? <FilterChip label={`近${updatedWithin}天`} onRemove={() => setUpdatedWithin("")} /> : null}{association ? <FilterChip label={association === "linked" ? "已关联业务" : "未关联业务"} onRemove={() => setAssociation("")} /> : null}{format ? <FilterChip label={format.toUpperCase()} onRemove={() => setFormat("")} /> : null}{tagFilter ? <FilterChip label={`标签：${tagFilter}`} onRemove={() => setTagFilter("")} /> : null}{versionFilter ? <FilterChip label={`v${versionFilter}`} onRemove={() => setVersionFilter("")} /> : null}{view !== "all" ? <FilterChip label={views.find((item) => item.value === view)?.label ?? view} onRemove={() => setView("all")} /> : null}<button type="button" className="ml-1 font-medium text-brand-600 hover:text-brand-700" onClick={clearFilters}>清空</button></div> : null}

        <nav aria-label="资料库快捷视图" className="flex gap-1 overflow-x-auto border-b border-gray-100 pb-1 dark:border-gray-800">{views.map((item) => <button key={item.value} type="button" aria-current={view === item.value ? "page" : undefined} onClick={() => setView(item.value)} className={`shrink-0 rounded-lg px-3 py-2 text-sm font-medium ${view === item.value ? "bg-brand-50 text-brand-700 dark:bg-brand-500/10 dark:text-brand-300" : "text-gray-500 hover:bg-gray-50 hover:text-gray-900 dark:hover:bg-white/5 dark:hover:text-white"}`}>{item.label}</button>)}</nav>

        {visibleSelectedIds.length ? <BulkActionBar count={visibleSelectedIds.length} busy={batchReprocess.isPending} message={batchMessage} onReprocess={() => batchReprocess.mutate(visibleSelectedIds)} onUnsupported={(label) => setBatchMessage(`批量${label}需要后端批量接口；当前可打开单项预览完成。`)} onClear={() => setSelectedIds([])} /> : null}
        {documents.isPending ? <Skeleton className="h-72" /> : null}
        {documents.isError ? <div role="alert" className="rounded-xl border border-error-200 bg-error-50 p-6 text-center dark:border-error-500/20 dark:bg-error-500/10"><CircleAlert className="mx-auto size-7 text-error-600" /><p className="mt-2 font-medium text-error-700">业务资料库加载失败</p><p className="mt-1 text-sm text-error-600">{documents.error.message}</p></div> : null}
        {resumeUpload.isError ? <p role="alert" className="text-sm text-error-600">{resumeUpload.error.message}</p> : null}
        {batchReprocess.isError ? <p role="alert" className="text-sm text-error-600">批量重新解析失败：{batchReprocess.error.message}</p> : null}
        {documents.data && !items.length ? <EmptyDocuments filtered={activeFilter} onUpload={() => setShowUpload(true)} /> : null}
        {items.length ? <DocumentTable
          items={items}
          columns={columns}
          selectedIds={visibleSelectedIds}
          allSelected={allVisibleSelected}
          sort={sort}
          onToggleAll={toggleAll}
          onToggleSelected={toggleSelected}
          onSort={toggleSort}
          onSelect={selectDocument}
          onResume={(item) => resumeUpload.mutate(item.documentId)}
          onReprocess={(item) => batchReprocess.mutate([item.documentId])}
          resumingId={resumeUpload.isPending ? resumeUpload.variables ?? null : null}
        /> : null}
      </CardContent>
    </Card>

    {selectedDocument.isError ? <p role="alert" className="text-sm text-error-600">文件详情加载失败：{selectedDocument.error.message}</p> : null}
    {selectedDocument.data ? <DocumentDetailsDialog tenantId={tenantId} projectId={projectId} document={selectedDocument.data} onClose={() => { void navigate(`${workspacePath}/documents`); }} onChanged={async () => { await queryClient.invalidateQueries({ queryKey: ["documents", tenantId, projectId] }); await selectedDocument.refetch(); }} /> : null}
  </div>;
}

function OverviewStats({ stats, onSelect }: { stats: { all: number; available: number; processing: number; failed: number; unlinked: number }; onSelect: (value: "all" | "available" | "processing" | "failed" | "unlinked") => void }) {
  const values = [{ key: "all", label: "全部", value: stats.all }, { key: "available", label: "可用", value: stats.available }, { key: "processing", label: "处理中", value: stats.processing }, { key: "failed", label: "异常", value: stats.failed }, { key: "unlinked", label: "未关联", value: stats.unlinked }] as const;
  return <div aria-label="资料库概览" className="flex flex-wrap items-center gap-x-6 gap-y-2 border-y border-gray-200/80 py-3 text-sm dark:border-gray-800">{values.map((item) => <button type="button" key={item.key} onClick={() => onSelect(item.key)} className="group text-left"><span className="text-gray-500 group-hover:text-brand-600">{item.label}</span><span className="ml-1.5 text-base font-semibold text-gray-900 group-hover:text-brand-600 dark:text-white">{item.value}</span></button>)}</div>;
}

function BulkActionBar({ count, busy, message, onReprocess, onUnsupported, onClear }: { count: number; busy: boolean; message: string | null; onReprocess: () => void; onUnsupported: (label: string) => void; onClear: () => void }) {
  return <div className="flex flex-wrap items-center gap-2 rounded-xl border border-brand-200 bg-brand-50/70 px-3 py-2 text-sm dark:border-brand-500/20 dark:bg-brand-500/10"><span className="font-semibold text-brand-800 dark:text-brand-200">已选择 {count} 项</span><span className="hidden text-brand-700/70 sm:inline">·</span><Button variant="ghost" size="sm" onClick={() => onUnsupported("关联业务")}>关联业务</Button><Button variant="ghost" size="sm" onClick={() => onUnsupported("添加标签")}>添加标签</Button><Button variant="ghost" size="sm" loading={busy} onClick={onReprocess}>重新解析</Button><Button variant="ghost" size="sm" onClick={() => onUnsupported("停用")}>停用</Button><Button variant="ghost" size="sm" onClick={() => onUnsupported("删除")}>删除</Button>{message ? <span role="status" className="basis-full text-xs text-brand-700 dark:text-brand-300">{message}</span> : null}<button type="button" className="ml-auto text-xs text-brand-700 hover:underline" onClick={onClear}>取消选择</button></div>;
}

function FilterChip({ label, onRemove }: { label: string; onRemove: () => void }) {
  return <span className="inline-flex items-center gap-1 rounded-full bg-gray-100 px-2.5 py-1 text-gray-600 dark:bg-gray-800 dark:text-gray-300">{label}<button type="button" aria-label={`移除筛选：${label}`} onClick={onRemove}><X className="size-3.5" /></button></span>;
}

function DocumentTable({ items, columns, selectedIds, allSelected, sort, onToggleAll, onToggleSelected, onSort, onSelect, onResume, onReprocess, resumingId }: { items: DocumentSnapshot[]; columns: Record<ColumnKey, boolean>; selectedIds: string[]; allSelected: boolean; sort: { key: SortKey; direction: "asc" | "desc" }; onToggleAll: () => void; onToggleSelected: (id: string) => void; onSort: (key: SortKey) => void; onSelect: (item: DocumentSnapshot) => void; onResume: (item: DocumentSnapshot) => void; onReprocess: (item: DocumentSnapshot) => void; resumingId: string | null }) {
  return <div className="max-h-[min(62vh,720px)] overflow-auto rounded-xl border border-gray-100 dark:border-gray-800"><table className="w-full min-w-[980px] text-left text-sm"><thead className="sticky top-0 z-10 bg-gray-50/95 text-xs text-gray-500 backdrop-blur dark:bg-gray-900/95"><tr className="border-b border-gray-200 dark:border-gray-800"><th className="w-11 px-3 py-3"><input aria-label="选择全部资料" type="checkbox" checked={allSelected} onChange={onToggleAll} /></th><th className="min-w-[310px] px-3 py-3 font-medium"><SortableHeader label="文件名称" sortKey="name" sort={sort} onSort={onSort} /></th><th className="w-36 px-3 py-3 font-medium"><SortableHeader label="资料类型／大小" sortKey="size" sort={sort} onSort={onSort} /></th>{columns.version ? <th className="w-20 px-3 py-3 font-medium">版本</th> : null}{columns.status ? <th className="w-28 px-3 py-3 font-medium">处理状态</th> : null}{columns.binding ? <th className="w-28 px-3 py-3 font-medium">关联业务</th> : null}{columns.usage ? <th className="w-32 px-3 py-3 font-medium">使用情况</th> : null}{columns.updatedAt ? <th className="w-36 px-3 py-3 font-medium"><SortableHeader label="更新时间" sortKey="updatedAt" sort={sort} onSort={onSort} /></th> : null}<th className="sticky right-0 w-28 bg-inherit px-3 py-3 font-medium">操作</th></tr></thead><tbody>{items.map((item) => <DocumentRow key={item.documentId} item={item} columns={columns} selected={selectedIds.includes(item.documentId)} onToggle={() => onToggleSelected(item.documentId)} onSelect={() => onSelect(item)} onResume={() => onResume(item)} onReprocess={() => onReprocess(item)} resuming={resumingId === item.documentId} />)}</tbody></table></div>;
}

function DocumentRow({ item, columns, selected, onToggle, onSelect, onResume, onReprocess, resuming }: { item: DocumentSnapshot; columns: Record<ColumnKey, boolean>; selected: boolean; onToggle: () => void; onSelect: () => void; onResume: () => void; onReprocess: () => void; resuming: boolean }) {
  const [menuOpen, setMenuOpen] = useState(false);
  const stop = (event: React.MouseEvent) => event.stopPropagation();
  return <tr className={`group border-b border-gray-100 last:border-0 dark:border-gray-800/70 ${selected ? "bg-brand-50/40 dark:bg-brand-500/5" : "hover:bg-gray-50/70 dark:hover:bg-white/[0.025]"}`} onClick={onSelect}><td className="px-3 py-3" onClick={stop}><input aria-label={`选择资料：${item.name}`} type="checkbox" checked={selected} onChange={onToggle} /></td><td className="px-3 py-3"><button type="button" className="flex min-w-0 items-center gap-2 text-left" onClick={(event) => { stop(event); onSelect(); }}><span className="grid size-9 shrink-0 place-items-center rounded-lg bg-brand-50 text-brand-600 dark:bg-brand-500/10"><FileText className="size-4" /></span><span className="min-w-0"><span className="block max-w-[380px] truncate font-medium text-gray-900 hover:text-brand-600 dark:text-white" title={item.name}>{item.name}</span><span className="block max-w-[380px] truncate text-xs text-gray-500" title={item.current?.filename ?? ""}>{item.current?.filename ?? "文件已接收，等待完成登记"}</span></span></button></td><td className="px-3 py-3 text-gray-600 dark:text-gray-300"><span>{categoryLabel(item.category)}</span><span className="block text-xs text-gray-500">{item.current ? formatBytes(item.current.sizeBytes) : "—"}</span></td>{columns.version ? <td className="px-3 py-3">v{item.currentVersion || "—"}</td> : null}{columns.status ? <td className="px-3 py-3"><StatusBadge status={item.status} />{item.status === "FAILED" ? <div className="mt-1 flex gap-2 text-[11px]"><button type="button" className="text-error-700 hover:underline" onClick={(event) => { stop(event); onSelect(); }}>查看原因</button><button type="button" className="text-brand-600 hover:underline" onClick={(event) => { stop(event); onReprocess(); }}>重新解析</button></div> : null}</td> : null}{columns.binding ? <td className="px-3 py-3 text-xs text-gray-500">{item.businessObjectIds.length ? `${item.businessObjectIds.length} 项关联` : "未关联"}</td> : null}{columns.usage ? <td className="px-3 py-3 text-xs text-gray-500">{item.businessWorkKeys.length ? `${item.businessWorkKeys.length} 个工作流` : "暂未使用"}</td> : null}{columns.updatedAt ? <td className="px-3 py-3 text-xs text-gray-500">{formatDate(item.updatedAt)}</td> : null}<td className="sticky right-0 bg-white/95 px-3 py-3 dark:bg-gray-900/95" onClick={stop}><div className="flex items-center justify-end gap-1"><Button variant="ghost" size="sm" aria-label={`预览：${item.name}`} onClick={onSelect}><Eye />预览</Button><div className="relative"><Button variant="ghost" size="icon" aria-label={`更多操作：${item.name}`} onClick={() => setMenuOpen((current) => !current)}><MoreHorizontal /></Button>{menuOpen ? <div role="menu" className="absolute right-0 top-11 z-20 w-36 rounded-xl border border-gray-200 bg-white p-1 text-sm shadow-theme-lg dark:border-gray-700 dark:bg-gray-900"><MenuButton label="查看详情" onClick={onSelect} /><MenuButton label="下载" onClick={onSelect} /><MenuButton label="上传新版本" onClick={onSelect} />{item.status === "UPLOADING" ? <MenuButton label={resuming ? "继续中" : "继续完成"} onClick={onResume} disabled={resuming} /> : null}<MenuButton label="关联业务" onClick={onSelect} /><MenuButton label="添加标签" onClick={onSelect} /><MenuButton label="停用" onClick={onSelect} /><MenuButton label="删除" destructive onClick={onSelect} /></div> : null}</div></div></td></tr>;
}

function MenuButton({ label, onClick, destructive = false, disabled = false }: { label: string; onClick: () => void; destructive?: boolean; disabled?: boolean }) {
  return <button type="button" role="menuitem" disabled={disabled} className={`block w-full rounded-lg px-3 py-2 text-left text-xs hover:bg-gray-50 dark:hover:bg-white/5 ${destructive ? "text-error-600" : "text-gray-700 dark:text-gray-300"}`} onClick={onClick}>{label}</button>;
}

function SortableHeader({ label, sortKey, sort, onSort }: { label: string; sortKey: SortKey; sort: { key: SortKey; direction: "asc" | "desc" }; onSort: (key: SortKey) => void }) {
  const active = sort.key === sortKey;
  return <button type="button" className="inline-flex items-center gap-1 font-medium hover:text-gray-900 dark:hover:text-white" onClick={() => onSort(sortKey)}>{label}{active ? sort.direction === "asc" ? <ArrowUp className="size-3.5" /> : <ArrowDown className="size-3.5" /> : <ChevronDown className="size-3.5 opacity-30" />}</button>;
}

function UploadDrawer({ tenantId, projectId, onClose, onCompleted }: { tenantId: string; projectId: string; onClose: () => void; onCompleted: (documents: DocumentSnapshot[]) => Promise<void> }) {
  return <Dialog.Root open onOpenChange={(open) => { if (!open) onClose(); }}><Dialog.Portal><Dialog.Overlay className="fixed inset-0 z-40 bg-gray-950/50 backdrop-blur-[2px]" /><Dialog.Content className="fixed inset-y-0 right-0 z-50 w-[min(620px,100vw)] overflow-y-auto border-l border-gray-200 bg-white p-5 shadow-theme-xl outline-none dark:border-gray-800 dark:bg-gray-900"><Dialog.Title className="sr-only">上传文件</Dialog.Title><Dialog.Description className="sr-only">上传并解析业务资料</Dialog.Description><DocumentUploadPanel tenantId={tenantId} projectId={projectId} context={{ businessWorkKeys: [], category: "CONTRACT" }} onClose={onClose} onCompleted={onCompleted} /></Dialog.Content></Dialog.Portal></Dialog.Root>;
}

function UploadSuccessNotice({ documents, onDismiss, onContinue, onBind }: { documents: DocumentSnapshot[]; onDismiss: () => void; onContinue: () => void; onBind: () => void }) {
  const first = documents[0];
  if (!first) return null;
  return <div className="flex flex-wrap items-start gap-3 rounded-xl border border-success-200 bg-success-50/70 p-4 dark:border-success-500/20 dark:bg-success-500/10"><Check className="mt-0.5 size-5 shrink-0 text-success-600" /><div className="min-w-0 flex-1"><p className="font-medium text-success-800 dark:text-success-200">文件上传成功</p><p className="mt-1 text-sm text-success-700 dark:text-success-300">已识别类型：{categoryLabel(first.category)} <span className="mx-1">·</span> 建议标签：{first.tags.length ? first.tags.join("、") : "待补充"}</p><p className="mt-1 text-xs text-success-700/80 dark:text-success-300/80">{first.businessObjectIds.length ? `已关联 ${first.businessObjectIds.length} 个业务对象` : "暂未关联业务"}</p><div className="mt-3 flex flex-wrap gap-2"><Button size="sm" onClick={onBind}>关联业务</Button><Button size="sm" variant="outline" onClick={onContinue}>继续上传</Button><Button size="sm" variant="ghost" onClick={onDismiss}>完成</Button></div></div></div>;
}

function DocumentDetailsDialog({ tenantId, projectId, document, onClose, onChanged }: { tenantId: string; projectId: string; document: DocumentSnapshot; onClose: () => void; onChanged: () => Promise<void> }) {
  const download = useMutation({ mutationFn: async () => { const result = await api.downloadDocumentVersion(tenantId, projectId, document.documentId, document.currentVersion); const url = URL.createObjectURL(result.content); const link = globalThis.document.createElement("a"); link.href = url; link.download = result.filename; link.click(); URL.revokeObjectURL(url); } });
  const reprocess = useMutation({ mutationFn: () => api.reprocessDocument(tenantId, projectId, document.documentId), onSuccess: onChanged });
  return <Dialog.Root open onOpenChange={(open) => { if (!open) onClose(); }}><Dialog.Portal><Dialog.Overlay className="fixed inset-0 z-40 bg-gray-950/50 backdrop-blur-[2px]" /><Dialog.Content className="fixed inset-y-0 right-0 z-50 flex h-full w-[min(720px,100vw)] max-w-full flex-col border-l border-gray-200 bg-white shadow-theme-xl outline-none dark:border-gray-800 dark:bg-gray-900"><div className="flex shrink-0 items-start justify-between gap-4 border-b border-gray-100 p-5 dark:border-gray-800"><div className="min-w-0"><p className="text-xs text-brand-500">文件预览与资料治理</p><Dialog.Title asChild><h2 className="mt-1 truncate font-semibold text-gray-900 dark:text-white">{document.name}</h2></Dialog.Title><Dialog.Description className="mt-1 text-sm text-gray-500">查看资料内容、处理状态、版本与关联关系。</Dialog.Description></div><div className="flex shrink-0 items-center gap-2"><StatusBadge status={document.status} /><Dialog.Close asChild><Button variant="ghost" size="icon" aria-label="关闭文件详情"><X /></Button></Dialog.Close></div></div><div className="min-h-0 flex-1 space-y-4 overflow-y-auto p-5"><section className="rounded-xl border border-gray-200 bg-gray-50/70 p-4 dark:border-gray-800 dark:bg-gray-900/60"><div className="flex items-center gap-3"><span className="grid size-11 place-items-center rounded-xl bg-brand-50 text-brand-600 dark:bg-brand-500/10"><FileText /></span><div className="min-w-0 flex-1"><p className="font-medium text-gray-900 dark:text-white">{document.current?.filename ?? "文件已接收，等待完成登记"}</p><p className="mt-1 text-xs text-gray-500">当前版本 v{document.currentVersion || 1} · {document.current ? formatBytes(document.current.sizeBytes) : "等待上传"}</p></div>{document.current ? <Button variant="outline" size="sm" loading={download.isPending} onClick={() => download.mutate()}><Download />下载</Button> : null}</div></section><section><h3 className="text-sm font-semibold text-gray-900 dark:text-white">基本信息</h3><div className="mt-2 grid gap-3 sm:grid-cols-2"><Detail label="资料类型" value={categoryLabel(document.category)} /><Detail label="技术类型" value={document.category} /><Detail label="文件大小" value={document.current ? formatBytes(document.current.sizeBytes) : "—"} /><Detail label="更新时间" value={formatDate(document.updatedAt)} /><Detail label="校验摘要" value={document.current ? document.current.sha256.slice(0, 16) : "—"} /><Detail label="版本数量" value={`${document.versions.length || document.currentVersion || 1} 个版本`} /></div></section><section><h3 className="text-sm font-semibold text-gray-900 dark:text-white">标签</h3><div className="mt-2 flex flex-wrap gap-2">{document.tags.length ? document.tags.map((tag) => <span key={tag} className="inline-flex items-center gap-1 rounded-full bg-gray-100 px-2.5 py-1 text-xs text-gray-600 dark:bg-gray-800 dark:text-gray-300"><Tag className="size-3.5" />{tag}</span>) : <span className="text-sm text-gray-500">暂未添加标签</span>}</div></section><section><h3 className="text-sm font-semibold text-gray-900 dark:text-white">关联业务与使用情况</h3><div className="mt-2 rounded-xl border border-gray-200 p-3 text-sm dark:border-gray-800"><p className="text-gray-600 dark:text-gray-300">{document.businessObjectIds.length ? `已关联 ${document.businessObjectIds.length} 个业务对象` : "暂未关联业务"}</p><div className="mt-2 flex flex-wrap gap-2">{document.businessWorkKeys.length ? document.businessWorkKeys.map((key) => <span key={key} className="rounded-full bg-brand-50 px-2.5 py-1 text-xs text-brand-700 dark:bg-brand-500/10 dark:text-brand-300">{BUSINESS_WORKS.find((work) => work.key === key)?.shortName ?? key}</span>) : <span className="text-xs text-gray-500">暂未被工作流使用</span>}</div></div></section><DocumentProcessingStatus tenantId={tenantId} projectId={projectId} documentId={document.documentId} /><DocumentClassificationReview tenantId={tenantId} projectId={projectId} documentId={document.documentId} onConfirmed={onChanged} /><DocumentExtractionReviewForm tenantId={tenantId} projectId={projectId} documentId={document.documentId} onConfirmed={onChanged} /><DocumentBindingEditor tenantId={tenantId} projectId={projectId} document={document} workOptions={BUSINESS_WORKS.map((work) => ({ key: work.key, label: work.shortName }))} onSaved={onChanged} /><section><div className="flex items-center justify-between"><h3 className="text-sm font-semibold text-gray-900 dark:text-white">版本记录</h3><Button variant="outline" size="sm" loading={reprocess.isPending} onClick={() => reprocess.mutate()}>重新解析</Button></div><div className="mt-2 space-y-2">{(document.versions.length ? document.versions : document.current ? [document.current] : []).map((version) => <div key={version.documentVersionId} className="flex items-center justify-between rounded-lg bg-gray-50 px-3 py-2 text-xs dark:bg-gray-900"><span>v{version.version} · {version.filename}</span><span className="text-gray-500">{formatDate(version.createdAt)}</span></div>)}</div></section><section><h3 className="text-sm font-semibold text-gray-900 dark:text-white">操作日志</h3><p className="mt-2 text-sm text-gray-500">暂无可展示的操作日志。</p></section>{download.isError ? <p role="alert" className="text-sm text-error-600">{download.error.message}</p> : null}{reprocess.isError ? <p role="alert" className="text-sm text-error-600">{reprocess.error.message}</p> : null}</div></Dialog.Content></Dialog.Portal></Dialog.Root>;
}

function EmptyDocuments({ filtered, onUpload }: { filtered: boolean; onUpload: () => void }) {
  return <div className="flex min-h-64 flex-col items-center justify-center rounded-xl border border-dashed border-gray-200 px-6 text-center dark:border-gray-800"><span className="grid size-12 place-items-center rounded-full bg-brand-50 text-brand-600 dark:bg-brand-500/10"><FileText /></span><h2 className="mt-3 font-medium text-gray-900 dark:text-white">{filtered ? "没有匹配的资料" : "还没有业务资料"}</h2><p className="mt-1 max-w-md text-sm text-gray-500">{filtered ? "调整搜索或筛选条件后再试。" : "上传文件并完成解析确认后，即可绑定到业务工作。"}</p>{!filtered ? <Button className="mt-4" onClick={onUpload}><Upload />上传第一个文件</Button> : null}</div>;
}

function StatusBadge({ status }: { status: string }) {
  const item = statuses[status] ?? { label: status, tone: "bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-300" };
  const Icon = status === "AVAILABLE" ? Check : status === "UPLOADING" || status === "PROCESSING" ? LoaderCircle : CircleAlert;
  return <span className={`inline-flex items-center gap-1 rounded-full px-2 py-1 text-xs font-medium ${item.tone}`}><Icon className={`size-3.5 ${status === "UPLOADING" || status === "PROCESSING" ? "animate-spin" : ""}`} />{item.label}</span>;
}

function Detail({ label, value }: { label: string; value: string }) {
  return <div className="rounded-lg bg-gray-50 p-3 dark:bg-gray-900"><p className="text-xs text-gray-500">{label}</p><p className="mt-1 truncate text-sm font-medium text-gray-800 dark:text-gray-200" title={value}>{value}</p></div>;
}

function categoryLabel(value: string) {
  return categories.find((item) => item.value === value)?.label ?? ({
    ACCEPTANCE: "验收资料",
    PAYMENT: "付款资料",
    RISK: "风险资料",
    PROCUREMENT: "招采资料",
    SUPPLEMENTAL_FACTS: "补充结构化事实",
    SCOPE_BASELINE: "范围基线",
    SCHEDULE_BASELINE: "进度基线",
    COST_BASELINE: "成本基线",
    PROGRESS_ACTUAL: "实际进度",
    DELIVERY_ACCEPTANCE: "交付与验收",
    COST_ACTUAL: "实际成本",
    APPROVED_CHANGE: "批准变更",
    CAUSE_EVIDENCE: "原因证据",
    RESPONSIBILITY_BASIS: "责任依据",
    INVOICE_ORIGINAL: "发票原件",
    CONTRACT_ORDER: "合同／订单",
    RECEIPT_ACCEPTANCE: "收货／验收",
    SUPPLIER_MASTER: "供应商主数据",
    OTHER: "其他资料",
  }[value] ?? value);
}

function columnLabel(value: ColumnKey) {
  return ({ version: "版本", status: "处理状态", binding: "关联业务", usage: "使用情况", updatedAt: "更新时间" })[value];
}

function formatBytes(value: number) {
  if (value < 1024) return `${value} B`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`;
  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDate(value: string) {
  return new Date(value).toLocaleString("zh-CN", { month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" });
}

export async function sha256File(file: File) {
  const digest = await crypto.subtle.digest("SHA-256", await file.arrayBuffer());
  return Array.from(new Uint8Array(digest), (value) => value.toString(16).padStart(2, "0")).join("");
}

export const ResourceCenterPage = DocumentLibraryPage;
