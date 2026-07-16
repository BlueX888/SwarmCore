# Skill 快照固定与升级策略

> COMPAT-002 产物。业务项目 vendored 或复制 TailAdmin-Radix 模板后，必须先固定 Skill 快照，再按需升级。

## 何时必须固定快照

- 项目已复制 `templates/**` 到业务仓库，且短期内不会跟随 Skill 自动演化。
- 生产环境已验收截图/类型检查，不希望自动演化静默改变默认样式或 props。
- 多团队协作，需要统一引用同一套契约版本。

## 推荐固定方式

### 方式 A：Git submodule / subtree（推荐）

```bash
# 在业务仓库根目录
git submodule add https://github.com/kinda22/design-system.git vendor/design-system
cd vendor/design-system && git checkout <pinned-sha>
```

业务代码从 `vendor/design-system/b-design-system-tailadmin-radix/templates/` 复制或 symlink 所需模板。

### 方式 B：Vendored copy + 版本记录

1. 复制所需 `templates/` 子目录到业务 `src/components/tailadmin/`。
2. 在业务仓库 `docs/design-system-pin.md` 记录：

```yaml
skill: b-design-system-tailadmin-radix
upstream_repo: https://github.com/kinda22/design-system
pinned_commit: <sha>
pinned_date: 2026-06-25
pinned_round: G47
local_skill: .agents/skills/b-design-system/
runtime_roots:
  ui: fe/src/components/ui/
contracts_ref: references/api-contracts.md@<sha>
last_synced_at: 2026-06-25
```

3. 复制 `upstream-changelog-template.md` 为 `docs/design-system-upstream.md`；可泛化改动按 `upstream-contribution-guide.md` 登记。
4. 升级前对比 `api-contracts.md` 风险总表与 `migration-scenarios.md`。

### 方式 C：npm workspace / monorepo path

```json
{
  "dependencies": {
    "@fortress/tailadmin-radix": "workspace:*"
  }
}
```

在 `package.json` 或 changeset 中记录 Skill 快照 commit；CI 运行 `audit_compat_contracts.py` 检测契约漂移。

## 升级前检查清单

| 步骤 | 动作 | 通过标准 |
|---|---|---|
| 1 | 读取 `api-contracts.md` 风险总表 | 确认受影响组件风险等级 |
| 2 | 运行 `audit_compat_contracts.py` | exit 0 |
| 3 | 对比 `migration-scenarios.md` | 业务用法无未覆盖的 breaking 场景 |
| 4 | 业务侧 `tsc --noEmit` | 无类型错误 |
| 5 | 关键页面截图对比 | 无 visual-breaking 回归 |
| 6 | 更新 `docs/design-system-pin.md` | 记录新 sha 与轮次 |

## 升级决策树

```
Skill 有新演化轮次？
├─ 否 → 维持当前 pin
└─ 是 → 读 api-contracts 风险总表
    ├─ 仅 additive（新 props/新模板）→ 可选升级，旧代码无需改
    ├─ visual-breaking（默认尺寸/密度变更）→ 截图对比后决定
    └─ breaking（删除/重命名 API）→ 必须读 migration note + deprecated wrapper
```

## 回滚

- **Git pin**：`git checkout <old-sha>` 在 submodule 或 vendor 目录。
- **Vendored copy**：从备份分支恢复 `src/components/tailadmin/`。
- **紧急**：业务层 wrapper 保留旧 props 映射，见 `migration-note-template.md`。
- **症状定位**：按 `upgrade-troubleshooting.md` 症状路由表（TS-/VIS-/MER-/SEL-/RUN-*）选择 MN、SOR 降级或 pin 回滚。

## 与自动演化的关系

- 首次接入完成后必须执行 `adoption-onboarding-checklist.md` ADOPT-04 pin 记录。
- 自动演化不会主动修改已 pin 的业务代码；升级需人工对比 changelog 与 `api-contracts.md`。

TailAdmin-Radix Skill 在 `dev-auto` 分支持续演化。业务项目**不自动跟随**；仅当团队主动升级 pin 时才引入新能力。演化轮次编号（G47 等）仅用于 Skill 内部 changelog，业务项目以 **commit sha** 为准。

## 检索入口

| 意图 | 读 |
|---|---|
| 公开 API 契约 | `api-contracts.md` |
| 预防性迁移示例 | `migration-scenarios.md` |
| 破坏性变更模板 | `migration-note-template.md` |
| 兼容原则 | `backward-compatibility.md` |
| 升级故障排查 | `upgrade-troubleshooting.md` |
| 业务回流与 upstream 登记 | `upstream-contribution-guide.md` |
| upstream changelog 模板 | `upstream-changelog-template.md` |
