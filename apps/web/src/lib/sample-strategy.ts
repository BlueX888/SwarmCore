export const sampleStrategy: Record<string, unknown> = {
  apiVersion: "swarmcore.io/v1",
  kind: "SwarmStrategy",
  metadata: { name: "phase1-demo" },
  spec: {
    inputSchema: { type: "object", properties: { topic: { type: "string" } }, required: ["topic"], additionalProperties: false },
    outputSchema: { type: "object" },
    defaults: { model: "model://fake-deterministic" },
    agents: { worker: { role: "worker", instructions: "返回简洁的结构化响应。" } },
    graph: { entrypoint: "work", nodes: { work: { type: "agent", agent: "worker", input: { topic: "{{ input.topic }}" } } }, output: { result: "{{ tasks.work.output }}" } },
  },
};
