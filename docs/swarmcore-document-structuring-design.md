# 智能体业务开发功能设计文档

## 1. 需求概述

### 1.1 业务目标

建设“文件结构化”业务工作：用户上传一批真实业务文件后，系统自动识别格式，完成原生解析或 OCR、版面与表格提取、语义切片、业务字段抽取、自动归类和质量校验；不确定项进入人工确认，最终形成可下载、可检索、可被后续业务工作冻结引用的结构化资料包。

该能力属于 SwarmCore 共享 Document Intelligence，不理解上游调用方的业务目标，不替代合同、财务或合规判断。

### 1.2 目标用户

- 资料专员：批量上传和整理合同、报告、表格及扫描件。
- 业务审核员：确认分类、关键字段、表格和低置信 OCR 结果。
- 项目管理员：配置处理 Profile、Schema、模型路由、权限和预算。
- 审计员：查看原件、处理步骤、工具调用、人工改动和结果版本。
- 下游业务工作：只读取已确认或满足质量门的结构化结果及冻结证据。

### 1.3 输入

- ODF：ODT、ODS、ODP。
- 常用办公格式：PDF、DOCX、XLSX、PPTX、TXT、Markdown、CSV、JSON。
- 扫描件：PNG、JPEG、TIFF、图像型 PDF。
- 上传时上下文：tenant、project、业务对象、业务工作、候选分类、抽取 Schema、保留期。

### 1.4 输出

`StructuredDocumentPackage` 至少包含：

- 文件真实类型、原始文件名、SHA-256、版本和处理状态；
- 文档分类、语言、标题、章节树、页、段落和阅读顺序；
- 表格、工作表及单元格坐标；
- 按标题、段落和表格边界生成的 Chunk；
- Schema 驱动的字段、实体、关系和质量标记；
- 每个结果对应的页码、坐标、原文片段和证据哈希；
- 机器值、人工确认值、处理版本及完整 provenance；
- JSON 主结果、Markdown 正文、表格 CSV 和证据清单 Artifact。

### 1.5 成功定义

使用公开、合法、可重复下载的真实业务文档，完成“真实文件获取 → 上传 → 安全扫描 → 格式路由 → 解析/OCR → Agent 抽取与整理 → 工具校验 → 人工确认 → 结构化结果发布”，页面可看到每一步状态、耗时、依据和版本；任何关键结果都能定位回原件页或 ODF/OOXML 结构。

## 2. 自主决策与关键假设

| 决策或假设 | 依据 | 影响 | 验证方式 |
|---|---|---|---|
| Demo 聚焦“公共采购合同资料结构化” | 合同同时包含长正文、章节、表格、占位字段和多格式发布，能覆盖主能力 | 不扩展到具体合同合规结论 | 使用同一份官方合同的 ODT、DOCX、PDF 三种原件运行 |
| `ODF` 按 OASIS OpenDocument 理解 | ODF 包括文本、表格、演示文稿；不是中国电子文件 OFD | P0 支持 ODT/ODS/ODP；OFD 单列为暂不实现 | 用 OASIS ODF 1.3 文档和官方 ODT 输入验证 |
| Demo 面向中英文企业资料 | SwarmCore 业务场景以中文界面为主，真实样例为英文 | OCR 和 NLP 必须支持中英文，结果 Schema 使用稳定英文键和中文展示名 | 英文官方样例通过；中文使用已授权业务样本做实施资格评测 |
| “大文件”定义为满足任一条件：≥50 页、≥25 MiB、表格 ≥100,000 行 | 便于稳定触发分段处理，避免只按文件字节判断 | 68 页官方 PDF 会进入大文件路径 | 运行记录出现页组切分、并行度和分片重试 |
| 原生结构优先，OCR 只处理无文本或低质量页面 | 原生 XML/文本通常比 OCR 更准确且成本更低 | ODT/DOCX 不做整页 OCR；混合 PDF 可逐页路由 | 过程页显示每页 `NATIVE` 或 `OCR` 决策及原因 |
| 采用单智能体，解析和写入由显式 Tool/Activity 完成 | 分类与 Schema 抽取需要语义能力；格式识别、分片、校验和持久化应确定性执行 | 不建立多智能体聊天或投票 | Execution Plan 只有一个 Agent 节点，副作用均为显式 Tool 节点 |
| Demo 不伪造模型或 OCR 成功 | 验收要求真实处理和真实工具调用 | Provider 未配置时运行停在 `BLOCKED_PROVIDER`，不能回退到静态结果 | 检查 Provider trace、模型版本、token/耗时和真实 OCR 响应 |
| 现有业务资料库和处理契约继续作为事实源 | 本地代码已有 BusinessDocument、Version、ProcessingRun、Result、上传批次、复核接口 | 只补充 ODF、大文件、Chunk、表格和真实 Provider 链，不另建存储 | REST/MCP 复用同一应用服务；数据库只保存摘要，大结果写 Artifact |
| 当前实现不等于本设计已完成 | 截至 2026-07-28，本地代码已有基础 TXT/PDF/DOCX/XLSX/CSV/JSON 解析和 HTTP OCR Adapter，但未形成 ODF、高保真版面表格、大文件异步分片和真实模型资格闭环 | 本文是待开发设计，不标记 IMPLEMENTED 或 VERIFIED | 实施后按第 17 节验收并更新开发计划 |

## 3. Demo 范围

### 3.1 范围内

- 单批最多 20 个文件、合计不超过 1 GiB；单文件最多 200 MiB、PDF 最多 500 页、电子表格最多 500,000 行。
- 基于内容签名、MIME、扩展名和容器结构的格式检测及冲突告警。
- ODT/ODS/ODP 原生 XML 解析；DOCX/XLSX/PPTX、PDF、文本、表格和图片解析。
- 数字 PDF 原生文本优先；无文本、乱码、低覆盖率或图像页按页 OCR。
- 标题层级、段落、列表、页、表格、工作表、图片区域和阅读顺序恢复。
- 结构感知切片：目标 800–1,200 tokens，硬上限 1,600，文本块重叠 100 tokens；表格不按普通文本边界截断。
- 文档分类、合同通用字段抽取、占位值识别、跨格式一致性检查。
- 低置信结果人工确认，机器值不可覆盖。
- JSON、Markdown、CSV、证据清单 Artifact 发布及处理过程展示。
- REST 与 MCP 复用同一 DocumentProcessingService。

