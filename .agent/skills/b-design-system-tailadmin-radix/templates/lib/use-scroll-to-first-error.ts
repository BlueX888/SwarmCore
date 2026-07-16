import * as React from "react";

export function scrollToFirstError(root?: HTMLElement | null) {
  const scope = root ?? document;
  const el = scope.querySelector<HTMLElement>("[data-field-invalid]");
  el?.scrollIntoView({ behavior: "smooth", block: "center" });
  el?.focus?.();
}

export function useFormSubmit(options: {
  onValid?: () => void;
  onInvalid?: () => void;
  scrollToFirstError?: boolean;
  formRef?: React.RefObject<HTMLElement>;
}) {
  return (event: React.FormEvent) => {
    event.preventDefault();
    const form = event.currentTarget as HTMLFormElement;
    if (!form.checkValidity()) {
      options.onInvalid?.();
      if (options.scrollToFirstError !== false) {
        scrollToFirstError(options.formRef?.current ?? form);
      }
      return;
    }
    options.onValid?.();
  };
}
