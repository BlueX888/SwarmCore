import * as React from "react";

export type FormLayout = "vertical" | "horizontal" | "inline";
export type LabelWidth = "sm" | "md" | "lg";
export type RequiredMark = "required" | "optional";
export type InputSkin = "outlined" | "filled" | "borderless" | "underlined";

export type FormContextValue = {
  layout: FormLayout;
  labelWidth: LabelWidth;
  inputSkin?: InputSkin;
  requiredMark: RequiredMark;
  scrollToFirstError?: boolean;
};

const defaultValue: FormContextValue = {
  layout: "vertical",
  labelWidth: "md",
  requiredMark: "required",
  scrollToFirstError: false,
};

export const FormContext = React.createContext<FormContextValue>(defaultValue);

export type FormProviderProps = Partial<FormContextValue> & {
  children: React.ReactNode;
};

export function FormProvider({
  children,
  layout = "vertical",
  labelWidth = "md",
  inputSkin,
  requiredMark = "required",
  scrollToFirstError = false,
}: FormProviderProps) {
  return (
    <FormContext.Provider
      value={{ layout, labelWidth, inputSkin, requiredMark, scrollToFirstError }}
    >
      {children}
    </FormContext.Provider>
  );
}

export function useFormContext() {
  return React.useContext(FormContext);
}

export const labelWidthClass: Record<LabelWidth, string> = {
  sm: "sm:w-20",
  md: "sm:w-30",
  lg: "sm:w-40",
};
