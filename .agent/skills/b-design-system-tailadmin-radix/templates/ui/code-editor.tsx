import * as React from "react";
import { Check, Copy, LayoutTemplate, Pencil, Save } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { CodeBlock } from "@/components/ui/code-block";
import {
  codeBlockShellClass,
  supportedPrismLanguages,
  type PrismLanguage,
} from "@/lib/editor-theme";

export type CodeEditorMode = "split" | "edit" | "preview";

export type CodeEditorProps = {
  value: string;
  onChange?: (value: string) => void;
  language?: PrismLanguage;
  onLanguageChange?: (language: PrismLanguage) => void;
  mode?: CodeEditorMode;
  onModeChange?: (mode: CodeEditorMode) => void;
  dirty?: boolean;
  saving?: boolean;
  readOnly?: boolean;
  error?: string;
  showLineNumbers?: boolean;
  onSave?: () => void;
  onCopy?: () => void;
  placeholder?: string;
  title?: React.ReactNode;
  className?: string;
};

const modeLabel: Record<CodeEditorMode, string> = {
  split: "分屏",
  edit: "编辑",
  preview: "预览",
};

const languageLabel: Record<PrismLanguage, string> = {
  jsx: "JSX",
  tsx: "TSX",
  typescript: "TypeScript",
  bash: "Bash",
  json: "JSON",
  css: "CSS",
  scss: "SCSS",
  markdown: "Markdown",
  html: "HTML",
};

/**
 * 可编辑代码编辑器 — Textarea 输入 + Prism 实时预览，适用于 AI 代码生成、工单片段编辑。
 * @see references/layout-patterns/code-editor-editable.md
 * @see templates/ui/code-block.tsx
 */
export function CodeEditor({
  value,
  onChange,
  language = "tsx",
  onLanguageChange,
  mode = "split",
  onModeChange,
  dirty = false,
  saving = false,
  readOnly = false,
  error,
  showLineNumbers = true,
  onSave,
  onCopy,
  placeholder = "在此输入或粘贴代码…",
  title,
  className,
}: CodeEditorProps) {
  const [copied, setCopied] = React.useState(false);

  const handleCopy = async () => {
    if (!value.trim()) return;
    try {
      await navigator.clipboard.writeText(value);
      setCopied(true);
      onCopy?.();
      window.setTimeout(() => setCopied(false), 1500);
    } catch {
      /* clipboard unavailable */
    }
  };

  const showEditPane = mode === "split" || mode === "edit";
  const showPreviewPane = mode === "split" || mode === "preview";

  return (
    <div className={cn(codeBlockShellClass, "flex flex-col", className)}>
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-gray-200 px-5 py-4 dark:border-gray-800">
        <div className="flex min-w-0 flex-wrap items-center gap-2">
          <div className="flex items-center gap-1.5 text-sm text-gray-500 dark:text-gray-400">
            <span aria-hidden="true">{"{ }"}</span>
            <span>{title ?? "代码编辑器"}</span>
          </div>
          {dirty ? (
            <Badge variant="light" color="warning" className="shrink-0">
              未保存
            </Badge>
          ) : null}
          {error ? (
            <Badge variant="light" color="error" className="shrink-0">
              语法错误
            </Badge>
          ) : null}
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Select
            value={language}
            onValueChange={(next) => onLanguageChange?.(next as PrismLanguage)}
            disabled={readOnly}
          >
            <SelectTrigger className="h-9 w-[132px]" aria-label="选择语言">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {supportedPrismLanguages.map((lang) => (
                <SelectItem key={lang} value={lang}>
                  {languageLabel[lang]}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <div className="inline-flex rounded-lg border border-gray-200 p-0.5 dark:border-gray-800">
            {(["split", "edit", "preview"] as const).map((item) => (
              <button
                key={item}
                type="button"
                className={cn(
                  "inline-flex h-8 items-center gap-1 rounded-md px-2.5 text-xs font-medium transition-colors",
                  mode === item
                    ? "bg-brand-500 text-white"
                    : "text-gray-600 hover:bg-gray-50 dark:text-gray-400 dark:hover:bg-white/5",
                )}
                aria-pressed={mode === item}
                onClick={() => onModeChange?.(item)}
              >
                {item === "split" ? (
                  <LayoutTemplate className="size-3.5" aria-hidden="true" />
                ) : item === "edit" ? (
                  <Pencil className="size-3.5" aria-hidden="true" />
                ) : (
                  <span aria-hidden="true">◎</span>
                )}
                {modeLabel[item]}
              </button>
            ))}
          </div>
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="h-9"
            onClick={handleCopy}
            disabled={!value.trim()}
            aria-label={copied ? "已复制" : "复制代码"}
          >
            {copied ? <Check className="size-4" /> : <Copy className="size-4" />}
          </Button>
          {onSave ? (
            <Button
              type="button"
              size="sm"
              className="h-9"
              onClick={onSave}
              disabled={readOnly || saving || !dirty}
            >
              {saving ? "保存中…" : "保存"}
              {!saving ? <Save className="size-4" /> : null}
            </Button>
          ) : null}
        </div>
      </div>

      <div
        className={cn(
          "grid min-h-[320px] flex-1",
          mode === "split" ? "lg:grid-cols-2" : "grid-cols-1",
        )}
      >
        {showEditPane ? (
          <div className="flex min-h-[240px] flex-col border-b border-gray-200 dark:border-gray-800 lg:border-b-0 lg:border-r">
            <div className="border-b border-gray-200 px-4 py-2 text-xs font-medium text-gray-500 dark:border-gray-800 dark:text-gray-400">
              编辑区
            </div>
            <Textarea
              value={value}
              onChange={(event) => onChange?.(event.target.value)}
              readOnly={readOnly}
              variant={error ? "error" : "default"}
              placeholder={placeholder}
              spellCheck={false}
              aria-label="代码编辑区"
              className="min-h-[280px] flex-1 resize-none rounded-none border-0 bg-gray-50 font-mono text-sm shadow-none focus-visible:ring-0 dark:bg-gray-900/60"
            />
            {error ? (
              <p className="border-t border-error-200 bg-error-50 px-4 py-2 text-xs text-error-600 dark:border-error-500/30 dark:bg-error-500/10 dark:text-error-400">
                {error}
              </p>
            ) : null}
          </div>
        ) : null}
        {showPreviewPane ? (
          <div className="flex min-h-[240px] flex-col">
            <div className="border-b border-gray-200 px-4 py-2 text-xs font-medium text-gray-500 dark:border-gray-800 dark:text-gray-400">
              预览区
            </div>
            <div className="flex-1 p-4">
              <CodeBlock
                code={value}
                language={language}
                status={value.trim() ? "ready" : "empty"}
                showLineNumbers={showLineNumbers}
                showCopy={false}
                showEdit={false}
                emptyMessage="输入代码后此处实时高亮预览"
                className="h-full border-0 shadow-none"
              />
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}
