import { useParams } from "react-router";

/** Local/dev default scope used by the short workspace routes. */
export const DEMO_TENANT_ID = "00000000-0000-0000-0000-000000000001";
export const DEMO_PROJECT_ID = "00000000-0000-0000-0000-000000000002";

export const demoWorkspacePath = `/t/${DEMO_TENANT_ID}/p/${DEMO_PROJECT_ID}`;
export const demoOverviewPath = "/overview";
export const demoRunsPath = "/runs";

export function useWorkspaceScope() {
  const { tenantId, projectId } = useParams();
  const isExplicitScope = Boolean(tenantId && projectId);
  return {
    tenantId: tenantId ?? DEMO_TENANT_ID,
    projectId: projectId ?? DEMO_PROJECT_ID,
    workspacePath: isExplicitScope ? `/t/${tenantId}/p/${projectId}` : "",
  };
}
