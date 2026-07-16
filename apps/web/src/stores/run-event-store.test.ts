import { beforeEach, describe, expect, it } from "vitest";
import type { RunEvent } from "@/api/types";
import { useRunEventStore } from "./run-event-store";

const event = (seq: number): RunEvent => ({ id: String(seq), seq, type: "task.completed", schemaVersion: "run-event.v1", runId: "run", taskId: null, attemptId: null, occurredAt: new Date(0).toISOString(), redacted: false, data: {} });

describe("run event reducer", () => {
  beforeEach(() => useRunEventStore.setState({ runs: {} }));
  it("is idempotent and rejects gaps", () => {
    const store = useRunEventStore.getState();
    store.initialize("run", 0);
    expect(store.append("run", event(1))).toBe(true);
    expect(store.append("run", event(1))).toBe(false);
    expect(store.append("run", event(3))).toBe(false);
    expect(useRunEventStore.getState().runs.run.lastAppliedSeq).toBe(1);
  });
  it("resets an expired cursor without retaining stale events", () => {
    const store = useRunEventStore.getState();
    store.initialize("run", 0);
    store.append("run", event(1));
    store.reset("run", 9);
    expect(useRunEventStore.getState().runs.run).toMatchObject({
      lastAppliedSeq: 9,
      events: [],
    });
  });
});
