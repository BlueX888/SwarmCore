import * as React from "react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { Tree, type TreeNode } from "@/components/ui/tree";
import { File, Folder, FolderOpen } from "lucide-react";

export type FileTreeNode = {
  id: string;
  name: string;
  type: "file" | "folder";
  children?: FileTreeNode[];
};

export type FileTreeProps = {
  nodes: FileTreeNode[];
  selectedId?: string;
  onSelect?: (id: string, node: FileTreeNode) => void;
  loading?: boolean;
  className?: string;
};

export type CodeViewerProps = {
  fileName?: string;
  language?: string;
  content?: string;
  status?: "ready" | "loading" | "error" | "binary" | "large";
  className?: string;
};

function mapFileNodes(nodes: FileTreeNode[]): TreeNode[] {
  return nodes.map((node) => ({
    id: node.id,
    label: node.name,
    icon:
      node.type === "folder" ? (
        <Folder className="size-3.5 shrink-0 text-gray-400" />
      ) : (
        <File className="size-3.5 shrink-0 text-gray-400" />
      ),
    children: node.children ? mapFileNodes(node.children) : undefined,
  }));
}

function findFileNode(nodes: FileTreeNode[], id: string): FileTreeNode | undefined {
  for (const node of nodes) {
    if (node.id === id) return node;
    if (node.children) {
      const found = findFileNode(node.children, id);
      if (found) return found;
    }
  }
  return undefined;
}

/**
 * Repository file tree — selected/loading/empty states.
 * @see references/layout-patterns/code-repository.md
 */
export function FileTree({ nodes, selectedId, onSelect, loading, className }: FileTreeProps) {
  const treeNodes = React.useMemo(() => mapFileNodes(nodes), [nodes]);

  return (
    <div className={cn(className)}>
      {loading ? (
        <div className="flex items-center justify-center gap-2 rounded-xl border border-gray-200 py-12 text-theme-sm text-gray-500 dark:border-gray-800">
          <Spinner className="size-4" />
          Loading tree…
        </div>
      ) : nodes.length === 0 ? (
        <p className="rounded-xl border border-gray-200 py-12 text-center text-theme-sm text-gray-500 dark:border-gray-800">
          No files in this path.
        </p>
      ) : (
        <Tree
          nodes={treeNodes}
          selectedKeys={selectedId ? [selectedId] : []}
          onSelect={(id) => {
            const node = findFileNode(nodes, id);
            if (node && node.type === "file") {
              onSelect?.(id, node);
            }
          }}
          className="border-0"
        />
      )}
    </div>
  );
}

/**
 * Code viewer panel — monospace content with binary/large/error fallback.
 */
export function CodeViewer({ fileName, language, content, status = "ready", className }: CodeViewerProps) {
  if (status === "loading") {
    return (
      <div className={cn("flex items-center justify-center gap-2 rounded-xl border border-gray-200 py-16 dark:border-gray-800", className)}>
        <Spinner className="size-4" />
        <span className="text-theme-sm text-gray-500">正在加载文件...</span>
      </div>
    );
  }

  if (status === "binary" || status === "large") {
    return (
      <div className={cn("flex flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-gray-300 py-16 text-center dark:border-gray-700", className)}>
        <p className="text-theme-sm font-medium text-gray-800 dark:text-white/90">
          {status === "binary" ? "二进制文件" : "文件过大"}
        </p>
        <p className="text-theme-sm text-gray-500">{fileName ?? "暂无预览"}</p>
        <Button type="button" variant="outline" size="sm">
          下载原文件
        </Button>
      </div>
    );
  }

  if (status === "error") {
    return (
      <div className={cn("rounded-xl border border-error-200 bg-error-50/50 p-6 text-center dark:border-error-500/30 dark:bg-error-500/5", className)}>
        <p className="text-theme-sm font-medium text-error-700 dark:text-error-400">文件加载失败</p>
        <Button type="button" variant="outline" size="sm" className="mt-3">
          重试
        </Button>
      </div>
    );
  }

  return (
    <div className={cn("flex min-h-0 flex-col overflow-hidden rounded-xl border border-gray-200 dark:border-gray-800", className)}>
      <div className="flex items-center justify-between border-b border-gray-200 px-4 py-2 dark:border-gray-800">
        <span className="truncate text-theme-sm font-medium">{fileName ?? "请选择文件"}</span>
        {language ? <span className="text-theme-xs text-gray-500">{language}</span> : null}
      </div>
      <pre className="max-h-[480px] overflow-auto bg-gray-950 p-4 font-mono text-[11px] leading-relaxed text-gray-200">
        <code>{content ?? "// 请从文件树选择文件"}</code>
      </pre>
    </div>
  );
}

export type FileBrowserProps = {
  tree: FileTreeNode[];
  selectedId?: string;
  onSelectFile?: (id: string, node: FileTreeNode) => void;
  fileName?: string;
  language?: string;
  content?: string;
  fileStatus?: CodeViewerProps["status"];
  treeLoading?: boolean;
  className?: string;
};

/**
 * File tree + code viewer split — stable 240px + 1fr layout.
 */
export function FileBrowser({
  tree,
  selectedId,
  onSelectFile,
  fileName,
  language,
  content,
  fileStatus,
  treeLoading,
  className,
}: FileBrowserProps) {
  return (
    <div
      className={cn(
        "grid min-h-[360px] grid-cols-1 gap-0 overflow-hidden rounded-xl border border-gray-200 lg:grid-cols-[minmax(200px,240px)_minmax(0,1fr)] dark:border-gray-800",
        className,
      )}
    >
      <FileTree
        nodes={tree}
        selectedId={selectedId}
        onSelect={onSelectFile}
        loading={treeLoading}
        className="max-h-[480px] border-0 border-b border-gray-200 lg:max-h-none lg:border-b-0 lg:border-r dark:border-gray-800"
      />
      <CodeViewer
        fileName={fileName}
        language={language}
        content={content}
        status={fileStatus}
        className="border-0"
      />
    </div>
  );
}
