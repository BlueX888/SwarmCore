# 业务智能体扩展 v1 兼容性说明

## 1. 兼容边界

- 本扩展只新增 Capability Pack、Workbench、BlobObject、RuleSet、Evaluation、Finding 和 Report 资源，不改变既有 Run、Artifact、Strategy、RunEvent 或控制命令字段语义。
- Capability Pack Manifest、CapabilityPackVersion、RuleSetVersion 和 WorkItemRevision 发布或创建后不可更新；升级产生新版本。
- 项目必须显式绑定不可变 CapabilityPackVersion。禁用只阻止新执行，历史 WorkItem、Evaluation、Finding 和 Report 仍按快照读取。
- REST 与 MCP 调用同一 `CapabilityPackService`、`WorkbenchService` 和 `RuleSetService`；MCP 不维护独立业务状态。
- 输入 BlobObject 与 Run 输出 Artifact 分表并复用同一对象存储。Blob 在哈希、扫描和保留检查通过前不能绑定 WorkItemRevision。

## 2. 数据库兼容性

Migration `0008_business_workbench` 只新增表、索引、外键、RLS Policy 和不可变触发器，不修改 0001–0007。新增表均保留 tenant 边界；项目资源同时保留 project RLS。通用表只保存 `work_item_type`、版本化 Schema 引用和经 Schema 校验的 payload，不包含合同专用列。

幂等唯一约束：

- Capability Pack：`pack_id + version`、`pack_id + content_hash`；
- WorkItemRevision：`work_item_id + revision`；
- Evaluation：`project_id + revision_id + pack_version_id + idempotency_key`；
- Finding：`work_item_id + rule_key`，重检更新生命周期并保留 FindingAction；
- Report：`evaluation_id + format`。

## 3. API、错误与权限

新增资源位于 `/v1/projects/{project_id}` 下。写请求要求 `Idempotency-Key`；草稿和 WorkItem 更新要求 `If-Match`。稳定业务诊断包括：

- `CAPABILITY_PACK_NOT_ENABLED`、`CAPABILITY_PACK_AMBIGUOUS`；
- `CAPABILITY_REFERENCE_MISSING`；
- `RULE_SET_NO_MATCH`、`RULE_SET_AMBIGUOUS_MATCH`；
- `BLOB_HASH_MISMATCH`、`BLOB_SCAN_REJECTED`；
- `IDEMPOTENCY_KEY_REUSED`。

权限 Scope 冻结为 `capability.read/manage`、`work-item.read/write/execute`、`finding.read/act`、`rule.read/manage`、`report.read/write`、`blob.read/write` 和内部 `evaluation.write`。tenant/project、OPA 与 RLS 同时生效。

## 4. 事件兼容性

业务事件通过既有 Outbox 发布，使用新增命名空间，不复用或改变 `run.*`：

- `capability.rule-set.published`；
- `evaluation.succeeded`；
- `finding.action-recorded`；
- `report.created`。

事件 payload 只增加字段时保持向后兼容；破坏性变更必须发布新 schemaVersion。Evaluation 快照保留 Pack、RuleSet、Strategy、Plan Hash、Registry、附件清单、Schema、报告模板和 Policy Revision，历史读取不依赖当前启用版本。
