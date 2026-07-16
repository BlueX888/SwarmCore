import * as React from "react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { CodeEditor } from "@/components/ui/code-editor";
import type { PrismLanguage } from "@/lib/editor-theme";

export type AiCodeGeneratorShellProps = {
  title?: React.ReactNode;
  description?: React.ReactNode;
  prompt?: string;
  onPromptChange?: (value: string) => void;
  code?: string;
  onCodeChange?: (value: string) => void;
  language?: PrismLanguage;
  onLanguageChange?: (language: PrismLanguage) => void;
  generating?: boolean;
  dirty?: boolean;
  error?: string;
  onGenerate?: () => void;
  onSave?: () => void;
  onReset?: () => void;
  className?: string;
};

const defaultPrompt = "生成一个 TailAdmin 风格的 Primary Button 组件，支持 loading 与 disabled 状态。";

const defaultCode = `export function PrimaryButton({ loading, children }) {
  return (
    <button
      className="h-11 rounded-lg bg-brand-500 px-5 text-white disabled:opacity-40"
      disabled={loading}
    >
      {loading ? "提交中…" : children}
    </button>
  );
}`;

/**
 * AI 代码生成页组合 — 提示词输入 + CodeEditor 分屏编辑 + 生成/保存动作。
 * @see references/layout-patterns/code-editor-editable.md
 * @see templates/ui/code-editor.tsx
 */
export function AiCodeGeneratorShell({
  title = "AI 代码生成器",
  description = "输入自然语言提示，生成可编辑的 React 组件代码，并实时预览语法高亮。",
  prompt = defaultPrompt,
  onPromptChange,
  code = defaultCode,
  onCodeChange,
  language = "tsx",
  onLanguageChange,
  generating = false,
  dirty = false,
  error,
  onGenerate,
  onSave,
  onReset,
  className,
}: AiCodeGeneratorShellProps) {
  return (
    <div className={cn("space-y-6", className)}>
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="space-y-1">
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="text-title-md font-semibold text-gray-800 dark:text-white/90">{title}</h1>
            {generating ? <Badge variant="light" color="primary">生成中</Badge> : null}
            {dirty && !generating ? <Badge variant="light" color="warning">代码未保存</Badge> : null}
          </div>
          <p className="text-theme-sm text-gray-500 dark:text-gray-400">{description}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          {onReset ? (
            <Button type="button" variant="outline" onClick={onReset} disabled={generating}>
              重置
            </Button>
          ) : null}
          {onGenerate ? (
            <Button type="button" onClick={onGenerate} disabled={generating || !prompt.trim()}>
              {generating ? "生成中…" : "生成代码"}
            </Button>
          ) : null}
        </div>
      </div>

      <div className="rounded-2xl border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-gray-900">
        <Label htmlFor="ai-codegen-prompt" className="mb-2 block text-sm font-medium">
          提示词
        </Label>
        <Textarea
          id="ai-codegen-prompt"
          value={prompt}
          onChange={(event) => onPromptChange?.(event.target.value)}
          rows={3}
          placeholder="描述你想生成的组件、页面或脚本…"
          disabled={generating}
        />
        <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
          示例：生成带搜索、筛选与分页的 DataTableCard 列表页骨架。
        </p>
      </div>

      <CodeEditor
        value={code}
        onChange={onCodeChange}
        language={language}
        onLanguageChange={onLanguageChange}
        dirty={dirty}
        saving={generating}
        error={error}
        onSave={onSave}
        title="生成结果"
        placeholder="生成完成后可在此继续编辑代码…"
      />
    </div>
  );
}
