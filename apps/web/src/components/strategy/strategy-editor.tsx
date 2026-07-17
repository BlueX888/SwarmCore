import * as React from "react";
import type { Diagnostic } from "@/api/types";
import { Button } from "@/components/ui/button";
import { parseSpec, serializeSpec, type SpecFormat } from "./spec-editor";
import { StrategyCanvas } from "./strategy-canvas";
import { isSwarmSpecDocument, type EditorState, type SwarmSpecDocument } from "./strategy-editor-model";

export type StrategyEditorMode = "canvas" | SpecFormat;

export function StrategyEditor({ spec, editorState, nodeTypes, diagnostics, onSpecChange, onEditorStateChange, onError }: {
  spec: SwarmSpecDocument;
  editorState: EditorState;
  nodeTypes: string[];
  diagnostics: Diagnostic[];
  onSpecChange: (spec: SwarmSpecDocument) => void;
  onEditorStateChange: (state: EditorState) => void;
  onError: (message: string) => void;
}) {
  const [mode, setMode] = React.useState<StrategyEditorMode>("canvas");
  const [buffers, setBuffers] = React.useState<Record<SpecFormat, string>>({
    json: serializeSpec(spec, "json"),
    yaml: serializeSpec(spec, "yaml"),
  });
  const [invalid, setInvalid] = React.useState<Partial<Record<SpecFormat, string>>>({});
  const lastSpec = React.useRef(spec);

  React.useEffect(() => {
    if (lastSpec.current === spec) return;
    lastSpec.current = spec;
    setBuffers((current) => ({
      json: invalid.json ? current.json : serializeSpec(spec, "json"),
      yaml: invalid.yaml ? current.yaml : serializeSpec(spec, "yaml"),
    }));
  }, [invalid.json, invalid.yaml, spec]);

  const switchMode = (next: StrategyEditorMode) => {
    if (mode !== "canvas") syncText(mode, buffers[mode]);
    if (next !== "canvas" && !invalid[next]) {
      setBuffers((current) => ({ ...current, [next]: serializeSpec(spec, next) }));
    }
    setMode(next);
  };

  const syncText = (format: SpecFormat, source: string) => {
    try {
      const parsed = parseSpec(source, format);
      if (!isSwarmSpecDocument(parsed)) throw new Error("文档必须包含 spec.graph.nodes。");
      setInvalid((current) => ({ ...current, [format]: undefined }));
      lastSpec.current = parsed;
      onSpecChange(parsed);
      return true;
    } catch (error) {
      const message = error instanceof Error ? error.message : "策略文档无效。";
      setInvalid((current) => ({ ...current, [format]: message }));
      onError(`${format.toUpperCase()} 格式无效，仍保留最近一次有效的 SwarmSpec：${message}`);
      return false;
    }
  };

  const changeText = (format: SpecFormat, source: string) => {
    setBuffers((current) => ({ ...current, [format]: source }));
    syncText(format, source);
  };

  return <div className="min-w-0 space-y-4">
    <div className="flex flex-wrap items-center justify-between gap-3">
      <div><p className="text-sm font-medium text-gray-700 dark:text-gray-300">策略编辑器</p><p className="text-xs text-gray-500">SwarmSpec 是执行来源，画布布局会单独保存。</p></div>
      <div className="flex gap-1" role="tablist" aria-label="编辑模式">
        {(["canvas", "json", "yaml"] as const).map((item) => <Button key={item} type="button" size="sm" role="tab" aria-selected={mode === item} variant={mode === item ? "primary" : "ghost"} onClick={() => switchMode(item)}>{item === "canvas" ? "画布" : item.toUpperCase()}</Button>)}
      </div>
    </div>
    {mode === "canvas" ? <StrategyCanvas spec={spec} editorState={editorState} nodeTypes={nodeTypes} diagnostics={diagnostics} onSpecChange={onSpecChange} onEditorStateChange={onEditorStateChange} onError={onError} /> : <div>
      <textarea
        aria-label={`${mode.toUpperCase()} 策略规范`}
        spellCheck={false}
        value={buffers[mode]}
        onChange={(event) => changeText(mode, event.target.value)}
        className={`min-h-[620px] w-full resize-y rounded-xl border bg-white p-4 font-mono text-xs text-gray-800 outline-none focus:ring-3 dark:bg-gray-900 dark:text-gray-200 ${invalid[mode] ? "border-error-500 focus:ring-error-500/10" : "border-gray-300 focus:border-brand-500 focus:ring-brand-500/10 dark:border-gray-700"}`}
      />
      {invalid[mode] ? <p role="alert" className="mt-2 rounded-lg bg-error-50 p-3 text-sm text-error-600 dark:bg-error-500/10">{invalid[mode]} 画布中仍保留最近一次有效的规范。</p> : null}
    </div>}
  </div>;
}
