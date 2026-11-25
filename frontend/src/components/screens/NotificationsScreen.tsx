"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { toApiError } from "@/lib/axios";
import { formatNotificationTime } from "@/lib/datetime";
import {
  NOTIFICATIONS_PAGE_SIZE,
  useMarkAllNotificationsRead,
  useMarkNotificationRead,
  useNotifications,
  useUnreadCount,
} from "@/lib/notifications-api";
import type { NotificationResponse } from "@/types/notification";
import { Button } from "../Button";
import { Icons } from "../Icons";
import { NoticeBanner } from "../NoticeBanner";
import { Pagination } from "../Pagination";
import { EmptyState, ErrorAlert, LoadingSpinner } from "../StateFeedback";

type Filter = "all" | "unread";

// SCR-COM-01 — Thông báo (FR-32). page.tsx của cả ba vai trò chỉ render component này.
// Không có nút xóa thông báo (BR-27).
export default function NotificationsScreen() {
  const router = useRouter();
  const { user } = useAuth();
  const [filter, setFilter] = useState<Filter>("all");
  const [page, setPage] = useState(1);
  const [actionError, setActionError] = useState<string | null>(null);

  const unreadOnly = filter === "unread";
  const { data, isPending, isError, error, refetch } = useNotifications(unreadOnly, page);
  const { data: unreadCount } = useUnreadCount();
  const markRead = useMarkNotificationRead();
  const markAllRead = useMarkAllNotificationsRead();

  const settingsHref = user ? `/${user.role.toLowerCase()}/notifications/settings` : "#";
  const unread = unreadCount ?? 0;
  const totalPages = data ? Math.max(1, Math.ceil(data.totalCount / NOTIFICATIONS_PAGE_SIZE)) : 1;

  function changeFilter(next: Filter) {
    setFilter(next);
    setPage(1);
  }

  // Bấm một thông báo: chưa đọc thì đánh dấu, không chờ xong mới chuyển trang; có link thì đi tới
  function openNotification(item: NotificationResponse) {
    setActionError(null);
    if (!item.isRead) {
      markRead.mutate(item.id, {
        onError: (err) => setActionError(toApiError(err).message),
      });
    }
    if (item.link) router.push(item.link);
  }

  function readAll() {
    setActionError(null);
    markAllRead.mutate(undefined, {
      onError: (err) => setActionError(toApiError(err).message),
    });
  }

  return (
    <div className="py-8 space-y-4 sm:space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <h1 className="text-2xl font-bold text-on-surface">Thông báo</h1>
        <div className="flex flex-col items-start gap-2 sm:items-end">
          <Button
            variant="outline"
            size="sm"
            onClick={readAll}
            disabled={unread === 0}
            isLoading={markAllRead.isPending}
            className="min-h-11 sm:min-h-0"
          >
            Đánh dấu đã đọc tất cả
          </Button>
          <Link href={settingsHref} className="text-sm font-semibold text-primary hover:underline">
            Cài đặt email →
          </Link>
        </div>
      </div>

      {/* [1] Bộ lọc */}
      <div role="group" aria-label="Lọc thông báo" className="flex flex-wrap gap-2">
        <FilterButton active={filter === "all"} onClick={() => changeFilter("all")}>
          Tất cả
        </FilterButton>
        <FilterButton active={filter === "unread"} onClick={() => changeFilter("unread")}>
          Chưa đọc{unread > 0 ? ` ${unread}` : ""}
        </FilterButton>
      </div>

      {actionError ? (
        <NoticeBanner message={actionError} role="alert" onClose={() => setActionError(null)} />
      ) : null}

      {isPending ? (
        <LoadingSpinner label="Đang tải thông báo..." />
      ) : data === undefined ? (
        <ErrorAlert
          title="Không tải được thông báo"
          message={toApiError(error).message}
          onRetry={() => void refetch()}
        />
      ) : (
        <>
          {isError ? (
            <p role="status" className="rounded-2xl border border-amber-200 bg-amber-100 p-3 text-sm font-semibold text-amber-800">
              Không tải lại được thông báo, đang hiện dữ liệu cũ.
            </p>
          ) : null}

          {data.items.length === 0 ? (
            <EmptyState
              title={unreadOnly ? "Không có thông báo chưa đọc" : "Chưa có thông báo"}
              message={unreadOnly ? "Bạn đã đọc hết thông báo." : "Bạn chưa có thông báo nào."}
            />
          ) : (
            <ul className="rounded-3xl border border-slate-200/90 bg-surface-container-lowest shadow-sm divide-y divide-slate-200/80 overflow-hidden">
              {data.items.map((item) => (
                <li key={item.id}>
                  <NotificationRow item={item} onOpen={() => openNotification(item)} />
                </li>
              ))}
            </ul>
          )}

          {/* [5] Phân trang ở server, 20/trang */}
          {data.totalCount > NOTIFICATIONS_PAGE_SIZE ? (
            <Pagination
              currentPage={page}
              totalPages={totalPages}
              onPageChange={setPage}
              totalItems={data.totalCount}
              pageSize={NOTIFICATIONS_PAGE_SIZE}
            />
          ) : null}
        </>
      )}
    </div>
  );
}

function FilterButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={active}
      className={`min-h-11 sm:min-h-0 px-4 py-1.5 rounded-full text-sm font-semibold transition-colors cursor-pointer ${
        active
          ? "bg-primary text-on-primary shadow-sm"
          : "border border-slate-300 bg-surface-container-lowest text-on-surface hover:bg-surface-container-low"
      }`}
    >
      {children}
    </button>
  );
}

// [4] Một dòng thông báo: chưa đọc có chấm và chữ đậm; message hiện dạng văn bản thuần
function NotificationRow({ item, onOpen }: { item: NotificationResponse; onOpen: () => void }) {
  return (
    <button
      type="button"
      onClick={onOpen}
      className={`w-full text-left px-4 py-3 sm:px-6 sm:py-4 flex items-start gap-3 transition-colors cursor-pointer hover:bg-surface-container-low ${
        item.isRead ? "" : "bg-primary-fixed/20"
      }`}
    >
      <span className="mt-2 w-2 shrink-0" aria-hidden="true">
        {item.isRead ? null : <span className="block w-2 h-2 rounded-full bg-primary" />}
      </span>
      <span className="flex-1 min-w-0 space-y-1">
        <span className="flex flex-col gap-1 sm:flex-row sm:items-start sm:justify-between sm:gap-4">
          <span
            className={`text-sm break-words ${
              item.isRead ? "font-medium text-on-surface" : "font-bold text-on-surface"
            }`}
          >
            {item.isRead ? null : <span className="sr-only">Chưa đọc: </span>}
            {item.title}
          </span>
          <span className="shrink-0 text-xs text-on-surface-variant">
            {formatNotificationTime(item.createdAtUtc)}
          </span>
        </span>
        <span className="block text-sm text-on-surface-variant whitespace-pre-wrap break-words">
          {item.message}
        </span>
      </span>
      {item.link ? (
        <span className="mt-1 shrink-0 text-outline" aria-hidden="true">
          <Icons.ChevronRight />
        </span>
      ) : null}
    </button>
  );
}
