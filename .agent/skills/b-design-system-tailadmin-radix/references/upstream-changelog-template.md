# design-system-upstream.md 模板

> 复制到业务仓库 `docs/design-system-upstream.md`。与 `design-system-pin.md` 配对使用。约定见 `upstream-contribution-guide.md`。

```yaml
# docs/design-system-upstream.md
skill: b-design-system-tailadmin-radix
upstream_repo: https://github.com/kinda22/design-system
pinned_commit: <与 design-system-pin.md 一致>
local_skill: .agents/skills/b-design-system/
last_entry_at: YYYY-MM-DD

entries:
  - id: <project>-YYYY-MM-DD-001
    status: pending              # pending | merged | rejected | local-only
    type: bugfix                 # bugfix | component | docs | breaking
    date: YYYY-MM-DD
    title: <一句话说明可泛化价值>
    local_paths:
      - <local_skill 或 runtime 相对路径>
    upstream_paths:
      - templates/ui/<file>.tsx
      # - references/<file>.md
    breaking: false
    notes: |
      <根因、验证方式、是否已同步 local_skill>

  # - id: <project>-YYYY-MM-DD-002
  #   status: local-only
  #   type: component
  #   title: <业务专属，不回流>
  #   local_paths:
  #     - fe/src/components/<domain>/Foo.tsx
  #   notes: 绑定 <产品域>，不泛化

  # - id: <project>-YYYY-MM-DD-003
  #   status: merged
  #   type: bugfix
  #   title: <已吸收>
  #   upstream_paths:
  #     - templates/ui/button.tsx
  #   upstream_pr: https://github.com/kinda22/design-system/pull/123
  #   upstream_commit: abcdef1
  #   merged_at: YYYY-MM-DD
```

## 字段说明

| 字段 | 必填 | 说明 |
|---|---|---|
| `id` | 是 | `<项目名>-日期-序号`，全局唯一 |
| `status` | 是 | 见 `upstream-contribution-guide.md` |
| `type` | 是 | 改动类别 |
| `local_paths` | 是 | 业务仓库内已改文件 |
| `upstream_paths` | pending/merged 时必填 | 相对本尊 skill 根路径 |
| `breaking` | 是 | 默认 `false` |
| `upstream_pr` / `upstream_commit` | merged 时填 | 便于业务更新 pin |
