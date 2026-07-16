import "@testing-library/jest-dom/vitest";

class ResizeObserverMock {
  observe() { /* test stub */ }
  unobserve() { /* test stub */ }
  disconnect() { /* test stub */ }
}

globalThis.ResizeObserver = ResizeObserverMock;
