import * as React from "react";
import { Button } from "@/components/ui/button";

export function schemaInitialValues(schema: Record<string, unknown>): Record<string, unknown> {
  const properties = typeof schema["properties"] === "object" && schema["properties"]
    ? schema["properties"] as Record<string, Record<string, unknown>>
    : {};
  return Object.fromEntries(Object.entries(properties).flatMap(([key, definition]) => {
    if (definition["default"] !== undefined) return [[key, definition["default"]]];
    return definition["type"] === "boolean" ? [[key, false]] : [];
  }));
}

export function validateSchemaValues(schema: Record<string, unknown>, values: Record<string, unknown>): string | null {
  const required = Array.isArray(schema["required"])
    ? schema["required"].filter((item): item is string => typeof item === "string")
    : [];
  const missing = required.find((key) => values[key] === undefined || values[key] === "");
  return missing ? `${missing} 为必填项。` : null;
}

export function SchemaForm({ schema, submitLabel, busy, icon, values, onValuesChange, onSubmit }: {
  schema: Record<string, unknown>;
  submitLabel: string;
  busy: boolean;
  icon?: React.ReactNode;
  values?: Record<string, unknown>;
  onValuesChange?: (value: Record<string, unknown>) => void;
  onSubmit: (value: Record<string, unknown>) => void;
}) {
  const properties = typeof schema["properties"] === "object" && schema["properties"]
    ? schema["properties"] as Record<string, Record<string, unknown>>
    : {};
  const required = new Set(
    Array.isArray(schema["required"])
      ? schema["required"].filter((item): item is string => typeof item === "string")
      : [],
  );
  const [internalValues, setInternalValues] = React.useState<Record<string, unknown>>(() => schemaInitialValues(schema));
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
    const validationError = validateSchemaValues(schema, currentValues);
    if (validationError) {
      setError(validationError);
      return;
    }
    setError(null);
    onSubmit(currentValues);
  };

  return <form className="min-w-0 space-y-3" onSubmit={submit}>
    {Object.entries(properties).map(([key, definition]) => {
      const type = definition["type"];
      const label = typeof definition["title"] === "string" ? definition["title"] : key;
      const description = typeof definition["description"] === "string" ? definition["description"] : "";
      const currentValue = currentValues[key];
      const displayValue = typeof currentValue === "string" || typeof currentValue === "number" ? String(currentValue) : "";
      if (type === "boolean") {
        return <label key={key} className="block rounded-xl border border-gray-200 p-3 dark:border-gray-800">
          <span className="flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-gray-300"><input type="checkbox" checked={currentValue === true} onChange={(event) => updateValue(key, event.target.checked)} />{label}{required.has(key) ? " *" : ""}</span>
          {description ? <span className="mt-1 block pl-6 text-xs text-gray-500">{description}</span> : null}
        </label>;
      }
      const options = Array.isArray(definition["enum"]) ? definition["enum"].filter((item): item is string | number => typeof item === "string" || typeof item === "number") : [];
      return <label key={key} className="block min-w-0 text-sm">
        <span className="mb-1 block font-medium text-gray-700 dark:text-gray-300">{label}{required.has(key) ? " *" : ""}</span>
        {options.length ? <select className="h-11 w-full min-w-0 rounded-lg border border-gray-300 bg-transparent px-3 outline-none focus-visible:ring-3 focus-visible:ring-brand-500/20 dark:border-gray-700 dark:bg-gray-900" value={displayValue} onChange={(event) => updateValue(key, event.target.value === "" ? undefined : type === "number" || type === "integer" ? Number(event.target.value) : event.target.value)}><option value="">请选择{label}</option>{options.map((option) => <option key={option} value={option}>{option}</option>)}</select> : <input
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
    <Button className="w-full sm:w-auto" type="submit" loading={busy}>{icon}{submitLabel}</Button>
  </form>;
}
