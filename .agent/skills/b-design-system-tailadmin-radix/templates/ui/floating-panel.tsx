import * as React from "react";
import { GripHorizontal } from "lucide-react";
import { cn } from "@/lib/utils";
import { Surface } from "@/components/ui/surface";

export type FloatingPanelProps = {
  title?: React.ReactNode;
  children: React.ReactNode;
  defaultPosition?: { x: number; y: number };
  defaultSize?: { width: number; height: number };
  minWidth?: number;
  minHeight?: number;
  className?: string;
};

export function FloatingPanel({
  title,
  children,
  defaultPosition = { x: 24, y: 24 },
  defaultSize = { width: 320, height: 400 },
  minWidth = 240,
  minHeight = 160,
  className,
}: FloatingPanelProps) {
  const [position, setPosition] = React.useState(defaultPosition);
  const [size, setSize] = React.useState(defaultSize);
  const dragRef = React.useRef<{ startX: number; startY: number; originX: number; originY: number } | null>(null);
  const resizeRef = React.useRef<{ startX: number; startY: number; w: number; h: number } | null>(null);

  const onDragStart = (event: React.PointerEvent) => {
    dragRef.current = {
      startX: event.clientX,
      startY: event.clientY,
      originX: position.x,
      originY: position.y,
    };
    (event.target as HTMLElement).setPointerCapture(event.pointerId);
  };

  const onDragMove = (event: React.PointerEvent) => {
    if (!dragRef.current) return;
    setPosition({
      x: dragRef.current.originX + (event.clientX - dragRef.current.startX),
      y: dragRef.current.originY + (event.clientY - dragRef.current.startY),
    });
  };

  const onDragEnd = () => {
    dragRef.current = null;
  };

  const onResizeStart = (event: React.PointerEvent) => {
    event.stopPropagation();
    resizeRef.current = {
      startX: event.clientX,
      startY: event.clientY,
      w: size.width,
      h: size.height,
    };
    (event.target as HTMLElement).setPointerCapture(event.pointerId);
  };

  const onResizeMove = (event: React.PointerEvent) => {
    if (!resizeRef.current) return;
    setSize({
      width: Math.max(minWidth, resizeRef.current.w + (event.clientX - resizeRef.current.startX)),
      height: Math.max(minHeight, resizeRef.current.h + (event.clientY - resizeRef.current.startY)),
    });
  };

  const onResizeEnd = () => {
    resizeRef.current = null;
  };

  return (
    <Surface
      elevation={8}
      variant="elevated"
      className={cn("fixed z-50 flex flex-col overflow-hidden", className)}
      style={{
        left: position.x,
        top: position.y,
        width: size.width,
        height: size.height,
      }}
      role="dialog"
      aria-label={typeof title === "string" ? title : "浮动面板"}
    >
      <div
        className="flex cursor-grab items-center gap-2 border-b border-gray-100 px-3 py-2 active:cursor-grabbing dark:border-white/[0.05]"
        onPointerDown={onDragStart}
        onPointerMove={onDragMove}
        onPointerUp={onDragEnd}
        onPointerCancel={onDragEnd}
      >
        <GripHorizontal className="size-4 text-gray-400" />
        {title ? (
          <span className="text-theme-sm font-medium text-gray-800 dark:text-white/90">
            {title}
          </span>
        ) : null}
      </div>
      <div className="min-h-0 flex-1 overflow-auto p-4">{children}</div>
      <div
        className="absolute bottom-0 right-0 size-4 cursor-se-resize"
        onPointerDown={onResizeStart}
        onPointerMove={onResizeMove}
        onPointerUp={onResizeEnd}
        onPointerCancel={onResizeEnd}
        aria-hidden
      />
    </Surface>
  );
}
