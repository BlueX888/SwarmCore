# 吸收业务 upstream 模式

本尊仓库维护者或 Agent：给定**业务项目目录**，读取其 `docs/design-system-upstream.md`，将 `status: pending` 条目预览或合并进 `b-design-system-tailadmin-radix/`。

## 何时使用

| 场景 | 用本模式 |
|---|---|
| 业务仓库登记了 `pending` upstream 条目 | ✅ |
| 只想整包同步业务 `.agents/skills/b-design-system/` | ❌ 用 `rsync` + pin；见 `upstream-contribution-guide.md` |
| 业务项目尚未创建 `design-system-upstream.md` | 先让对方补 ADOPT-06 |

## 前置

业务仓库必须有：

- `docs/design-system-upstream.md`（模板：`references/upstream-changelog-template.md`）
- `docs/design-system-pin.md`（含 `local_skill` / `skill_path`）

## 执行步骤

### 1. 预览（默认，不写文件）

```bash
python3 create-design-system/scripts/absorb_upstream.py /absolute/path/to/business-repo
```

**Cursor 斜杠命令（推荐）**：在 Chat 输入

```text
/absorb-upstream /absolute/path/to/business-repo
```

Agent 会执行 `create-design-system/scripts/absorb_upstream.sh`（预览 → 写入 → 验证一条龙）。

示例：

```bash
python3 create-design-system/scripts/absorb_upstream.py /Users/kevinhan/Code/kinda22/nex
python3 create-design-system/scripts/absorb_upstream.py /Users/kevinhan/Code/ontomind/deeptalk-gateway-tob
```

输出：`pending` 条目列表、源路径 → 本尊 `templates/` / `references/` 映射、unified diff。

### 2. 吸收单条

```bash
python3 create-design-system/scripts/absorb_upstream.py /path/to/nex --entry nex-2026-06-27-001
```

### 3. 写入本尊 skill

```bash
python3 create-design-system/scripts/absorb_upstream.py /path/to/nex --apply
```

`breaking: true` 的条目默认拒绝；确认 migration 路径后：

```bash
python3 create-design-system/scripts/absorb_upstream.py /path/to/nex --entry <id> --apply --include-breaking
```

### 4. 吸收后验证（必须）

```bash
python3 create-design-system/scripts/verify_design_system.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_compat_contracts.py b-design-system-tailadmin-radix
```

若改了可视模板，同步 `examples/b-design-system-tailadmin-radix/`。

### 5. 通知业务方

请业务仓库将对应 entry 标为 `merged`，并更新 `docs/design-system-pin.md` 的 `pinned_commit` / `last_synced_at`。

## 源文件选取规则

对每个 `upstream_paths` 项，脚本在 entry 的 `local_paths` 中按优先级选取：

1. `local_skill` 下路径后缀与 upstream 一致
2. 同名文件且在 `local_skill` 内
3. 其他存在的 `local_paths`（如 `fe/src/components/ui/`）

**建议业务侧**：可泛化改动先同步到 `local_skill/templates/**`，再登记 upstream。

## 红线

- 默认 **dry-run**；必须显式 `--apply` 才写入本尊。
- 不修改业务仓库文件。
- 不自动改 `design-system-upstream.md` 的 `status`（合并后人工或另开 PR 回业务仓）。
- `local-only` / `merged` / `rejected` 条目跳过。

## 检索入口

| 意图 | 读 |
|---|---|
| 业务如何登记 upstream | `references/upstream-contribution-guide.md` |
| changelog 模板 | `references/upstream-changelog-template.md` |
| pin 字段 | `references/version-pinning-guide.md` |
| 破坏性变更 | `references/backward-compatibility.md` |
