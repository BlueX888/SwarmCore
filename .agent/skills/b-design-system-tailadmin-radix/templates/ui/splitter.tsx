import * as React from "react";
import { Panel, PanelGroup, PanelResizeHandle } from "react-resizable-panels";
import { cn } from "@/lib/utils";

export type SplitterProps = {
  orientation?: "horizontal" | "vertical";
  defaultLayout?: number[];
  minSize?: number;
  collapsible?: boolean;
  className?: string;
  children: [React.ReactNode, React.ReactNode];
};

export function Splitter({
  orientation = "horizontal",
  defaultLayout = [30, 70],
  minSize = 15,
  collapsible = false,
  className,
  children,
}: SplitterProps) {
  const [first, second] = children;

  return (
    <PanelGroup
      direction={orientation === "horizontal" ? "horizontal" : "vertical"}
      className={cn("min-h-0", className)}
    >
      <Panel defaultSize={defaultLayout[0]} minSize={minSize} collapsible={collapsible}>
        {first}
      </Panel>
      <PanelResizeHandle
        className={cn(
          "bg-gray-200 transition-colors hover:bg-brand-500/40 focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-brand-500/30 dark:bg-gray-800",
          orientation === "horizontal" ? "w-1" : "h-1",
        )}
      />
      <Panel defaultSize={defaultLayout[1]} minSize={minSize}>
        {second}
      </Panel>
    </PanelGroup>
  );
}
