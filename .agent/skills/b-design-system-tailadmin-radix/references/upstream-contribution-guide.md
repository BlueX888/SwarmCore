# 业务回流与上游贡献约定

> DOCS-044 产物。业务项目 copy 本 Skill 后，Agent 修复 bug、改组件或沉淀设计时，**必须先读本文件**，再决定：只改业务本地、同步本地 Skill copy，还是准备回流本尊仓库 `.agents/skills/b-design-system-tailadmin-radix/`。

## 适用场景

| 你在哪工作 | 是否读本文件 |
|---|---|
| 业务仓库（copy 了 Skill 到 `.agents/skills/...`） | **必读** |
| 本尊仓库 `design-system` 吸收业务回流 | 读本文件 + 各 pending `design-system-upstream.md` |
| 本尊仓库日常自动演化 | 读 `docs/spec/.../sop.md`；业务 pending 条目作为 G2 选题输入 |

## 两文件约定（业务仓库根目录 `docs/`）

业务项目维护**两个**文件，分工固定：

| 文件 | 职责 | 谁写 | 谁读 |
|---|---|---|---|
| `design-system-pin.md` | 基线：从哪版 copy、本地 Skill 路径、运行时模板路径 | 首次接入 + 每次与上游同步后 | 业务 Agent、本尊维护者 |
| `design-system-upstream.md` | 增量队列：相对 pin 改了什么、是否建议回流 | 业务 Agent 每次可泛化改动后 | 本尊维护者、业务 Agent 自查 |

**禁止**把待回流项只写在业务总 `CHANGELOG.md` 里——噪音太大，本尊无法机械检索。可在总 changelog 加一句「详见 `docs/design-system-upstream.md`」。

### `design-system-pin.md` 最低字段

```yaml
skill: b-design-system-tailadmin-radix
upstream_repo: https://github.com/kinda22/design-system    # 或等效远端
pinned_commit: <本尊 copy 或上次同步时的 git sha>
pinned_date: YYYY-MM-DD
local_skill: .agents/skills/b-design-system/               # 业务侧 Skill copy 根
runtime_roots:                                             # 从 templates 复制到运行时的路径
  ui: fe/src/components/ui/                                # 对应 templates/ui/
  layout: fe/src/layouts/                                  # 可选
last_synced_at: YYYY-MM-DD
```

### `design-system-upstream.md`

复制 `upstream-changelog-template.md` 到业务仓库 `docs/design-system-upstream.md`，按条维护 `entries`。

---

## 何时改、何时回流（决策树）

```
在业务仓库改动了 Skill 相关文件？
├─ 否 → 无需登记 upstream
└─ 是 → 能否去掉业务域名词/API/路由后仍成立？
    ├─ 否 → status: local-only（留在业务，不写 pending）
    └─ 是 → 改动类型？
        ├─ bugfix（模板/props/状态/可访问性）→ 通常 pending 回流
        ├─ docs（guards、decision-matrix 反例、检索路径）→ 通常 pending 回流
        ├─ 新组件/变体（≥2 个业务场景会用）→ 先泛化设计，再 pending
        ├─ 业务专属页面/领域组件 → local-only
        └─ breaking API → pending + breaking: true；本尊需 migration note
```

### 必须登记 `design-system-upstream.md` 的情况

- 修改了本地 Skill copy 的 `templates/**` 或 `references/**`。
- 修改了 `runtime_roots` 下与 Skill 模板 1:1 对应的运行时文件（如 `fe/src/components/ui/button.tsx`），且修复/改进可泛化。
- 发现 Skill 文档缺口、错选反例、接入步骤缺失——即使代码只在业务层 workaround，也应登记 `type: docs`。

### 不必回流（标 `local-only`）

- 绑定单一产品域：工单状态机、租户计费、项目 ID 路由等。
- 仅调整 mock 数据、中文业务文案（非组件默认 placeholder）。
- 业务门禁脚本（如 `check-design-strict-baseline.sh`）且无通用价值。

---

## 三层同步顺序（copy 模式）

业务 copy Skill 时，**禁止**跳过中间层直接从 `fe/` 改本尊。

```text
runtime（如 fe/src/components/ui/）
    ↓ 先同步
local_skill（如 .agents/skills/b-design-system/templates/）
    ↓ 再登记 + 可选 PR
upstream（.agents/skills/b-design-system-tailadmin-radix/）
```

Agent 在业务仓库完成 runtime 修复后：

1. 将同名文件同步到 `local_skill` 对应 `templates/**` 路径。
2. 在 `design-system-upstream.md` 追加 `status: pending` 条目。
3. 若 breaking，在 `notes` 写明旧行为与新行为。

---

## 如何设计（按改动类型）

### bugfix（模板 / 状态 / a11y）

1. 读 `engineering-guards.md`、`state-index.md`、对应 `component-styles/*-template.md`。
2. 最小 diff 修复；优先 additive（新 props）而非改默认行为。
3. 若改默认视觉/尺寸 → 视为 visual-breaking，见 `backward-compatibility.md`。
4. 业务侧：`tsc`、设计门禁（若有）、关键页面截图。
5. 登记 upstream 条目 `type: bugfix`。

### 新组件或变体（认为「设计不错」）

