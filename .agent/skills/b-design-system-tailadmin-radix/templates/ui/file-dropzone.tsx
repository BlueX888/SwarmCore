import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { FileText, Upload, X } from "lucide-react";
import { cn } from "@/lib/utils";
import { Progress } from "@/components/ui/progress";
import { Spinner } from "@/components/ui/spinner";

const dropzoneVariants = cva(
  "relative flex w-full flex-col items-center justify-center rounded-xl border-2 border-dashed px-6 py-8 text-center transition-colors",
  {
    variants: {
      variant: {
        default:
          "border-gray-300 bg-gray-50/50 hover:border-brand-300 hover:bg-brand-50/30 dark:border-gray-700 dark:bg-white/[0.02] dark:hover:border-brand-800 dark:hover:bg-brand-500/5",
        error:
          "border-error-500 bg-error-50/30 dark:border-error-500 dark:bg-error-500/10",
        disabled: "cursor-not-allowed border-gray-200 bg-gray-50 opacity-50 dark:border-gray-800",
      },
      active: {
        true: "border-brand-500 bg-brand-50/50 dark:border-brand-500 dark:bg-brand-500/10",
        false: "",
      },
    },
    defaultVariants: {
      variant: "default",
      active: false,
    },
  },
);

export type FileDropzoneItem = {
  id: string;
  name: string;
  size?: number;
  progress?: number;
  status?: "pending" | "uploading" | "done" | "error";
  error?: string;
};

export type FileDropzoneProps = Omit<
  React.ComponentProps<"input">,
  "type" | "value" | "onChange"
> &
  VariantProps<typeof dropzoneVariants> & {
    label?: string;
    hint?: string;
    error?: string;
    accept?: string;
    multiple?: boolean;
    maxSizeMb?: number;
    files?: FileDropzoneItem[];
    onFilesSelected?: (files: FileList) => void;
    onRemoveFile?: (id: string) => void;
    emptyTitle?: string;
    emptyHint?: string;
  };

function formatFileSize(bytes?: number): string {
  if (!bytes) return "";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

/**
 * 拖拽上传区 — 多文件预览、进度条、错误态。
 * 与基础 `FileUpload`（原生 input）互补，不破坏既有 API。
 * @see references/component-styles/composite-template.md#fileupload
 * @see templates/ui/file-upload.tsx
 */
export function FileDropzone({
  className,
  variant,
  label,
  hint,
  error,
  accept,
  multiple = true,
  maxSizeMb = 10,
  disabled,
  files = [],
  onFilesSelected,
  onRemoveFile,
  emptyTitle = "拖拽文件到此处，或点击选择",
  emptyHint,
  id,
  ...props
}: FileDropzoneProps) {
  const inputId = id ?? React.useId();
  const inputRef = React.useRef<HTMLInputElement>(null);
  const [dragActive, setDragActive] = React.useState(false);
  const hintId = hint ? `${inputId}-hint` : undefined;
  const errorId = error ? `${inputId}-error` : undefined;
  const resolvedVariant = disabled ? "disabled" : error ? "error" : variant;
  const resolvedHint =
    emptyHint ?? `支持 ${multiple ? "多文件" : "单文件"}，单个不超过 ${maxSizeMb} MB`;

  const handleFiles = (list: FileList | null) => {
    if (!list?.length || disabled) return;
    onFilesSelected?.(list);
  };

  const onDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    if (!disabled) setDragActive(true);
  };

  const onDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
    handleFiles(e.dataTransfer.files);
  };

  return (
    <div className={cn("w-full", className)}>
      {label ? (
        <label
          htmlFor={inputId}
          className="mb-1.5 block text-sm font-medium text-gray-700 dark:text-gray-400"
        >
          {label}
        </label>
      ) : null}
      <div
        className={dropzoneVariants({
          variant: resolvedVariant,
          active: dragActive && !disabled,
        })}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
        onClick={() => !disabled && inputRef.current?.click()}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            inputRef.current?.click();
          }
        }}
        role="button"
        tabIndex={disabled ? -1 : 0}
        aria-disabled={disabled}
        aria-describedby={[hintId, errorId].filter(Boolean).join(" ") || undefined}
      >
        <input
          ref={inputRef}
          id={inputId}
          type="file"
          className="sr-only"
          accept={accept}
          multiple={multiple}
          disabled={disabled}
          onChange={(e) => handleFiles(e.target.files)}
          {...props}
        />
        <Upload className="mb-3 size-8 text-brand-500" aria-hidden />
        <p className="text-theme-sm font-medium text-gray-800 dark:text-white/90">
          {emptyTitle}
        </p>
        <p className="mt-1 text-theme-xs text-gray-500 dark:text-gray-400">
          {resolvedHint}
        </p>
      </div>
      {hint && !error ? (
        <p id={hintId} className="mt-1.5 text-theme-xs text-gray-500 dark:text-gray-400">
          {hint}
        </p>
      ) : null}
      {error ? (
        <p id={errorId} className="mt-1.5 text-theme-xs text-error-500">
          {error}
        </p>
      ) : null}
      {files.length > 0 ? (
        <ul className="mt-4 space-y-2" aria-label="已选文件列表">
          {files.map((file) => (
            <li
              key={file.id}
              className="flex items-start gap-3 rounded-lg border border-gray-200 bg-white px-3 py-2.5 dark:border-gray-800 dark:bg-white/[0.03]"
            >
              <FileText className="mt-0.5 size-4 shrink-0 text-gray-500" aria-hidden />
              <div className="min-w-0 flex-1">
                <div className="flex items-center justify-between gap-2">
                  <span className="truncate text-theme-sm font-medium text-gray-800 dark:text-white/90">
                    {file.name}
                  </span>
                  {file.size ? (
                    <span className="shrink-0 text-theme-xs text-gray-500">
                      {formatFileSize(file.size)}
                    </span>
                  ) : null}
                </div>
                {file.status === "uploading" && file.progress !== undefined ? (
                  <Progress value={file.progress} className="mt-2 h-1.5" />
                ) : null}
                {file.status === "uploading" ? (
                  <span className="mt-1 inline-flex items-center gap-1.5 text-theme-xs text-gray-500">
                    <Spinner size="sm" aria-label="上传中" />
                    上传中 {file.progress ?? 0}%
                  </span>
                ) : null}
                {file.status === "error" && file.error ? (
                  <p className="mt-1 text-theme-xs text-error-500">{file.error}</p>
                ) : null}
                {file.status === "done" ? (
                  <p className="mt-1 text-theme-xs text-success-500">上传完成</p>
                ) : null}
              </div>
              {onRemoveFile ? (
                <button
                  type="button"
                  className="inline-flex size-7 shrink-0 items-center justify-center rounded-md text-gray-500 hover:bg-gray-100 dark:hover:bg-white/5"
                  aria-label={`移除 ${file.name}`}
                  onClick={(e) => {
                    e.stopPropagation();
                    onRemoveFile(file.id);
                  }}
                >
                  <X className="size-4" />
                </button>
              ) : null}
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}

export { dropzoneVariants };
