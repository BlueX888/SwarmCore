import { describe, expect, it } from "vitest";
import { parseSseFrame } from "./use-run-events";

describe("parseSseFrame", () => {
  it("parses the durable event envelope", () => {
    expect(parseSseFrame('id: 42\nevent: task.completed\ndata: {"seq":42}')).toEqual({ id: "42", event: "task.completed", data: '{"seq":42}' });
  });
  it("ignores heartbeat comments", () => { expect(parseSseFrame(": heartbeat")).toEqual({}); });
});
