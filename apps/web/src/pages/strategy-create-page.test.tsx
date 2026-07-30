import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { api } from "@/api/client";
import { StrategyCreatePage } from "./strategy-create-page";

vi.mock("@/api/client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/api/client")>();
  return {
    ...actual,
    api: {
      ...actual.api,
      getCapabilities: vi.fn(),
      listConfigurations: vi.fn(),
      compileStrategy: vi.fn(),
      createStrategy: vi.fn(),
    },
  };
});

vi.mock("@/components/strategy/strategy-editor", () => ({
  StrategyEditor: ({
    agentConfigurations,
    agentConfigurationsError,
  }: {
    agentConfigurations?: Array<{ kind: string; name: string }>;
    agentConfigurationsError?: string;
  }) => (
    <div>
      <span>strategy-editor</span>
      <span data-testid="agent-config-count">{agentConfigurations?.length ?? 0}</span>
      {agentConfigurationsError ? <span role="alert">{agentConfigurationsError}</span> : null}
    </div>
  ),
}));

describe("StrategyCreatePage", () => {
  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
  });

  beforeEach(() => {
    vi.mocked(api.getCapabilities).mockResolvedValue({
      schemaVersion: "1",
      registrySnapshot: "snap",
      nodeTypes: [{ type: "agent", schema: {} }],
      agents: [],
      tools: [],
      models: [],
      limits: {},
      swarmSpecSchema: {},
    });
    vi.mocked(api.listConfigurations).mockResolvedValue({
      items: [{
        configurationId: "agent-1",
        kind: "agent",
        name: "合同审查智能体",
        sourceRef: "inline/agno",
        configuration: { spec: { agents: { reviewer: { role: "审核员", instructions: "审" } } } },
        revision: 1,
        createdBy: "t",
        updatedBy: "t",
        createdAt: "2026-01-01",
        updatedAt: "2026-01-01",
      }],
      total: 1,
    });
  });

  it("omits the top project configuration picker and passes agents to the editor", async () => {
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={client}>
        <MemoryRouter>
          <StrategyCreatePage />
        </MemoryRouter>
      </QueryClientProvider>,
    );

    expect(await screen.findByText("strategy-editor")).toBeInTheDocument();
    await waitFor(() => expect(screen.getByTestId("agent-config-count")).toHaveTextContent("1"));
    expect(screen.queryByText("项目能力配置")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("项目能力配置")).not.toBeInTheDocument();
  });
});
