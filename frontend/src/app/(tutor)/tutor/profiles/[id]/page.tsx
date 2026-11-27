"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import {
  Badge,
  ConfirmDialog,
  EmptyState,
  ErrorAlert,
  Icons,
  LoadingSpinner,
  NoticeBanner,
} from "@/components";
import { toApiError } from "@/lib/axios";
import {
  TUTOR_PROFILE_STATUS_LABELS,
  TUTOR_PROFILE_STATUS_TONES,
  type TutorProfileUpsertRequest,
} from "@/types/tutor-profile";
import { EvidenceSection } from "../_components/EvidenceSection";
import { ProfileForm } from "../_components/ProfileForm";
import { useTutorProfile, useUpdateTutorProfile } from "../_lib/tutor-profiles-api";
import {
  toFormValues,
  toUpsertRequest,
  type TutorProfileFormValues,
} from "../_lib/tutor-profile-rules";
import { useNotice } from "../_lib/use-notice";

const CREATED_MESSAGE =
  "Đã lưu hồ sơ nháp. Tải lên minh chứng rồi gửi duyệt ở trang Hồ sơ gia sư.";

// SCR-TUT-02 — Sửa hồ sơ (FR-03, FR-04). useSearchParams cần Suspense để trang dựng tĩnh được.
export default function EditTutorProfilePage() {
  return (
    <Suspense fallback={<LoadingSpinner label="Đang tải hồ sơ..." />}>
      <EditTutorProfile />
    </Suspense>
  );
}

function EditTutorProfile() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const searchParams = useSearchParams();
  const isJustCreated = searchParams.get("created") === "1";

  const { data: profile, isPending, isError, isFetching, error, refetch } = useTutorProfile(id);
  const updateProfile = useUpdateTutorProfile(id);
  const { notice, showSuccess, clear } = useNotice(
    isJustCreated ? { message: CREATED_MESSAGE, role: "status" } : null
  );
  const [submitError, setSubmitError] = useState<unknown>(null);
  // Hồ sơ Approved: giữ dữ liệu chờ người dùng xác nhận chuyển về Chờ duyệt (BR-25)
  const [pendingApprovedSave, setPendingApprovedSave] =
    useState<TutorProfileUpsertRequest | null>(null);

  // Bỏ ?created=1 khỏi URL để tải lại trang không hiện lại dải báo
  useEffect(() => {
    if (isJustCreated) router.replace(`/tutor/profiles/${id}`);
  }, [isJustCreated, id, router]);

  async function save(body: TutorProfileUpsertRequest) {
    setSubmitError(null);
    try {
      await updateProfile.mutateAsync(body);
      showSuccess("Đã lưu hồ sơ.");
      return true;
    } catch (err) {
      setSubmitError(err);
      return false;
    }
  }

  async function handleSave(values: TutorProfileFormValues) {
    const body = toUpsertRequest(values);
    if (profile?.status === "Approved") {
      setPendingApprovedSave(body);
      return false;
    }
    return save(body);
  }

  async function confirmApprovedSave() {
    if (!pendingApprovedSave) return;
    await save(pendingApprovedSave);
    setPendingApprovedSave(null);
  }

  if (isPending) {
    return (
      <div className="py-8">
        <LoadingSpinner label="Đang tải hồ sơ..." />
      </div>
    );
  }

  if (!profile) {
    const apiError = toApiError(error);
    return (
      <div className="py-8">
        {apiError.status === 404 || !error ? (
          <EmptyState
            title="Không tìm thấy hồ sơ."
            message="Hồ sơ không tồn tại hoặc không thuộc tài khoản của bạn."
            actionText="Về danh sách hồ sơ"
            onAction={() => router.push("/tutor/profiles")}
          />
        ) : (
          <ErrorAlert
            title="Không tải được hồ sơ"
            message={apiError.message}
            onRetry={() => void refetch()}
          />
        )}
      </div>
    );
  }

  const isPendingReview = profile.status === "PendingReview";

  return (
    <div className="py-8 space-y-4 sm:space-y-6">
      <div className="space-y-2">
        <Link
          href="/tutor/profiles"
          className="inline-flex min-h-11 sm:min-h-0 items-center text-sm font-semibold text-primary hover:underline"
        >
          ← Hồ sơ gia sư
        </Link>
        <div className="flex flex-wrap items-center gap-3">
          <h1 className="text-2xl font-bold text-on-surface">Sửa hồ sơ</h1>
          <Badge tone={TUTOR_PROFILE_STATUS_TONES[profile.status]}>
            {TUTOR_PROFILE_STATUS_LABELS[profile.status]}
          </Badge>
        </div>
        {/* [0] Lý do từ chối */}
        {profile.status === "Rejected" && profile.rejectReason ? (
          <div className="rounded-2xl border border-error/30 bg-error-container/40 p-3 flex items-start gap-2 text-sm text-on-error-container">
            <span className="text-error shrink-0 mt-0.5">
              <Icons.Alert />
            </span>
            <p className="whitespace-pre-wrap break-words">
              <span className="font-semibold">Lý do từ chối: </span>
              {profile.rejectReason}
            </p>
          </div>
        ) : null}
      </div>

      {isError && !isFetching ? (
        <ErrorAlert
          title="Không làm mới được hồ sơ"
          message={toApiError(error).message}
          onRetry={() => void refetch()}
        />
      ) : null}

      {notice ? (
        <NoticeBanner message={notice.message} role={notice.role} onClose={clear} />
      ) : null}

      {isPendingReview ? (
        <div
          role="status"
          className="rounded-2xl border border-amber-200 bg-amber-100 p-4 text-sm font-semibold text-amber-800"
        >
          Hồ sơ đang chờ duyệt, chưa sửa được.
        </div>
      ) : null}

      {/* Khóa theo id và trạng thái để đổi trạng thái (Approved → PendingReview) thì reset, còn tải/gỡ minh chứng không làm mất chữ đang nhập */}
      <ProfileForm
        key={`${profile.id}:${profile.status}`}
        defaultValues={toFormValues(profile)}
        readOnly={isPendingReview}
        submitError={submitError}
        onSave={handleSave}
        onLeave={() => router.push("/tutor/profiles")}
      />

      <EvidenceSection profile={profile} onSuccess={showSuccess} />

      <ConfirmDialog
        isOpen={pendingApprovedSave !== null}
        onClose={() => setPendingApprovedSave(null)}
        onConfirm={confirmApprovedSave}
        isLoading={updateProfile.isPending}
        variant="warning"
        title="Lưu thay đổi hồ sơ đã duyệt?"
        confirmText="Lưu"
        message="Hồ sơ sẽ chuyển sang Chờ duyệt và tạm ẩn với phụ huynh cho tới khi Admin duyệt lại."
      />
    </div>
  );
}
