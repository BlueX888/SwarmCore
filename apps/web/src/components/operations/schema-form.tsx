import * as React from "react";
import { Button } from "@/components/ui/button";

const FIELD_LABELS: Record<string, string> = {
  approved: "确认批准",
  comment: "审批意见",
  confirmations: "核对说明",
  decision: "处理决定",
  reason: "原因说明",
  notes: "备注",
  topic: "主题",
  query: "检索词",
};

export function schemaFieldLabel(key: string, definition?: Record<string, unknown>): string {
  const titled = definition && typeof definition["title"] === "string" ? definition["title"] : null;
  return titled || FIELD_LABELS[key] || key;
}

export function schemaInitialValues(schema: Record<string, unknown>): Record<string, unknown> {
  const properties = typeof schema["properties"] === "object" && schema["properties"]
    ? schema["properties"] as Record<string, Record<string, unknown>>
    : {};
  return Object.fromEntries(Object.entries(properties).flatMap(([key, definition]) => {
    if (definition["default"] !== undefined) return [[key, definition["default"]]];
    if (definition["type"] === "boolean") return [[key, false]];
    if (definition["type"] === "array") return [[key, []]];
    return [];
  }));
}

export function validateSchemaValues(schema: Record<string, unknown>, values: Record<string, unknown>): string | null {
  const properties = typeof schema["properties"] === "object" && schema["properties"]
    ? schema["properties"] as Record<string, Record<string, unknown>>
    : {};
  const required = Array.isArray(schema["required"])
    ? schema["required"].filter((item): item is string => typeof item === "string")
    : [];
  const missing = required.find((key) => {
    const value = values[key];
    if (value === undefined || value === "") return true;
    if (Array.isArray(value) && value.length === 0) return true;
    return false;
  });
  if (!missing) return null;
  return `${schemaFieldLabel(missing, properties[missing])} 为必填项。`;
}

export function omitSchemaKeys(schema: Record<string, unknown>, keys: string[]): Record<string, unknown> {
  const omit = new Set(keys);
  const properties = typeof schema["properties"] === "object" && schema["properties"]
    ? Object.fromEntries(
      Object.entries(schema["properties"] as Record<string, unknown>).filter(([key]) => !omit.has(key)),
    )
    : {};
  const required = Array.isArray(schema["required"])
    ? schema["required"].filter((item): item is string => typeof item === "string" && !omit.has(item))
    : [];
  return { ...schema, properties, required };
}

function arrayDisplayValue(value: unknown): string {
  if (Array.isArray(value)) {
    return value
      .map((item) => (typeof item === "string" || typeof item === "number" ? String(item) : JSON.stringify(item)))
      .join("\n");
  }
  return typeof value === "string" ? value : "";
}

function parseArrayInput(raw: string): string[] | undefined {
  const lines = raw.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
  return lines.length ? lines : undefined;
}

