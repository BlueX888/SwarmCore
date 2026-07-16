import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { CommandStatus, SchemaForm, validateSchemaValues } from "./run-detail-page";

const schema = {
  type: "object",
  required: ["reason"],
  properties: { reason: { type: "string", title: "Reason" } },
};

describe("human control forms", () => {
  it("validates required external input fields", () => {
    expect(validateSchemaValues(schema, {})).toBe("reason is required.");
    expect(validateSchemaValues(schema, { reason: "approved" })).toBeNull();
  });

  it("does not submit an approval until its schema is satisfied", () => {
    const submit = vi.fn();
    render(<SchemaForm schema={schema} submitLabel="Approve" busy={false} onSubmit={submit} />);
    fireEvent.click(screen.getByRole("button", { name: "Approve" }));
    expect(screen.getByRole("alert")).toHaveTextContent("reason is required");
    fireEvent.change(screen.getByLabelText(/Reason/), { target: { value: "safe" } });
    fireEvent.click(screen.getByRole("button", { name: "Approve" }));
    expect(submit).toHaveBeenCalledWith({ reason: "safe" });
  });

  it("shows pending and rejected command outcomes without changing Run state", () => {
    const { rerender } = render(<CommandStatus command={{ commandId: "c", requestId: "r", commandSeq: 2, status: "ACCEPTED" }} loading={false} />);
    expect(screen.getByRole("status")).toHaveTextContent("ACCEPTED");
    rerender(<CommandStatus command={{ commandId: "c", requestId: "r", commandSeq: 2, status: "REJECTED", result: { code: "RUN_NOT_PAUSED" } }} loading={false} />);
    expect(screen.getByRole("status")).toHaveTextContent("RUN_NOT_PAUSED");
  });
});
