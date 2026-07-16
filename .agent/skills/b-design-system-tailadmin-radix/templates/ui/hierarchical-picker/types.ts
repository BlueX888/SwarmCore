import type * as React from "react";

export type HierarchicalNode = {
  id: string;
  label: React.ReactNode;
  disabled?: boolean;
  isLeaf?: boolean;
  children?: HierarchicalNode[];
};

export type LoadDataFn = (node: HierarchicalNode) => Promise<HierarchicalNode[]>;

export type CheckStrategy = "all" | "parent" | "child";

export type HierarchicalPath = string[];
