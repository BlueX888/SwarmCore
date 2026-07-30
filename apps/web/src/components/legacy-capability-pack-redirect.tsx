import { Navigate, useParams, useSearchParams } from "react-router";
import { workKeyForPackName } from "@/lib/capability-pack-routes";
import { useWorkspaceScope } from "@/lib/demo-scope";

export function LegacyCapabilityPackListRedirect() {
  const { workspacePath } = useWorkspaceScope();
  return <Navigate to={`${workspacePath}/overview`} replace />;
}

export function LegacyCapabilityPackDetailRedirect({ mode }: { mode: "settings" | "workbench" }) {
  const { packName = "" } = useParams();
  const { workspacePath } = useWorkspaceScope();
  const [params] = useSearchParams();
  const workKey = workKeyForPackName(decodeURIComponent(packName));
  if (!workKey) {
    return <Navigate to={`${workspacePath}/overview`} replace />;
  }
  const suffix = mode === "workbench" ? "workbench" : "settings";
  const search = params.toString();
  return <Navigate to={`${workspacePath}/business-works/${workKey}/${suffix}${search ? `?${search}` : ""}`} replace />;
}
