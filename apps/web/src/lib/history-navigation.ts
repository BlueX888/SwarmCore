/** Whether React Router's history index allows a browser-style back. */
export function canGoBackInHistory(historyState: unknown): boolean {
  if (typeof historyState !== "object" || historyState === null || !("idx" in historyState)) return false;
  const idx = historyState.idx;
  return typeof idx === "number" && Number.isFinite(idx) && idx > 0;
}
