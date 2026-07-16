import "@xyflow/react/dist/style.css";
import "./index.css";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { lazy, StrictMode, Suspense } from "react";
import { createRoot } from "react-dom/client";
import { Navigate, RouterProvider, createBrowserRouter } from "react-router";
import { AppShell } from "@/components/layout/app-shell";
import { ThemeProvider } from "@/context/theme-context";
import { RunsPage } from "@/pages/runs-page";
import { NewRunPage } from "@/pages/new-run-page";
import { StrategiesPage } from "@/pages/strategies-page";
import { StrategyCreatePage } from "@/pages/strategy-create-page";
import { StrategyDetailPage } from "@/pages/strategy-detail-page";
import { Skeleton } from "@/components/ui/skeleton";
import { demoRunsPath } from "@/lib/demo-scope";

const RunDetailPage = lazy(() => import("@/pages/run-detail-page").then((module) => ({ default: module.RunDetailPage })));

const router = createBrowserRouter([
  { path: "/", element: <Navigate to={demoRunsPath} replace /> },
  { path: "/t/:tenantId/p/:projectId", element: <AppShell />, children: [
    { index: true, element: <Navigate to="runs" replace /> },
    { path: "runs", children: [
      { index: true, element: <RunsPage /> },
      { path: "new", element: <NewRunPage /> },
      { path: ":runId", element: <Suspense fallback={<Skeleton className="h-96" />}><RunDetailPage /></Suspense> },
    ] },
    { path: "strategies", children: [
      { index: true, element: <StrategiesPage /> },
      { path: "new", element: <StrategyCreatePage /> },
      { path: ":strategyId", element: <StrategyDetailPage /> },
    ] },
  ] },
  { path: "*", element: <div className="grid min-h-screen place-items-center p-6 text-center"><div><h1 className="text-2xl font-semibold">Page not found</h1><p className="mt-2 text-sm text-gray-500">Open a workspace at /t/&lt;tenantId&gt;/p/&lt;projectId&gt;/runs.</p></div></div> },
]);
const queryClient = new QueryClient({ defaultOptions: { queries: { retry: 1, staleTime: 1000 } } });

const root = document.getElementById("root");
if (!root) throw new Error("Root element is missing");
createRoot(root).render(<StrictMode><ThemeProvider><QueryClientProvider client={queryClient}><RouterProvider router={router} /></QueryClientProvider></ThemeProvider></StrictMode>);
