import * as React from "react";
import { ChevronLeft, ChevronRight, GripVertical } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  DndContext,
  SortableContext,
  closestCenter,
  useSortableItem,
  useSortableList,
} from "@/lib/use-sortable-list";

export type TransferItem = {
  key: string;
  title: React.ReactNode;
  description?: React.ReactNode;
  disabled?: boolean;
};

export type TransferProps = {
  dataSource: TransferItem[];
  targetKeys: string[];
  onChange: (targetKeys: string[]) => void;
  titles?: [string, string];
  showSearch?: boolean;
  oneWay?: boolean;
  render?: (item: TransferItem) => React.ReactNode;
  className?: string;
  /** 目标栏（右侧）内拖拽排序，对标 PrimeVue PickList */
  targetSortable?: boolean;
  onTargetOrderChange?: (orderedKeys: string[]) => void;
};

function filterItems(items: TransferItem[], query: string): TransferItem[] {
  if (!query.trim()) return items;
  const lower = query.toLowerCase();
  return items.filter((item) => {
    const title = typeof item.title === "string" ? item.title : String(item.title);
    const description =
      item.description == null
        ? ""
        : typeof item.description === "string"
          ? item.description
          : String(item.description);
    return title.toLowerCase().includes(lower) || description.toLowerCase().includes(lower);
  });
}

type TransferPanelProps = {
  title: string;
  items: TransferItem[];
  selectedKeys: Set<string>;
  onToggle: (key: string) => void;
  onToggleAll: (keys: string[], checked: boolean) => void;
  showSearch?: boolean;
  searchQuery: string;
  onSearchChange: (query: string) => void;
  render?: (item: TransferItem) => React.ReactNode;
};

