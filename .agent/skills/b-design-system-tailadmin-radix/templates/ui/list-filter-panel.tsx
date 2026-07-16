import { useEffect, useState } from "react";
import type { ListFilterField } from "@/components/ui/list-filter-types";
import {
  appliedToDraftValues,
  emptyFilterValues,
} from "@/components/ui/list-filter-utils";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Sheet,
  SheetContent,
  SheetFooter,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";

type Props = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  fields: ListFilterField[];
  values: Record<string, string | undefined>;
  onApply: (values: Record<string, string | undefined>) => void;
  panel?: "popover" | "drawer";
  disabled?: boolean;
  trigger: React.ReactNode;
};

function FilterFields({
  fields,
  draft,
  setDraft,
  disabled,
}: {
  fields: ListFilterField[];
  draft: Record<string, string | undefined>;
  setDraft: React.Dispatch<React.SetStateAction<Record<string, string | undefined>>>;
  disabled?: boolean;
}) {
  return (
    <div className="flex flex-col gap-4">
      {fields.map((field) => {
        const id = `list-filter-${field.id}`;
        if (field.kind === "select") {
          return (
            <div key={field.id} className="space-y-2">
              <Label htmlFor={id}>{field.label}</Label>
              <Select
                value={draft[field.id] ?? field.allValue ?? "all"}
                onValueChange={(v) => setDraft((d) => ({ ...d, [field.id]: v }))}
                disabled={disabled}
              >
                <SelectTrigger id={id} aria-label={field.label} className="h-11 w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {field.options.map((opt) => (
                    <SelectItem key={opt.value} value={opt.value}>
                      {opt.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          );
        }
        if (field.kind === "checkbox") {
          return (
            <div key={field.id} className="flex items-center gap-2">
              <Checkbox
                id={id}
                checked={draft[field.id] === "true"}
                disabled={disabled}
                onCheckedChange={(checked) =>
                  setDraft((d) => ({ ...d, [field.id]: checked === true ? "true" : undefined }))
                }
              />
              <Label htmlFor={id} className="font-normal">
                {field.label}
              </Label>
            </div>
          );
        }
        return (
          <div key={field.id} className="space-y-2">
            <Label htmlFor={id}>{field.label}</Label>
            <Input
              id={id}
              value={draft[field.id] ?? ""}
              onChange={(e) => setDraft((d) => ({ ...d, [field.id]: e.target.value || undefined }))}
              placeholder={field.placeholder}
              disabled={disabled}
              className="h-11"
              aria-label={field.label}
            />
          </div>
        );
      })}
    </div>
  );
}

function FilterFooter({
  onReset,
  onCancel,
  onApply,
  disabled,
}: {
  onReset: () => void;
  onCancel: () => void;
  onApply: () => void;
  disabled?: boolean;
}) {
  return (
    <div className="flex w-full items-center justify-between gap-3">
      <Button type="button" variant="outline" disabled={disabled} onClick={onReset}>
        重置
      </Button>
      <div className="flex items-center gap-2">
        <Button type="button" variant="outline" disabled={disabled} onClick={onCancel}>
          取消
        </Button>
        <Button type="button" disabled={disabled} onClick={onApply}>
          应用
        </Button>
      </div>
    </div>
  );
}

export function ListFilterPanel({
  open,
  onOpenChange,
  fields,
  values,
  onApply,
  panel = "popover",
  disabled,
  trigger,
}: Props) {
  const [draft, setDraft] = useState<Record<string, string | undefined>>(() =>
    appliedToDraftValues(fields, values),
  );

  useEffect(() => {
    if (open) setDraft(appliedToDraftValues(fields, values));
  }, [open, fields, values]);

  const handleApply = () => {
    onApply(draft);
    onOpenChange(false);
  };

  const body = (
    <FilterFields fields={fields} draft={draft} setDraft={setDraft} disabled={disabled} />
  );

  if (panel === "drawer") {
    return (
      <>
        {trigger}
        <Sheet modal={false} open={open} onOpenChange={onOpenChange}>
          <SheetContent side="right" size="filter" showOverlay={false} className="flex flex-col">
            <SheetHeader>
              <SheetTitle>筛选</SheetTitle>
            </SheetHeader>
            <div className="min-h-0 flex-1 overflow-y-auto px-6 py-4">{body}</div>
            <SheetFooter className="shrink-0">
              <FilterFooter
                onReset={() => setDraft(emptyFilterValues(fields))}
                onCancel={() => onOpenChange(false)}
                onApply={handleApply}
                disabled={disabled}
              />
            </SheetFooter>
          </SheetContent>
        </Sheet>
      </>
    );
  }

  return (
    <Popover open={open} onOpenChange={onOpenChange}>
      <PopoverTrigger asChild>{trigger}</PopoverTrigger>
      <PopoverContent align="start" className="w-80 p-0">
        <div className="p-4">{body}</div>
        <div className="border-t border-gray-200 px-4 py-3 dark:border-gray-800">
          <FilterFooter
            onReset={() => setDraft(emptyFilterValues(fields))}
            onCancel={() => onOpenChange(false)}
            onApply={handleApply}
            disabled={disabled}
          />
        </div>
      </PopoverContent>
    </Popover>
  );
}
