/**
 * TailAdmin SVG 语义注册表 — semantic key → TailAdmin export name → lucide fallback。
 * @see references/icon-system.md
 */

export type IconSemanticCategory =
  | "navigation"
  | "user"
  | "action"
  | "direction"
  | "status"
  | "security"
  | "file"
  | "devops"
  | "paas"
  | "bi"
  | "communication"
  | "ai-media"
  | "commerce";

export type IconRegistryEntry = {
  /** 业务语义键，供 Agent 检索 */
  semanticKey: string;
  /** TailAdmin barrel 导出名 */
  tailadminName: string;
  /** lucide-react fallback */
  lucideFallback: string;
  category: IconSemanticCategory;
  /** 中文可访问名称 */
  ariaLabel: string;
  /** 适用场景提示 */
  scenes: string[];
};

export const iconRegistry: IconRegistryEntry[] = [
  { semanticKey: "dashboard", tailadminName: "DashboardAltIcon", lucideFallback: "LayoutDashboard", category: "navigation", ariaLabel: "仪表盘", scenes: ["总览", "运维大盘"] },
  { semanticKey: "grid-layout", tailadminName: "GridIcon", lucideFallback: "LayoutGrid", category: "navigation", ariaLabel: "网格布局", scenes: ["应用入口", "模块导航"] },
  { semanticKey: "sidebar-menu", tailadminName: "MenuIcon", lucideFallback: "Menu", category: "navigation", ariaLabel: "菜单", scenes: ["侧栏折叠", "移动端导航"] },
  { semanticKey: "table-view", tailadminName: "TableIcon", lucideFallback: "Table2", category: "navigation", ariaLabel: "表格视图", scenes: ["列表页", "资源表"] },
  { semanticKey: "list-view", tailadminName: "ListIcon", lucideFallback: "List", category: "navigation", ariaLabel: "列表视图", scenes: ["任务列表", "日志列表"] },
  { semanticKey: "page", tailadminName: "PageIcon", lucideFallback: "FileText", category: "navigation", ariaLabel: "页面", scenes: ["内容页", "文档页"] },
  { semanticKey: "layout", tailadminName: "LayoutIcon", lucideFallback: "PanelsTopLeft", category: "navigation", ariaLabel: "布局", scenes: ["页面构建", "模板选择"] },
  { semanticKey: "user", tailadminName: "UserIcon", lucideFallback: "User", category: "user", ariaLabel: "用户", scenes: ["账号", "个人中心"] },
  { semanticKey: "user-circle", tailadminName: "UserCircleIcon", lucideFallback: "CircleUser", category: "user", ariaLabel: "用户头像", scenes: ["顶栏用户菜单"] },
  { semanticKey: "user-group", tailadminName: "GroupIcon", lucideFallback: "Users", category: "user", ariaLabel: "用户组", scenes: ["团队", "组织"] },
  { semanticKey: "multi-user", tailadminName: "MultiUserIcon", lucideFallback: "UsersRound", category: "user", ariaLabel: "多用户", scenes: ["租户", "协作成员"] },
  { semanticKey: "profile", tailadminName: "ProfileAltIcon", lucideFallback: "UserRound", category: "user", ariaLabel: "个人资料", scenes: ["设置", "账号详情"] },
  { semanticKey: "add", tailadminName: "PlusIcon", lucideFallback: "Plus", category: "action", ariaLabel: "新增", scenes: ["创建资源", "添加条目"] },
  { semanticKey: "add-line", tailadminName: "PlusLineIcon", lucideFallback: "Plus", category: "action", ariaLabel: "新增", scenes: ["工具栏", "内联添加"] },
  { semanticKey: "edit", tailadminName: "EditIcon", lucideFallback: "Pencil", category: "action", ariaLabel: "编辑", scenes: ["行内编辑", "配置修改"] },
  { semanticKey: "delete", tailadminName: "TrashBinIcon", lucideFallback: "Trash2", category: "action", ariaLabel: "删除", scenes: ["危险操作", "清理"] },
  { semanticKey: "download", tailadminName: "DownloadIcon", lucideFallback: "Download", category: "action", ariaLabel: "下载", scenes: ["导出", "制品下载"] },
  { semanticKey: "upload", tailadminName: "UploadIcon", lucideFallback: "Upload", category: "action", ariaLabel: "上传", scenes: ["导入", "文件上传"] },
  { semanticKey: "copy", tailadminName: "CopyIcon", lucideFallback: "Copy", category: "action", ariaLabel: "复制", scenes: ["API Key", "配置复制"] },
  { semanticKey: "search", tailadminName: "SearchIcon", lucideFallback: "Search", category: "action", ariaLabel: "搜索", scenes: ["筛选", "命令面板"] },
  { semanticKey: "close", tailadminName: "CloseIcon", lucideFallback: "X", category: "action", ariaLabel: "关闭", scenes: ["弹窗", "抽屉"] },
  { semanticKey: "share", tailadminName: "ShareIcon", lucideFallback: "Share2", category: "action", ariaLabel: "分享", scenes: ["仪表盘分享", "嵌入"] },
  { semanticKey: "chevron-down", tailadminName: "ChevronDownIcon", lucideFallback: "ChevronDown", category: "direction", ariaLabel: "展开", scenes: ["下拉", "折叠"] },
  { semanticKey: "chevron-up", tailadminName: "ChevronUpIcon", lucideFallback: "ChevronUp", category: "direction", ariaLabel: "收起", scenes: ["手风琴", "排序"] },
  { semanticKey: "arrow-up", tailadminName: "ArrowUpIcon", lucideFallback: "ArrowUp", category: "direction", ariaLabel: "上升", scenes: ["趋势上升", "排序"] },
  { semanticKey: "arrow-down", tailadminName: "ArrowDownIcon", lucideFallback: "ArrowDown", category: "direction", ariaLabel: "下降", scenes: ["趋势下降", "下钻"] },
  { semanticKey: "success", tailadminName: "CheckCircleIcon", lucideFallback: "CircleCheck", category: "status", ariaLabel: "成功", scenes: ["健康", "通过"] },
  { semanticKey: "check-line", tailadminName: "CheckLineIcon", lucideFallback: "Check", category: "status", ariaLabel: "已选", scenes: ["多选", "完成步骤"] },
  { semanticKey: "alert", tailadminName: "AlertIcon", lucideFallback: "TriangleAlert", category: "status", ariaLabel: "警告", scenes: ["告警", "风险提示"] },
  { semanticKey: "alert-hexa", tailadminName: "AlertHexaIcon", lucideFallback: "TriangleAlert", category: "status", ariaLabel: "严重告警", scenes: ["安全事件", "合规"] },
  { semanticKey: "info", tailadminName: "InfoIcon", lucideFallback: "Info", category: "status", ariaLabel: "信息", scenes: ["提示", "帮助"] },
  { semanticKey: "error", tailadminName: "ErrorIcon", lucideFallback: "CircleX", category: "status", ariaLabel: "错误", scenes: ["失败", "异常"] },
  { semanticKey: "bolt", tailadminName: "BoltIcon", lucideFallback: "Zap", category: "status", ariaLabel: "即时状态", scenes: ["实时指标", "快速操作"] },
  { semanticKey: "flash", tailadminName: "FlashIcon", lucideFallback: "Zap", category: "status", ariaLabel: "活跃", scenes: ["热点", "实时流"] },
  { semanticKey: "lock", tailadminName: "LockIcon", lucideFallback: "Lock", category: "security", ariaLabel: "锁定", scenes: ["权限", "加密"] },
  { semanticKey: "key", tailadminName: "KeyIcon", lucideFallback: "KeyRound", category: "security", ariaLabel: "密钥", scenes: ["API Key", "Token"] },
  { semanticKey: "eye", tailadminName: "EyeIcon", lucideFallback: "Eye", category: "security", ariaLabel: "显示", scenes: ["Secret 显示"] },
  { semanticKey: "eye-off", tailadminName: "EyeCloseIcon", lucideFallback: "EyeOff", category: "security", ariaLabel: "隐藏", scenes: ["Secret 隐藏"] },
  { semanticKey: "folder", tailadminName: "FolderIcon", lucideFallback: "Folder", category: "file", ariaLabel: "文件夹", scenes: ["代码仓库", "目录"] },
  { semanticKey: "file", tailadminName: "FileIcon", lucideFallback: "File", category: "file", ariaLabel: "文件", scenes: ["文件浏览", "附件"] },
  { semanticKey: "docs", tailadminName: "DocsIcon", lucideFallback: "FileText", category: "file", ariaLabel: "文档", scenes: ["API 文档", "说明"] },
  { semanticKey: "paper-clip", tailadminName: "PaperClipIcon", lucideFallback: "Paperclip", category: "file", ariaLabel: "附件", scenes: ["工单", "上传记录"] },
  { semanticKey: "star", tailadminName: "StarLine", lucideFallback: "Star", category: "file", ariaLabel: "收藏", scenes: ["收藏仓库", "标记"] },
  { semanticKey: "pipeline", tailadminName: "PlugInIcon", lucideFallback: "Plug", category: "devops", ariaLabel: "流水线", scenes: ["CI/CD", "集成"] },
  { semanticKey: "integration", tailadminName: "IntegrationAltIcon", lucideFallback: "Workflow", category: "devops", ariaLabel: "集成", scenes: ["Webhook", "连接器"] },
  { semanticKey: "system", tailadminName: "SystemIcon", lucideFallback: "Cpu", category: "devops", ariaLabel: "系统", scenes: ["系统设置", "平台"] },
  { semanticKey: "stack", tailadminName: "StackIcon", lucideFallback: "Layers", category: "devops", ariaLabel: "堆栈", scenes: ["制品", "版本层"] },
  { semanticKey: "artifact", tailadminName: "BoxCubeIcon", lucideFallback: "Package", category: "devops", ariaLabel: "制品", scenes: ["构建产物", "镜像"] },
  { semanticKey: "chip", tailadminName: "ChipIcon", lucideFallback: "Cpu", category: "paas", ariaLabel: "芯片/节点", scenes: ["K8s 节点", "计算"] },
  { semanticKey: "cube", tailadminName: "CubeAltIcon", lucideFallback: "Box", category: "paas", ariaLabel: "集群", scenes: ["K8s", "资源块"] },
  { semanticKey: "database", tailadminName: "DataBaseIcon", lucideFallback: "Database", category: "paas", ariaLabel: "数据库", scenes: ["MySQL", "ES", "Redis"] },
  { semanticKey: "globe", tailadminName: "GlobeIcon", lucideFallback: "Globe", category: "paas", ariaLabel: "网络/区域", scenes: ["Endpoint", "多区域"] },
  { semanticKey: "map", tailadminName: "MapIcon", lucideFallback: "Map", category: "paas", ariaLabel: "地图", scenes: ["拓扑", "区域分布"] },
  { semanticKey: "clock", tailadminName: "ClockIcon", lucideFallback: "Clock", category: "paas", ariaLabel: "定时", scenes: ["Cron", "调度"] },
  { semanticKey: "telescope", tailadminName: "TelescopeIcon", lucideFallback: "Telescope", category: "paas", ariaLabel: "观测", scenes: ["监控", "追踪"] },
  { semanticKey: "chart", tailadminName: "ChartAltIcon", lucideFallback: "ChartNoAxesCombined", category: "bi", ariaLabel: "图表", scenes: ["BI", "指标趋势"] },
  { semanticKey: "pie-chart", tailadminName: "PieChartIcon", lucideFallback: "PieChart", category: "bi", ariaLabel: "饼图", scenes: ["占比", "分布"] },
  { semanticKey: "slider", tailadminName: "HorizontalSlideIcon", lucideFallback: "SlidersHorizontal", category: "bi", ariaLabel: "筛选配置", scenes: ["图表编码", "筛选器"] },
  { semanticKey: "dollar", tailadminName: "DollarLineIcon", lucideFallback: "DollarSign", category: "bi", ariaLabel: "金额", scenes: ["收入", "成本"] },
  { semanticKey: "user-money", tailadminName: "UserMoneyIcon", lucideFallback: "CircleDollarSign", category: "bi", ariaLabel: "客单价", scenes: ["经营分析", "客户价值"] },
  { semanticKey: "bell", tailadminName: "BellAltIcon", lucideFallback: "Bell", category: "communication", ariaLabel: "通知", scenes: ["告警中心", "消息"] },
  { semanticKey: "mail", tailadminName: "MailIcon", lucideFallback: "Mail", category: "communication", ariaLabel: "邮件", scenes: ["通知配置", "收件箱"] },
  { semanticKey: "chat", tailadminName: "ChatIcon", lucideFallback: "MessageSquare", category: "communication", ariaLabel: "消息", scenes: ["客服", "协作"] },
  { semanticKey: "call", tailadminName: "CallIcon", lucideFallback: "Phone", category: "communication", ariaLabel: "呼叫", scenes: ["外呼", "值班"] },
  { semanticKey: "headphone", tailadminName: "HeadphoneAltIcon", lucideFallback: "Headphones", category: "communication", ariaLabel: "客服", scenes: ["支持", "工单"] },
  { semanticKey: "ai", tailadminName: "AiIcon", lucideFallback: "Bot", category: "ai-media", ariaLabel: "智能", scenes: ["AI 控台", "助手"] },
  { semanticKey: "brain", tailadminName: "BrainIcon", lucideFallback: "Brain", category: "ai-media", ariaLabel: "智能分析", scenes: ["模型", "推理"] },
  { semanticKey: "spark", tailadminName: "SparkIcon", lucideFallback: "Sparkles", category: "ai-media", ariaLabel: "生成", scenes: ["AI 生成", "推荐"] },
  { semanticKey: "audio", tailadminName: "AudioIcon", lucideFallback: "Volume2", category: "ai-media", ariaLabel: "音频", scenes: ["语音", "媒体"] },
  { semanticKey: "video", tailadminName: "VideoIcon", lucideFallback: "Video", category: "ai-media", ariaLabel: "视频", scenes: ["录制", "回放"] },
  { semanticKey: "play", tailadminName: "PlayIcon", lucideFallback: "Play", category: "ai-media", ariaLabel: "播放", scenes: ["媒体控制", "演示"] },
  { semanticKey: "cart", tailadminName: "CartIcon", lucideFallback: "ShoppingCart", category: "commerce", ariaLabel: "订单", scenes: ["电商", "交易"] },
  { semanticKey: "delivery", tailadminName: "TruckDelivery", lucideFallback: "Truck", category: "commerce", ariaLabel: "物流", scenes: ["配送", "运输"] },
  { semanticKey: "package", tailadminName: "BoxTapped", lucideFallback: "Package", category: "commerce", ariaLabel: "包裹", scenes: ["库存", "发货"] },
  { semanticKey: "settings", tailadminName: "SettingsAltIcon", lucideFallback: "Settings", category: "navigation", ariaLabel: "设置", scenes: ["系统设置", "偏好"] },
  { semanticKey: "task", tailadminName: "TaskIcon", lucideFallback: "ListTodo", category: "navigation", ariaLabel: "任务", scenes: ["待办", "工单"] },
  { semanticKey: "time", tailadminName: "TimeIcon", lucideFallback: "Timer", category: "status", ariaLabel: "时间", scenes: ["耗时", "SLA"] },
  { semanticKey: "calendar", tailadminName: "CalenderIcon", lucideFallback: "Calendar", category: "navigation", ariaLabel: "日历", scenes: ["排期", "日程"] },
  { semanticKey: "regenerate", tailadminName: "RegenerateIcon", lucideFallback: "RefreshCw", category: "action", ariaLabel: "重新生成", scenes: ["AI", "重试"] },
  { semanticKey: "logout", tailadminName: "LogoutIcon", lucideFallback: "LogOut", category: "action", ariaLabel: "退出", scenes: ["登出", "会话"] },
];

