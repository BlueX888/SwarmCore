import * as React from "react";

export type FormListField<T> = { id: string; value: T };

export type UseFormListOptions<T> = {
  initialValue?: T[];
  min?: number;
  max?: number;
};

export function useFormList<T>({
  initialValue = [],
  min = 0,
  max = Number.POSITIVE_INFINITY,
}: UseFormListOptions<T> = {}) {
  const baseId = React.useId();
  const idRef = React.useRef(0);
  const makeId = () => `${baseId}-${idRef.current++}`;

  const [fields, setFields] = React.useState<FormListField<T>[]>(() =>
    initialValue.map((value) => ({ id: makeId(), value })),
  );

  const values = React.useMemo(() => fields.map((f) => f.value), [fields]);

  const add = React.useCallback(
    (value?: T) => {
      setFields((prev) => {
        if (prev.length >= max) return prev;
        return [...prev, { id: makeId(), value: value as T }];
      });
    },
    [max],
  );

  const remove = React.useCallback(
    (index: number) => {
      setFields((prev) => {
        if (prev.length <= min) return prev;
        return prev.filter((_, i) => i !== index);
      });
    },
    [min],
  );

  const move = React.useCallback((from: number, to: number) => {
    setFields((prev) => {
      const next = [...prev];
      const [item] = next.splice(from, 1);
      next.splice(to, 0, item);
      return next;
    });
  }, []);

  const replace = React.useCallback((index: number, value: T) => {
    setFields((prev) => prev.map((f, i) => (i === index ? { ...f, value } : f)));
  }, []);

  const setValues = React.useCallback((next: T[]) => {
    setFields(next.map((value) => ({ id: makeId(), value })));
  }, []);

  return {
    fields,
    values,
    add,
    remove,
    move,
    replace,
    setValues,
    canAdd: fields.length < max,
    canRemove: fields.length > min,
  };
}
