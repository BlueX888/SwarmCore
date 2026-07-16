import * as React from "react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  ShareEmbedDialog,
  type ShareLink,
  type SharePermission,
} from "./share-embed-dialog";

export type ShareAccessDashboardProps = {
  title?: React.ReactNode;
  description?: React.ReactNode;
  tenantId?: string;
  links?: ShareLink[];
  shareOpen?: boolean;
  onShareOpenChange?: (open: boolean) => void;
  permission?: SharePermission;
  onPermissionChange?: (permission: SharePermission) => void;
  allowedDomains?: string;
  onAllowedDomainsChange?: (value: string) => void;
  expiry?: string;
  onExpiryChange?: (value: string) => void;
  shareSaving?: boolean;
  onGenerateShare?: (permission: SharePermission) => void;
  onRevokeShare?: (link: ShareLink) => void;
  onCopyLink?: (url: string) => void;
  onCopyEmbed?: (code: string) => void;
  renderMain: () => React.ReactNode;
  className?: string;
};

const permissionBadge: Record<SharePermission, string> = {
  view: "只读",
  edit: "可编辑",
  public: "公开",
  embed: "嵌入",
};

/**
 * BI 分享与权限仪表盘 — 主内容区 + ShareEmbedDialog 入口 + 租户隔离提示。
 * @see references/layout-patterns/bi-share-embed.md
 */
export function ShareAccessDashboard({
  title = "经营分析仪表盘",
  description,
  tenantId = "tenant-acme",
  links = [],
  shareOpen = false,
  onShareOpenChange,
  permission = "view",
  onPermissionChange,
  allowedDomains,
  onAllowedDomainsChange,
  expiry,
  onExpiryChange,
  shareSaving = false,
  onGenerateShare,
  onRevokeShare,
  onCopyLink,
  onCopyEmbed,
  renderMain,
  className,
}: ShareAccessDashboardProps) {
  const activeLinks = links.filter((l) => l.status === "active");

  return (
    <div className={cn("flex flex-col gap-4", className)}>
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          {title ? (
            <h2 className="text-title-sm font-semibold text-gray-900 dark:text-white/90">{title}</h2>
          ) : null}
          {description ? (
            <p className="mt-1 text-theme-sm text-gray-500">{description}</p>
          ) : (
            <p className="mt-1 text-theme-sm text-gray-500">
              租户 <code className="text-theme-xs">{tenantId}</code> · 分享与嵌入受租户隔离约束
            </p>
          )}
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {activeLinks.map((link) => (
            <Badge key={link.id} variant="secondary" className="text-theme-xs">
              {permissionBadge[link.permission]}
              {link.expiresAt ? ` · 至 ${link.expiresAt}` : ""}
            </Badge>
          ))}
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => onShareOpenChange?.(true)}
          >
            分享
          </Button>
        </div>
      </div>

      <div className="min-w-0">{renderMain()}</div>

      <ShareEmbedDialog
        open={shareOpen}
        onOpenChange={(open) => onShareOpenChange?.(open)}
        resourceName={title}
        tenantId={tenantId}
        permission={permission}
        onPermissionChange={onPermissionChange}
        links={links}
        allowedDomains={allowedDomains}
        onAllowedDomainsChange={onAllowedDomainsChange}
        expiry={expiry}
        onExpiryChange={onExpiryChange}
        saving={shareSaving}
        onGenerate={onGenerateShare}
        onRevoke={onRevokeShare}
        onCopyLink={onCopyLink}
        onCopyEmbed={onCopyEmbed}
      />
    </div>
  );
}
