# ruff: noqa: RUF001
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Literal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from swarmcore_persistence.models import (
    CapabilityPack,
    CapabilityPackVersion,
    Evaluation,
    ProjectCapabilityBinding,
    Strategy,
    StrategyVersion,
    WorkItem,
    WorkItemRevision,
)
from swarmcore_registry import CapabilityPackManifest

from .capability_packs import CapabilityPackService
from .cases import CaseService, CaseSubjectInput
from .document_library import DocumentLibraryService
from .workbench import WorkbenchService

BusinessWorkStatus = Literal[
    "planned",
    "not_configured",
    "incomplete",
    "runnable",
    "unavailable",
]

STATUS_LABELS: dict[BusinessWorkStatus, str] = {
    "planned": "规划中",
    "not_configured": "未配置",
    "incomplete": "配置不完整",
    "runnable": "可运行",
    "unavailable": "暂不可用",
}

BusinessWorkCategory = Literal["foundation", "business", "governance"]


@dataclass(frozen=True, slots=True)
class BusinessWorkFunction:
    name: str
    description: str


@dataclass(frozen=True, slots=True)
class BusinessWorkDefinition:
    key: str
    name: str
    short_name: str
    category: BusinessWorkCategory
    summary: str
    functions: tuple[BusinessWorkFunction, ...]
    pack_name: str | None = None


@dataclass(frozen=True, slots=True)
class BusinessWorkBlocker:
    code: str
    message: str
    ref: str | None = None


@dataclass(frozen=True, slots=True)
class BusinessWorkSummary:
    work_key: str
    name: str
    short_name: str
    category: BusinessWorkCategory
    summary: str
    status: BusinessWorkStatus
    status_label: str
    pack_name: str | None
    pack_version_id: UUID | None
    pack_version: str | None
    enabled: bool
    binding_status: str | None
    blockers: tuple[BusinessWorkBlocker, ...] = ()
    agents: tuple[str, ...] = ()
    tools: tuple[str, ...] = ()
    models: tuple[str, ...] = ()
    document_requirements: tuple[dict[str, Any], ...] = ()
    decision_slots: tuple[dict[str, Any], ...] = ()
    functions: tuple[BusinessWorkFunction, ...] = ()
    configuration: dict[str, Any] = field(default_factory=dict)
    work_item_type: str | None = None
    case_based: bool = False
    bound_strategy_version_id: UUID | None = None
    bound_strategy_name: str | None = None
    bound_strategy_version: int | None = None