function TransferPanel({
  title,
  items,
  selectedKeys,
  onToggle,
  onToggleAll,
  showSearch,
  searchQuery,
  onSearchChange,
  render,
}: TransferPanelProps) {
  const enabledItems = items.filter((item) => !item.disabled);
  const allChecked = enabledItems.length > 0 && enabledItems.every((item) => selectedKeys.has(item.key));
  const someChecked = enabledItems.some((item) => selectedKeys.has(item.key));

  return (
    <Card variant="outlined" className="flex min-h-[280px] flex-col overflow-hidden rounded-xl">
      <CardHeader className="gap-2 border-b border-gray-200 px-4 py-3 dark:border-gray-800">
        <div className="flex items-center gap-2">
          <Checkbox
            checked={allChecked ? true : someChecked ? "indeterminate" : false}
            onCheckedChange={(checked) =>
              onToggleAll(
                enabledItems.map((item) => item.key),
                checked === true,
              )
            }
            aria-label={`全选${title}`}
          />
          <CardTitle className="text-sm font-medium">{title}</CardTitle>
          <span className="ml-auto text-theme-xs text-gray-500 dark:text-gray-400">
            {selectedKeys.size}/{items.length}
          </span>
        </div>
        {showSearch ? (
          <Input
            inputSkin="borderless"
            placeholder="搜索…"
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            className="h-9"
          />
        ) : null}
      </CardHeader>
      <CardContent className="flex-1 p-0">
        <ScrollArea className="h-[220px]">
          <ul className="p-2">
            {items.length === 0 ? (
              <li className="px-3 py-6 text-center text-sm text-gray-500 dark:text-gray-400">暂无数据</li>
            ) : (
              items.map((item) => (
                <li key={item.key}>
                  <label
                    className={cn(
                      "flex cursor-pointer items-start gap-2 rounded-lg px-3 py-2 text-sm transition-colors hover:bg-gray-50 dark:hover:bg-white/5",
                      item.disabled && "cursor-not-allowed opacity-50",
                    )}
                  >
                    <Checkbox
                      checked={selectedKeys.has(item.key)}
                      disabled={item.disabled}
                      onCheckedChange={() => onToggle(item.key)}
                      className="mt-0.5"
                      aria-label={`选择 ${typeof item.title === "string" ? item.title : item.key}`}
                    />
                    <span className="min-w-0 flex-1">
                      {render ? render(item) : (
                        <>
                          <span className="block truncate text-gray-800 dark:text-white/90">{item.title}</span>
                          {item.description ? (
                            <span className="mt-0.5 block truncate text-theme-xs text-gray-500 dark:text-gray-400">
                              {item.description}
                            </span>
                          ) : null}
                        </>
                      )}
                    </span>
                  </label>
                </li>
              ))
            )}
          </ul>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}

function SortableTransferRow({
  item,
  selectedKeys,
  onToggle,
  render,
}: {
  item: TransferItem;
  selectedKeys: Set<string>;
  onToggle: (key: string) => void;
  render?: (item: TransferItem) => React.ReactNode;
}) {
  const { setNodeRef, style, attributes, listeners, isDragging } = useSortableItem(
    item.key,
    item.disabled,
  );

  return (
    <li ref={setNodeRef} style={style} className={cn(isDragging && "z-10")}>
      <div
        className={cn(
          "flex items-start gap-1 rounded-lg px-2 py-2 text-sm transition-colors hover:bg-gray-50 dark:hover:bg-white/5",
          item.disabled && "opacity-50",
        )}
      >
        <button
          type="button"
          className="mt-0.5 shrink-0 cursor-grab touch-none p-1 text-gray-400 hover:text-gray-600 active:cursor-grabbing dark:hover:text-gray-300"
          aria-label={`拖拽排序 ${typeof item.title === "string" ? item.title : item.key}`}
          {...attributes}
          {...listeners}
        >
          <GripVertical className="size-4" />
        </button>
        <label
          className={cn(
            "flex min-w-0 flex-1 cursor-pointer items-start gap-2",
            item.disabled && "cursor-not-allowed",
          )}
        >
          <Checkbox
            checked={selectedKeys.has(item.key)}
            disabled={item.disabled}
            onCheckedChange={() => onToggle(item.key)}
            className="mt-0.5"
            aria-label={`选择 ${typeof item.title === "string" ? item.title : item.key}`}
          />
          <span className="min-w-0 flex-1">
            {render ? (
              render(item)
            ) : (
              <>
                <span className="block truncate text-gray-800 dark:text-white/90">{item.title}</span>
                {item.description ? (
                  <span className="mt-0.5 block truncate text-theme-xs text-gray-500 dark:text-gray-400">
                    {item.description}
                  </span>
                ) : null}
              </>
            )}
          </span>
        </label>
      </div>
    </li>
  );
}

type SortableTransferPanelProps = Omit<TransferPanelProps, "onToggleAll"> & {
  onReorder: (items: TransferItem[]) => void;
};

function SortableTransferPanel({
  title,
  items,
  selectedKeys,
  onToggle,
  onReorder,
  showSearch,
  searchQuery,
  onSearchChange,
  render,
}: SortableTransferPanelProps) {
  const enabledItems = items.filter((item) => !item.disabled);
  const allChecked = enabledItems.length > 0 && enabledItems.every((item) => selectedKeys.has(item.key));
  const someChecked = enabledItems.some((item) => selectedKeys.has(item.key));
  const { sensors, handleDragEnd, strategy, ids } = useSortableList({
    items,
    getId: (item) => item.key,
    onReorder,
  });

  return (
    <Card variant="outlined" className="flex min-h-[280px] flex-col overflow-hidden rounded-xl">
      <CardHeader className="gap-2 border-b border-gray-200 px-4 py-3 dark:border-gray-800">
        <div className="flex items-center gap-2">
          <Checkbox
            checked={allChecked ? true : someChecked ? "indeterminate" : false}
            onCheckedChange={(checked) => {
              const keys = enabledItems.map((item) => item.key);
              keys.forEach((key) => {
                if (checked === true && !selectedKeys.has(key)) onToggle(key);
                if (checked === false && selectedKeys.has(key)) onToggle(key);
              });
            }}
            aria-label={`全选${title}`}
          />
          <CardTitle className="text-sm font-medium">{title}</CardTitle>
          <span className="ml-auto text-theme-xs text-gray-500 dark:text-gray-400">
            {selectedKeys.size}/{items.length}
          </span>
        </div>
        {showSearch ? (
          <Input
            inputSkin="borderless"
            placeholder="搜索…"
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            className="h-9"
          />
        ) : null}
      </CardHeader>
      <CardContent className="flex-1 p-0">
        <ScrollArea className="h-[220px]">
          <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
            <SortableContext items={ids} strategy={strategy}>
              <ul className="p-2">
                {items.length === 0 ? (
                  <li className="px-3 py-6 text-center text-sm text-gray-500 dark:text-gray-400">暂无数据</li>
                ) : (
                  items.map((item) => (
                    <SortableTransferRow
                      key={item.key}
                      item={item}
                      selectedKeys={selectedKeys}
                      onToggle={onToggle}
                      render={render}
                    />
                  ))
                )}
              </ul>
            </SortableContext>
          </DndContext>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}

export function Transfer({
  dataSource,
  targetKeys,
  onChange,
  titles = ["可选", "已选"],
  showSearch = false,
  oneWay = false,
  render,
  className,
  targetSortable = false,
  onTargetOrderChange,
}: TransferProps) {
  const [leftSelected, setLeftSelected] = React.useState<Set<string>>(new Set());
  const [rightSelected, setRightSelected] = React.useState<Set<string>>(new Set());
  const [leftQuery, setLeftQuery] = React.useState("");
  const [rightQuery, setRightQuery] = React.useState("");

  const targetSet = React.useMemo(() => new Set(targetKeys), [targetKeys]);
  const sourceItems = React.useMemo(
    () => dataSource.filter((item) => !targetSet.has(item.key)),
    [dataSource, targetSet],
  );
  const targetItems = React.useMemo(
    () => targetKeys.map((key) => dataSource.find((item) => item.key === key)).filter(Boolean) as TransferItem[],
    [dataSource, targetKeys],
  );

  const filteredSource = React.useMemo(
    () => filterItems(sourceItems, leftQuery),
    [sourceItems, leftQuery],
  );
  const filteredTarget = React.useMemo(
    () => filterItems(targetItems, rightQuery),
    [targetItems, rightQuery],
  );

  const toggleInSet = (set: Set<string>, key: string) => {
    const next = new Set(set);
    if (next.has(key)) next.delete(key);
    else next.add(key);
    return next;
  };

  const toggleAllInSet = (set: Set<string>, keys: string[], checked: boolean) => {
    const next = new Set(set);
    keys.forEach((key) => {
      if (checked) next.add(key);
      else next.delete(key);
    });
    return next;
  };

  const moveToTarget = () => {
    const keysToMove = [...leftSelected];
    if (keysToMove.length === 0) return;
    onChange([...targetKeys, ...keysToMove.filter((key) => !targetSet.has(key))]);
    setLeftSelected(new Set());
  };

  const moveToSource = () => {
    const keysToRemove = new Set(rightSelected);
    if (keysToRemove.size === 0) return;
    onChange(targetKeys.filter((key) => !keysToRemove.has(key)));
    setRightSelected(new Set());
  };

  const handleTargetReorder = (reorderedItems: TransferItem[]) => {
    const nextKeys = reorderedItems.map((item) => item.key);
    onChange(nextKeys);
    onTargetOrderChange?.(nextKeys);
  };

  return (
    <div className={cn("grid grid-cols-[1fr_auto_1fr] items-stretch gap-4", className)}>
      <TransferPanel
        title={titles[0]}
        items={filteredSource}
        selectedKeys={leftSelected}
        onToggle={(key) => setLeftSelected((prev) => toggleInSet(prev, key))}
        onToggleAll={(keys, checked) => setLeftSelected((prev) => toggleAllInSet(prev, keys, checked))}
        showSearch={showSearch}
        searchQuery={leftQuery}
        onSearchChange={setLeftQuery}
        render={render}
      />

      <div className="flex flex-col items-center justify-center gap-2">
        <Button
          type="button"
          variant="outline"
          size="icon"
          aria-label="移入"
          disabled={leftSelected.size === 0}
          onClick={moveToTarget}
        >
          <ChevronRight className="size-4" />
        </Button>
        {!oneWay ? (
          <Button
            type="button"
            variant="outline"
            size="icon"
            aria-label="移出"
            disabled={rightSelected.size === 0}
            onClick={moveToSource}
          >
            <ChevronLeft className="size-4" />
          </Button>
        ) : null}
      </div>

      {targetSortable ? (
        <SortableTransferPanel
          title={titles[1]}
          items={filteredTarget}
          selectedKeys={rightSelected}
          onToggle={(key) => setRightSelected((prev) => toggleInSet(prev, key))}
          onReorder={handleTargetReorder}
          showSearch={showSearch}
          searchQuery={rightQuery}
          onSearchChange={setRightQuery}
          render={render}
        />
      ) : (
        <TransferPanel
          title={titles[1]}
          items={filteredTarget}
          selectedKeys={rightSelected}
          onToggle={(key) => setRightSelected((prev) => toggleInSet(prev, key))}
          onToggleAll={(keys, checked) => setRightSelected((prev) => toggleAllInSet(prev, keys, checked))}
          showSearch={showSearch}
          searchQuery={rightQuery}
          onSearchChange={setRightQuery}
          render={render}
        />
      )}
    </div>
  );
}
