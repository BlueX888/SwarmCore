import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const imageRoundedVariants = cva("", {
  variants: {
    rounded: {
      none: "rounded-none",
      md: "rounded-lg",
      lg: "rounded-2xl",
      full: "rounded-full",
    },
  },
  defaultVariants: { rounded: "md" },
});

export type ImageProps = React.ImgHTMLAttributes<HTMLImageElement> &
  VariantProps<typeof imageRoundedVariants> & {
    fallback?: React.ReactNode;
    lazy?: boolean;
  };

/**
 * 懒加载展示图片 — 与 ImagePreview（灯箱）分工。
 */
export function Image({
  src,
  alt,
  fallback,
  lazy = true,
  rounded,
  className,
  onError,
  ...props
}: ImageProps) {
  const [error, setError] = React.useState(false);

  React.useEffect(() => {
    setError(false);
  }, [src]);

  if ((error || !src) && fallback) {
    return <>{fallback}</>;
  }

  return (
    <img
      src={src}
      alt={alt}
      loading={lazy ? "lazy" : undefined}
      onError={(event) => {
        setError(true);
        onError?.(event);
      }}
      className={cn(imageRoundedVariants({ rounded }), className)}
      {...props}
    />
  );
}

export { imageRoundedVariants };
