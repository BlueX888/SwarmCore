import * as React from "react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  useFormList,
  type FormListField,
  type UseFormListOptions,
} from "@/lib/use-form-list";

const FormListContext = React.createContext<ReturnType<typeof useFormList<unknown>> | null>(
  null,
);

export type FormListProps<T> = UseFormListOptions<T> & {
  children: React.ReactNode;
  className?: string;
};

export function FormList<T>({ children, className, ...options }: FormListProps<T>) {
  const api = useFormList<T>(options);
  return (
    <FormListContext.Provider value={api as ReturnType<typeof useFormList<unknown>>}>
      <div className={cn("grid gap-4", className)}>{children}</div>
    </FormListContext.Provider>
  );
}

export function useFormListContext<T = unknown>() {
  const ctx = React.useContext(FormListContext);
  if (!ctx) {
    throw new Error("useFormListContext must be used within FormList");
  }
  return ctx as ReturnType<typeof useFormList<T>>;
}

export type FormListItemsProps<T> = {
  renderItem: (
    index: number,
    field: FormListField<T>,
    ops: { remove: () => void },
  ) => React.ReactNode;
};

export function FormListItems<T>({ renderItem }: FormListItemsProps<T>) {
  const ctx = useFormListContext<T>();
  return (
    <>
      {ctx.fields.map((field, index) => (
        <div
          key={field.id}
          className="rounded-xl border border-gray-200 p-4 dark:border-gray-800"
        >
          {renderItem(index, field, { remove: () => ctx.remove(index) })}
        </div>
      ))}
    </>
  );
}

export type FormListAddProps = {
  label?: string;
};

export function FormListAdd({ label = "添加一项" }: FormListAddProps) {
  const ctx = useFormListContext();
  if (!ctx.canAdd) return null;
  return (
    <Button type="button" variant="outline" onClick={() => ctx.add()}>
      {label}
    </Button>
  );
}
