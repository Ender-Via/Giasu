"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { toApiError } from "@/lib/axios";
import {
  useNotificationPreferences,
  useUpdateNotificationPreferences,
} from "@/lib/notifications-api";
import {
  NOTIFICATION_TYPE_LABELS,
  type NotificationPreferenceItem,
  type NotificationType,
} from "@/types/notification";
import { ApiErrorAlert } from "../ApiErrorAlert";
import { Button } from "../Button";
import { ConfirmDialog } from "../ConfirmDialog";
import { Icons } from "../Icons";
import { NoticeBanner } from "../NoticeBanner";
import { EmptyState, ErrorAlert, LoadingSpinner } from "../StateFeedback";

const UNSAVED_MESSAGE = "Bạn có thay đổi chưa lưu. Rời trang?";
const SAVED_MESSAGE = "Đã lưu cài đặt email.";

// SCR-COM-02 — Cài đặt email (FR-32, D13). Công tắc chỉ đổi trên màn hình, bấm Lưu mới gửi toàn
// bộ danh sách. Thông báo trong ứng dụng luôn được gửi, ở đây chỉ bật/tắt email từng loại (BR-27).
export default function NotificationSettingsScreen() {
  const router = useRouter();
  const { user } = useAuth();
  const { data, isPending, error, refetch } = useNotificationPreferences();
  const updatePreferences = useUpdateNotificationPreferences();

  // Thay đổi chưa lưu, theo loại; null = chưa đổi gì
  const [draft, setDraft] = useState<Partial<Record<NotificationType, boolean>> | null>(null);
  const [saveError, setSaveError] = useState<unknown>(null);
  const [saved, setSaved] = useState(false);
  const [leaveOpen, setLeaveOpen] = useState(false);

  const notificationsHref = user ? `/${user.role.toLowerCase()}/notifications` : "/";

  const items: NotificationPreferenceItem[] = (data ?? []).map((item) => ({
    type: item.type,
    emailEnabled: draft?.[item.type] ?? item.emailEnabled,
  }));
  const isDirty = (data ?? []).some(
    (item) => draft?.[item.type] !== undefined && draft[item.type] !== item.emailEnabled
  );

  // Hỏi trước khi đóng tab hay tải lại khi có thay đổi chưa lưu (ui-screens.md §4.3)
  useEffect(() => {
    if (!isDirty) return;
    const handler = (event: BeforeUnloadEvent) => {
      event.preventDefault();
    };
    window.addEventListener("beforeunload", handler);
    return () => window.removeEventListener("beforeunload", handler);
  }, [isDirty]);

  useEffect(() => {
    if (!saved) return;
    const timer = setTimeout(() => setSaved(false), 6000);
    return () => clearTimeout(timer);
  }, [saved]);

  function toggle(type: NotificationType, value: boolean) {
    setSaved(false);
    setDraft((prev) => ({ ...(prev ?? {}), [type]: value }));
  }

  function leave() {
    if (isDirty) {
      setLeaveOpen(true);
      return;
    }
    router.push(notificationsHref);
  }

  async function save() {
    setSaveError(null);
    setSaved(false);
    try {
      await updatePreferences.mutateAsync({ items });
      setDraft(null);
      setSaved(true);
    } catch (err) {
      setSaveError(err);
    }
  }

  return (
    <div className="py-8 space-y-4 sm:space-y-6">
      <div className="space-y-1">
        <button
          type="button"
          onClick={leave}
          className="inline-flex items-center gap-1 text-sm font-semibold text-primary hover:underline cursor-pointer"
        >
          <Icons.ChevronLeft />
          Thông báo
        </button>
        <h1 className="text-2xl font-bold text-on-surface">Cài đặt email</h1>
        <p className="text-sm text-on-surface-variant">
          Thông báo trong ứng dụng luôn được gửi. Tắt một loại ở đây chỉ ngừng gửi email loại đó.
        </p>
      </div>

      {saved ? (
        <NoticeBanner message={SAVED_MESSAGE} role="status" onClose={() => setSaved(false)} />
      ) : null}

      {isPending ? (
        <LoadingSpinner label="Đang tải cài đặt email..." />
      ) : data === undefined ? (
        <ErrorAlert
          title="Không tải được cài đặt email"
          message={toApiError(error).message}
          onRetry={() => void refetch()}
        />
      ) : items.length === 0 ? (
        <EmptyState
          title="Chưa có loại thông báo"
          message="Vai trò của bạn chưa có loại thông báo nào gửi qua email."
        />
      ) : (
        <form
          onSubmit={(event) => {
            event.preventDefault();
            void save();
          }}
          className="rounded-3xl border border-slate-200/90 bg-surface-container-lowest p-4 sm:p-6 shadow-sm space-y-4"
        >
          {saveError ? <ApiErrorAlert error={saveError} /> : null}

          {/* [1] Danh sách loại thông báo của vai trò */}
          <ul className="divide-y divide-slate-200/80">
            {items.map((item) => (
              <li key={item.type} className="flex items-center justify-between gap-4 py-3">
                <span id={`pref-${item.type}`} className="text-sm font-medium text-on-surface">
                  {NOTIFICATION_TYPE_LABELS[item.type] ?? item.type}
                </span>
                <EmailSwitch
                  labelledBy={`pref-${item.type}`}
                  checked={item.emailEnabled}
                  disabled={updatePreferences.isPending}
                  onChange={(value) => toggle(item.type, value)}
                />
              </li>
            ))}
          </ul>

          {/* [2] Hủy / Lưu */}
          <div className="flex justify-end gap-2">
            <Button
              type="button"
              variant="outline"
              onClick={leave}
              disabled={updatePreferences.isPending}
              className="min-h-11 sm:min-h-0"
            >
              Hủy
            </Button>
            <Button
              type="submit"
              variant="primary"
              isLoading={updatePreferences.isPending}
              disabled={!isDirty}
              className="min-h-11 sm:min-h-0"
            >
              Lưu
            </Button>
          </div>
        </form>
      )}

      <ConfirmDialog
        isOpen={leaveOpen}
        onClose={() => setLeaveOpen(false)}
        onConfirm={() => {
          setLeaveOpen(false);
          router.push(notificationsHref);
        }}
        title="Rời trang?"
        message={UNSAVED_MESSAGE}
        confirmText="Rời trang"
      />
    </div>
  );
}

// Công tắc bật/tắt email một loại
function EmailSwitch({
  checked,
  disabled,
  labelledBy,
  onChange,
}: {
  checked: boolean;
  disabled?: boolean;
  labelledBy: string;
  onChange: (value: boolean) => void;
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-labelledby={labelledBy}
      disabled={disabled}
      onClick={() => onChange(!checked)}
      className="shrink-0 inline-flex items-center gap-2 min-h-11 sm:min-h-0 cursor-pointer disabled:cursor-not-allowed disabled:opacity-50 focus-visible:outline-none group"
    >
      <span
        className={`relative inline-block w-11 h-6 rounded-full transition-colors group-focus-visible:ring-2 group-focus-visible:ring-primary group-focus-visible:ring-offset-2 ${
          checked ? "bg-primary" : "bg-slate-300"
        }`}
      >
        <span
          className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white shadow transition-transform ${
            checked ? "translate-x-5" : ""
          }`}
        />
      </span>
      <span className="w-8 text-left text-sm font-semibold text-on-surface-variant">
        {checked ? "Bật" : "Tắt"}
      </span>
    </button>
  );
}
