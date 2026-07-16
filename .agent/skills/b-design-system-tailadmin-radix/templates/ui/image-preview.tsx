import * as React from "react";
import { cn } from "@/lib/utils";
import {
  Dialog,
  DialogContent,
  DialogTitle,
} from "@/components/ui/dialog";

export type ImagePreviewProps = {
  src: string;
  alt: string;
  fallback?: React.ReactNode;
  /** 是否可点击打开灯箱，默认 true */
  preview?: boolean;
  className?: string;
  thumbnailClassName?: string;
};

export function ImagePreview({
  src,
  alt,
  fallback,
  preview = true,
  className,
  thumbnailClassName,
}: ImagePreviewProps) {
  const [open, setOpen] = React.useState(false);
  const [hasError, setHasError] = React.useState(false);

  React.useEffect(() => {
    setHasError(false);
  }, [src]);

  const fallbackContent = fallback ?? (
    <div className="flex size-full items-center justify-center bg-gray-100 text-theme-xs text-gray-400 dark:bg-white/5 dark:text-gray-500">
      无法加载
    </div>
  );

  const thumbnail = hasError ? (
    <div
      className={cn(
        "size-12 overflow-hidden rounded-lg border border-gray-200 dark:border-gray-800",
        thumbnailClassName,
      )}
    >
      {fallbackContent}
    </div>
  ) : (
    <img
      src={src}
      alt={alt}
      loading="lazy"
      className={cn(
        "size-12 rounded-lg border border-gray-200 object-cover dark:border-gray-800",
        thumbnailClassName,
      )}
      onError={() => setHasError(true)}
    />
  );

  if (!preview) {
    return <div className={className}>{thumbnail}</div>;
  }

  return (
    <>
      <button
        type="button"
        className={cn(
          "inline-flex shrink-0 overflow-hidden rounded-lg transition-opacity hover:opacity-90 focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-brand-500/40",
          className,
        )}
        aria-label={`预览 ${alt}`}
        onClick={() => setOpen(true)}
      >
        {thumbnail}
      </button>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent
          className="max-w-3xl border-0 bg-transparent p-2 shadow-none sm:max-w-4xl"
          data-preview-open={open ? "true" : undefined}
        >
          <DialogTitle className="sr-only">{alt}</DialogTitle>
          {hasError ? (
            <div className="flex min-h-48 items-center justify-center rounded-xl bg-gray-100 dark:bg-gray-900">
              {fallbackContent}
            </div>
          ) : (
            <img
              src={src}
              alt={alt}
              className="max-h-[min(80vh,720px)] w-full rounded-xl object-contain"
            />
          )}
        </DialogContent>
      </Dialog>
    </>
  );
}
