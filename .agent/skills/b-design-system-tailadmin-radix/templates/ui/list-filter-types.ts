export type ListFilterField =
  | {
      kind: "select";
      id: string;
      label: string;
      options: { value: string; label: string }[];
      allValue?: string;
    }
  | {
      kind: "text";
      id: string;
      label: string;
      placeholder?: string;
    }
  | {
      kind: "checkbox";
      id: string;
      label: string;
    };

export type ListFilterConfig = {
  fields: ListFilterField[];
  values: Record<string, string | undefined>;
  onApply: (values: Record<string, string | undefined>) => void;
  /** Simple filters: popover (default). Complex (3+ fields): drawer. */
  panel?: "popover" | "drawer";
};

export type ListSearchConfig = {
  placeholder: string;
  value: string;
  onChange: (value: string) => void;
  onSearch: (value: string) => void;
};
