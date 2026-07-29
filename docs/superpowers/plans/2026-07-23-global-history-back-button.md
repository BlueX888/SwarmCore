# Global History Back Button Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a global browser-history back button to the AppShell top bar that is disabled when there is no history to go back to.

**Architecture:** Extend `AppShell` header with a ghost icon button. Use `useNavigate(-1)` for back. Derive enabled state from React Router's `window.history.state.idx` (`idx > 0`). Keep page-level `BackLink`s unchanged.

**Tech Stack:** React 19, React Router (data router), Vitest, Testing Library, existing `Button` UI.

## Global Constraints

- Behavior is browser history back only (`navigate(-1)`), not parent-route links.
- Placement: AppShell top bar, after mobile nav button, before page title.
- No history → button visible and disabled.
- Do not modify page-level `BackLink` usages.
- Chinese UI: `aria-label="返回上一页"`.

---

### Task 1: AppShell history back button

**Files:**
- Modify: `apps/web/src/components/layout/app-shell.tsx`
- Modify: `apps/web/src/components/layout/app-shell.test.tsx`
- Spec: `docs/superpowers/specs/2026-07-23-global-history-back-button-design.md`

**Interfaces:**
- Consumes: `useNavigate` from `react-router`, `Button` from `@/components/ui/button`, `ArrowLeft` from `lucide-react`, `ThemeProvider` if needed for shell render
- Produces: Top-bar control `aria-label="返回上一页"`; click → `navigate(-1)` when `canGoBack`; `disabled` when `!canGoBack`

- [x] **Step 1: Write the failing tests**
- [x] **Step 2: Run tests to verify they fail**
- [x] **Step 3: Implement minimal AppShell change**
- [x] **Step 4: Run tests to verify they pass**
- [x] **Step 5: Lint / related checks**
- [ ] **Step 6: Commit only if user requests**