# Product catalog. Only works with pack_name have an executable internal definition.
BUSINESS_WORK_DEFINITIONS: tuple[BusinessWorkDefinition, ...] = (
    BusinessWorkDefinition(
        key="ai-foundation-quality",
        name="基础 AI 能力集成与质量评测",
        short_name="AI 基础与评测",
        category="foundation",
        summary="统一接入基础 AI 能力，并用样本、规则、置信度和人工复核建立质量闭环。",
        functions=(
            BusinessWorkFunction(
                "基础能力接入", "封装 LLM、Embedding、Vision、OCR、NLP、文档解析和结构化抽取。"
            ),
            BusinessWorkFunction("检索与问答", "提供向量检索、知识库索引和带证据的知识问答能力。"),
            BusinessWorkFunction(
                "规则与提示词", "版本化管理规则、Prompt、输出 Schema 和任务参数。"
            ),
            BusinessWorkFunction(
                "置信度校准", "基于样本指标校准置信度，设置自动通过、降级和拦截阈值。"
            ),
            BusinessWorkFunction("人工复核", "对低置信度、证据不足和高风险结果发起人工确认。"),
            BusinessWorkFunction("样本评测", "管理评测样本、指标、基线、回归结果和质量变化。"),
        ),
    ),
    BusinessWorkDefinition(
        key="document-structuring",
        name="文件结构化智能体",
        short_name="文件结构化",
        category="foundation",
        summary="把多格式、大体量文件转换为可检索、可追溯、可人工确认的结构化数据。",
        pack_name="document-structuring",
        functions=(
            BusinessWorkFunction("格式自适应识别", "识别文件类型、编码、版式和处理路径。"),
            BusinessWorkFunction(
                "ODF 与办公文档解析", "解析 ODF、PDF、Word、Excel 等常见文档格式。"
            ),
            BusinessWorkFunction("大文件处理", "按页或分片并行处理，支持断点、重试和结果合并。"),
            BusinessWorkFunction("OCR 与 NLP 抽取", "提取文字、实体、字段、关系及其原文证据。"),
            BusinessWorkFunction("切片与表格提取", "生成语义切片，恢复表格结构并保留页码和坐标。"),
            BusinessWorkFunction(
                "自动整理与确认", "按业务 Schema 整理结果，并把疑点提交人工确认。"
            ),
        ),
    ),
    BusinessWorkDefinition(
        key="document-integrity",
        name="文件完整性校验智能体",
        short_name="文件完整性校验",
        category="business",
        summary="根据合同类型和资料规则检查文件是否齐全、有效、一致并可追踪。",
        pack_name="contract-integrity",
        functions=(
            BusinessWorkFunction("资料清单匹配", "按合同类型、阶段和项目规则匹配应提交资料清单。"),
            BusinessWorkFunction(
                "多维完整性检查", "检查缺失、版本、签章、日期、附件和跨文件关联。"
            ),
            BusinessWorkFunction("缺失预警追踪", "形成缺失项、责任人、期限、提醒和闭环状态。"),
            BusinessWorkFunction("规则可视化配置", "配置清单、条件、阈值、例外和人工复核要求。"),
            BusinessWorkFunction("校验报告", "输出结论、缺失明细、证据引用和整改建议。"),
        ),
    ),
    BusinessWorkDefinition(
        key="performance-plan-collection",
        name="履约计划与执行采集智能体",
        short_name="履约计划与采集",
        category="business",
        summary="从合同提取履约计划，并持续采集执行证据、里程碑状态和变更历史。",
        pack_name="contract-performance",
        functions=(
            BusinessWorkFunction("合同义务提取", "提取工期、交付、付款、服务标准和验收要求。"),
            BusinessWorkFunction("里程碑与甘特图", "生成里程碑、依赖关系、计划日期和甘特视图。"),
            BusinessWorkFunction(
                "执行资料采集", "采集验收单、发货单、到货单、付款凭证和会议纪要。"
            ),
            BusinessWorkFunction("状态更新", "把执行证据关联至义务和里程碑并更新完成状态。"),
            BusinessWorkFunction("变更历史", "记录计划调整、合同变更、责任主体和版本差异。"),
        ),
    ),
    BusinessWorkDefinition(
        key="invoice-assurance",
        name="发票一致性校验智能体",
        short_name="发票一致性校验",
        category="business",
        summary="识别发票事实，并与合同、订单、履约和付款条件执行一致性及合规检查。",
        pack_name="invoice-assurance",
        functions=(
            BusinessWorkFunction(
                "发票信息识别", "提取购买方、销售方、税号、金额、税率、品项和日期。"
            ),
            BusinessWorkFunction(
                "多维一致性校验", "与合同、订单、收货、验收和付款计划进行交叉核验。"
            ),
            BusinessWorkFunction("合规性检查", "检查票面规范、重复发票、异常税率和关键字段风险。"),
            BusinessWorkFunction(
                "付款前置条件", "判断验收、交付、审批和资料完整性是否满足付款条件。"
            ),
            BusinessWorkFunction("报告与风险预警", "输出差异证据、风险等级、处置建议和校验报告。"),
        ),
    ),
    BusinessWorkDefinition(
        key="deviation-analysis",
        name="偏差分析智能体",
        short_name="偏差分析",
        category="business",
        summary="对计划与实际执行进行时间、内容和成本偏差计算，并解释原因和趋势。",
        pack_name="deviation-analysis",
        functions=(
            BusinessWorkFunction("时间偏差", "计算计划与实际节点的提前、延迟和关键路径影响。"),
            BusinessWorkFunction("内容偏差", "比对约定范围、交付内容、质量要求和实际完成情况。"),
            BusinessWorkFunction("成本偏差", "分析合同金额、变更、支付和实际成本之间的差异。"),
            BusinessWorkFunction("AI 根因分析", "结合证据生成结构化根因、影响和纠正建议。"),
            BusinessWorkFunction(
                "趋势与责任归属", "展示偏差趋势并记录责任主体、确认意见和处理状态。"
            ),
        ),
    ),
    BusinessWorkDefinition(
        key="report-generation",
        name="报告生成智能体",
        short_name="报告生成",
        category="business",
        summary="聚合文件、履约、偏差、发票和风险事实，生成可追溯的后评价报告。",
        pack_name="contract-post-evaluation",
        functions=(
            BusinessWorkFunction("多源结果聚合", "汇总结构化事实、规则结论、风险、问题和证据。"),
            BusinessWorkFunction("七维评价", "按七大评价维度计算指标、分值、结论和改进项。"),
            BusinessWorkFunction("AI 报告叙述", "基于已确认事实生成摘要、分析、建议和管理层结论。"),
            BusinessWorkFunction("模板与版本", "管理报告模板、章节、样式、口径和版本。"),
            BusinessWorkFunction("多格式输出", "输出结构化 JSON、在线预览和 PDF 等正式报告。"),
        ),
    ),
    BusinessWorkDefinition(
        key="contract-post-evaluation",
        name="合同后评价",
        short_name="合同后评价",
        category="business",
        summary="围绕合同履约全过程聚合资料、履约、偏差、发票与风险事实，完成七维评价并生成可追溯报告。",
        pack_name="contract-post-evaluation",
        functions=(
            BusinessWorkFunction(
                "资料与履约采集", "匹配合同、履约、偏差、发票和供应商等业务资料。"
            ),
            BusinessWorkFunction("七维评价", "按七大评价维度计算指标、分值、结论和改进项。"),
            BusinessWorkFunction("风险与偏差分析", "识别履约偏差、发票差异和供应商风险关注项。"),
            BusinessWorkFunction("综合结论", "输出总分、等级、风险等级和是否需要复核。"),
            BusinessWorkFunction("报告与证据", "生成可追溯 JSON/PDF 报告，并冻结资料与决策快照。"),
        ),
    ),
    BusinessWorkDefinition(
        key="swarm-calibration",
        name="智能体调度校准智能体",
        short_name="调度校准",
        category="governance",
        summary="监督多智能体任务的数据流和输出质量，为调度、降级与切换提供校准建议。",
        pack_name="swarm-calibration",
        functions=(
            BusinessWorkFunction("任务编排", "定义任务依赖、并行关系、输入输出和人工等待节点。"),
            BusinessWorkFunction(
                "智能体数据流转", "校验上游输出 Schema，向下游传递冻结数据和证据。"
            ),
            BusinessWorkFunction("结果质量校验", "检查结构、证据、置信度、规则结果和交叉一致性。"),
            BusinessWorkFunction("备用智能体切换", "按策略建议重试、降级或切换备用 Agent 与模型。"),
            BusinessWorkFunction(
                "执行日志与监控", "查看运行状态、任务耗时、异常、成本和完整链路日志。"
            ),
        ),
    ),
    BusinessWorkDefinition(
        key="procurement-supplier-risk",
        name="招采一致性与供应商风控智能体",
        short_name="招采与供应商风控",
        category="business",
        summary="比对招投标与合同条款，结合多源风险和绩效数据持续识别供应商风险。",
        pack_name="procurement-supplier-risk",
        functions=(
            BusinessWorkFunction(
                "招采合同深度比对", "对招标文件、投标文件、中标结果和合同条款进行语义比对。"
            ),
            BusinessWorkFunction("分级差异清单", "按影响和风险输出新增、缺失、冲突及弱化条款。"),
            BusinessWorkFunction(
                "多源风险数据", "接入工商、司法、舆情、制裁和内部履约等风险数据。"
            ),
            BusinessWorkFunction("黑名单预警", "实时检查黑名单、关联方和高风险状态并触发预警。"),
            BusinessWorkFunction(
                "绩效与风控工单", "评估供应商绩效，形成责任明确、可跟踪的风控工单。"
            ),
            BusinessWorkFunction(
                "历史变化追溯", "保留风险事实、评分、处置和供应商状态的版本历史。"
            ),
        ),
    ),
)

