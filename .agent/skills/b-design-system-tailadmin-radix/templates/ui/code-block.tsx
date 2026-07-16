import * as React from "react";
import { Check, Copy, Pencil } from "lucide-react";
import { cn } from "@/lib/utils";
import { Alert } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import {
  codeBlockBodyClass,
  codeBlockHeaderClass,
  codeBlockLanguageLabelClass,
  codeBlockPreClass,
  codeBlockPreWithLineNumbersClass,
  codeBlockShellClass,
  codeBlockToolbarButtonClass,
  codeBlockToolbarClass,
  getPrismLanguageClass,
  type PrismLanguage,
} from "@/lib/editor-theme";

export type CodeBlockStatus = "ready" | "loading" | "empty" | "error";

export type CodeBlockProps = {
  code?: string;
  language?: PrismLanguage;
  title?: React.ReactNode;
  status?: CodeBlockStatus;
  error?: string;
  showLineNumbers?: boolean;
  showCopy?: boolean;
  showEdit?: boolean;
  onCopy?: () => void;
  onEdit?: () => void;
  emptyMessage?: string;
  className?: string;
};

/**
 * Prism 只读代码块 — AI 生成、工单片段、DevOps 日志高亮展示。
 * @see references/component-styles/editor-theme.md
 * @see templates/lib/editor-theme.ts
 */
export function CodeBlock({
  code = "",
  language = "tsx",
  title,
  status = "ready",
  error,
  showLineNumbers = false,
  showCopy = true,
  showEdit = false,
  onCopy,
  onEdit,
  emptyMessage = "暂无代码内容",
  className,
}: CodeBlockProps) {
  const codeRef = React.useRef<HTMLElement>(null);
  const [copied, setCopied] = React.useState(false);

  React.useEffect(() => {
    if (status !== "ready" || !code || !codeRef.current) return;
    let cancelled = false;
    (async () => {
      const Prism = (await import("prismjs")).default;
      await import("prismjs/plugins/line-numbers/prism-line-numbers");
      const lang = getPrismLanguageClass(language).replace("language-", "");
      try {
        await import(`prismjs/components/prism-${lang}`);
      } catch {
        /* host may preload languages via editor-theme prismLanguageImports */
      }
      if (!cancelled && codeRef.current) {
        Prism.highlightElement(codeRef.current);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [code, language, status]);

  const handleCopy = async () => {
    if (!code) return;
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      onCopy?.();
      window.setTimeout(() => setCopied(false), 1500);
    } catch {
      /* clipboard unavailable */
    }
  };

  const renderBody = () => {
    if (status === "loading") {
      return (
        <div className={codeBlockBodyClass} aria-busy="true" aria-label="代码加载中">
          <Skeleton className="mb-2 h-4 w-full" />
          <Skeleton className="mb-2 h-4 w-[92%]" />
          <Skeleton className="mb-2 h-4 w-[78%]" />
          <Skeleton className="h-4 w-[85%]" />
        </div>
      );
    }
    if (status === "error" && error) {
      return (
        <div className={cn(codeBlockBodyClass, "p-4")}>
          <Alert variant="error" title="代码加载失败" description={error} />
        </div>
      );
    }
    if (status === "empty" || !code.trim()) {
      return (
        <div
          className={cn(codeBlockBodyClass, "flex items-center justify-center text-theme-sm text-gray-500")}
        >
          {emptyMessage}
        </div>
      );
    }
    return (
      <div className={codeBlockBodyClass}>
        <pre
          className={showLineNumbers ? codeBlockPreWithLineNumbersClass : codeBlockPreClass}
        >
          <code
            ref={codeRef}
            className={getPrismLanguageClass(language)}
          >
            {code}
          </code>
        </pre>
      </div>
    );
  };

  return (
    <div className={cn(codeBlockShellClass, className)}>
      <div className={codeBlockHeaderClass}>
        <div className={codeBlockLanguageLabelClass}>
          <span aria-hidden="true">{"{ }"}</span>
          <span>{title ?? language.toUpperCase()}</span>
        </div>
        {(showCopy || showEdit) && status === "ready" && code ? (
          <div className={codeBlockToolbarClass}>
            {showCopy ? (
              <button
                type="button"
                className={codeBlockToolbarButtonClass}
                aria-label={copied ? "已复制" : "复制代码"}
                onClick={handleCopy}
              >
                {copied ? <Check className="size-4" /> : <Copy className="size-4" />}
              </button>
            ) : null}
            {showEdit && onEdit ? (
              <button
                type="button"
                className={codeBlockToolbarButtonClass}
                aria-label="编辑代码"
                onClick={onEdit}
              >
                <Pencil className="size-4" />
              </button>
            ) : null}
          </div>
        ) : null}
      </div>
      {renderBody()}
    </div>
  );
}
