import * as React from "react";
import { cn } from "@/lib/utils";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Popover, PopoverAnchor, PopoverContent } from "@/components/ui/popover";
import { ScrollArea } from "@/components/ui/scroll-area";
import { inputVariants } from "@/components/ui/input";

type InputSkin = "outlined" | "filled" | "borderless" | "underlined";

export type MentionsOption = {
  value: string;
  label: string;
  avatar?: string;
};

export type MentionsProps = {
  value?: string;
  onChange?: (value: string) => void;
  options: MentionsOption[];
  onSearch?: (query: string) => void;
  prefix?: string;
  rows?: number;
  inputSkin?: InputSkin;
  placeholder?: string;
  disabled?: boolean;
  className?: string;
};

type MentionState = {
  start: number;
  query: string;
};

function getMentionAtCursor(text: string, cursor: number, prefix: string): MentionState | null {
  const before = text.slice(0, cursor);
  const atIndex = before.lastIndexOf(prefix);
  if (atIndex === -1) return null;

  const fragment = before.slice(atIndex + prefix.length);
  if (/\s/.test(fragment)) return null;

  return { start: atIndex, query: fragment };
}

export function Mentions({
  value = "",
  onChange,
  options,
  onSearch,
  prefix = "@",
  rows = 3,
  inputSkin = "outlined",
  placeholder = "输入内容，使用 @ 提及…",
  disabled = false,
  className,
}: MentionsProps) {
  const textareaRef = React.useRef<HTMLTextAreaElement>(null);
  const [open, setOpen] = React.useState(false);
  const [mention, setMention] = React.useState<MentionState | null>(null);
  const [activeIndex, setActiveIndex] = React.useState(0);

  const filteredOptions = React.useMemo(() => {
    if (!mention) return options;
    const query = mention.query.toLowerCase();
    return options.filter(
      (option) =>
        option.label.toLowerCase().includes(query) ||
        option.value.toLowerCase().includes(query),
    );
  }, [mention, options]);

  React.useEffect(() => {
    if (mention) {
      onSearch?.(mention.query);
    }
  }, [mention, onSearch]);

  React.useEffect(() => {
    setActiveIndex(0);
  }, [mention?.query, filteredOptions.length]);

  const detectMention = (text: string, cursor: number) => {
    const next = getMentionAtCursor(text, cursor, prefix);
    setMention(next);
  };

  const handleChange = (event: React.ChangeEvent<HTMLTextAreaElement>) => {
    const nextValue = event.target.value;
    onChange?.(nextValue);
    detectMention(nextValue, event.target.selectionStart ?? nextValue.length);
  };

  const handleKeyUp = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    const target = event.currentTarget;
    detectMention(target.value, target.selectionStart ?? target.value.length);
  };

  const insertMention = (option: MentionsOption) => {
    if (!mention || !textareaRef.current) return;

    const before = value.slice(0, mention.start);
    const after = value.slice(textareaRef.current.selectionStart ?? value.length);
    const insertion = `${prefix}${option.label} `;
    const nextValue = `${before}${insertion}${after}`;

    onChange?.(nextValue);
    setOpen(false);
    setMention(null);

    const nextCursor = before.length + insertion.length;
    requestAnimationFrame(() => {
      textareaRef.current?.focus();
      textareaRef.current?.setSelectionRange(nextCursor, nextCursor);
    });
  };

  const handleKeyDown = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (!open || filteredOptions.length === 0) return;

    if (event.key === "ArrowDown") {
      event.preventDefault();
      setActiveIndex((prev) => (prev + 1) % filteredOptions.length);
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setActiveIndex((prev) => (prev - 1 + filteredOptions.length) % filteredOptions.length);
    } else if (event.key === "Enter" && mention) {
      event.preventDefault();
      insertMention(filteredOptions[activeIndex]);
    } else if (event.key === "Escape") {
      setOpen(false);
      setMention(null);
    }
  };

  React.useEffect(() => {
    if (mention && filteredOptions.length > 0) {
      setOpen(true);
    } else if (!mention) {
      setOpen(false);
    }
  }, [filteredOptions.length, mention]);

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverAnchor asChild>
        <textarea
          ref={textareaRef}
          value={value}
          onChange={handleChange}
          onKeyUp={handleKeyUp}
          onKeyDown={handleKeyDown}
          rows={rows}
          disabled={disabled}
          placeholder={placeholder}
          className={cn(
            inputVariants({ inputSkin, fieldState: "default", size: "md" }),
            "min-h-0 resize-y py-3",
            className,
          )}
        />
      </PopoverAnchor>
      <PopoverContent
        className="w-[var(--radix-popover-trigger-width)] p-0"
        align="start"
        onOpenAutoFocus={(event) => event.preventDefault()}
      >
        <ScrollArea className="max-h-[220px]">
          <ul className="p-1">
            {filteredOptions.map((option, index) => (
              <li key={option.value}>
                <button
                  type="button"
                  className={cn(
                    "flex w-full items-center gap-2 rounded-md px-2 py-2 text-left text-sm transition-colors",
                    index === activeIndex
                      ? "bg-brand-50 text-brand-600 dark:bg-brand-500/15 dark:text-brand-400"
                      : "text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-white/5",
                  )}
                  onMouseDown={(event) => event.preventDefault()}
                  onClick={() => insertMention(option)}
                >
                  {option.avatar ? (
                    <Avatar size="sm" className="size-6">
                      <AvatarImage src={option.avatar} alt={option.label} />
                      <AvatarFallback name={option.label} className="text-theme-xs" />
                    </Avatar>
                  ) : null}
                  <span className="truncate">{option.label}</span>
                </button>
              </li>
            ))}
          </ul>
        </ScrollArea>
      </PopoverContent>
    </Popover>
  );
}
