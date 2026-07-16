import * as React from "react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Spinner } from "@/components/ui/spinner";

export type SharePermission = "view" | "edit" | "public" | "embed";

export type ShareLinkStatus = "active" | "expired" | "revoked";

export type ShareLink = {
  id: string;
  permission: SharePermission;
  token: string;
  url: string;
  embedCode?: string;
  expiresAt?: string;
  allowedDomains?: string[];
  status: ShareLinkStatus;
  tenantId?: string;
  createdAt?: string;
};

const permissionLabel: Record<SharePermission, string> = {
  view: "只读查看",
  edit: "可编辑",
  public: "公开链接",
  embed: "嵌入式 iframe",
};

const permissionDescription: Record<SharePermission, string> = {
  view: "登录用户可查看，不可修改图表与筛选",
  edit: "协作者可编辑布局、筛选与图表配置",
  public: "持有链接的任何人可只读访问，无需登录",
  embed: "生成 iframe 代码，可嵌入外部门户或 Wiki",
};

const statusLabel: Record<ShareLinkStatus, string> = {
  active: "有效",
  expired: "已过期",
  revoked: "已撤销",
};

const statusVariant: Record<
  ShareLinkStatus,
  "default" | "secondary" | "success" | "warning" | "destructive"
> = {
  active: "success",
  expired: "secondary",
  revoked: "destructive",
};

export type ShareEmbedDialogProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  resourceName: React.ReactNode;
  description?: React.ReactNode;
  tenantId?: string;
  /** 当前选中的权限模式 */
  permission?: SharePermission;
  onPermissionChange?: (permission: SharePermission) => void;
  /** 已有分享链接列表 */
  links?: ShareLink[];
  /** 域名白名单，逗号分隔输入 */
  allowedDomains?: string;
  onAllowedDomainsChange?: (value: string) => void;
  /** 过期时间，如 7 天 / 2026-07-01 */
  expiry?: string;
  onExpiryChange?: (value: string) => void;
  saving?: boolean;
  onGenerate?: (permission: SharePermission) => void;
  onRevoke?: (link: ShareLink) => void;
  onCopyLink?: (url: string) => void;
  onCopyEmbed?: (code: string) => void;
  className?: string;
};

/**
 * BI 分享与嵌入式对话框 — view/edit/public/embed 权限、iframe code、token/过期/域名白名单、撤销共享。
 * @see references/layout-patterns/bi-share-embed.md
 */
