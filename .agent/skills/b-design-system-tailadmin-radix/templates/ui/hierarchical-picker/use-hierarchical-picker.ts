import * as React from "react";
import type { CheckStrategy, HierarchicalNode, HierarchicalPath, LoadDataFn } from "./types";

export type UseHierarchicalPickerOptions = {
  nodes: HierarchicalNode[];
  value?: HierarchicalPath;
  onChange?: (path: HierarchicalPath) => void;
  multiple?: boolean;
  checkedKeys?: string[];
  onCheckedKeysChange?: (keys: string[]) => void;
  checkStrategy?: CheckStrategy;
  loadData?: LoadDataFn;
  showSearch?: boolean;
  filterTreeNode?: (node: HierarchicalNode, query: string) => boolean;
  expandedKeys?: string[];
  onExpandedKeysChange?: (keys: string[]) => void;
  disabled?: boolean;
};

function defaultFilter(node: HierarchicalNode, query: string): boolean {
  const text = typeof node.label === "string" ? node.label : "";
  return text.toLowerCase().includes(query.toLowerCase());
}

function collectDescendantIds(node: HierarchicalNode): string[] {
  const ids = [node.id];
  node.children?.forEach((child) => ids.push(...collectDescendantIds(child)));
  return ids;
}

function findNodeByPath(nodes: HierarchicalNode[], path: string[]): HierarchicalNode | null {
  let current: HierarchicalNode[] = nodes;
  let found: HierarchicalNode | null = null;
  for (const id of path) {
    found = current.find((n) => n.id === id) ?? null;
    if (!found) return null;
    current = found.children ?? [];
  }
  return found;
}

export function useHierarchicalPicker(options: UseHierarchicalPickerOptions) {
  const {
    nodes,
    value = [],
    onChange,
    multiple = false,
    checkedKeys = [],
    onCheckedKeysChange,
    checkStrategy = "child",
    loadData,
    showSearch = false,
    filterTreeNode = defaultFilter,
    expandedKeys: expandedKeysProp,
    onExpandedKeysChange,
    disabled = false,
  } = options;

  const [internalExpanded, setInternalExpanded] = React.useState<string[]>([]);
  const [loadingKeys, setLoadingKeys] = React.useState<Set<string>>(new Set());
  const [loadedNodes, setLoadedNodes] = React.useState<Map<string, HierarchicalNode[]>>(new Map());
  const [searchQuery, setSearchQuery] = React.useState("");

  const expandedKeys = expandedKeysProp ?? internalExpanded;

  const setExpandedKeys = (keys: string[]) => {
    if (expandedKeysProp == null) setInternalExpanded(keys);
    onExpandedKeysChange?.(keys);
  };

  const mergeLoadedChildren = React.useCallback(
    (source: HierarchicalNode[]): HierarchicalNode[] =>
      source.map((node) => {
        const loaded = loadedNodes.get(node.id);
        const children = loaded ?? node.children;
        return children ? { ...node, children: mergeLoadedChildren(children) } : node;
      }),
    [loadedNodes],
  );

  const displayNodes = React.useMemo(() => mergeLoadedChildren(nodes), [nodes, mergeLoadedChildren]);

  const filteredNodes = React.useMemo(() => {
    if (!showSearch || !searchQuery.trim()) return displayNodes;
    const filterRecursive = (list: HierarchicalNode[]): HierarchicalNode[] =>
      list
        .map((node) => {
          const children = node.children ? filterRecursive(node.children) : undefined;
          const selfMatch = filterTreeNode(node, searchQuery);
          if (selfMatch || (children && children.length > 0)) {
            return { ...node, children };
          }
          return null;
        })
        .filter(Boolean) as HierarchicalNode[];
    return filterRecursive(displayNodes);
  }, [displayNodes, showSearch, searchQuery, filterTreeNode]);

  const toggleExpand = async (node: HierarchicalNode) => {
    if (disabled || node.disabled) return;
    const next = new Set(expandedKeys);
    const isExpanded = next.has(node.id);
    if (isExpanded) {
      next.delete(node.id);
      setExpandedKeys([...next]);
      return;
    }
    const hasChildren = (node.children?.length ?? 0) > 0;
    if (!hasChildren && loadData && !node.isLeaf) {
      setLoadingKeys((prev) => new Set(prev).add(node.id));
      try {
        const children = await loadData(node);
        setLoadedNodes((prev) => new Map(prev).set(node.id, children));
      } finally {
        setLoadingKeys((prev) => {
          const n = new Set(prev);
          n.delete(node.id);
          return n;
        });
      }
    }
    next.add(node.id);
    setExpandedKeys([...next]);
  };

  const selectPath = (path: HierarchicalPath) => {
    if (disabled) return;
    onChange?.(path);
  };

  const toggleCheck = (node: HierarchicalNode) => {
    if (!onCheckedKeysChange || disabled || node.disabled) return;
    const next = new Set(checkedKeys);
    const related = collectDescendantIds(node);
    const shouldCheck = !next.has(node.id);
    related.forEach((id) => {
      if (shouldCheck) next.add(id);
      else next.delete(id);
    });
    if (checkStrategy === "parent" && shouldCheck && node.children?.length) {
      related.forEach((id) => next.add(id));
    }
    onCheckedKeysChange([...next]);
  };

  return {
    nodes: filteredNodes,
    value,
    expandedKeys,
    loadingKeys,
    searchQuery,
    setSearchQuery,
    toggleExpand,
    selectPath,
    toggleCheck,
    checkedKeys,
    multiple,
    findNodeByPath: (path: HierarchicalPath) => findNodeByPath(displayNodes, path),
    disabled,
  };
}
