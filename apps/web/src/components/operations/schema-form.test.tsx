import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { SchemaForm, omitSchemaKeys, schemaFieldLabel, validateSchemaValues } from "@/components/operations/schema-form";

describe("schema field helpers", () => {
  it("uses Chinese labels for common approval fields", () => {
    expect(schemaFieldLabel("comment")).toBe("审批意见");
    expect(schemaFieldLabel("approved")).toBe("确认批准");
    expect(schemaFieldLabel("confirmations")).toBe("核对说明");
    expect(schemaFieldLabel("topic", { title: "主题词" })).toBe("主题词");
  });

  it("omits keys from schema and validates with Chinese messages", () => {
    const schema = {
      type: "object",
      required: ["approved", "reason"],
      properties: {
        approved: { type: "boolean" },
        reason: { type: "string" },
      },
    };
    expect(omitSchemaKeys(schema, ["approved"]).required).toEqual(["reason"]);
    expect(validateSchemaValues(schema, {})).toBe("确认批准 为必填项。");
    expect(validateSchemaValues(omitSchemaKeys(schema, ["approved"]), {})).toBe("原因说明 为必填项。");
  });
});

describe("SchemaForm", () => {
  it("treats array fields as newline-separated notes", () => {
    const onSubmit = vi.fn();
    render(
      <SchemaForm
        schema={{
          type: "object",
          properties: {
            confirmations: { type: "array" },
          },
        }}
        submitLabel="提交"
        busy={false}
        onSubmit={onSubmit}
      />,
    );

    fireEvent.change(screen.getByPlaceholderText("每行一条核对说明"), {
      target: { value: "第一条\n第二条" },
    });
    fireEvent.click(screen.getByRole("button", { name: "提交" }));
    expect(onSubmit).toHaveBeenCalledWith({ confirmations: ["第一条", "第二条"] });
  });
});
