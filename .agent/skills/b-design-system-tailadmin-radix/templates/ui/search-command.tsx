import * as React from "react";
import { useNavigate } from "react-router";
import {
  Command,
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
  CommandShortcut,
} from "@/components/ui/command";

export type SearchCommandItem = {
  id: string;
  label: string;
  keywords?: string[];
  icon?: React.ReactNode;
  shortcut?: string;
  href?: string;
  onSelect?: () => void;
  disabled?: boolean;
};

export type SearchCommandGroup = {
  heading: string;
  items: SearchCommandItem[];
};

export type SearchCommandProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  groups: SearchCommandGroup[];
  placeholder?: string;
  emptyMessage?: string;
  /** 覆盖默认 href navigate；无 react-router 时必传。见 migration-notes/MN-02 */
  onItemSelect?: (item: SearchCommandItem) => void;
};

export function SearchCommand({
  open,
  onOpenChange,
  groups,
  placeholder = "搜索或输入命令...",
  emptyMessage = "没有找到结果。",
  onItemSelect,
}: SearchCommandProps) {
  const navigate = useNavigate();

  const handleSelect = (item: SearchCommandItem) => {
    onOpenChange(false);
    if (onItemSelect) {
      onItemSelect(item);
      return;
    }
    if (item.onSelect) {
      item.onSelect();
      return;
    }
    if (item.href) {
      navigate(item.href);
    }
  };

  return (
    <CommandDialog open={open} onOpenChange={onOpenChange}>
      <CommandInput placeholder={placeholder} />
      <CommandList>
        <CommandEmpty>{emptyMessage}</CommandEmpty>
        {groups.map((group, index) => (
          <React.Fragment key={group.heading}>
            {index > 0 ? <CommandSeparator /> : null}
            <CommandGroup heading={group.heading}>
              {group.items.map((item) => (
                <CommandItem
                  key={item.id}
                  value={[item.label, ...(item.keywords ?? [])].join(" ")}
                  disabled={item.disabled}
                  onSelect={() => handleSelect(item)}
                >
                  {item.icon}
                  <span>{item.label}</span>
                  {item.shortcut ? (
                    <CommandShortcut>{item.shortcut}</CommandShortcut>
                  ) : null}
                </CommandItem>
              ))}
            </CommandGroup>
          </React.Fragment>
        ))}
      </CommandList>
    </CommandDialog>
  );
}

export function useSearchCommand() {
  const [open, setOpen] = React.useState(false);

  React.useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setOpen((current) => !current);
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, []);

  return { open, setOpen };
}

export type ComboboxOption = {
  value: string;
  label: string;
  keywords?: string[];
};

export type ComboboxPanelProps = {
  options: ComboboxOption[];
  value?: string;
  onValueChange?: (value: string) => void;
  placeholder?: string;
  emptyMessage?: string;
  className?: string;
};

/**
 * Popover + Command combobox panel for MultiSelect / searchable Select.
 * Pair with PopoverTrigger in the host component.
 */
export function ComboboxPanel({
  options,
  value,
  onValueChange,
  placeholder = "搜索...",
  emptyMessage = "没有找到选项。",
  className,
}: ComboboxPanelProps) {
  return (
    <div className={className}>
      <Command>
        <CommandInput placeholder={placeholder} />
        <CommandList>
          <CommandEmpty>{emptyMessage}</CommandEmpty>
          <CommandGroup>
            {options.map((option) => (
              <CommandItem
                key={option.value}
                value={[option.label, ...(option.keywords ?? [])].join(" ")}
                onSelect={() => onValueChange?.(option.value)}
              >
                <span
                  className={
                    value === option.value
                      ? "text-brand-500"
                      : "text-gray-700 dark:text-gray-300"
                  }
                >
                  {option.label}
                </span>
              </CommandItem>
            ))}
          </CommandGroup>
        </CommandList>
      </Command>
    </div>
  );
}
