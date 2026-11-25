"use client";

import Link from "next/link";
import { useId } from "react";
import { Badge, Button, Icons } from "@/components";
import { formatVietnamDateTime } from "@/lib/datetime";
import { formatMoney } from "@/lib/format";
import { EDUCATION_LEVEL_LABELS, TEACHING_MODE_LABELS } from "@/types/catalog";
import {
  AVAILABILITY_LABELS,
  TUTOR_PROFILE_STATUS_LABELS,
  TUTOR_PROFILE_STATUS_TONES,
  type Availability,
  type TutorProfileResponse,
} from "@/types/tutor-profile";
import { canSubmit, getMissingSubmitRequirements } from "../_lib/tutor-profile-rules";

const AVAILABILITY_OPTIONS = Object.entries(AVAILABILITY_LABELS) as [Availability, string][];

interface ProfileCardProps {
  profile: TutorProfileResponse;
  // Giá trị đang gửi lên server; null khi không có thao tác nào
  pendingAvailability: Availability | null;
  isSettingDefault: boolean;
  onAvailabilityChange: (availability: Availability) => void;
  onSetDefault: () => void;
  onSubmit: () => void;
}

// SCR-TUT-01 [3] — một thẻ hồ sơ
export function ProfileCard({
  profile,
  pendingAvailability,
  isSettingDefault,
  onAvailabilityChange,
  onSetDefault,
  onSubmit,
}: ProfileCardProps) {
  const availabilityId = useId();
  const missing = getMissingSubmitRequirements(profile);
  const showSubmit = canSubmit(profile);
  const isRejected = profile.status === "Rejected";
  const isPendingReview = profile.status === "PendingReview";
  // Hồ sơ chỉ dạy Online không có phường/xã, chỉ còn tỉnh/thành
  const area = [profile.province, profile.teachingWards.join(", ")].filter(Boolean).join(" — ");

  return (
    <article className="rounded-2xl border border-slate-200/90 bg-surface-container-lowest p-4 shadow-sm space-y-3">
      <div className="flex flex-wrap items-center gap-2">
        {profile.isDefault ? (
          <Badge tone="positive" icon={<Icons.Check />}>
            Mặc định
          </Badge>
        ) : null}
        <Badge tone={TUTOR_PROFILE_STATUS_TONES[profile.status]}>
          {TUTOR_PROFILE_STATUS_LABELS[profile.status]}
        </Badge>
      </div>

      <div className="space-y-1">
        <h2 className="text-base font-bold text-on-surface break-words">{profile.title}</h2>
        <p className="text-sm text-on-surface-variant">
          {profile.subjects.map((subject) => subject.name).join(", ")} ·{" "}
          {EDUCATION_LEVEL_LABELS[profile.educationLevel]} ·{" "}
          {TEACHING_MODE_LABELS[profile.teachingMode]}
        </p>
        <p className="text-sm text-on-surface-variant break-words">{area}</p>
        <p className="text-sm text-on-surface-variant">
          {formatMoney(profile.expectedFeePerSession)}/buổi · {profile.evidenceCount} minh chứng ·
          Cập nhật {formatVietnamDateTime(profile.updatedAtUtc)}
        </p>
      </div>

      {isRejected && profile.rejectReason ? (
        <div className="rounded-2xl border border-error/30 bg-error-container/40 p-3 flex items-start gap-2 text-sm text-on-error-container">
          <span className="text-error shrink-0 mt-0.5">
            <Icons.Alert />
          </span>
          <p className="whitespace-pre-wrap break-words">
            <span className="font-semibold">Lý do: </span>
            {profile.rejectReason}
          </p>
        </div>
      ) : null}

      {/* Trạng thái nhận dạy (FR-36): đổi là ghi ngay, không hỏi lại */}
      <div className="space-y-1">
        <div className="flex flex-wrap items-center gap-2">
          <label htmlFor={availabilityId} className="text-sm font-semibold text-on-surface">
            Nhận dạy:
          </label>
          <select
            id={availabilityId}
            value={pendingAvailability ?? profile.availability}
            disabled={pendingAvailability !== null}
            onChange={(event) => onAvailabilityChange(event.target.value as Availability)}
            className="min-h-11 sm:min-h-0 rounded-2xl border border-slate-300 bg-surface-container-lowest px-3 py-1.5 text-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary disabled:bg-slate-100 disabled:cursor-not-allowed cursor-pointer"
          >
            {AVAILABILITY_OPTIONS.map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </div>
        {profile.status !== "Approved" ? (
          <p className="text-xs text-on-surface-variant">
            Chỉ hiển thị cho phụ huynh khi hồ sơ đã duyệt.
          </p>
        ) : null}
      </div>

      <div className="flex flex-wrap items-center gap-2 pt-1">
        {isPendingReview ? (
          <p className="text-sm text-on-surface-variant">Đang chờ duyệt, chưa sửa được.</p>
        ) : (
          <Link
            href={`/tutor/profiles/${profile.id}`}
            className="inline-flex min-h-11 sm:min-h-0 items-center rounded-full border border-slate-300 px-4 py-2 text-sm font-semibold text-on-surface hover:bg-surface-container-low focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
          >
            Sửa
          </Link>
        )}
        {!profile.isDefault ? (
          <Button
            variant="outline"
            className="min-h-11 sm:min-h-0"
            isLoading={isSettingDefault}
            onClick={onSetDefault}
          >
            Đặt làm mặc định
          </Button>
        ) : null}
        {showSubmit ? (
          <Button
            variant="primary"
            className="min-h-11 sm:min-h-0"
            disabled={missing.length > 0}
            onClick={onSubmit}
          >
            {isRejected ? "Gửi duyệt lại" : "Gửi duyệt"}
          </Button>
        ) : null}
      </div>
      {showSubmit && missing.length > 0 ? (
        <p className="text-xs font-medium text-amber-800">Cần bổ sung: {missing.join(", ")}.</p>
      ) : null}
    </article>
  );
}
