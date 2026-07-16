import * as React from "react";

export type DialogSize = "xs" | "sm" | "md" | "lg" | "xl" | "full";

export type DialogOpenOptions = {
  title?: React.ReactNode;
  content: React.ReactNode;
  size?: DialogSize;
  onClose?: () => void;
};

export type DialogState = DialogOpenOptions & {
  open: boolean;
};

const closedState: DialogState = {
  open: false,
  content: null,
};

let dialogState: DialogState = closedState;
const listeners = new Set<(state: DialogState) => void>();

function emit(next: DialogState) {
  dialogState = next;
  listeners.forEach((listener) => listener(next));
}

export function setDialogState(state: DialogState) {
  emit(state);
}

export function subscribeDialogState(listener: (state: DialogState) => void) {
  listeners.add(listener);
  listener(dialogState);
  return () => {
    listeners.delete(listener);
  };
}

export function getDialogState() {
  return dialogState;
}

export function openDialog(options: DialogOpenOptions) {
  setDialogState({ open: true, ...options });
}

export function closeDialog() {
  const onClose = dialogState.onClose;
  setDialogState(closedState);
  onClose?.();
}

export function useDialogState() {
  return React.useSyncExternalStore(subscribeDialogState, getDialogState, getDialogState);
}

export function useDialog() {
  return {
    open: openDialog,
    close: closeDialog,
  };
}
