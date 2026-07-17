import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { StatusBadge, statusColor } from "./status-badge";

describe("statusColor", () => {
  it("uses stable semantic colors", () => {
    expect(statusColor("SUCCEEDED")).toBe("success");
    expect(statusColor("FAILED")).toBe("error");
    expect(statusColor("RUNNING")).toBe("primary");
  });

  it("shows the Chinese status label", () => {
    render(<StatusBadge status="RUNNING" />);
    expect(screen.getByText("运行中")).toBeVisible();
  });
});
