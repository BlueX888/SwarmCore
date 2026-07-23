import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { describe, expect, it } from "vitest";
import { BackLink } from "./back-link";

describe("BackLink", () => {
  it("renders an accessible navigation link", () => {
    render(<MemoryRouter><BackLink to="/runs">运行记录</BackLink></MemoryRouter>);

    expect(screen.getByRole("link", { name: "运行记录" })).toHaveAttribute("href", "/runs");
  });
});
