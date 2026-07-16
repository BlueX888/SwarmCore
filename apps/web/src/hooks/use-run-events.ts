import { useQueryClient } from "@tanstack/react-query";
import * as React from "react";
import { api, ApiError } from "@/api/client";
import type { RunEvent, RunSnapshot } from "@/api/types";
import { useRunEventStore } from "@/stores/run-event-store";

export interface ParsedSse { id?: string; event?: string; data?: string; }
export function parseSseFrame(frame: string): ParsedSse {
  const parsed: ParsedSse = {};
  const data: string[] = [];
  for (const line of frame.split("\n")) {
    if (line.startsWith("id:")) parsed.id = line.slice(3).trim();
    else if (line.startsWith("event:")) parsed.event = line.slice(6).trim();
    else if (line.startsWith("data:")) data.push(line.slice(5).trimStart());
  }
  if (data.length) parsed.data = data.join("\n");
  return parsed;
}

const delays = [1000, 2000, 5000, 10000, 30000];

export function useRunEvents(tenantId: string, projectId: string, run: RunSnapshot | undefined) {
  const queryClient = useQueryClient();
  const initialize = useRunEventStore((state) => state.initialize);
  const append = useRunEventStore((state) => state.append);
  const reset = useRunEventStore((state) => state.reset);
  const setConnection = useRunEventStore((state) => state.setConnection);
  const runId = run?.runId;
  const initialSeq = run?.snapshotSeq;

  React.useEffect(() => {
    if (!runId || initialSeq === undefined) return;
    initialize(runId, initialSeq);
    const abort = new AbortController();
    let retry = 0;

    const apply = async (event: RunEvent) => {
      let current = useRunEventStore.getState().runs[runId]?.lastAppliedSeq ?? initialSeq;
      while (event.seq > current + 1) {
        const history = await api.history(tenantId, projectId, runId, current);
        for (const missing of history.items) append(runId, missing);
        const next = useRunEventStore.getState().runs[runId]?.lastAppliedSeq ?? current;
        if (next === current) break;
        current = next;
      }
      if (append(runId, event)) {
        await queryClient.invalidateQueries({ queryKey: ["run", tenantId, projectId, runId] });
      }
    };

    const connect = async (): Promise<void> => {
      while (!abort.signal.aborted) {
        const current = useRunEventStore.getState().runs[runId]?.lastAppliedSeq ?? initialSeq;
        setConnection(runId, retry ? "RECONNECTING" : "CONNECTING");
        try {
          const response = await fetch(api.eventUrl(projectId, runId, current), {
            headers: { Accept: "text/event-stream", "X-Tenant-ID": tenantId },
            signal: abort.signal,
          });
          if (response.status === 410) throw new ApiError(410, "CURSOR_EXPIRED");
          if (!response.ok || !response.body) throw new ApiError(response.status, "stream unavailable");
          setConnection(runId, "OPEN");
          retry = 0;
          const reader = response.body.pipeThrough(new TextDecoderStream()).getReader();
          let buffer = "";
          while (!abort.signal.aborted) {
            const { value, done } = await reader.read();
            if (done) break;
            buffer += value;
            const frames = buffer.split("\n\n");
            buffer = frames.pop() ?? "";
            for (const frame of frames) {
              const parsed = parseSseFrame(frame);
              if (parsed.data) await apply(JSON.parse(parsed.data) as RunEvent);
            }
          }
        } catch (error) {
          if (abort.signal.aborted) break;
          if (error instanceof ApiError && error.status === 410) {
            const snapshot = await queryClient.fetchQuery({ queryKey: ["run", tenantId, projectId, runId], queryFn: () => api.getRun(tenantId, projectId, runId) });
            reset(runId, snapshot.snapshotSeq);
            setConnection(runId, "STALE");
          } else {
            setConnection(runId, "RECONNECTING");
          }
          const wait = delays[Math.min(retry, delays.length - 1)] + Math.random() * 250;
          retry += 1;
          await new Promise((resolve) => window.setTimeout(resolve, wait));
        }
      }
      setConnection(runId, "CLOSED");
    };
    void connect();
    return () => abort.abort();
  }, [append, initialSeq, initialize, projectId, queryClient, reset, runId, setConnection, tenantId]);
}
