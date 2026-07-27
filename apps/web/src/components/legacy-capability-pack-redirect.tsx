import { Navigate, useParams, useSearchParams } from "react-router";
import { workKeyForPackName } from "@/lib/capability-pack-routes";
import { useWorkspaceScope } from "@/lib/demo-scope";

export function LegacyCapabilityPackListRedirect() {
  const { workspacePath } = useWorkspaceScope();
  const notice = encodeURIComponent("业务能力包入口已迁移到业务工作。");
  return <Navigate to={`${workspacePath}/business-works?notice=${notice}`} replace />;
}

export function LegacyCapabilityPackDetailRedirect({ mode }: { mode: "settings" | "workbench" }) {
  const { packName = "" } = useParams();
  const { workspacePath } = useWorkspaceScope();
  const [params] = useSearchParams();
  const workKey = workKeyForPackName(decodeURIComponent(packName));
  if (!workKey) {
    const notice = encodeURIComponent(`无法将能力包「${decodeURIComponent(packName)}」映射到业务工作，已返回总览。`);
    return <Navigate to={`${workspacePath}/business-works?notice=${notice}`} replace />;
  }
  const suffix = mode === "workbench" ? "workbench" : "settings";
  const search = params.toString();
  return <Navigate to={`${workspacePath}/business-works/${workKey}/${suffix}${search ? `?${search}` : ""}`} replace />;
}
