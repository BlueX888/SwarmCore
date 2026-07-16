import * as React from "react";
import { cn } from "@/lib/utils";
import { Chip } from "@/components/ui/chip";
import { Input } from "@/components/ui/input";

export type TagsInputProps = {
  value: string[];
  onChange: (tags: string[]) => void;
  placeholder?: string;
  maxTags?: number;
  disabled?: boolean;
  readOnly?: boolean;
  className?: string;
};

function normalizeTag(raw: string) {
  return raw.trim();
}

export function TagsInput({
  value,
  onChange,
  placeholder = "输入后按 Enter 添加",
  maxTags,
  disabled = false,
  readOnly = false,
  className,
}: TagsInputProps) {
  const [draft, setDraft] = React.useState("");
  const inputRef = React.useRef<HTMLInputElement>(null);

  const addTag = (raw: string) => {
    const tag = normalizeTag(raw);
    if (!tag) return;
    if (value.includes(tag)) return;
    if (maxTags != null && value.length >= maxTags) return;
    onChange([...value, tag]);
    setDraft("");
  };

  const removeTag = (tag: string) => {
    onChange(value.filter((item) => item !== tag));
  };

  const handleKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "Enter") {
      event.preventDefault();
      addTag(draft);
      return;
    }
    if (event.key === "Backspace" && draft === "" && value.length > 0) {
      onChange(value.slice(0, -1));
    }
  };

  return (
    <div
      className={cn(
        "flex min-h-11 flex-wrap items-center gap-2 rounded-lg border border-gray-300 bg-white px-3 py-2 dark:border-gray-700 dark:bg-gray-900",
        disabled && "cursor-not-allowed opacity-60",
        className,
      )}
      onClick={() => inputRef.current?.focus()}
    >
      {value.map((tag) => (
        <Chip
          key={tag}
          color="neutral"
          variant="outlined"
          size="sm"
          onDelete={disabled || readOnly ? undefined : () => removeTag(tag)}
          deleteLabel={`移除 ${tag}`}
        >
          {tag}
        </Chip>
      ))}
      {!readOnly ? (
        <Input
          ref={inputRef}
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={value.length === 0 ? placeholder : ""}
          disabled={disabled || (maxTags != null && value.length >= maxTags)}
          inputSkin="borderless"
          className="h-8 min-w-[120px] flex-1 border-0 px-0 py-0 shadow-none focus-visible:ring-0"
        />
      ) : null}
    </div>
  );
}
