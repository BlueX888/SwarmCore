import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { api } from "@/api/client";
import { PolicyCreatePage, buildPolicyRules } from "./policy-create-page";

vi.mock("@/api/client", () => ({ api: {
  createRuleSet: vi.fn(), validateRuleSet: vi.fn(), publishRuleSet: vi.fn(),
} }));

function renderPage() {
  const client = new QueryClient({ defaultOptions: { mutations: { retry: false } } });
  return render(<QueryClientProvider client={client}><MemoryRouter><PolicyCreatePage /></MemoryRouter></QueryClientProvider>);
}

describe("policy create page", () => {
  afterEach(cleanup);

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.createRuleSet).mockResolvedValue({ ruleSetId: "rule-1", draftId: "draft-1", revision: 1, rules: {} });
    vi.mocked(api.validateRuleSet).mockResolvedValue({ valid: true, normalizedRules: {}, preview: null });
    vi.mocked(api.publishRuleSet).mockResolvedValue({ ruleSetId: "rule-1", ruleSetVersionId: "version-1", version: 1, schemaVersion: "schema://contract/checklist-rule@1", contentHash: "abcdef1234567890", rules: {} });
  });

  it("normalizes comma-separated media types", () => {
    expect(buildPolicyRules([{ id: 1, key: " contract ", documentType: "contract", mediaTypes: "application/pdf, image/png", required: true, severity: "HIGH" }])).toMatchObject({
      requirements: [{ key: "contract", mediaTypes: ["application/pdf", "image/png"] }],
    });
  });

  it("creates, validates, and publishes a policy", async () => {
    renderPage();
    fireEvent.change(screen.getByLabelText("策略名称"), { target: { value: "采购资料策略" } });
    fireEvent.change(screen.getByLabelText("策略用途"), { target: { value: "采购合同资料校验" } });
    fireEvent.click(screen.getByRole("button", { name: "校验并发布" }));

    await waitFor(() => expect(api.createRuleSet).toHaveBeenCalledWith(expect.any(String), expect.any(String), expect.objectContaining({ name: "采购资料策略", purpose: "采购合同资料校验" })));
    expect(api.validateRuleSet).toHaveBeenCalledWith(expect.any(String), expect.any(String), "draft-1");
    expect(api.publishRuleSet).toHaveBeenCalledWith(expect.any(String), expect.any(String), "draft-1");
    expect(await screen.findByRole("status")).toHaveTextContent("策略版本 1 已发布");
  });

  it("explains missing required fields instead of silently disabling publish", () => {
    renderPage();
    const publish = screen.getByRole("button", { name: "校验并发布" });
    expect(publish).toBeEnabled();
    fireEvent.click(publish);
    expect(screen.getByRole("alert")).toHaveTextContent("请先填写策略名称和策略用途");
    expect(api.createRuleSet).not.toHaveBeenCalled();
  });
});