export function ShareEmbedDialog({
  open,
  onOpenChange,
  resourceName,
  description,
  tenantId,
  permission = "view",
  onPermissionChange,
  links = [],
  allowedDomains = "",
  onAllowedDomainsChange,
  expiry = "7 天",
  onExpiryChange,
  saving = false,
  onGenerate,
  onRevoke,
  onCopyLink,
  onCopyEmbed,
  className,
}: ShareEmbedDialogProps) {
  const activeLink = links.find((l) => l.permission === permission && l.status === "active");
  const embedCode =
    activeLink?.embedCode ??
    (permission === "embed"
      ? `<iframe src="https://bi.example.com/embed/dash-001?token=***" width="100%" height="600" frameborder="0" allowfullscreen></iframe>`
      : undefined);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className={cn("sm:max-w-[560px]", className)}>
        <DialogHeader>
          <DialogTitle>分享与嵌入</DialogTitle>
          <DialogDescription>
            {description ?? (
              <>
                配置 <strong>{resourceName}</strong> 的访问权限与分享方式
                {tenantId ? (
                  <>
                    {" "}
                    · 租户 <code className="text-theme-xs">{tenantId}</code>
                  </>
                ) : null}
              </>
            )}
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-5 py-2">
          <div className="grid gap-3">
            <Label className="text-theme-sm font-medium text-gray-900 dark:text-white/90">
              访问权限
            </Label>
            <RadioGroup
              value={permission}
              onValueChange={(v) => onPermissionChange?.(v as SharePermission)}
              className="grid gap-2"
            >
              {(Object.keys(permissionLabel) as SharePermission[]).map((key) => (
                <label
                  key={key}
                  className={cn(
                    "flex cursor-pointer items-start gap-3 rounded-xl border px-4 py-3 transition-colors",
                    permission === key
                      ? "border-brand-500 bg-brand-50/50 dark:border-brand-500/50 dark:bg-brand-500/10"
                      : "border-gray-200 dark:border-gray-800"
                  )}
                >
                  <RadioGroupItem value={key} className="mt-0.5" />
                  <div className="min-w-0 flex-1">
                    <p className="text-theme-sm font-medium text-gray-900 dark:text-white/90">
                      {permissionLabel[key]}
                    </p>
                    <p className="mt-0.5 text-theme-xs text-gray-500">
                      {permissionDescription[key]}
                    </p>
                  </div>
                </label>
              ))}
            </RadioGroup>
          </div>

          {(permission === "public" || permission === "embed") && (
            <div className="grid gap-4 rounded-xl border border-gray-200 bg-gray-50/50 p-4 dark:border-gray-800 dark:bg-white/[0.02]">
              <div className="grid gap-2">
                <Label htmlFor="share-expiry" className="text-theme-sm">
                  链接有效期
                </Label>
                <Input
                  id="share-expiry"
                  value={expiry}
                  onChange={(e) => onExpiryChange?.(e.target.value)}
                  placeholder="7 天 / 30 天 / 2026-07-01"
                />
                <p className="text-theme-xs text-gray-500">过期后链接自动失效，需重新生成</p>
              </div>
              {permission === "embed" ? (
                <div className="grid gap-2">
                  <Label htmlFor="share-domains" className="text-theme-sm">
                    域名白名单
                  </Label>
                  <Input
                    id="share-domains"
                    value={allowedDomains}
                    onChange={(e) => onAllowedDomainsChange?.(e.target.value)}
                    placeholder="portal.example.com, wiki.example.com"
                  />
                  <p className="text-theme-xs text-gray-500">
                    仅允许列出的域名通过 iframe 嵌入；留空表示不限制
                  </p>
                </div>
              ) : null}
            </div>
          )}

          {activeLink ? (
            <div className="grid gap-3">
              <div className="flex items-center justify-between gap-2">
                <Label className="text-theme-sm font-medium">当前链接</Label>
                <Badge variant={statusVariant[activeLink.status]}>
                  {statusLabel[activeLink.status]}
                </Badge>
              </div>
              <div className="flex gap-2">
                <Input readOnly value={activeLink.url} className="font-mono text-theme-xs" />
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => onCopyLink?.(activeLink.url)}
                >
                  复制
                </Button>
              </div>
              {activeLink.expiresAt ? (
                <p className="text-theme-xs text-gray-500">有效期至 {activeLink.expiresAt}</p>
              ) : null}
              {activeLink.allowedDomains?.length ? (
                <p className="text-theme-xs text-gray-500">
                  允许域名：{activeLink.allowedDomains.join("、")}
                </p>
              ) : null}
              {embedCode ? (
                <div className="grid gap-2">
                  <Label className="text-theme-sm">iframe 嵌入代码</Label>
                  <Textarea
                    readOnly
                    value={embedCode}
                    rows={3}
                    className="font-mono text-theme-xs"
                  />
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    className="w-fit"
                    onClick={() => onCopyEmbed?.(embedCode)}
                  >
                    复制嵌入代码
                  </Button>
                </div>
              ) : null}
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="w-fit text-error-500 hover:text-error-600"
                onClick={() => onRevoke?.(activeLink)}
              >
                撤销此分享
              </Button>
            </div>
          ) : null}

          {links.filter((l) => l.status !== "active").length > 0 ? (
            <div className="grid gap-2">
              <Label className="text-theme-sm font-medium text-gray-500">历史链接</Label>
              <ul className="divide-y divide-gray-100 rounded-xl border border-gray-200 dark:divide-white/[0.05] dark:border-gray-800">
                {links
                  .filter((l) => l.status !== "active")
                  .map((link) => (
                    <li
                      key={link.id}
                      className="flex items-center justify-between gap-2 px-4 py-2.5 text-theme-xs"
                    >
                      <span className="truncate text-gray-500">
                        {permissionLabel[link.permission]} · {link.token.slice(0, 8)}…
                      </span>
                      <Badge variant={statusVariant[link.status]} className="shrink-0">
                        {statusLabel[link.status]}
                      </Badge>
                    </li>
                  ))}
              </ul>
            </div>
          ) : null}
        </div>

        <DialogFooter className="gap-2 sm:gap-0">
          <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
            关闭
          </Button>
          <Button type="button" disabled={saving} onClick={() => onGenerate?.(permission)}>
            {saving ? (
              <>
                <Spinner className="mr-2 size-4" />
                生成中…
              </>
            ) : activeLink ? (
              "重新生成链接"
            ) : (
              "生成分享链接"
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
