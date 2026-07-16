import * as React from "react";
import { useVirtualizer } from "@tanstack/react-virtual";
import { Check } from "lucide-react";
import { cn } from "@/lib/utils";
import { CommandGroup, CommandItem } from "@/components/ui/command";
import type { AutocompleteOption } from "@/components/ui/autocomplete";

type VirtualListProps = {
  options: AutocompleteOption[];
  selected: string[];
  itemHeight: number;
  overscan?: number;
  onToggle: (value: string) => void;
  scrollElementRef: React.RefObject<HTMLElement | null>;
};

export function AutocompleteVirtualList({
  options,
  selected,
  itemHeight,
  overscan = 5,
  onToggle,
  scrollElementRef,
}: VirtualListProps) {
  const virtualizer = useVirtualizer({
    count: options.length,
    getScrollElement: () => scrollElementRef.current,
    estimateSize: () => itemHeight,
    overscan,
  });

  const virtualItems = virtualizer.getVirtualItems();
  const totalSize = virtualizer.getTotalSize();

  return (
    <CommandGroup>
      <div style={{ height: totalSize, position: "relative", width: "100%" }}>
        {virtualItems.map((virtualItem) => {
          const option = options[virtualItem.index];
          const isSelected = selected.includes(option.value);

          return (
            <CommandItem
              key={option.value}
              value={option.value}
              disabled={option.disabled}
              onSelect={() => onToggle(option.value)}
              style={{
                position: "absolute",
                top: 0,
                left: 0,
                width: "100%",
                height: itemHeight,
                transform: `translateY(${virtualItem.start}px)`,
              }}
            >
              <Check className={cn("size-4", isSelected ? "opacity-100" : "opacity-0")} />
              {option.label}
            </CommandItem>
          );
        })}
      </div>
    </CommandGroup>
  );
}
