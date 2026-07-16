import type { HierarchicalNode } from "@/components/ui/hierarchical-picker/types";

export type FlatTreeRow<T extends HierarchicalNode = HierarchicalNode> = {
  node: T;
  depth: number;
  hasChildren: boolean;
  isExpanded: boolean;
};

function nodeHasChildren(node: HierarchicalNode): boolean {
  if (node.isLeaf) return false;
  return (node.children?.length ?? 0) > 0;
}

/**
 * DFS flatten visible tree rows for TreeTable rendering.
 */
export function flattenTreeRows<T extends HierarchicalNode>(
  nodes: T[],
  expandedKeys: Set<string> | string[],
): FlatTreeRow<T>[] {
  const expanded =
    expandedKeys instanceof Set ? expandedKeys : new Set(expandedKeys);
  const rows: FlatTreeRow<T>[] = [];

  const walk = (list: T[], depth: number) => {
    for (const node of list) {
      const hasChildren = nodeHasChildren(node) || (!node.isLeaf && !node.children);
      const isExpanded = expanded.has(node.id);
      rows.push({ node, depth, hasChildren, isExpanded });
      if (isExpanded && node.children?.length) {
        walk(node.children as T[], depth + 1);
      }
    }
  };

  walk(nodes, 0);
  return rows;
}

/**
 * Collect all node ids for defaultExpandAll (non-lazy leaves only).
 */
export function collectExpandableIds(nodes: HierarchicalNode[]): string[] {
  const ids: string[] = [];
  const walk = (list: HierarchicalNode[]) => {
    for (const node of list) {
      if (!node.isLeaf && (node.children?.length ?? 0) > 0) {
        ids.push(node.id);
        if (node.children) walk(node.children);
      }
    }
  };
  walk(nodes);
  return ids;
}
