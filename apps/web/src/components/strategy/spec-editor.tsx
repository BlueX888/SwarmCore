import * as React from "react";
import { parse, stringify } from "yaml";
import { Button } from "@/components/ui/button";

export type SpecFormat = "json" | "yaml";

export function serializeSpec(spec: Record<string, unknown>, format: SpecFormat) {
  return format === "json" ? JSON.stringify(spec, null, 2) : stringify(spec, { indent: 2 });
}

export function parseSpec(source: string, format: SpecFormat): Record<string, unknown> {
  const value: unknown = format === "json" ? JSON.parse(source) : parse(source);
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new Error("Strategy document must be an object.");
  }
  return value as Record<string, unknown>;
}

export function SpecEditor({ value, onChange, format, onFormatChange, label = "Strategy spec" }: {
  value: string; onChange: (value: string) => void; format: SpecFormat;
  onFormatChange: (format: SpecFormat) => void; label?: string;
}) {
  const switchFormat = (next: SpecFormat) => {
    try { onChange(serializeSpec(parseSpec(value, format), next)); } catch { /* Preserve invalid text. */ }
    onFormatChange(next);
  };
  return <div className="min-w-0 space-y-2">
    <div className="flex items-center justify-between gap-3"><label htmlFor="spec-editor" className="text-sm font-medium text-gray-700 dark:text-gray-300">{label}</label><div className="flex gap-1"><Button type="button" size="sm" variant={format === "json" ? "primary" : "ghost"} onClick={() => switchFormat("json")}>JSON</Button><Button type="button" size="sm" variant={format === "yaml" ? "primary" : "ghost"} onClick={() => switchFormat("yaml")}>YAML</Button></div></div>
    <textarea id="spec-editor" spellCheck={false} value={value} onChange={(event) => onChange(event.target.value)} className="min-h-[420px] w-full resize-y rounded-xl border border-gray-300 bg-white p-4 font-mono text-xs text-gray-800 outline-none focus:border-brand-500 focus:ring-3 focus:ring-brand-500/10 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-200" />
  </div>;
}
