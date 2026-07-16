import * as React from "react";
import { createRoot, type Root } from "react-dom/client";

export type TourStep = {
  element: string;
  title: React.ReactNode;
  description?: React.ReactNode;
  side?: "top" | "right" | "bottom" | "left";
};

export type TourProps = {
  steps: TourStep[];
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  mask?: boolean;
  onFinish?: () => void;
  onSkip?: () => void;
};

type DriverHookOptions = {
  driver: { destroy: () => void };
  state: { activeIndex?: number };
};

type DriverInstance = {
  drive: () => void;
  destroy: () => void;
};

type DriverFactory = (config: Record<string, unknown>) => DriverInstance;

function mountPopoverNode(container: HTMLElement, node: React.ReactNode): Root | null {
  container.replaceChildren();

  if (node == null) {
    container.hidden = true;
    return null;
  }

  container.hidden = false;

  if (typeof node === "string" || typeof node === "number") {
    container.textContent = String(node);
    return null;
  }

  const root = createRoot(container);
  root.render(<>{node}</>);
  return root;
}

export function Tour({
  steps,
  open = false,
  onOpenChange,
  mask = true,
  onFinish,
  onSkip,
}: TourProps) {
  const driverRef = React.useRef<DriverInstance | null>(null);
  const popoverRootsRef = React.useRef<{ title: Root | null; description: Root | null }>({
    title: null,
    description: null,
  });

  const cleanupPopoverRoots = React.useCallback(() => {
    popoverRootsRef.current.title?.unmount();
    popoverRootsRef.current.description?.unmount();
    popoverRootsRef.current = { title: null, description: null };
  }, []);

  React.useEffect(() => {
    if (!open) {
      driverRef.current?.destroy();
      driverRef.current = null;
      return;
    }

    let cancelled = false;

    void (async () => {
      try {
        const mod = await import("driver.js");
        await import("driver.js/dist/driver.css");

        if (cancelled) return;

        const driver = mod.driver as DriverFactory;
        const driverObj = driver({
          showProgress: true,
          overlayOpacity: mask ? 0.6 : 0,
          popoverClass: "driver-popover-tailadmin",
          stagePadding: 8,
          stageRadius: 12,
          steps: steps.map((step) => ({
            element: step.element,
            popover: {
              title: typeof step.title === "string" ? step.title : "",
              description: typeof step.description === "string" ? step.description : undefined,
              side: step.side ?? "bottom",
            },
          })),
          onPopoverRender: (
            popover: { title?: HTMLElement; description?: HTMLElement },
            opts: DriverHookOptions,
          ) => {
            cleanupPopoverRoots();

            const step = steps[opts.state.activeIndex ?? 0];
            if (!step) return;

            if (typeof step.title !== "string" && popover.title) {
              popoverRootsRef.current.title = mountPopoverNode(popover.title, step.title);
            }

            if (typeof step.description !== "string" && popover.description) {
              popoverRootsRef.current.description = mountPopoverNode(
                popover.description,
                step.description,
              );
            }
          },
          onDoneClick: (
            _element: Element | undefined,
            _step: unknown,
            opts: DriverHookOptions,
          ) => {
            onFinish?.();
            opts.driver.destroy();
          },
          onCloseClick: (
            _element: Element | undefined,
            _step: unknown,
            opts: DriverHookOptions,
          ) => {
            onSkip?.();
            opts.driver.destroy();
          },
          onDestroyed: () => {
            cleanupPopoverRoots();
            driverRef.current = null;
            onOpenChange?.(false);
          },
        });

        driverRef.current = driverObj;
        driverObj.drive();
      } catch {
        onOpenChange?.(false);
      }
    })();

    return () => {
      cancelled = true;
      cleanupPopoverRoots();
      driverRef.current?.destroy();
      driverRef.current = null;
    };
  }, [open, steps, mask, onOpenChange, onFinish, onSkip, cleanupPopoverRoots]);

  return null;
}