1. 读 `output-modes/missing-component.md` 或 `decision-matrix.md`，确认 index 无覆盖。
2. **泛化**：去掉业务 API、路由、领域名词；props 受控、可复用。
3. 实现：`cva` + `cn()` + Radix；状态全覆盖（见 `state-index.md`）。
4. 文档：`component-index.md` 一行 + `component-styles/` section（本尊侧；业务侧先在 local_skill 镜像）。
5. 登记 `type: component`；`upstream_paths` 列出新文件。

### 文档 / 选型 / 接入经验

1. 错选修复 → 写 `decision-matrix.md` 正例/反例。
2. 接入步骤缺口 → 写 `adoption-onboarding-checklist.md` 或 `upgrade-troubleshooting.md` 症状行（UP-*，见下）。
3. 登记 `type: docs`。

### breaking 变更

业务侧**不得**静默改已发布 props/导出名。必须：

1. `breaking: true` + `api-contracts.md` 风险等级自查。
2. 本尊合并时提供 deprecated wrapper + `migration-notes/`（见 `migration-note-template.md`）。

---

## 如何记录（Agent 收尾清单）

每次可泛化改动，PR 或任务结束前完成：

| # | 动作 | 通过标准 |
|---|---|---|
| UP-01 | runtime → local_skill 已同步 | 同名模板路径一致，或文档说明映射 |
| UP-02 | `design-system-upstream.md` 已追加条目 | 含 `id`、`status`、`type`、`local_paths`、`upstream_paths` |
| UP-03 | `local-only` 已显式标注 | 避免本尊误收业务域组件 |
| UP-04 | breaking 已标注 | `breaking: true` + notes |
| UP-05 | 错选/文档缺口已写回 | `decision-matrix.md` 或症状表（若已回流本尊则改本尊文件） |

### 条目 `status` 流转

| status | 含义 |
|---|---|
| `pending` | 待本尊吸收 |
| `merged` | 已入本尊；填 `upstream_pr` / `upstream_commit` |
| `rejected` | 本尊不收；`notes` 写原因 |
| `local-only` | 永不回流，仅业务留存 |

本尊合并后，业务维护者将条目改为 `merged` 并更新 `design-system-pin.md` 的 `pinned_commit`、`last_synced_at`。

---

## 路径映射（copy 到 `.agents/skills/b-design-system/`）

本地 Skill 与本尊目录结构 **1:1**，仅根路径不同：

```text
<local_skill>/templates/ui/button.tsx
  → b-design-system-tailadmin-radix/templates/ui/button.tsx

<local_skill>/references/engineering-guards.md
  → b-design-system-tailadmin-radix/references/engineering-guards.md
```

`upstream_paths` **始终写相对本尊 skill 根的路径**（不含 `b-design-system-tailadmin-radix/` 前缀亦可，但全文统一一种风格）。

常见 runtime 映射（按 pin 中 `runtime_roots` 为准）：

```text
runtime_roots.ui/button.tsx ↔ templates/ui/button.tsx
```

---

## 本尊如何吸收

本尊维护者或 Agent **不自动 merge**；以 `design-system-upstream.md` 为 intake 队列。

**推荐执行**（给业务仓库目录即可）：

```text
/absorb-upstream /absolute/path/to/business-repo
```

或在终端：

```bash
bash create-design-system/scripts/absorb_upstream.sh /absolute/path/to/business-repo
```

仅预览、不写入时：

```bash
python3 create-design-system/scripts/absorb_upstream.py /absolute/path/to/business-repo
```

详见 `output-modes/absorb-upstream.md`。

手工流程（脚本未覆盖时）：

1. 收集各业务仓库 `status: pending` 条目。
2. 按 `upstream_paths` 对 `pinned_commit` 做 diff。
3. 查 `api-contracts.md`；breaking 走 migration 流程。
4. 合并后更新 `examples/b-design-system-tailadmin-radix/`（若涉及可视模板）。
5. 跑 `verify_design_system.py`、`audit_compat_contracts.py`。
6. 通知业务方改 `status: merged` + 更新 pin。

---

## 验证命令

**业务仓库（改 runtime / local_skill 后）：**

```bash
# 按项目实际门禁
pnpm exec tsc --noEmit
# 例：nex
cd fe && pnpm run check:design
```

**本尊仓库（吸收回流后）：**

```bash
python3 create-design-system/scripts/verify_design_system.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_compat_contracts.py b-design-system-tailadmin-radix
```

---

## 症状 ID（upgrade-troubleshooting 扩展）

| ID | 场景 | 处理 |
|---|---|---|
| UP-01 | runtime 改了但未同步 local_skill | 先同步再登记 upstream |
| UP-02 | 只改 local_skill 未写 upstream | 补 `design-system-upstream.md` |
| UP-03 | 业务域组件误标 pending | 改 `local-only` |
| UP-04 | breaking 未标且本尊 compat 失败 | 补 migration + deprecated wrapper |
| UP-05 | pin 无 `pinned_commit` 无法 diff | 补 `design-system-pin.md` |

---

## 检索入口

| 意图 | 读 |
|---|---|
| 上游 changelog 模板 | `upstream-changelog-template.md` |
| pin 与升级 | `version-pinning-guide.md` |
| 首次接入 | `adoption-onboarding-checklist.md` |
| 缺组件设计 | `output-modes/missing-component.md` |
| 破坏性变更 | `backward-compatibility.md` → `migration-note-template.md` |
| Agent 路由 | `agent-retrieval-guide.md` |
| 本尊吸收 upstream | `output-modes/absorb-upstream.md` |
| 选型反例写回 | `decision-matrix.md` |
