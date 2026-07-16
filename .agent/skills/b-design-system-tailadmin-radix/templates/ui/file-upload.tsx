import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { FileText, X } from "lucide-react";
import { cn } from "@/lib/utils";

const fileUploadVariants = cva(
  "flex h-11 w-full overflow-hidden rounded-lg border bg-transparent text-sm text-gray-500 shadow-theme-xs transition-colors file:mr-5 file:cursor-pointer file:border-0 file:border-r file:border-solid file:border-gray-200 file:bg-gray-50 file:py-3 file:pl-3.5 file:pr-3 file:text-sm file:font-medium file:text-gray-700 hover:file:bg-gray-100 focus-visible:outline-hidden focus-visible:ring-3 focus-visible:ring-brand-500/20 disabled:cursor-not-allowed disabled:opacity-40 dark:text-gray-400 dark:file:border-gray-800 dark:file:bg-white/[0.03] dark:file:text-gray-400 dark:hover:file:bg-white/[0.06]",
  {
    variants: {
      variant: {
        default:
          "border-gray-300 focus-visible:border-brand-300 dark:border-gray-700 dark:bg-gray-900 dark:focus-visible:border-brand-800",
        error:
          "border-error-500 focus-visible:ring-error-500/20 dark:border-error-500",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  },
);

export type FileUploadListType = "text" | "picture" | "picture-card";

export type FileUploadProps = Omit<
  React.ComponentProps<"input">,
  "type"
> &
  VariantProps<typeof fileUploadVariants> & {
    label?: string;
    hint?: string;
    error?: string;
    /** text：文件名列表；picture：横向缩略图；picture-card：方框预览网格 */
    listType?: FileUploadListType;
  };

function fileKey(file: File, index: number) {
  return `${file.name}-${file.size}-${file.lastModified}-${index}`;
}

function FilePreviewThumb({ file }: { file: File }) {
  const [url, setUrl] = React.useState<string | null>(null);
  const isImage = file.type.startsWith("image/");

  React.useEffect(() => {
    if (!isImage) {
      setUrl(null);
      return;
    }
    const objectUrl = URL.createObjectURL(file);
    setUrl(objectUrl);
    return () => URL.revokeObjectURL(objectUrl);
  }, [file, isImage]);

  if (isImage && url) {
    return (
      <img
        src={url}
        alt={file.name}
        className="size-full object-cover"
        loading="lazy"
      />
    );
  }

  return (
    <div className="flex size-full items-center justify-center bg-gray-100 dark:bg-white/[0.06]">
      <FileText className="size-5 text-gray-400" aria-hidden />
    </div>
  );
}

const FileUpload = React.forwardRef<HTMLInputElement, FileUploadProps>(
  (
    {
      className,
      variant,
      label,
      hint,
      error,
      listType = "text",
      id,
      disabled,
      multiple,
      onChange,
      "aria-invalid": ariaInvalid,
      ...props
    },
    ref,
  ) => {
    const inputId = id ?? React.useId();
    const hintId = hint ? `${inputId}-hint` : undefined;
    const errorId = error ? `${inputId}-error` : undefined;
    const resolvedVariant = error ? "error" : variant;
    const describedBy =
      [hintId, errorId].filter(Boolean).join(" ") || undefined;
    const [files, setFiles] = React.useState<File[]>([]);

    const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
      const selected = event.target.files ? Array.from(event.target.files) : [];
      setFiles(selected);
      onChange?.(event);
    };

    const removeFile = (index: number) => {
      setFiles((prev) => prev.filter((_, i) => i !== index));
    };

    return (
      <div className="w-full" data-list-type={listType}>
        {label ? (
          <label
            htmlFor={inputId}
            className="mb-1.5 block text-sm font-medium text-gray-700 dark:text-gray-400"
          >
            {label}
          </label>
        ) : null}
        <input
          ref={ref}
          id={inputId}
          type="file"
          disabled={disabled}
          multiple={multiple}
          aria-invalid={ariaInvalid ?? Boolean(error)}
          aria-describedby={describedBy}
          className={cn(fileUploadVariants({ variant: resolvedVariant, className }))}
          onChange={handleChange}
          {...props}
        />
        {files.length > 0 && listType === "text" ? (
          <ul className="mt-3 space-y-1.5">
            {files.map((file, index) => (
              <li
                key={fileKey(file, index)}
                className="flex items-center justify-between gap-2 rounded-lg border border-gray-200 px-3 py-2 text-theme-sm text-gray-700 dark:border-gray-800 dark:text-gray-300"
              >
                <span className="min-w-0 truncate">{file.name}</span>
                <button
                  type="button"
                  onClick={() => removeFile(index)}
                  className="inline-flex size-7 shrink-0 items-center justify-center rounded-md text-gray-400 hover:bg-gray-100 hover:text-gray-600 dark:hover:bg-white/5"
                  aria-label={`移除 ${file.name}`}
                >
                  <X className="size-4" />
                </button>
              </li>
            ))}
          </ul>
        ) : null}
        {files.length > 0 && listType === "picture" ? (
          <ul className="mt-3 flex flex-wrap gap-3">
            {files.map((file, index) => (
              <li
                key={fileKey(file, index)}
                className="flex w-40 items-center gap-2 rounded-lg border border-gray-200 p-2 dark:border-gray-800"
              >
                <div className="size-10 shrink-0 overflow-hidden rounded-md">
                  <FilePreviewThumb file={file} />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-theme-xs font-medium text-gray-700 dark:text-gray-300">
                    {file.name}
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => removeFile(index)}
                  className="inline-flex size-7 shrink-0 items-center justify-center rounded-md text-gray-400 hover:bg-gray-100 dark:hover:bg-white/5"
                  aria-label={`移除 ${file.name}`}
                >
                  <X className="size-4" />
                </button>
              </li>
            ))}
          </ul>
        ) : null}
        {files.length > 0 && listType === "picture-card" ? (
          <ul className="mt-3 grid grid-cols-[repeat(auto-fill,minmax(104px,1fr))] gap-3">
            {files.map((file, index) => (
              <li
                key={fileKey(file, index)}
                className="group relative aspect-square overflow-hidden rounded-xl border border-gray-200 dark:border-gray-800"
              >
                <FilePreviewThumb file={file} />
                <button
                  type="button"
                  onClick={() => removeFile(index)}
                  className="absolute right-1.5 top-1.5 inline-flex size-7 items-center justify-center rounded-full bg-gray-900/60 text-white opacity-0 transition-opacity group-hover:opacity-100 group-focus-within:opacity-100"
                  aria-label={`移除 ${file.name}`}
                >
                  <X className="size-3.5" />
                </button>
                <p className="absolute inset-x-0 bottom-0 truncate bg-gray-900/60 px-2 py-1 text-[10px] text-white">
                  {file.name}
                </p>
              </li>
            ))}
          </ul>
        ) : null}
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
      </div>
    );
  },
);
FileUpload.displayName = "FileUpload";

export { FileUpload, fileUploadVariants };
