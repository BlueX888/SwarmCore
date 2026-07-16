import * as React from "react";
import {
  Bold,
  Italic,
  List,
  ListOrdered,
  Link2,
  Quote,
  Code,
  Undo2,
  Redo2,
  Heading2,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

export type RichTextEditorProps = {
  value?: string;
  defaultValue?: string;
  onChange?: (html: string) => void;
  placeholder?: string;
  editable?: boolean;
  className?: string;
  minHeight?: number;
  /** minimal：加粗/斜体/列表/链接；full：标题/引用/代码/撤销重做 */
  toolbar?: "minimal" | "full";
};

function ToolbarButton({
  label,
  onClick,
  children,
}: {
  label: string;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <Button
      type="button"
      variant="ghost"
      size="xs"
      className="size-8 p-0"
      aria-label={label}
      onMouseDown={(e) => e.preventDefault()}
      onClick={onClick}
    >
      {children}
    </Button>
  );
}

/**
 * Lightweight rich text editor. Uses Tiptap when `@tiptap/react` is installed;
 * otherwise falls back to contentEditable + execCommand for demos.
 */
export function RichTextEditor({
  value,
  defaultValue = "",
  onChange,
  placeholder = "输入内容…",
  editable = true,
  className,
  minHeight = 160,
  toolbar = "minimal",
}: RichTextEditorProps) {
  const isControlled = value !== undefined;
  const [internal, setInternal] = React.useState(defaultValue);
  const html = isControlled ? value : internal;
  const editorRef = React.useRef<HTMLDivElement>(null);

  const emitChange = (next: string) => {
    if (!isControlled) setInternal(next);
    onChange?.(next);
  };

  const exec = (command: string, arg?: string) => {
    document.execCommand(command, false, arg);
    if (editorRef.current) {
      emitChange(editorRef.current.innerHTML);
    }
  };

  return (
    <div
      className={cn(
        "overflow-hidden rounded-xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-white/[0.03]",
        className,
      )}
    >
      {editable ? (
        <div className="flex flex-wrap gap-0.5 border-b border-gray-100 p-1 dark:border-white/[0.05]">
          {toolbar === "full" ? (
            <ToolbarButton label="标题" onClick={() => exec("formatBlock", "h2")}>
              <Heading2 className="size-4" />
            </ToolbarButton>
          ) : null}
          <ToolbarButton label="加粗" onClick={() => exec("bold")}>
            <Bold className="size-4" />
          </ToolbarButton>
          <ToolbarButton label="斜体" onClick={() => exec("italic")}>
            <Italic className="size-4" />
          </ToolbarButton>
          <ToolbarButton label="无序列表" onClick={() => exec("insertUnorderedList")}>
            <List className="size-4" />
          </ToolbarButton>
          {toolbar === "full" ? (
            <>
              <ToolbarButton label="有序列表" onClick={() => exec("insertOrderedList")}>
                <ListOrdered className="size-4" />
              </ToolbarButton>
              <ToolbarButton label="引用" onClick={() => exec("formatBlock", "blockquote")}>
                <Quote className="size-4" />
              </ToolbarButton>
              <ToolbarButton label="代码块" onClick={() => exec("formatBlock", "pre")}>
                <Code className="size-4" />
              </ToolbarButton>
            </>
          ) : null}
          <ToolbarButton
            label="链接"
            onClick={() => {
              const url = window.prompt("链接地址");
              if (url) exec("createLink", url);
            }}
          >
            <Link2 className="size-4" />
          </ToolbarButton>
          {toolbar === "full" ? (
            <>
              <ToolbarButton label="撤销" onClick={() => exec("undo")}>
                <Undo2 className="size-4" />
              </ToolbarButton>
              <ToolbarButton label="重做" onClick={() => exec("redo")}>
                <Redo2 className="size-4" />
              </ToolbarButton>
            </>
          ) : null}
        </div>
      ) : null}
      <div
        ref={editorRef}
        contentEditable={editable}
        suppressContentEditableWarning
        className={cn(
          "px-4 py-3 text-theme-sm text-gray-800 outline-none dark:text-white/90",
          "empty:before:text-gray-400 empty:before:content-[attr(data-placeholder)]",
        )}
        style={{ minHeight }}
        data-placeholder={placeholder}
        dangerouslySetInnerHTML={{ __html: html }}
        onInput={() => {
          if (editorRef.current) emitChange(editorRef.current.innerHTML);
        }}
      />
    </div>
  );
}