_DEFINITIONS_BY_KEY = {item.key: item for item in BUSINESS_WORK_DEFINITIONS}
_PACK_TO_WORK_KEY = {
    item.pack_name: item.key for item in BUSINESS_WORK_DEFINITIONS if item.pack_name is not None
}


def get_business_work_definition(work_key: str) -> BusinessWorkDefinition | None:
    return _DEFINITIONS_BY_KEY.get(work_key)


def pack_name_for_work_key(work_key: str) -> str | None:
    definition = _DEFINITIONS_BY_KEY.get(work_key)
    return definition.pack_name if definition is not None else None


def work_key_for_pack_name(pack_name: str) -> str | None:
    return _PACK_TO_WORK_KEY.get(pack_name)


def document_binding_keys(pack_name: str, work_item_type: str) -> tuple[str, ...]:
    """Keys used when selecting documents for an internal pack execution."""
    if pack_name == "contract-post-evaluation":
        # A post-evaluation can aggregate many evidence categories, but it must
        # not absorb documents merely because another case in the same project
        # is bound to a contributing business work (for example deviation
        # analysis). Explicitly bind every selected document to this case's
        # pack or work-item key to preserve case isolation.
        return (pack_name, work_item_type)
    if pack_name == "deviation-analysis":
        return (
            pack_name,
            work_item_type,
            "deviation-analysis",
            "performance-plan-collection",
            "document-integrity",
            "invoice-assurance",
        )
    if pack_name == "invoice-assurance":
        return (pack_name, work_item_type, "invoice-assurance")
    mapped = work_key_for_pack_name(pack_name)
    if mapped is not None:
        return (pack_name, work_item_type, mapped)
    return (pack_name, work_item_type)


