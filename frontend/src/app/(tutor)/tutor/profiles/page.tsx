"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import {
  ApiErrorAlert,
  Button,
  ConfirmDialog,
  EmptyState,
  ErrorAlert,
  LoadingSpinner,
  NoticeBanner,
} from "@/components";
import { toApiError } from "@/lib/axios";
import type { Availability, TutorProfileResponse } from "@/types/tutor-profile";
import { ProfileCard } from "./_components/ProfileCard";
import { VerificationBand } from "./_components/VerificationBand";
import {
  useMyTutorProfiles,
  useSetAvailability,
  useSetDefaultProfile,
  useSubmitProfile,
} from "./_lib/tutor-profiles-api";
import { MAX_PROFILES } from "./_lib/tutor-profile-rules";
import { useNotice } from "./_lib/use-notice";

// Hồ sơ mặc định lên đầu, còn lại mới cập nhật trước (SCR-TUT-01 [3])
function sortProfiles(profiles: TutorProfileResponse[]) {
  return [...profiles].sort((a, b) => {
    if (a.isDefault !== b.isDefault) return a.isDefault ? -1 : 1;
    return b.updatedAtUtc.localeCompare(a.updatedAtUtc);
  });
}

// SCR-TUT-01 — Hồ sơ gia sư (FR-03, FR-04, FR-36)
export default function TutorProfilesPage() {
  const router = useRouter();
  const { data, isPending, isError, error, refetch, isFetching } = useMyTutorProfiles();
  const setAvailability = useSetAvailability();
  const setDefault = useSetDefaultProfile();
  const submitProfile = useSubmitProfile();
  const { notice, showSuccess, showError, clear } = useNotice();

  const [pendingAvailability, setPendingAvailability] = useState<{
    id: string;
    value: Availability;
  } | null>(null);
  const [settingDefaultId, setSettingDefaultId] = useState<string | null>(null);
  const [submitTarget, setSubmitTarget] = useState<TutorProfileResponse | null>(null);
  const [submitError, setSubmitError] = useState<unknown>(null);

  const profiles = useMemo(() => (data ? sortProfiles(data) : []), [data]);
  const isFull = profiles.length >= MAX_PROFILES;

  function handleAvailabilityChange(profile: TutorProfileResponse, value: Availability) {
    setPendingAvailability({ id: profile.id, value });
    clear();
    setAvailability.mutate(
      { id: profile.id, availability: value },
      {
        onSuccess: () => showSuccess("Đã cập nhật trạng thái nhận dạy."),
        // Lỗi: ô chọn tự về giá trị cũ vì hiển thị lại theo dữ liệu server
        onError: (err) => showError(toApiError(err).message),
        onSettled: () => setPendingAvailability(null),
      }
    );
  }

  function handleSetDefault(profile: TutorProfileResponse) {
    setSettingDefaultId(profile.id);
    clear();
    setDefault.mutate(profile.id, {
      onSuccess: () => showSuccess(`Đã đặt "${profile.title}" làm hồ sơ mặc định.`),
      onError: (err) => showError(toApiError(err).message),
      onSettled: () => setSettingDefaultId(null),
    });
  }

  function openSubmit(profile: TutorProfileResponse) {
    setSubmitError(null);
    setSubmitTarget(profile);
  }

  async function confirmSubmit() {
    if (!submitTarget) return;
    try {
      await submitProfile.mutateAsync(submitTarget.id);
      showSuccess(`Đã gửi hồ sơ "${submitTarget.title}" cho Admin duyệt.`);
      setSubmitTarget(null);
    } catch (err) {
      // 400 liệt kê điều còn thiếu do backend xác định; giữ hộp thoại mở để đọc
      setSubmitError(err);
    }
  }

  return (
    <div className="py-8 space-y-4 sm:space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="space-y-1">
          <h1 className="text-2xl font-bold text-on-surface">Hồ sơ gia sư</h1>
          <p className="text-sm text-on-surface-variant">
            Tạo hồ sơ riêng cho từng nhóm môn/cấp học để phụ huynh tìm thấy bạn.
          </p>
        </div>
        {data ? (
          <div className="flex flex-col items-start gap-1 sm:items-end">
            <Button
              variant="primary"
              className="min-h-11 sm:min-h-0"
              disabled={isFull}
              onClick={() => router.push("/tutor/profiles/new")}
            >
              + Tạo hồ sơ mới
            </Button>
            <span className="text-xs text-on-surface-variant">
              {profiles.length}/{MAX_PROFILES} hồ sơ{isFull ? " · Tối đa 5 hồ sơ" : ""}
            </span>
          </div>
        ) : null}
      </div>

      {notice ? (
        <NoticeBanner message={notice.message} role={notice.role} onClose={clear} />
      ) : null}

      <VerificationBand />

      {isPending ? (
        <LoadingSpinner label="Đang tải hồ sơ..." />
      ) : !data ? (
        <ErrorAlert
          title="Không tải được hồ sơ"
          message={toApiError(error).message}
          onRetry={() => void refetch()}
        />
      ) : (
        <>
          {/* Đã có dữ liệu mà lần tải lại lỗi: giữ danh sách cũ, cảnh báo phía trên (§4.2) */}
          {isError && !isFetching ? (
            <ErrorAlert
              title="Không làm mới được danh sách"
              message={toApiError(error).message}
              onRetry={() => void refetch()}
            />
          ) : null}

          {profiles.length === 0 ? (
            <EmptyState
              title="Bạn chưa có hồ sơ nào"
              message="Bạn chưa có hồ sơ nào. Tạo hồ sơ đầu tiên để phụ huynh tìm thấy bạn."
              actionText="Tạo hồ sơ"
              onAction={() => router.push("/tutor/profiles/new")}
            />
          ) : (
            <div className="space-y-3">
              {profiles.map((profile) => (
                <ProfileCard
                  key={profile.id}
                  profile={profile}
                  pendingAvailability={
                    pendingAvailability?.id === profile.id ? pendingAvailability.value : null
                  }
                  isSettingDefault={settingDefaultId === profile.id}
                  onAvailabilityChange={(value) => handleAvailabilityChange(profile, value)}
                  onSetDefault={() => handleSetDefault(profile)}
                  onSubmit={() => openSubmit(profile)}
                />
              ))}
            </div>
          )}
        </>
      )}

      <ConfirmDialog
        isOpen={submitTarget !== null}
        onClose={() => setSubmitTarget(null)}
        onConfirm={confirmSubmit}
        isLoading={submitProfile.isPending}
        title="Gửi duyệt hồ sơ"
        confirmText="Gửi duyệt"
        message={
          <div className="space-y-3 text-left">
            <p>
              Gửi hồ sơ &apos;{submitTarget?.title}&apos; cho Admin duyệt? Trong lúc chờ
              duyệt bạn không sửa được hồ sơ.
            </p>
            {submitError ? <ApiErrorAlert error={submitError} /> : null}
          </div>
        }
      />
    </div>
  );
}
