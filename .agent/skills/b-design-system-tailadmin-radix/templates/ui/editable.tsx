import * as React from "react";
import { cn } from "@/lib/utils";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";

export type EditableProps = {
  value?: string;
  onChange?: (value: string) => void;
  onSubmit?: (value: string) => void;
  onCancel?: () => void;
  placeholder?: string;
  submitOnBlur?: boolean;
  className?: string;
};

function useEditableState({
  value = "",
  onChange,
  onSubmit,
  onCancel,
  submitOnBlur = true,
}: EditableProps) {
  const [editing, setEditing] = React.useState(false);
  const [draft, setDraft] = React.useState(value);
  const inputRef = React.useRef<HTMLInputElement | HTMLTextAreaElement>(null);

  React.useEffect(() => {
    if (!editing) {
      setDraft(value);
    }
  }, [editing, value]);

  React.useEffect(() => {
    if (editing) {
      inputRef.current?.focus();
      if (inputRef.current instanceof HTMLInputElement) {
        inputRef.current.select();
      }
    }
  }, [editing]);

  const startEditing = () => {
    setDraft(value);
    setEditing(true);
  };

  const cancelEditing = () => {
    setDraft(value);
    setEditing(false);
    onCancel?.();
  };

  const submitEditing = () => {
    onChange?.(draft);
    onSubmit?.(draft);
    setEditing(false);
  };

  const handleBlur = () => {
    if (submitOnBlur) {
      submitEditing();
      return;
    }
    cancelEditing();
  };

  return {
    editing,
    draft,
    setDraft,
    inputRef,
    startEditing,
    cancelEditing,
    submitEditing,
    handleBlur,
  };
}

export function Editable({
  value,
  onChange,
  onSubmit,
  onCancel,
  placeholder = "点击编辑",
  submitOnBlur = true,
  className,
}: EditableProps) {
  const {
    editing,
    draft,
    setDraft,
    inputRef,
    startEditing,
    cancelEditing,
    submitEditing,
    handleBlur,
  } = useEditableState({ value, onChange, onSubmit, onCancel, submitOnBlur });

  if (editing) {
    return (
      <Input
        ref={inputRef as React.RefObject<HTMLInputElement>}
        value={draft}
        onChange={(event) => setDraft(event.target.value)}
        onBlur={handleBlur}
        onKeyDown={(event) => {
          if (event.key === "Enter") {
            event.preventDefault();
            submitEditing();
          } else if (event.key === "Escape") {
            event.preventDefault();
            cancelEditing();
          }
        }}
        inputSkin="borderless"
        className={cn("h-auto min-h-0 px-0 py-0", className)}
        aria-label="编辑内容"
        data-state="editing"
      />
    );
  }

  return (
    <button
      type="button"
      onClick={startEditing}
      className={cn(
        "w-full rounded-md px-0 py-1 text-left text-sm text-gray-800 transition-colors",
        "border-b border-transparent hover:border-dashed hover:border-gray-400",
        "dark:text-white/90 dark:hover:border-gray-600",
        !value && "text-gray-400 dark:text-white/30",
        className,
      )}
      data-state="viewing"
    >
      {value || placeholder}
    </button>
  );
}

export function EditableTextarea({
  value,
  onChange,
  onSubmit,
  onCancel,
  placeholder = "点击编辑",
  submitOnBlur = true,
  className,
}: EditableProps) {
  const {
    editing,
    draft,
    setDraft,
    inputRef,
    startEditing,
    cancelEditing,
    submitEditing,
    handleBlur,
  } = useEditableState({ value, onChange, onSubmit, onCancel, submitOnBlur });

  if (editing) {
    return (
      <Textarea
        ref={inputRef as React.RefObject<HTMLTextAreaElement>}
        value={draft}
        onChange={(event) => setDraft(event.target.value)}
        onBlur={handleBlur}
        onKeyDown={(event) => {
          if (event.key === "Escape") {
            event.preventDefault();
            cancelEditing();
          } else if (event.key === "Enter" && (event.metaKey || event.ctrlKey)) {
            event.preventDefault();
            submitEditing();
          }
        }}
        variant="default"
        className={cn("min-h-[80px] border-transparent shadow-none focus-visible:ring-0", className)}
        aria-label="编辑内容"
        data-state="editing"
      />
    );
  }

  return (
    <button
      type="button"
      onClick={startEditing}
      className={cn(
        "w-full whitespace-pre-wrap rounded-md px-0 py-1 text-left text-sm text-gray-800 transition-colors",
        "border-b border-transparent hover:border-dashed hover:border-gray-400",
        "dark:text-white/90 dark:hover:border-gray-600",
        !value && "text-gray-400 dark:text-white/30",
        className,
      )}
      data-state="viewing"
    >
      {value || placeholder}
    </button>
  );
}