class BusinessWorkService:
    """Product-facing projection over internal Capability Pack execution definitions."""

    def __init__(
        self,
        capability_packs: CapabilityPackService,
        workbench: WorkbenchService,
        cases: CaseService,
        *,
        documents: DocumentLibraryService | None = None,
    ) -> None:
        self._capability_packs = capability_packs
        self._workbench = workbench
        self._cases = cases
        self._documents = documents or DocumentLibraryService()

    async def list_works(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
    ) -> list[BusinessWorkSummary]:
        await self._capability_packs.ensure_trusted(
            session, tenant_id=tenant_id, project_id=project_id
        )
        pack_index = await self._pack_index(session, tenant_id=tenant_id, project_id=project_id)
        return [
            await self._summarize(
                session,
                tenant_id=tenant_id,
                project_id=project_id,
                definition=definition,
                pack_index=pack_index,
            )
            for definition in BUSINESS_WORK_DEFINITIONS
        ]

    async def get_work(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        work_key: str,
    ) -> BusinessWorkSummary:
        definition = get_business_work_definition(work_key)
        if definition is None:
            raise LookupError("business work not found")
        await self._capability_packs.ensure_trusted(
            session, tenant_id=tenant_id, project_id=project_id
        )
        pack_index = await self._pack_index(session, tenant_id=tenant_id, project_id=project_id)
        return await self._summarize(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            definition=definition,
            pack_index=pack_index,
        )

    async def create_work_item(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        work_key: str,
        payload: dict[str, Any],
        owner: str | None,
        idempotency_key: str,
        actor: str,
    ) -> tuple[WorkItem, WorkItemRevision]:
        summary = await self.get_work(
            session, tenant_id=tenant_id, project_id=project_id, work_key=work_key
        )
        self._require_runnable(summary)
        assert summary.work_item_type is not None
        return await self._workbench.create_work_item(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            work_item_type=summary.work_item_type,
            payload=payload,
            owner=owner,
            idempotency_key=idempotency_key,
            actor=actor,
        )

    async def execute_work_item(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        work_key: str,
        work_item_id: UUID,
        idempotency_key: str,
        actor: str,
        submitted_scopes: tuple[str, ...] = (),
        auth_context_hash: str = "unknown",
    ) -> Evaluation:
        summary = await self.get_work(
            session, tenant_id=tenant_id, project_id=project_id, work_key=work_key
        )
        self._require_runnable(summary)
        return await self._workbench.execute(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            work_item_id=work_item_id,
            idempotency_key=idempotency_key,
            actor=actor,
            submitted_scopes=submitted_scopes,
            auth_context_hash=auth_context_hash,
        )

    async def create_case(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        work_key: str,
        payload: dict[str, Any],
        subjects: list[CaseSubjectInput],
        owner: str | None,
        idempotency_key: str,
        actor: str,
    ) -> tuple[WorkItem, WorkItemRevision, list[Any]]:
        summary = await self.get_work(
            session, tenant_id=tenant_id, project_id=project_id, work_key=work_key
        )
        self._require_runnable(summary)
        assert summary.work_item_type is not None
        return await self._cases.create(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            scenario_type=summary.work_item_type,
            payload=payload,
            subjects=subjects,
            owner=owner,
            idempotency_key=idempotency_key,
            actor=actor,
        )

    async def start_assessment(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        work_key: str,
        case_id: UUID,
        idempotency_key: str,
        actor: str,
        submitted_scopes: tuple[str, ...] = (),
        auth_context_hash: str = "unknown",
    ) -> Evaluation:
        summary = await self.get_work(
            session, tenant_id=tenant_id, project_id=project_id, work_key=work_key
        )
        self._require_runnable(summary)
        return await self._cases.assess(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            case_id=case_id,
            idempotency_key=idempotency_key,
            actor=actor,
            submitted_scopes=submitted_scopes,
            auth_context_hash=auth_context_hash,
        )

    async def get_assessment(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        assessment_id: UUID,
    ) -> tuple[Evaluation, WorkItem | None, WorkItemRevision | None]:
        evaluation = await session.scalar(
            select(Evaluation).where(
                Evaluation.id == assessment_id,
                Evaluation.tenant_id == tenant_id,
                Evaluation.project_id == project_id,
            )
        )
        if evaluation is None:
            raise LookupError("assessment not found")
        item = await session.scalar(
            select(WorkItem).where(
                WorkItem.id == evaluation.work_item_id,
                WorkItem.tenant_id == tenant_id,
                WorkItem.project_id == project_id,
            )
        )
        revision = await session.scalar(
            select(WorkItemRevision).where(
                WorkItemRevision.id == evaluation.work_item_revision_id,
                WorkItemRevision.tenant_id == tenant_id,
            )
        )
        return evaluation, item, revision

    async def bind_strategy(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        work_key: str,
        strategy_version_id: UUID,
        idempotency_key: str,
        actor: str,
    ) -> BusinessWorkSummary:
        """Bind a published StrategyVersion to a business work and enable it.

        Publishes a new immutable capability-pack version when the strategy changes,
        reusing CapabilityPackService.publish/enable without a separate business path.
        """
        definition = get_business_work_definition(work_key)
        if definition is None:
            raise LookupError("business work not found")
        if definition.pack_name is None:
            raise ValueError("BUSINESS_WORK_PLANNED")

        await self._capability_packs.ensure_trusted(
            session, tenant_id=tenant_id, project_id=project_id
        )
        pack_index = await self._pack_index(session, tenant_id=tenant_id, project_id=project_id)
        candidates = pack_index.get(definition.pack_name, [])
        # Template prefers complete document requirements; binding prefers enabled config.
        template_row = self._select_pack_template(candidates)
        binding_row = self._select_pack_version(candidates)
        if template_row is None:
            raise LookupError("capability pack version not found")
        _, template_version, _ = template_row
        binding = binding_row[2] if binding_row is not None else None

        strategy_row = await session.execute(
            select(StrategyVersion, Strategy)
            .join(Strategy, Strategy.id == StrategyVersion.strategy_id)
            .where(
                StrategyVersion.id == strategy_version_id,
                StrategyVersion.tenant_id == tenant_id,
                StrategyVersion.lifecycle.in_({"PUBLISHED", "TRUSTED"}),
                Strategy.project_id == project_id,
            )
        )
        selected = strategy_row.one_or_none()
        if selected is None:
            raise LookupError("published strategy version not found")
        strategy_version, strategy = selected

        current_bound = self._strategy_binding_from_version(template_version)
        if (
            current_bound[0] == strategy_version_id
            and binding is not None
            and binding.status in {"ENABLED", "DEGRADED"}
            and binding.pack_version_id == template_version.id
        ):
            await self._capability_packs.enable(
                session,
                tenant_id=tenant_id,
                project_id=project_id,
                version_id=template_version.id,
                configuration=dict(binding.configuration),
                idempotency_key=idempotency_key,
                actor=actor,
            )
            return await self.get_work(
                session,
                tenant_id=tenant_id,
                project_id=project_id,
                work_key=work_key,
            )

        snapshot = CapabilityPackService._strategy_version_snapshot(
            f"strategy://project/{strategy.id}@{strategy_version.version}",
            strategy_version,
        )
        manifest = self._manifest_for_strategy(
            template=template_version.manifest,
            pack_name=definition.pack_name,
            pack_version=self._next_pack_version([version.version for _, version, _ in candidates]),
            strategy_id=strategy.id,
            strategy_version_number=strategy_version.version,
            agents=list(snapshot["agents"]),
            tools=list(snapshot["tools"]),
        )
        published = await self._capability_packs.publish(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            manifest=manifest,
            strategy_version_id=strategy_version_id,
            actor=actor,
        )
        configuration = dict(binding.configuration) if binding is not None else {}
        await self._capability_packs.enable(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            version_id=published.id,
            configuration=configuration,
            idempotency_key=idempotency_key,
            actor=actor,
        )
        return await self.get_work(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            work_key=work_key,
        )

    async def _pack_index(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
    ) -> dict[
        str, list[tuple[CapabilityPack, CapabilityPackVersion, ProjectCapabilityBinding | None]]
    ]:
        rows = await self._capability_packs.list_project(
            session, tenant_id=tenant_id, project_id=project_id
        )
        index: dict[
            str, list[tuple[CapabilityPack, CapabilityPackVersion, ProjectCapabilityBinding | None]]
        ] = {}
        for pack, version, binding in rows:
            index.setdefault(pack.name, []).append((pack, version, binding))
        return index

    async def _summarize(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        definition: BusinessWorkDefinition,
        pack_index: dict[
            str, list[tuple[CapabilityPack, CapabilityPackVersion, ProjectCapabilityBinding | None]]
        ],
    ) -> BusinessWorkSummary:
        if definition.pack_name is None:
            return BusinessWorkSummary(
                work_key=definition.key,
                name=definition.name,
                short_name=definition.short_name,
                category=definition.category,
                summary=definition.summary,
                status="planned",
                status_label=STATUS_LABELS["planned"],
                pack_name=None,
                pack_version_id=None,
                pack_version=None,
                enabled=False,
                binding_status=None,
                functions=definition.functions,
            )

        candidates = pack_index.get(definition.pack_name, [])
        selected = self._select_pack_version(candidates)
        if selected is None:
            return BusinessWorkSummary(
                work_key=definition.key,
                name=definition.name,
                short_name=definition.short_name,
                category=definition.category,
                summary=definition.summary,
                status="not_configured",
                status_label=STATUS_LABELS["not_configured"],
                pack_name=definition.pack_name,
                pack_version_id=None,
                pack_version=None,
                enabled=False,
                binding_status=None,
                blockers=(
                    BusinessWorkBlocker(
                        code="EXECUTION_DEFINITION_MISSING",
                        message="尚未配置对应的内部执行定义。",
                    ),
                ),
                functions=definition.functions,
            )

        _, version, binding = selected
        manifest = CapabilityPackManifest.model_validate(version.manifest)
        enabled = binding is not None and binding.status in {"ENABLED", "DEGRADED"}
        binding_status = binding.status if binding is not None else None
        configuration = dict(binding.configuration) if binding is not None else {}
        dependency_blockers = await self._capability_packs.blockers_for_version(
            tenant_id=tenant_id,
            project_id=project_id,
            version=version,
            session=session,
        )
        document_blockers = await self._document_blockers(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            pack_name=definition.pack_name,
            manifest=manifest,
        )
        blockers = tuple(
            [
                *(
                    BusinessWorkBlocker(
                        code=str(item.get("reasons", ["DEPENDENCY_NOT_READY"])[0]),
                        message=self._blocker_message(item),
                        ref=str(item.get("ref")) if item.get("ref") is not None else None,
                    )
                    for item in dependency_blockers
                ),
                *document_blockers,
            ]
        )
        status = self._compute_status(
            enabled=enabled,
            binding_status=binding_status,
            has_binding=binding is not None,
            blockers=blockers,
        )
        models = self._models_from_manifest(manifest)
        (
            bound_strategy_version_id,
            bound_strategy_name,
            bound_strategy_version,
        ) = await self._resolve_bound_strategy(
            session,
            tenant_id=tenant_id,
            version=version,
        )
        return BusinessWorkSummary(
            work_key=definition.key,
            name=definition.name,
            short_name=definition.short_name,
            category=definition.category,
            summary=definition.summary,
            status=status,
            status_label=STATUS_LABELS[status],
            pack_name=definition.pack_name,
            pack_version_id=version.id,
            pack_version=version.version,
            enabled=enabled,
            binding_status=binding_status,
            blockers=blockers,
            agents=tuple(manifest.spec.agents),
            tools=tuple(manifest.spec.tools),
            models=models,
            document_requirements=tuple(
                {
                    "key": item.key or item.category,
                    "category": item.category,
                    "displayName": item.display_name or item.category,
                    "description": item.description or "",
                    "required": item.required,
                    "minCount": item.min_count,
                    "maxCount": item.max_count,
                    "acceptedMediaTypes": list(item.accepted_media_types),
                    "classificationLabels": list(item.classification_labels or (item.category,)),
                    "processingProfile": item.processing_profile
                    or manifest.spec.document_processing_profile(),
                    "extractionSchema": item.extraction_schema,
                }
                for item in manifest.spec.document_requirements()
            ),
            decision_slots=tuple(
                {
                    "slot": item.slot,
                    "required": item.required,
                    "inputSchema": item.input_schema,
                    "outputSchema": item.output_schema,
                    "allowedTypes": list(item.allowed_types),
                }
                for item in manifest.spec.decisions
            ),
            functions=definition.functions,
            configuration=configuration,
            work_item_type=manifest.case_type,
            case_based=manifest.spec.case is not None,
            bound_strategy_version_id=bound_strategy_version_id,
            bound_strategy_name=bound_strategy_name,
            bound_strategy_version=bound_strategy_version,
        )

    async def _document_blockers(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        pack_name: str,
        manifest: CapabilityPackManifest,
    ) -> tuple[BusinessWorkBlocker, ...]:
        required = [item for item in manifest.spec.document_requirements() if item.required]
        if not required:
            return ()
        document_versions = await self._documents.current_versions_for_work(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            business_work_keys=document_binding_keys(pack_name, manifest.case_type),
        )
        counts: dict[str, int] = {}
        for document, _, _ in document_versions:
            counts[document.category] = counts.get(document.category, 0) + 1
        blockers: list[BusinessWorkBlocker] = []
        for item in required:
            actual = counts.get(item.category, 0)
            if actual < item.min_count:
                blockers.append(
                    BusinessWorkBlocker(
                        code="DOCUMENT_BINDING_MISSING",
                        message=(
                            f"资料分类 {item.category} 需要至少 {item.min_count} 份，"
                            f"当前 {actual} 份。"
                        ),
                        ref=item.category,
                    )
                )
        return tuple(blockers)

    @staticmethod
    def _select_pack_version(
        candidates: list[
            tuple[CapabilityPack, CapabilityPackVersion, ProjectCapabilityBinding | None]
        ],
    ) -> tuple[CapabilityPack, CapabilityPackVersion, ProjectCapabilityBinding | None] | None:
        if not candidates:
            return None

        def sort_key(
            row: tuple[CapabilityPack, CapabilityPackVersion, ProjectCapabilityBinding | None],
        ) -> tuple[int, str]:
            _, version, binding = row
            enabled = 1 if binding is not None and binding.status in {"ENABLED", "DEGRADED"} else 0
            return (enabled, version.version)

        return sorted(candidates, key=sort_key, reverse=True)[0]

    @staticmethod
    def _select_pack_template(
        candidates: list[
            tuple[CapabilityPack, CapabilityPackVersion, ProjectCapabilityBinding | None]
        ],
    ) -> tuple[CapabilityPack, CapabilityPackVersion, ProjectCapabilityBinding | None] | None:
        """Prefer pack versions that still declare document requirements.

        Strategy binding must not inherit an older resource-plane template that
        dropped ``spec.documents``, or assessments fail input schema minItems.
        """
        if not candidates:
            return None

        def sort_key(
            row: tuple[CapabilityPack, CapabilityPackVersion, ProjectCapabilityBinding | None],
        ) -> tuple[int, str]:
            _, version, _ = row
            spec = version.manifest.get("spec") if isinstance(version.manifest, dict) else None
            documents = spec.get("documents") if isinstance(spec, dict) else None
            if isinstance(documents, dict):
                requirements = documents.get("requirements")
                has_documents = 1 if isinstance(requirements, list) and len(requirements) > 0 else 0
            else:
                has_documents = 1 if isinstance(documents, list) and len(documents) > 0 else 0
            return (has_documents, version.version)

        return sorted(candidates, key=sort_key, reverse=True)[0]

    @staticmethod
    def _compute_status(
        *,
        enabled: bool,
        binding_status: str | None,
        has_binding: bool,
        blockers: tuple[BusinessWorkBlocker, ...],
    ) -> BusinessWorkStatus:
        if not has_binding:
            return "not_configured"
        if binding_status == "DISABLED":
            return "unavailable"
        if binding_status == "DEGRADED" or not enabled:
            return "unavailable"
        if blockers:
            return "incomplete"
        return "runnable"

    @staticmethod
    def _models_from_manifest(manifest: CapabilityPackManifest) -> tuple[str, ...]:
        raw = getattr(manifest.spec, "models", None)
        if raw is None:
            return ()
        if isinstance(raw, list | tuple):
            return tuple(str(item) for item in raw)
        return ()

    @staticmethod
    def _blocker_message(item: dict[str, Any]) -> str:
        ref = str(item.get("ref", "dependency"))
        reasons = item.get("reasons") or ["DEPENDENCY_NOT_READY"]
        reason = str(reasons[0])
        labels = {
            "DEPENDENCY_NOT_READY": f"{ref} 尚未就绪",
            "DECISION_BINDING_MISSING": f"决策槽位 {ref} 尚未绑定",
            "RESOURCE_BINDING_MISSING": f"资源槽位 {ref} 尚未绑定",
        }
        return labels.get(reason, f"{ref}：{reason}")

    @staticmethod
    def _require_runnable(summary: BusinessWorkSummary) -> None:
        if summary.status == "planned":
            raise ValueError("BUSINESS_WORK_PLANNED")
        if summary.status == "not_configured":
            raise ValueError("BUSINESS_WORK_NOT_CONFIGURED")
        if summary.status == "unavailable":
            raise ValueError("BUSINESS_WORK_UNAVAILABLE")
        if summary.status != "runnable":
            raise ValueError("BUSINESS_WORK_NOT_READY")

    @staticmethod
    def _strategy_binding_from_version(
        version: CapabilityPackVersion,
    ) -> tuple[UUID | None, int | None]:
        strategy_meta = version.dependency_snapshot.get("strategy")
        if not isinstance(strategy_meta, dict):
            return None, None
        raw_id = strategy_meta.get("strategyVersionId")
        if not isinstance(raw_id, str) or not raw_id:
            return None, None
        try:
            strategy_version_id = UUID(raw_id)
        except ValueError:
            return None, None
        ref = strategy_meta.get("ref")
        version_number: int | None = None
        if isinstance(ref, str) and "@" in ref:
            suffix = ref.rsplit("@", 1)[-1]
            if suffix.isdigit():
                version_number = int(suffix)
        return strategy_version_id, version_number

    async def _resolve_bound_strategy(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        version: CapabilityPackVersion,
    ) -> tuple[UUID | None, str | None, int | None]:
        strategy_version_id, version_number = self._strategy_binding_from_version(version)
        if strategy_version_id is None:
            return None, None, None
        row = await session.execute(
            select(StrategyVersion, Strategy)
            .join(Strategy, Strategy.id == StrategyVersion.strategy_id)
            .where(
                StrategyVersion.id == strategy_version_id,
                StrategyVersion.tenant_id == tenant_id,
            )
        )
        selected = row.one_or_none()
        if selected is None:
            return strategy_version_id, None, version_number
        strategy_version, strategy = selected
        return strategy_version_id, strategy.name, int(strategy_version.version)

    @staticmethod
    def _next_pack_version(existing: list[str]) -> str:
        best = (0, 0, 0)
        for value in existing:
            parts = value.split(".")
            if len(parts) != 3 or not all(part.isdigit() for part in parts):
                continue
            candidate = (int(parts[0]), int(parts[1]), int(parts[2]))
            if candidate > best:
                best = candidate
        return f"{best[0]}.{best[1]}.{best[2] + 1}"

    @staticmethod
    def _manifest_for_strategy(
        *,
        template: dict[str, Any],
        pack_name: str,
        pack_version: str,
        strategy_id: UUID,
        strategy_version_number: int,
        agents: list[str],
        tools: list[str],
    ) -> dict[str, Any]:
        manifest = deepcopy(template)
        metadata = manifest.get("metadata")
        if not isinstance(metadata, dict):
            metadata = {}
            manifest["metadata"] = metadata
        metadata["name"] = pack_name
        metadata["version"] = pack_version
        spec = manifest.get("spec")
        if not isinstance(spec, dict):
            spec = {}
            manifest["spec"] = spec
        spec["strategies"] = {
            "execute": f"strategy://project/{strategy_id}@{strategy_version_number}"
        }
        spec["agents"] = agents
        spec["tools"] = tools
        return manifest