### 3.2 Demo 边界

- 仅管理用户上传文件及其业务绑定，不连接 ERP、邮箱、网盘或外部业务数据库。
- 不从互联网自动抓取客户文件；Demo 准备脚本只下载明确列出的公开样例。
- Agent 不执行文件、宏、嵌入脚本或外部链接。
- 不产生合同有效性、法律责任、付款或合规结论。

### 3.3 Demo 约束

- 所有文件先写 staging，校验 SHA-256、大小、MIME 和恶意内容后才能提交。
- Temporal Workflow 只传 Blob/Artifact 引用和小型 JSON；单个 Activity 内联结果不超过 256 KiB。
- 解析器、OCR、模型、Prompt、Schema 和 Tool 都必须版本化。
- 真实 Provider 不可用时允许“原生解析 + 人工整理”降级，但必须明确标记 `DEGRADED`，不得冒充 AI 处理完成。

## 4. 业务角色

| 角色 | 职责 | 最小权限 | 目标 |
|---|---|---|---|
| 资料专员 | 创建上传批次、绑定业务对象、启动或重试处理 | `document.create/read/process` | 快速得到可用结构化资料 |
| 审核员 | 查看证据、确认分类和字段、纠正表格或要求重跑 | `document.read/review` | 消除不确定项并保留改动依据 |
| 项目管理员 | 发布 Profile/Schema，绑定模型和 OCR Provider，设置预算 | `document.configure`, `provider.bind` | 控制能力、成本和数据边界 |
| 审计员 | 只读原件版本、处理事件、工具调用、结果和确认记录 | `document.audit` | 重建任一结果的形成过程 |
| 下游业务工作 | 读取冻结的 READY 结果与证据 | Capability Token：`document.read` | 避免重复解析并使用稳定版本 |
| 系统运维 | 查看基础设施健康和失败队列，不读取业务正文 | `runtime.operate`，正文默认脱敏 | 恢复服务但不扩大数据访问 |

## 5. 最小完整业务闭环

1. 资料专员创建上传批次并选择 `document-profile://business-structuring@1`。
2. 客户端计算 SHA-256，调用上传初始化接口，使用短期 Capability Token 上传原件。
3. 系统复算哈希、检测真实格式、检查扩展名冲突，并调用 ClamAV 扫描。
4. 扫描通过后创建不可变 BusinessDocumentVersion；失败文件隔离并终止。
5. 调度器读取页数、文件大小、表格规模，选择普通或大文件路径。
6. 原生解析 Tool 提取 ODF/OOXML/XML/PDF 结构；PDF 逐页计算文本覆盖率和可读性。
7. 需要 OCR 的页渲染为 200–300 DPI 图片，调用版面 OCR Tool；数字页不重复 OCR。
8. 合并 Tool 统一原生与 OCR 块，恢复页、坐标、标题层级、阅读顺序、表格和工作表。
9. 切片 Tool 按章节和表格边界生成 Chunk，并把大结果写入 Artifact。
10. 文件结构化 Agent 根据候选标签和版本化 Schema，完成分类、通用字段/实体抽取、占位值识别和自动归类。
11. 确定性质量 Tool 校验 JSON Schema、证据完整度、页范围、表格形状、跨格式关键字段一致性和预算。
12. 全部质量门通过时进入 `READY`；分类、关键字段、OCR 或表格低置信时进入 `REVIEW_REQUIRED`。
13. 审核员在原页/区域和机器值旁执行确认、纠正、重分类、排除页或重跑。
14. 系统追加新 ProcessingResult 版本，保留 machineValue、confirmedValue、操作者、时间和意见。
15. 发布 Tool 生成结构化 JSON、Markdown、表格 CSV 和 evidence manifest；下游业务工作冻结所用结果版本。

完成条件：结果状态为 `READY`，所有必需字段为 `AUTO_ACCEPTED` 或 `CONFIRMED/CORRECTED`，Artifact 可下载，且每项关键结果至少有一个可解析 Evidence 引用。取消、恶意文件、超限、不可解密或人工拒绝均为有说明的终止状态。

## 6. 功能清单

| 优先级 | 功能 | 使用者 | 输入与处理 | 输出 | 依赖 |
|---|---|---|---|---|---|
| P0 必需 | 批量上传与不可变版本 | 资料专员 | 文件、哈希、业务绑定、幂等键 | Blob、DocumentVersion、UploadBatch | Artifact Gateway、PostgreSQL |
| P0 必需 | 安全扫描与真实类型检测 | 系统 | 文件流；扫描、Magic/MIME/容器核验 | CLEAN/REJECTED、detectedMediaType | ClamAV、Tika/文件签名 |
| P0 必需 | 多格式自适应路由 | 系统 | 文件特征、Profile | 解析器选择及依据 | Parser Registry |
| P0 必需 | ODF 原生解析 | 系统 | ODT/ODS/ODP ZIP/XML | 段落、标题、表格、工作表、元数据 | ODF Adapter |
| P0 必需 | 大文件分片 | 系统 | 页数、大小、行数 | 页组/工作表任务、进度、分片重试 | Temporal、Artifact |
| P0 必需 | 混合 PDF 与 OCR | 系统 | 页文本密度、图片 | OCR 块、坐标、置信度、页路由 | PDF Renderer、PaddleOCR |
| P0 必需 | 表格提取 | 系统 | 原生 XML 或版面区域 | 网格、合并单元格、页/坐标、CSV | Native Parser、PP-StructureV3 |
| P0 必需 | 结构感知切片 | 系统 | 章节树、段落、表格 | Chunk[]、稳定 chunkId、证据范围 | Tokenizer、Artifact |
| P0 必需 | NLP 分类与抽取 | Agent | Chunk、候选标签、JSON Schema | 类型、字段、实体、占位标记 | Model Gateway |
| P0 必需 | 自动整理 | Agent/系统 | 分类、业务对象、质量结果 | 分类目录、标签、建议名称 | Document Library |
| P0 必需 | 质量门与人工确认 | 审核员 | 机器值、置信度、Evidence | 确认/纠正版本、审计事件 | Review Service |
| P0 必需 | 结果与过程展示 | 全部角色 | 状态、事件、结果版本 | 时间线、原页定位、Artifact 下载 | Web、REST/MCP |
| P1 | 重复/近重复文件识别 | 资料专员 | 哈希和内容指纹 | 重复组、版本建议 | 指纹或 Embedding |
| P1 | 自定义 Schema 设计器 | 管理员 | 字段、类型、必需性、阈值 | 发布的不可变 Schema | Registry |
| P1 | 中文专项质量集 | 管理员 | 已授权、脱敏样本 | OCR/字段/表格指标 | Quality Evaluation |

