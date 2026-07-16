import * as React from "react";

export type ConfirmOptions = {
  title: React.ReactNode;
  description?: React.ReactNode;
  confirmLabel?: string;
  cancelLabel?: string;
  destructive?: boolean;
};

export type ConfirmState = ConfirmOptions & {
  open: boolean;
};

const closedState: ConfirmState = {
  open: false,
  title: "",
};

let confirmState: ConfirmState = closedState;
let resolver: ((value: boolean) => void) | null = null;
const listeners = new Set<(state: ConfirmState) => void>();

function emit(next: ConfirmState) {
  confirmState = next;
  listeners.forEach((listener) => listener(next));
}

export function setConfirmState(state: ConfirmState) {
  emit(state);
}

export function subscribeConfirmState(listener: (state: ConfirmState) => void) {
  listeners.add(listener);
  listener(confirmState);
  return () => {
    listeners.delete(listener);
  };
}

export function getConfirmState() {
  return confirmState;
}

export function confirm(options: ConfirmOptions): Promise<boolean> {
  return new Promise((resolve) => {
    resolver = resolve;
    setConfirmState({ open: true, ...options });
  });
}

export function resolveConfirm(value: boolean) {
  if (!resolver) return;
  const resolve = resolver;
  resolver = null;
  resolve(value);
  setConfirmState(closedState);
}

export function useConfirmState() {
  return React.useSyncExternalStore(subscribeConfirmState, getConfirmState, getConfirmState);
}
