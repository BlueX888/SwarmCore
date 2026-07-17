import "@xyflow/react/dist/style.css";
import "./index.css";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { lazy, StrictMode, Suspense } from "react";
import { createRoot } from "react-dom/client";
import { Navigate, RouterProvider, createBrowserRouter, useLocation, useParams } from "react-router";
import { AppShell } from "@/components/layout/app-shell";
import { ActionCenterPage } from "@/pages/action-center-page";
import { AuditLogsPage } from "@/pages/audit-logs-page";
import { CapabilitiesPage } from "@/pages/capabilities-page";
import { CapabilityPacksPage } from "@/pages/capability-packs-page";
import { AgentConfigurationPage, ModelConfigurationPage, ToolConfigurationPage } from "@/pages/registry-config-page";
import { ThemeProvider } from "@/context/theme-context";
import { RunsPage } from "@/pages/runs-page";
import { NewRunPage } from "@/pages/new-run-page";
import { OverviewPage } from "@/pages/overview-page";
import { StrategiesPage } from "@/pages/strategies-page";
import { StrategyCreatePage } from "@/pages/strategy-create-page";
import { StrategyDetailPage } from "@/pages/strategy-detail-page";
import { RuleSetsPage } from "@/pages/rule-sets-page";
import { WorkItemDetailPage } from "@/pages/work-item-detail-page";
import { WorkItemsPage } from "@/pages/work-items-page";
import { Skeleton } from "@/components/ui/skeleton";
import { DEMO_PROJECT_ID, DEMO_TENANT_ID, demoOverviewPath, demoWorkspacePath } from "@/lib/demo-scope";

const RunDetailPage = lazy(() => import("@/pages/run-detail-page").then((module) => ({ default: module.RunDetailPage })));

const workspaceChildren = () => [
  { index: true, element: <Navigate to="overview" replace /> },
  { path: "overview", element: <OverviewPage /> },
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
  { path: "canvas", element: <StrategyCreatePage standalone /> },
  { path: "actions", element: <ActionCenterPage /> },
  { path: "capabilities", element: <CapabilitiesPage /> },
  { path: "capability-packs", element: <CapabilityPacksPage /> },
  { path: "work-items", children: [
    { index: true, element: <WorkItemsPage /> },
    { path: ":workItemId", element: <WorkItemDetailPage /> },
  ] },
  { path: "rule-sets", element: <RuleSetsPage /> },
  { path: "agents", element: <AgentConfigurationPage /> },
  { path: "tools", element: <ToolConfigurationPage /> },
  { path: "models", element: <ModelConfigurationPage /> },
  { path: "audit-logs", element: <AuditLogsPage /> },
];

function DemoScopeRedirect() {
  const location = useLocation();
  const shortPath = location.pathname.slice(demoWorkspacePath.length) || demoOverviewPath;
  return <Navigate to={`${shortPath}${location.search}${location.hash}`} replace />;
}

function ScopedAppShell() {
  const { tenantId, projectId } = useParams();
  return tenantId === DEMO_TENANT_ID && projectId === DEMO_PROJECT_ID
    ? <DemoScopeRedirect />
    : <AppShell />;
}

const router = createBrowserRouter([
  { path: "/", element: <AppShell />, children: workspaceChildren() },
  { path: "/t/:tenantId/p/:projectId", element: <ScopedAppShell />, children: workspaceChildren() },
  { path: "*", element: <div className="grid min-h-screen place-items-center p-6 text-center"><div><h1 className="text-2xl font-semibold">页面不存在</h1><p className="mt-2 text-sm text-gray-500">请通过 /runs 打开执行控制台。</p></div></div> },
]);
const queryClient = new QueryClient({ defaultOptions: { queries: { retry: 1, staleTime: 1000 } } });

const root = document.getElementById("root");
if (!root) throw new Error("Root element is missing");
createRoot(root).render(<StrictMode><ThemeProvider><QueryClientProvider client={queryClient}><RouterProvider router={router} /></QueryClientProvider></ThemeProvider></StrictMode>);
