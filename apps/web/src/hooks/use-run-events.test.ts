import { afterEach, describe, expect, it, vi } from "vitest";
import { createInvalidationScheduler, parseSseFrame } from "./use-run-events";

afterEach(() => {
  vi.useRealTimers();
});

describe("parseSseFrame", () => {
  it("parses the durable event envelope", () => {
    expect(parseSseFrame('id: 42\nevent: task.completed\ndata: {"seq":42}')).toEqual({ id: "42", event: "task.completed", data: '{"seq":42}' });
  });
  it("ignores heartbeat comments", () => { expect(parseSseFrame(": heartbeat")).toEqual({}); });
});

describe("createInvalidationScheduler", () => {
  it("invalidates immediately, then coalesces events within the throttle window", () => {
    vi.useFakeTimers();
    vi.setSystemTime(10_000);
    const invalidate = vi.fn();
    const scheduler = createInvalidationScheduler(invalidate, 2000);

    scheduler.schedule();
    scheduler.schedule();
    scheduler.schedule();

    expect(invalidate).toHaveBeenCalledTimes(1);
    vi.advanceTimersByTime(1999);
    expect(invalidate).toHaveBeenCalledTimes(1);
    vi.advanceTimersByTime(1);
    expect(invalidate).toHaveBeenCalledTimes(2);
  });

  it("cancels a pending invalidation when disposed", () => {
    vi.useFakeTimers();
    vi.setSystemTime(10_000);
    const invalidate = vi.fn();
    const scheduler = createInvalidationScheduler(invalidate, 2000);

    scheduler.schedule();
    scheduler.schedule();
    scheduler.dispose();
    vi.advanceTimersByTime(2000);

    expect(invalidate).toHaveBeenCalledTimes(1);
  });
});
