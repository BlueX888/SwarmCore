import * as React from "react";

import { AuditLogTable } from "../../../governance/audit-log-table";
import { auditLogListMock, type AuditLogRow } from "./mock-data";

export type AuditLogListPageProps = {
  rows?: AuditLogRow[];
  loading?: boolean;
  onExport?: () => void;
};

/**
 * S01-C08 审计日志列表 — table-list + 筛选工具栏组合页。
 * 消费方项目请替换为 ListSearchFilterToolbar（templates/ui/list-search-filter-toolbar.tsx）。
 * @see docs/spec/b-design-system-tailadmin-radix/prd/scenarios/S01-common.md#s01-c08
 */
export function AuditLogListPage({
  rows = auditLogListMock,
  loading = false,
  onExport,
}: AuditLogListPageProps) {
  const [query, setQuery] = React.useState("");

  const governanceRows = rows.map((row) => ({
    id: row.id,
    timestamp: row.time,
    actor: row.operator,
    object: row.resource,
    action: row.action,
    ip: row.ip,
    severity: row.result === "failure" ? ("critical" as const) : ("info" as const),
  }));

  const filtered = governanceRows.filter((row) => {
    if (!query.trim()) return true;
    const haystack = `${row.actor} ${row.object} ${row.action} ${row.ip}`.toLowerCase();
    return haystack.includes(query.trim().toLowerCase());
  });

  return (
    <div className="space-y-4" data-scenario-page="audit-log-list">
      <header className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-lg font-semibold text-gray-900 dark:text-white/90">审计日志</h1>
          <p className="text-sm text-gray-500">按时间、操作人、动作类型检索并导出操作记录。</p>
        </div>
      </header>
      <AuditLogTable
        rows={filtered}
        loading={loading}
        onExport={onExport}
        onSearch={setQuery}
      />
    </div>
  );
}

export default AuditLogListPage;