export type IconSemanticKey = (typeof iconRegistry)[number]["semanticKey"];

const registryByKey = new Map(
  iconRegistry.map((entry) => [entry.semanticKey, entry] as const),
);

const registryByTailadmin = new Map(
  iconRegistry.map((entry) => [entry.tailadminName, entry] as const),
);

/** 按业务语义键检索图标元数据 */
export function getIconBySemanticKey(key: string): IconRegistryEntry | undefined {
  return registryByKey.get(key);
}

/** 按 TailAdmin 导出名反查语义 */
export function getIconByTailadminName(name: string): IconRegistryEntry | undefined {
  return registryByTailadmin.get(name);
}

/** 按场景关键词模糊检索推荐图标 */
export function searchIconsByScene(query: string): IconRegistryEntry[] {
  const q = query.trim().toLowerCase();
  if (!q) return iconRegistry;
  return iconRegistry.filter(
    (entry) =>
      entry.semanticKey.includes(q) ||
      entry.ariaLabel.includes(query) ||
      entry.scenes.some((scene) => scene.toLowerCase().includes(q) || scene.includes(query)),
  );
}

/** 按类别返回图标列表 */
export function getIconsByCategory(category: IconSemanticCategory): IconRegistryEntry[] {
  return iconRegistry.filter((entry) => entry.category === category);
}

export const iconRegistryStats = {
  total: iconRegistry.length,
  categories: [...new Set(iconRegistry.map((e) => e.category))].length,
} as const;