export function SchemaForm({ schema, submitLabel, busy, icon, values, onValuesChange, onSubmit, omitKeys, footer }: {
  schema: Record<string, unknown>;
  submitLabel: string;
  busy: boolean;
  icon?: React.ReactNode;
  values?: Record<string, unknown>;
  onValuesChange?: (value: Record<string, unknown>) => void;
  onSubmit: (value: Record<string, unknown>) => void;
  omitKeys?: string[];
  footer?: React.ReactNode;
}) {
  const effectiveSchema = omitKeys?.length ? omitSchemaKeys(schema, omitKeys) : schema;
  const properties = typeof effectiveSchema["properties"] === "object" && effectiveSchema["properties"]
    ? effectiveSchema["properties"] as Record<string, Record<string, unknown>>
    : {};
  const required = new Set(
    Array.isArray(effectiveSchema["required"])
      ? effectiveSchema["required"].filter((item): item is string => typeof item === "string")
      : [],
  );
  const [internalValues, setInternalValues] = React.useState<Record<string, unknown>>(() => schemaInitialValues(effectiveSchema));
  const [error, setError] = React.useState<string | null>(null);
  const currentValues = values ?? internalValues;
  const updateValues = (next: Record<string, unknown>) => {
    if (values === undefined) setInternalValues(next);
    onValuesChange?.(next);
    setError(null);
  };
  const updateValue = (key: string, value: unknown) => {
    const next = Object.fromEntries(Object.entries(currentValues).filter(([currentKey]) => currentKey !== key));
    if (value !== undefined && value !== "") next[key] = value;
    updateValues(next);
  };
  const submit = (event: React.FormEvent) => {
    event.preventDefault();
    const validationError = validateSchemaValues(effectiveSchema, currentValues);
    if (validationError) {
      setError(validationError);
      return;
    }
    setError(null);
    onSubmit(currentValues);
  };
  const propertyEntries = Object.entries(properties);

  return <form className="min-w-0 space-y-4" onSubmit={submit}>
    {propertyEntries.length === 0 ? null : propertyEntries.map(([key, definition]) => {
      const type = definition["type"];
      const label = schemaFieldLabel(key, definition);
      const description = typeof definition["description"] === "string" ? definition["description"] : "";
      const currentValue = currentValues[key];
      const displayValue = typeof currentValue === "string" || typeof currentValue === "number" ? String(currentValue) : "";
      if (type === "boolean") {
        return <label key={key} className="block rounded-xl border border-gray-200 bg-gray-50/70 p-3 dark:border-gray-800 dark:bg-white/[0.03]">
          <span className="flex items-center gap-2 text-sm font-medium text-gray-800 dark:text-gray-200">
            <input type="checkbox" className="size-4 rounded border-gray-300 text-brand-500 focus-visible:ring-brand-500/30" checked={currentValue === true} onChange={(event) => updateValue(key, event.target.checked)} />
            {label}{required.has(key) ? <span className="text-error-500">*</span> : null}
          </span>
          {description ? <span className="mt-1 block pl-6 text-xs text-gray-500">{description}</span> : null}
        </label>;
      }
      if (type === "array") {
        return <label key={key} className="block min-w-0 text-sm">
          <span className="mb-1.5 block font-medium text-gray-800 dark:text-gray-200">{label}{required.has(key) ? <span className="text-error-500"> *</span> : <span className="ml-1 font-normal text-gray-400">（可选）</span>}</span>
          <textarea
            className="min-h-24 w-full min-w-0 rounded-lg border border-gray-300 bg-transparent px-3 py-2 outline-none focus-visible:ring-3 focus-visible:ring-brand-500/20 dark:border-gray-700 dark:bg-gray-900"
            value={arrayDisplayValue(currentValue)}
            placeholder={typeof definition["placeholder"] === "string" ? definition["placeholder"] : "每行一条核对说明"}
            onChange={(event) => updateValue(key, parseArrayInput(event.target.value))}
          />
          {description ? <span className="mt-1 block text-xs text-gray-500">{description}</span> : <span className="mt-1 block text-xs text-gray-400">每行填写一条说明，便于留痕。</span>}
        </label>;
      }
      const options = Array.isArray(definition["enum"]) ? definition["enum"].filter((item): item is string | number => typeof item === "string" || typeof item === "number") : [];
      const isLongText = key === "comment" || key === "reason" || key === "notes" || definition["format"] === "textarea";
      return <label key={key} className="block min-w-0 text-sm">
        <span className="mb-1.5 block font-medium text-gray-800 dark:text-gray-200">{label}{required.has(key) ? <span className="text-error-500"> *</span> : <span className="ml-1 font-normal text-gray-400">（可选）</span>}</span>
        {options.length ? <select className="h-11 w-full min-w-0 rounded-lg border border-gray-300 bg-transparent px-3 outline-none focus-visible:ring-3 focus-visible:ring-brand-500/20 dark:border-gray-700 dark:bg-gray-900" value={displayValue} onChange={(event) => updateValue(key, event.target.value === "" ? undefined : type === "number" || type === "integer" ? Number(event.target.value) : event.target.value)}><option value="">请选择{label}</option>{options.map((option) => <option key={option} value={option}>{option}</option>)}</select> : isLongText ? <textarea
          className="min-h-24 w-full min-w-0 rounded-lg border border-gray-300 bg-transparent px-3 py-2 outline-none focus-visible:ring-3 focus-visible:ring-brand-500/20 dark:border-gray-700 dark:bg-gray-900"
          value={displayValue}
          placeholder={typeof definition["placeholder"] === "string" ? definition["placeholder"] : "例如：已核对材料，同意继续。"}
          onChange={(event) => updateValue(key, event.target.value === "" ? undefined : event.target.value)}
        /> : <input
          className="h-11 w-full min-w-0 rounded-lg border border-gray-300 bg-transparent px-3 outline-none focus-visible:ring-3 focus-visible:ring-brand-500/20 dark:border-gray-700"
          type={type === "number" || type === "integer" ? "number" : "text"}
          value={displayValue}
          placeholder={typeof definition["placeholder"] === "string" ? definition["placeholder"] : undefined}
          onChange={(event) => updateValue(key, event.target.value === "" ? undefined : type === "number" || type === "integer" ? Number(event.target.value) : event.target.value)}
        />}
        {description ? <span className="mt-1 block text-xs text-gray-500">{description}</span> : null}
      </label>;
    })}
    {error ? <p role="alert" className="text-sm text-error-600">{error}</p> : null}
    <div className="flex flex-wrap items-center gap-3">
      <Button className="w-full sm:w-auto" type="submit" loading={busy}>{icon}{submitLabel}</Button>
      {footer}
    </div>
  </form>;
}
