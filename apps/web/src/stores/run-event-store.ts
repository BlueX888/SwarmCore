import { create } from "zustand";
import type { ConnectionState, RunEvent } from "@/api/types";

interface RunStreamState { connection: ConnectionState; lastAppliedSeq: number; events: RunEvent[]; }
interface RunEventStore {
  runs: Record<string, RunStreamState>;
  initialize: (runId: string, seq: number) => void;
  setConnection: (runId: string, connection: ConnectionState) => void;
  append: (runId: string, event: RunEvent) => boolean;
  reset: (runId: string, seq: number) => void;
}
const initial = (seq = 0): RunStreamState => ({ connection: "CONNECTING", lastAppliedSeq: seq, events: [] });

export const useRunEventStore = create<RunEventStore>((set, get) => ({
  runs: {},
  initialize: (runId, seq) => set((state) => ({ runs: { ...state.runs, [runId]: state.runs[runId] ?? initial(seq) } })),
  setConnection: (runId, connection) => set((state) => ({ runs: { ...state.runs, [runId]: { ...(state.runs[runId] ?? initial()), connection } } })),
  append: (runId, event) => {
    const current = get().runs[runId] ?? initial();
    if (event.seq <= current.lastAppliedSeq || event.seq !== current.lastAppliedSeq + 1) return false;
    set((state) => ({ runs: { ...state.runs, [runId]: { ...current, lastAppliedSeq: event.seq, events: [...current.events, event].slice(-1000) } } }));
    return true;
  },
  reset: (runId, seq) => set((state) => ({ runs: { ...state.runs, [runId]: initial(seq) } })),
}));