## 7. 真实数据与资料方案

### 7.1 Demo 业务资料

以下公开样例已于 2026-07-28 实际下载并核验哈希。发布页说明该合同用于公共部门买方与供应商之间的采购，并同时提供 ODT、DOCX 和 68 页 PDF；页面内容适用 Open Government Licence v3.0，但已在 2024-08-08 因框架过期而撤回，因此只用于可重复的文档处理演示，不代表当前有效采购条款。[GOV.UK 发布页](https://www.gov.uk/government/publications/digital-outcomes-and-specialists-4-call-off-contract)

| 用途 | 具体来源及访问地址 | 真实数据证明 | 接入与权限 | 关键内容 | 更新、缓存与替代 | 合规要求 |
|---|---|---|---|---|---|---|
| ODF 主样例 | [官方 ODT 原件](https://assets.publishing.service.gov.uk/media/5f6a40e9d3bf7f7239aa1482/dos-4-call-off-contract.odt) | 94,899 bytes；SHA-256 `022e406c0d3f5ed3dc7968dcf8bb0e98b5665b0aaff8e7772a15b56688ad024d`；原生 XML 含 83 个标题、1,578 个段落、21 个表格 | 公网只读，无认证；准备脚本下载后上传 SwarmCore | 合同标题、RM1043.6、Part A/B/C、条款、表格、占位字段 | 静态归档；按哈希永久缓存；失效时从发布页人工下载 | 保留来源、访问日和 OGL 署名；不得暗示官方背书 |
| OOXML 对照样例 | [官方 DOCX 原件](https://assets.publishing.service.gov.uk/media/5d8de734e5274a2fab26b261/dos-4-call-off-contract.docx) | 195,679 bytes；SHA-256 `d95290ad5badf1bd6a7ddfb5bf12f4292ee28f651101bb769d544e6da3963bb5`；原生 XML 含 1,618 个段落、22 个表格 | 同上 | 与 ODT 同一业务文档的格式对照 | 同上 | 同上 |
| 长 PDF 与表格样例 | [官方 68 页 PDF](https://assets.publishing.service.gov.uk/media/5d8de7a5ed915d556c95a09e/dos-4-call-off-contract.pdf) | 901,706 bytes；SHA-256 `50a497b74e379cc1e6f13965636a6c58128901410ebe6c3070a3c2d5d5a10c66`；68 页、可提取文本约 143,929 字符 | 同上 | 触发 ≥50 页大文件路径；提供页级 Evidence | 同上 | 同上 |
| OCR 样例 | 从上述 PDF 第 4–7 页以固定 renderer 版本、300 DPI、灰度、无文本层方式生成 PDF | 内容来自真实官方原件；派生 manifest 保存源 SHA-256、页范围、命令参数、renderer 版本和派生 SHA-256 | Demo 准备步骤本地生成，不从第三方样例站下载 | 表单、表格、合同引用和占位字段 | 每次以相同容器镜像生成；派生哈希不一致则阻断基线比较 | 明确标记 `real-derived-ocr-fixture`，不得称为原始扫描件 |
| 企业真实输入 | 客户在业务资料库上传的已授权合同、报表和扫描件 | 原件来自客户业务流程，上传者声明权限；Blob 保存哈希和版本 | 登录、tenant/project、最小权限；不通过公网采集 | 中文字段、印章、真实填写值 | 按客户保留策略；Demo 无授权资料时不替代为伪造数据 | 不进入仓库；敏感数据不用于训练；演示前脱敏并取得授权 |

### 7.2 标准、组件与评测资料

| 用途 | 具体来源 | 作用 | 更新与失败替代 | 合规限制 |
|---|---|---|---|---|
| ODF 结构事实 | [OASIS OpenDocument 1.3 标准及 ODT/PDF 版本](https://docs.oasis-open.org/office/OpenDocument/v1.3/) | 确定 package、content.xml、styles、表格和演示文稿的解析边界；目录同时提供 23 MiB PDF，可作非业务压力样例 | 锁定 1.3；实现升级先跑兼容集 | 仅作标准与技术验证，不冒充业务输入 |
| 多格式覆盖依据 | [Apache Tika 支持格式](https://tika.apache.org/3.0.0/formats.html) | Tika 官方列出 ODF、OOXML、PDF 等解析支持；用于类型检测和宽格式 fallback | 锁定容器镜像；单格式高保真解析器优先 | Tika 运行在无网络、只读、受限沙箱 |
| OCR/版面/表格能力 | [PaddleOCR PP-StructureV3](https://www.paddleocr.ai/main/en/version3.x/algorithm/PP-StructureV3/PP-StructureV3.html) | 官方说明支持版面、表格、公式、阅读顺序和 Markdown 恢复 | 资格评测不达标时切换经批准的托管 OCR 或人工 | 模型权重和镜像许可证单独登记 |
| 多语言 OCR | [PP-OCRv5 多语言说明](https://www.paddleocr.ai/latest/en/version3.x/algorithm/PP-OCRv5/PP-OCRv5_multi_languages.html) | 覆盖中英文和多语言识别，作为 OCR 路由依据 | Demo 只启用中英文模型，避免无用模型加载 | 仅记录必要页图，不保留 Provider 调试副本 |
| 恶意文件扫描 | [ClamAV clamd 协议](https://docs.clamav.net/manual/Usage/ClamdProtocol.html) | 使用 INSTREAM 扫描文件流；官方说明流大小受 StreamMaxLength 限制且 TCP 无认证 | 配置上限 ≥单文件上限；超限分块/本地 socket，扫描不可用则阻断 | clamd 只暴露集群内 socket，不暴露公网 |
| 公开资料许可 | [Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/) | 允许在署名等条件下复制、改编和再利用公开资料 | 缓存许可文本与访问日 | 输出附来源和许可链接，不使用徽标暗示背书 |

## 8. 模型配置

| 逻辑模型 | 为什么需要 | 物理候选或能力要求 | 输入与输出 | 关键参数与约束 | 成本与降级 |
|---|---|---|---|---|---|
| `model://document-layout-ocr@1` | 扫描页需要文字、版面、阅读顺序和表格网格 | 默认本地 PP-StructureV3 + PP-OCRv5 中英文服务；必须通过项目资格评测 | 页图/PDF 页 → blocks、text、bbox、tableCells、confidence、orientation | 200–300 DPI；自动方向；中英文；启用表格，默认关闭公式/图表语义；每批 10 页 | GPU 按页计量；超预算只处理必需页；Provider 失败转经批准 OCR 或人工 |
| `model://document-nlp@1` | 规则无法稳定完成开放文档分类、字段语义映射、实体与占位识别 | 绑定项目内真实、已资格验证的中英文文本模型；要求严格 JSON Schema、≥32k 上下文、稳定结构化输出；不硬编码供应商 | Chunk + Schema + Evidence → classification、fields、entities、qualityFlags | `temperature=0`；每次最多 8 个 Chunk；禁止无 Evidence 值；Prompt 与 Schema 版本冻结；每文档最多 2 次修复调用 | 按 token 设预算；失败先缩小 Chunk 重试 1 次，再进入人工；不使用静态假结果 |

模型输出统一遵循：

```json
{
  "data": {},
  "evidence": [],
  "confidence": 0.0,
  "qualityFlags": [],
  "schemaVersion": "",
  "provenance": {
    "logicalModel": "",
    "physicalModel": "",
    "provider": "",
    "promptVersion": "",
    "requestHash": ""
  }
}
```

置信度不得直接采用模型自报概率。运行时置信度由离线样本校准结果、Evidence 完整度、解析器一致性和确定性规则共同计算。Demo 初始阈值是待实施验证值：分类自动接受 ≥0.90，普通字段 ≥0.85，关键字段 ≥0.95；未校准前关键字段必须人工确认。

## 9. 工具配置

| Tool | 能力与调用时机 | 接口摘要 | 权限与风险 | 超时、幂等 | 失败回退 |
|---|---|---|---|---|---|
| `tool://document/scan@1` | 上传完成后恶意内容扫描 | Blob stream → verdict、signatureVersion | `blob.read`；LOW；集群内 ClamAV | 120s；`sha256+signatureVersion` | 不可用或超限即阻断，不跳过 |
| `tool://document/detect@1` | 扫描通过后识别真实格式和容器 | bytes head/container → detectedMediaType、conflicts | `blob.read`；LOW | 30s；`sha256+detectorVersion` | Tika 失败用文件签名最小检测；仍未知则人工/拒绝 |
| `tool://document/parse-native@2` | ODF/OOXML/PDF/文本原生解析 | BlobRef、page/sheet range → ParsedContentRef | `blob.read/artifact.write`；MEDIUM；沙箱无网络 | 普通 120s；大文件每分片 180s；`sha256+range+parserVersion` | 单格式 Adapter → Tika fallback → OCR/人工 |
| `tool://document/render-pages@1` | 需要 OCR 时渲染指定页 | PDF/office ref、pages、dpi → imageRefs | `blob.read/artifact.write`；MEDIUM | 每 10 页 120s；页哈希幂等 | 降 DPI 至 200；仍失败则标记不可读页 |
| `tool://document/ocr-layout@1` | 对无文本或低质量页 OCR 与表格识别 | imageRefs → blocks、tables、quality | Provider Capability Token；MEDIUM | 每 10 页 300s；最多 2 次；`pageHash+ocrVersion` | 备用 OCR；否则 REVIEW_REQUIRED |
| `tool://document/merge-layout@1` | 合并原生与 OCR 结果、恢复阅读顺序 | page artifacts → normalized layout artifact | 无外部权限；LOW | 120s；输入 Artifact hash 幂等 | 保存已完成页并提示缺失页 |
| `tool://document/chunk@1` | 布局合并后确定性切片 | section tree、paragraphs、tables → Chunk[] | 无外部权限；LOW | 60s；`layoutHash+chunkerVersion` | 简化为按页切片并标记 DEGRADED |
| `tool://document/extract-schema@1` | Agent 节点调用模型分类和抽取 | ChunkRefs、SchemaRef → structured candidates | `model.invoke`；MEDIUM；只读 | 60s/调用；请求哈希幂等；每文档 2 次修复 | 缩小上下文重试；人工填写 |
| `tool://document/quality-check@1` | 抽取后做 Schema、证据、表格、跨格式校验 | package candidate → gates、flags、reviewItems | 无外部权限；LOW | 60s；结果哈希幂等 | 质量 Tool 失败不能 READY |
| `tool://document/publish@1` | 质量通过或人工确认后发布 Artifact 和结果版本 | confirmed package → JSON/MD/CSV/evidence artifacts | `artifact.write`, `document.result.append`；HIGH | 120s；EffectJournal；`resultHash` | 重试后人工运维；禁止重复写 |
| `tool://document/read-versions@1` | 下游业务工作只读冻结文档与处理结果 | DocumentUsageSnapshot[] → refs/metadata | 短期 Capability Token；LOW | 120s；快照哈希幂等 | 版本缺失即阻断下游运行 |

所有 Tool 调用记录 `executionId`、`effectId`、输入/输出哈希、开始/结束时间、版本、状态、错误码和 Trace ID。Agent 内不得直接调用有副作用的 publish Tool。

## 10. 智能体设计

### `agent://document/structurer@1`

| 项目 | 设计 |
|---|---|
| 为什么需要 | 将已解析的开放文档内容映射到候选分类和版本化业务 Schema；处理同义词、占位文本和跨章节字段关系 |
| 职责 | 文档分类；抽取字段/实体；识别未填写占位符；提出自动目录、标签和文件名；给出 Evidence 和质量标记 |
| 模型 | `model://document-nlp@1` |
| 可用工具 | 只读 Chunk/Evidence 查询、`tool://document/extract-schema@1`；不拥有 Blob 写入、发布、删除或外部网络权限 |
| 上下文 | 文件元数据、候选分类、Schema、单个章节或相关 Chunk、页级 Evidence、处理 Profile；不注入其他租户资料 |
| 输入 | `DocumentStructuringRequest{documentVersionId, layoutArtifactRef, chunkRefs, candidateLabels, schemaRef}` |
| 输出 | `DocumentStructuringCandidate{classification, fields, entities, organization, evidence, qualityFlags}` |
| 禁止事项 | 不猜测缺失值；不把模板占位符当真实字段；不改变原文；不决定是否跳过扫描/OCR；不发布结果；不作法律、财务或合规判断 |

协作关系：Workflow 和确定性 Tool 负责“读、解析、切片、校验、写”；Agent 只负责“理解和提出结构化候选”；审核员负责不确定项的最终确认。无需第二个 Agent，独立质量检查由确定性 Tool 完成。

## 11. 运行与协作策略

### 11.1 编排步骤

`intake → scan → detect → plan → parse_native → [render → ocr] → merge → chunk → agent_extract → quality_check → [human_review] → publish`

- Temporal Workflow 只编排引用、状态和重试；网络、文件、数据库、模型和 OCR I/O 均在 Activity。
- 普通文件单路处理；大文件按 10 页或一个工作表分片，最大并行度 4。
- 相同 document version、Profile 和 Provider 版本命中成功结果时复用；重新处理创建新 ProcessingRun 和 Result 版本。
- 页分片独立持久化，单页组失败只重试该分片。
- 模型只接收与 Schema 字段相关的 Top-K Chunk，不发送整份 68 页正文。

### 11.2 状态流转

`PENDING → UPLOADING → SCANNING → PARSING → OCR_PROCESSING? → CLASSIFYING → EXTRACTING → QUALITY_CHECK → REVIEW_REQUIRED? → READY`

终态：`READY`、`FAILED`、`CANCELLED`。补充阻断原因使用 `errorCode`，例如 `BLOCKED_PROVIDER`、`UNSUPPORTED_FORMAT`、`PASSWORD_PROTECTED`，不增加伪终态。

### 11.3 持久化与结果大小

- PostgreSQL 保存 Document、Version、Run、Result 摘要、状态、版本和审计索引。
- 原件、页图、布局、Chunk、完整表格和最终资料包写 Artifact。
- 任一 Activity 结果超过 256 KiB 时只返回 ArtifactRef、hash、count 和 excerpt。
- ProcessingResult 只追加，不覆盖既有结果；机器值和确认值同时保留。

### 11.4 超时、重试、取消和预算

- 安全扫描不可降级；暂时故障指数退避 2 次，仍失败进入 FAILED。
- 原生解析每分片最多 2 次；OCR 每分片最多 2 次；模型一次正常调用加一次 JSON 修复。
- 文件总运行默认 30 分钟；大文件 90 分钟；人工等待不占运行超时。
- 取消后停止未开始分片，已完成 Artifact 保留到运行保留期，不发布 READY 结果。
- 默认每文档模型输入 120k tokens、输出 12k tokens；OCR 最多 500 页；超预算进入 REVIEW_REQUIRED，由管理员增加预算或缩小范围。
- 同一 tenant 最多 2 个大文件运行，同一项目页分片并发最多 4，避免单租户占满 Worker。

### 11.5 失败收口

- 可恢复：创建新 Run，记录 `parentRunId` 和已复用的成功分片。
- 不可恢复：给出失败页/文件、错误码、已完成比例和用户可执行动作。
- Workflow 终态前必须完成 PostgreSQL 投影和 Outbox 写入；Trace 或缓存不能作为最终事实源。

## 12. 人工介入机制

### 12.1 触发条件

- 分类校准置信度 <0.90 或前两名差值 <0.10。
- 关键字段置信度 <0.95、普通字段 <0.85，或 Evidence 缺失。
- 占位符、空白表单、多个冲突候选值。
- OCR 页平均置信度 <0.90、文本覆盖异常、方向不确定或表格网格破损。
- ODT/DOCX/PDF 同源样例的标题、合同引用或章节数量不一致。
- 表格列数不稳定、跨页表头无法确认、合并单元格歧义。
- 用户 Profile 明确要求“所有关键字段人工确认”。

### 12.2 审批界面

界面同时展示：

- 左侧原页或 ODF/OOXML 结构预览，Evidence 区域高亮；
- 右侧机器值、候选值、置信度、质量标记、Schema 约束；
- 解析器/OCR/模型/Prompt/Schema 版本和对应工具调用；
- 当前 Result 版本、并发版本冲突提示和人工意见框。

### 12.3 可选动作与恢复

- 确认机器值；
- 修改值并填写原因；
- 重分类并触发对应 Schema 重抽取；
- 标记“原件未填写/不适用/不可读”；
- 排除无关页或选择局部重跑 OCR；
- 退回资料专员补充清晰原件；
- 拒绝整份结果或取消处理。

确认操作携带 `expectedResultVersion`。版本冲突返回 409 并要求刷新；成功后追加新 Result 版本，重新执行质量检查，通过后发布。

## 13. 异常处理

| 异常 | 检测方式 | 用户提示 | 自动处置 | 人工处置 | 最终状态 |
|---|---|---|---|---|---|
| 哈希不一致/上传中断 | 服务端复算 SHA-256、Blob 状态 | 文件未完整上传 | 保留 staging，允许同 uploadId 恢复 | 重新上传 | UPLOADING 或 FAILED |
| 恶意文件 | ClamAV verdict | 文件被隔离，不可处理 | 禁止解析、记录签名版本 | 安全人员按流程处理，不在 UI 下载 | FAILED |
| 扩展名与内容冲突 | detect Tool | 显示声明/检测类型 | 使用检测类型但加高风险标记 | 审核或拒绝 | REVIEW_REQUIRED/FAILED |
| 不支持格式 | Parser Registry 无匹配 | 列出支持格式 | 不调用模型 | 转换后重新上传 | FAILED |
| 加密/密码保护 | 容器或 PDF 检测 | 需要无密码副本 | 不尝试破解 | 上传解密后的授权副本 | FAILED |
| ODF 容器损坏 | ZIP/XML/manifest 校验 | 文件结构损坏 | Tika fallback 一次 | 换原件 | REVIEW_REQUIRED/FAILED |
| 页面过多/文件超限 | Intake limits | 显示具体上限 | 不进入解析 | 拆分或管理员批准新 Profile | FAILED |
| OCR Provider 不可用 | 健康检查/调用错误 | OCR 暂不可用 | 两次重试、备用 Provider | 稍后重跑或人工录入 | REVIEW_REQUIRED/FAILED |
| 模型输出不符合 Schema | JSON Schema 校验 | AI 结果需人工处理 | 缩小上下文并修复一次 | 人工填写 | REVIEW_REQUIRED |
| 表格跨页合并失败 | 列/表头一致性检查 | 高亮相关页 | 保留独立页表格 | 人工合并/确认 | REVIEW_REQUIRED |
| 单分片超时 | Activity heartbeat | 显示失败页组 | 仅重试该页组 | 排除页组或取消 | RUNNING/FAILED |
| 人工版本冲突 | expectedResultVersion | 结果已被他人更新 | 不覆盖 | 刷新后重新确认 | REVIEW_REQUIRED |
| Artifact 发布失败 | EffectJournal/对象存储错误 | 结果已确认但发布失败 | 幂等重试 | 运维恢复 | FAILED，不返回 READY |
| 租户越权 | RLS、Capability Token 校验 | 无权限 | 拒绝并审计 | 管理员检查授权 | 403，不改变运行 |

## 14. 权限与结果追溯

### 14.1 身份、权限与隔离

- 所有查询和写入同时限定 tenant_id、project_id；PostgreSQL RLS 作为第二道边界。
- Blob/Artifact 通过短期、动作级 Capability Token 访问；Token 限定 subject、blob/artifact、动作和到期时间。
- OCR 和模型凭据仅由 Secret Manager 注入 Provider Adapter，不进入 Prompt、Manifest、日志或前端。
- Parser/OCR Worker 无公网出口；只有 Model Gateway/OCR Adapter 可访问已批准 Provider。
- 运维日志默认只记录哈希、计数和错误码，不记录正文。

### 14.2 审计事件

至少记录：

`document.upload.initiated`、`document.upload.completed`、`document.scan.completed`、`document.type.detected`、`document.processing.started`、`document.page-batch.completed`、`document.ocr.completed`、`document.agent.completed`、`document.quality.checked`、`document.review.decided`、`document.result.published`、`document.processing.failed`、`document.processing.cancelled`。

每个事件包含 actor、tenant/project、document/version/run/result、eventSeq、requestId、Trace ID、输入/输出哈希、能力版本和时间。

### 14.3 Evidence 与版本

Evidence 最少包含：

```json
{
  "documentVersionId": "uuid",
  "blobSha256": "hex",
  "page": 4,
  "bbox": [0.10, 0.20, 0.80, 0.28],
  "text": "Call-Off Contract Ref.",
  "textSha256": "hex",
  "sourceKind": "NATIVE|OCR",
  "producerRef": "parser://...|ocr://...",
  "artifactRef": "artifact://..."
}
```

原件版本、处理 Profile、Parser、OCR、模型、Prompt、Schema、Chunker、Tool 和人工确认版本均冻结。Demo 私有资料默认保留 30 天，审计默认 365 天；实际部署由租户策略配置，法定保留优先。公开 Demo 原件可按哈希长期缓存并附 OGL 署名。

## 15. 核心数据结构与接口

### 15.1 核心实体

| 实体 | 关键字段 |
|---|---|
| `BusinessDocument` | `id, tenantId, projectId, name, category, tags, status, currentVersion` |
| `BusinessDocumentVersion` | `id, documentId, blobId, version, filename, mediaType, sizeBytes, sha256, processingStatus` |
| `UploadBatch` | `id, source, context, status, fileCount, succeededCount, failedCount` |
| `DocumentProcessingRun` | `id, documentVersionId, profileRef, status, currentStage, attempt, parserRef, classifierRef, extractorRefs, provenance, errorCode` |
| `DocumentProcessingResult` | `id, runId, resultVersion, status, schemaRef, producerRef, result, evidence, confirmedBy, confirmedAt` |
| `StructuredDocumentPackage` | `document, classification, sections, pagesRef, chunksRef, tablesRef, extractions, organization, quality, evidenceManifestRef, provenance` |
| `Page` | `pageNo, width, height, sourceKind, blocksRef, textCoverage, quality` |
| `Chunk` | `chunkId, sectionPath, ordinal, text, tokenCount, pageStart, pageEnd, evidenceRefs, contentHash` |
| `Table` | `tableId, title, pageStart, pageEnd, rows, columns, cellsRef, csvArtifactRef, evidenceRefs, quality` |
| `ExtractionField` | `fieldPath, valueType, machineValue, confirmedValue, effectiveValue, confidence, reviewStatus, evidenceRefs` |

Page、Chunk、Table 的大载荷在 Demo 中存 Artifact，数据库保存计数、摘要和 ArtifactRef；不为每个单元格增加高频 ORM 行。

### 15.2 状态枚举

- Stage：`PENDING, UPLOADING, SCANNING, PARSING, OCR_PROCESSING, CLASSIFYING, EXTRACTING, QUALITY_CHECK, REVIEW_REQUIRED, READY, FAILED, CANCELLED`。
- Result：`READY, REVIEW_REQUIRED, FAILED`。
- Field review：`AUTO_ACCEPTED, PENDING, CONFIRMED, CORRECTED, UNCONFIRMED`。
- Batch：`OPEN, IN_PROGRESS, COMPLETED, COMPLETED_WITH_ERRORS, CANCELLED`。

### 15.3 REST 接口

继续复用现有接口：

- `POST /api/v1/projects/{projectId}/upload-batches`
- `POST /api/v1/projects/{projectId}/documents:initiate`
- `POST /api/v1/projects/{projectId}/document-uploads/{uploadId}:complete`
- `GET /api/v1/projects/{projectId}/documents/{documentId}/processing`
- `GET /api/v1/projects/{projectId}/documents/{documentId}/processing-result`
- `POST /api/v1/projects/{projectId}/documents/{documentId}:confirm-classification`
- `POST /api/v1/projects/{projectId}/documents/{documentId}:confirm-fields`
- `POST /api/v1/projects/{projectId}/documents/{documentId}:reprocess`
- `POST /api/v1/projects/{projectId}/documents/{documentId}/versions/{version}:download`

为过程和结果 Artifact 增加：

- `GET /api/v1/projects/{projectId}/documents/{documentId}/processing/events?after={eventSeq}`
- `GET /api/v1/projects/{projectId}/documents/{documentId}/structured-package`
- `POST /api/v1/projects/{projectId}/documents/{documentId}:publish`

`complete` 接受文件后返回 DocumentSnapshot，状态为 `PROCESSING`；大文件处理异步执行。所有创建、完成、重处理和发布请求必须携带 `Idempotency-Key`。相同键和相同请求哈希返回原结果；相同键但请求不同返回 409。

### 15.4 MCP 与事件

MCP 暴露 `structure_document`、`get_document_processing`、`get_structured_package`、`confirm_document_fields`，必须直接调用上述应用服务，不复制业务逻辑。

Outbox 事件使用 `document.*` 命名空间，不修改 `run.*` 契约。页组事件只包含计数和 ArtifactRef，不把正文写入消息总线。

## 16. Demo 演示流程

### 16.1 准备条件

1. PostgreSQL、Temporal、Artifact Gateway、ClamAV、Tool Worker、Model Gateway 和 OCR Service 健康。
2. 项目绑定真实 `model://document-nlp@1` 和 `model://document-layout-ocr@1`；健康检查记录物理模型版本。
3. 发布 `document-profile://business-structuring@1`、合同通用 Schema 和 `agent://document/structurer@1`。
4. 下载第 7 节 ODT、DOCX、PDF，验证大小和 SHA-256。
5. 从 PDF 第 4–7 页生成无文本层 OCR 派生样例，保存 provenance manifest。

### 16.2 逐步演示

1. 资料专员在“文件结构化”工作台创建批次，上传 4 个文件。
2. 页面显示每个文件的上传、哈希、扫描和类型检测；ODT/DOCX/PDF 不依赖扩展名盲信。
3. ODT 进入 ODF 原生 Adapter，页面展示 83 个标题、1,578 个段落和 21 个源表格元素的基线核对。
4. DOCX 进入 OOXML Adapter，作为跨格式对照；PDF 因 68 页触发 7 个页组并行处理。
5. 派生扫描 PDF 显示 `NATIVE_TEXT_INSUFFICIENT → OCR`，可查看 OCR 文本框、表格框和置信度。
6. 切片页面显示章节路径、页范围、token 数和 Evidence；表格单独形成结构化对象和 CSV。
7. Agent 使用真实模型抽取：
   - 文档标题：`Digital Outcomes and Specialists 4 Framework Agreement Call-Off Contract`；
   - 框架/合同引用：`RM1043.6`；
   - 结构：Part A、Part B、Part C；
   - 买方、供应商、合同金额等未填写字段：值为 `null`，质量标记为 `PLACEHOLDER_NOT_FILLED`，不得把 “Click here to enter...” 当真实值。
8. 质量 Tool 比较三种格式的标题、引用和章节，展示一致或冲突依据。
9. 人为把一个字段阈值设为需确认，审核员查看原页后确认或纠正；页面同时保留 machineValue 和 confirmedValue。
10. 发布结构化资料包，下载 `structured-document.json`、`content.md`、`tables/*.csv`、`evidence-manifest.json` 和 `review-log.json`。
11. 审计员从任一字段下钻到原件页/坐标、Tool 调用、模型/Prompt/Schema 版本及人工记录。

### 16.3 可验证证据

- 公开来源 URL、访问日期、文件大小和 SHA-256；
- 4 个 DocumentVersion ID、Blob ID 和不可变哈希；
- ProcessingRun 时间线和各页组状态；
- ClamAV、Parser、OCR、Model、Quality Tool 的真实 Trace；
- 原生/OCR 页路由、表格/Chunk 计数和 Artifact 哈希；
- 人工确认前后 Result 版本；
- 最终资料包哈希和下载记录。

## 17. 验收标准

### 17.1 主流程与真实数据

- Given 第 7 节三个官方文件可下载，When 准备脚本执行，Then 文件大小与 SHA-256 必须完全匹配，来源、访问日和 OGL 链接写入 manifest。
- Given 真实 ODT 原件，When 完成处理，Then 系统必须识别为 ODT、使用 ODF Adapter、提取标题层级和不少于 20 个表格，并输出指向 ODF 结构或渲染页的 Evidence。
- Given 同一合同 ODT、DOCX、PDF，When 质量检查，Then 标题、`RM1043.6`、Part A/B/C 必须一致；不一致项进入 REVIEW_REQUIRED，不得自动择一。

### 17.2 格式自适应、ODF 与大文件

- Given 把 ODT 文件扩展名改为 `.bin`，When 检测，Then 系统仍按内容识别 ODF，并记录扩展名冲突。
- Given 68 页官方 PDF，When 处理，Then 必须进入大文件路径、形成 7 个 10 页以内页组、并行度不超过 4，且完整覆盖 68 页。
- Given 第 3 个页组首次超时，When 自动重试，Then 只重试该页组，已完成页组 Artifact 哈希不变。
- Given 任一解析结果超过 256 KiB，When Activity 完成，Then Workflow 历史只保存 ArtifactRef、hash 和摘要，不保存完整正文。

### 17.3 OCR、NLP、切片和表格

- Given 无文本层的真实派生扫描 PDF，When OCR，Then 页面必须产生文本、bbox、置信度和表格区域，`RM1043.6` 可被定位到对应页；与同页数字 PDF 归一化文本相似度达到实施资格阈值 0.95。
- Given 数字 PDF 页具有足够文本覆盖率，When 路由，Then 不调用 OCR，过程页显示原生解析依据。
- Given 合同 Schema，When 真实 NLP 模型抽取，Then 标题、合同引用和三部分结构通过 Schema；买方、供应商、金额等模板占位字段返回 `null + PLACEHOLDER_NOT_FILLED`。
- Given 章节和表格混排，When 切片，Then普通 Chunk 不超过 1,600 tokens、保留 sectionPath/page range/Evidence，表格行不被普通文本切片截断。
- Given ODT 原生表格，When 发布，Then每张表保留稳定 tableId、行列、合并单元格信息、来源位置和可下载 CSV。

### 17.4 人工介入

- Given 关键字段低于 0.95 或 Evidence 缺失，When 质量检查，Then状态必须为 REVIEW_REQUIRED，不能发布 READY。
- Given 审核员纠正字段，When 提交，Then machineValue 保持不变、confirmedValue 追加、resultVersion 递增，并记录操作者、时间和理由。
- Given 两名审核员基于同一旧版本提交，When 第二次提交，Then 返回 409，不覆盖第一个决定。

### 17.5 失败、权限和审计

- Given ClamAV 不可用或返回恶意文件，When 上传完成，Then不得调用 Parser/OCR/模型，不得生成 READY 结果。
- Given OCR 或模型未配置，When 文件需要该能力，Then显示 `BLOCKED_PROVIDER` 或 REVIEW_REQUIRED，不得使用 Fake/静态结果。
- Given跨 tenant 的用户读取 Document、Result 或 Artifact，When请求，Then返回 403/404，RLS 和审计日志均有证据。
- Given运行被取消，When仍有未开始页组，Then不再调度新页组、不发布结果，已完成 Artifact 按保留策略处理。
- Given最终资料包中的任一关键字段，When审计员下钻，Then能定位原件版本、页/坐标/片段、输入输出哈希、Parser/OCR/模型/Prompt/Schema/Tool 版本和人工决定。

### 17.6 过程与业务结果

- Given Demo 全流程完成，When打开工作台，Then同一页面可看到真实输入、数据来源、每一步 Agent/Tool 状态、处理依据、人工节点和最终结构化结果。
- Given最终发布成功，When下载资料包，Then JSON 通过版本化 Schema，所有 Artifact 哈希可复算，发布 Tool 的 EffectJournal 证明重复请求未产生重复结果。

## 18. 暂不实现内容

- OFD 电子文件：与 ODF 不同，P0 不混用；后续由独立 Adapter 接入。
- 密码破解、宏执行、嵌入对象执行、外部链接抓取。
- 手写体、印章真伪、签名真伪、公式和图表语义的生产级识别。
- PST/MSG 邮件归档、CAD、音视频、压缩包递归业务抽取。
- 自动训练、微调、客户数据进入公共训练集。
- 向 ERP、合同系统、知识库或外部网盘自动写入。
- 向量检索和近重复聚类；不影响本 Demo 的确定性切片和结构化输出。
- 生产级 HA、跨区域容灾、500 页以上超大文档 SLO；Demo 仍保留有界重试、取消和失败收口。
- 法律、财务、税务、合规或付款结论；下游能力必须基于已确认结构化事实另行决策。

## 19. 风险说明

| 风险 | 影响 | 缓解措施 |
|---|---|---|
| 公开合同已撤回 | 用户误认为条款仍有效 | 页面明确“仅文档处理样例”，不输出当前有效性结论 |
| ODF 与 OFD 名称混淆 | 实施错误或验收错位 | API、MIME、文档均使用全称；OFD 明确排除 |
| ODF/OOXML/PDF 版式差异 | 表格或章节计数不完全一致 | 以关键业务字段和 Evidence 一致性为门，不强求渲染像素一致 |
| 扫描质量、旋转、噪点 | OCR 和表格错误 | 页面预处理、逐页置信度、数字文本对照、人工确认 |
| 模型把模板占位符当真实值 | 形成错误业务事实 | Prompt 禁令、占位规则、Schema 校验、关键字段人工门 |
| 大文件耗时和内存峰值 | Worker OOM、演示超时 | 流式读取、10 页分片、并行度 4、Artifact 外置、预算门 |
| 恶意或畸形办公文件 | Parser 被利用 | ClamAV、容器限制、无网络、只读文件系统、CPU/内存/时间上限 |
| Provider 数据外发 | 敏感信息泄露 | 本地 OCR 优先、模型只传必要 Chunk、项目级 Provider 策略、脱敏和审计 |
| 模型/OCR版本漂移 | 结果不可复现 | 冻结镜像、物理模型、Prompt、Schema 和请求哈希；升级跑资格集 |
| 公开链接失效 | Demo 无法准备 | 按已核验哈希缓存原件；发布页和三种格式互为发现入口 |
| 人工审核积压 | READY 延迟 | 按关键性和置信度排序，只审核低置信项，显示 SLA 和批量确认 |
| 成本不可控 | 大文件调用过多 | 原生解析优先、按页 OCR、Top-K Chunk、文档预算和租户并发上限 |
| 审计日志泄露正文 | 扩大数据暴露 | 日志只存哈希/计数/引用，正文留在受控 Artifact |
| Demo 指标被当作生产指标 | 错误承诺准确率或 SLO | 所有阈值标记为待实施验证；中文和客户域样本通过后才能升级为 VERIFIED |
