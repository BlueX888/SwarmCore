import * as React from "react";
import { Link } from "react-router";
import { Bell, X } from "lucide-react";
import { cn } from "@/lib/utils";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

export type NotificationStatus = "online" | "offline" | "busy";

export type NotificationItem = {
  id: string;
  avatar?: string;
  name: string;
  message: string;
  category?: string;
  time: string;
  status?: NotificationStatus;
  href?: string;
};

export type NotificationDropdownProps = {
  items: NotificationItem[];
  title?: string;
  viewAllHref?: string;
  viewAllLabel?: string;
  hasUnread?: boolean;
  onOpenChange?: (open: boolean) => void;
  className?: string;
};

export function NotificationDropdown({
  items,
  title = "Notification",
  viewAllHref = "/notifications",
  viewAllLabel = "View All Notifications",
  hasUnread: hasUnreadProp,
  onOpenChange,
  className,
}: NotificationDropdownProps) {
  const [open, setOpen] = React.useState(false);
  const [hasUnread, setHasUnread] = React.useState(hasUnreadProp ?? true);

  React.useEffect(() => {
    if (hasUnreadProp !== undefined) {
      setHasUnread(hasUnreadProp);
    }
  }, [hasUnreadProp]);

  const handleOpenChange = (nextOpen: boolean) => {
    setOpen(nextOpen);
    if (nextOpen) {
      setHasUnread(false);
    }
    onOpenChange?.(nextOpen);
  };

  return (
    <DropdownMenu open={open} onOpenChange={handleOpenChange}>
      <DropdownMenuTrigger asChild>
        <Button
          variant="outline"
          size="icon"
          className={cn(
            "relative rounded-full border-gray-200 bg-white text-gray-500 hover:bg-gray-100 hover:text-gray-700 dark:border-gray-800 dark:bg-gray-900 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-white",
            className,
          )}
          aria-label={title}
        >
          {hasUnread ? (
            <span className="absolute top-0.5 right-0 z-10 flex size-2 rounded-full bg-orange-400">
              <span className="absolute inline-flex size-full animate-ping rounded-full bg-orange-400 opacity-75" />
            </span>
          ) : null}
          <Bell className="size-5" aria-hidden />
        </Button>
      </DropdownMenuTrigger>

      <DropdownMenuContent
        align="end"
        className="flex w-[350px] flex-col rounded-2xl border-gray-200 p-3 shadow-theme-lg sm:w-[361px] dark:border-gray-800"
      >
        <div className="mb-3 flex items-center justify-between border-b border-gray-100 pb-3 dark:border-gray-700">
          <h5 className="text-lg font-semibold text-gray-800 dark:text-gray-200">
            {title}
          </h5>
          <button
            type="button"
            onClick={() => handleOpenChange(false)}
            className="text-gray-500 transition hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
            aria-label="关闭通知"
          >
            <X className="size-6" aria-hidden />
          </button>
        </div>

        <ul className="custom-scrollbar flex max-h-[480px] flex-col overflow-y-auto">
          {items.map((item) => (
            <li key={item.id}>
              {item.href ? (
                <Link
                  to={item.href}
                  onClick={() => handleOpenChange(false)}
                  className="flex gap-3 rounded-lg border-b border-gray-100 p-3 px-4.5 py-3 transition-colors hover:bg-gray-100 dark:border-gray-800 dark:hover:bg-white/5"
                >
                  <NotificationRow item={item} />
                </Link>
              ) : (
                <button
                  type="button"
                  onClick={() => handleOpenChange(false)}
                  className="flex w-full gap-3 rounded-lg border-b border-gray-100 p-3 px-4.5 py-3 text-left transition-colors hover:bg-gray-100 dark:border-gray-800 dark:hover:bg-white/5"
                >
                  <NotificationRow item={item} />
                </button>
              )}
            </li>
          ))}
        </ul>

        <Link
          to={viewAllHref}
          onClick={() => handleOpenChange(false)}
          className="mt-3 block rounded-lg border border-gray-300 bg-white px-4 py-2 text-center text-sm font-medium text-gray-700 transition-colors hover:bg-gray-100 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-400 dark:hover:bg-gray-700"
        >
          {viewAllLabel}
        </Link>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

function NotificationRow({ item }: { item: NotificationItem }) {
  return (
    <>
      <span className="relative block size-10 shrink-0">
        <Avatar size="md" status={item.status ?? "none"}>
          {item.avatar ? (
            <AvatarImage src={item.avatar} alt={item.name} />
          ) : (
            <AvatarFallback name={item.name} />
          )}
        </Avatar>
      </span>

      <span className="block min-w-0">
        <span className="mb-1.5 block space-x-1 text-theme-sm text-gray-500 dark:text-gray-400">
          <span className="font-medium text-gray-800 dark:text-white/90">
            {item.name}
          </span>
          <span>{item.message}</span>
        </span>

        <span className="flex items-center gap-2 text-theme-xs text-gray-500 dark:text-gray-400">
          {item.category ? <span>{item.category}</span> : null}
          {item.category ? (
            <span className="size-1 rounded-full bg-gray-400" aria-hidden />
          ) : null}
          <span>{item.time}</span>
        </span>
      </span>
    </>
  );
}
