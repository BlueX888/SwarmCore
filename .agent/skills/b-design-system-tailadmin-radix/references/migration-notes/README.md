# Migration Notes 注册表

> COMPAT-003 产物。已填写的真实 migration note 演练记录，对应 `migration-scenarios.md` 中的预防性场景。发生新的破坏性变更时，复制 `migration-note-template.md` 新增条目。

| ID | 场景 | 状态 | 路径 | Wrapper |
|---|---|---|---|---|
| MN-01 | MS-01 ThemeToggle 导出名 alias | active | `MN-01-theme-toggle-alias.md` | `templates/ui/deprecated/theme-toggle-alias.tsx` |
| MN-02 | MS-02 SearchCommand 无 react-router | active | `MN-02-search-command-no-router.md` | `templates/ui/deprecated/search-command-static.tsx` |
| MN-03 | MS-03 Kanban 自建板 → KanbanBoard | active | `MN-03-kanban-legacy-board.md` | `templates/ui/deprecated/kanban-legacy-shell.tsx` |

## 演练验证

```bash
python3 create-design-system/scripts/audit_migration_drills.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_compat_contracts.py b-design-system-tailadmin-radix
```

场景路由见 `migration-playbook.md`。
