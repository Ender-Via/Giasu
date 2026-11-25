"use client";

import { useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useUnreadCount } from "@/lib/notifications-api";
import { Icons } from "./Icons";

const REFRESH_INTERVAL_MS = 60_000;

// Chuông thông báo ở khung trang (ui-screens.md §4.1 [7], FR-32): số chưa đọc tải lại mỗi 60 giây
// và khi đổi trang; 0 thì không hiện số, > 99 hiện "99+". Lỗi tải chỉ ẩn số, chuông vẫn bấm được.
export function NotificationBell({ href }: { href: string }) {
  const pathname = usePathname();
  const { data: count, refetch } = useUnreadCount(REFRESH_INTERVAL_MS);

  useEffect(() => {
    void refetch();
  }, [pathname, refetch]);

  const unread = count ?? 0;
  const badgeText = unread > 99 ? "99+" : String(unread);
  const label = unread > 0 ? `Thông báo, ${unread} chưa đọc` : "Thông báo";

  return (
    <Link
      href={href}
      aria-label={label}
      className="relative p-2 rounded-full text-on-surface-variant hover:bg-surface-container-low hover:text-on-surface transition-colors"
    >
      <Icons.Bell />
      {unread > 0 ? (
        <span
          aria-hidden="true"
          className="absolute -top-0.5 -right-0.5 min-w-5 h-5 px-1 rounded-full bg-error text-white text-[11px] font-bold leading-5 text-center"
        >
          {badgeText}
        </span>
      ) : null}
    </Link>
  );
}
