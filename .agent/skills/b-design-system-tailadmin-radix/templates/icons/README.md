# TailAdmin Icons

本目录同步自 TailAdmin React Pro v2.3.1 `src/icons`，包含 121 个 SVG 与 `index.ts` barrel。它是 `b-design-system-tailadmin-radix` 的内置资产，不依赖 vendored 源项目。

推荐复制到宿主项目的 `src/icons/`，并配置 `vite-plugin-svgr` 支持 `?react`：

```tsx
import { DataBaseIcon, AlertHexaIcon } from "@/icons";

export function ResourceStatusIcon() {
  return <DataBaseIcon className="size-5 text-brand-500" aria-hidden />;
}
```

图标语义、尺寸、状态与场景选择规则见 `references/icon-system.md`。
