"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { toApiError } from "@/lib/axios";
import { ProfileForm } from "../_components/ProfileForm";
import { useCreateTutorProfile } from "../_lib/tutor-profiles-api";
import {
  EMPTY_PROFILE_FORM,
  toUpsertRequest,
  type TutorProfileFormValues,
} from "../_lib/tutor-profile-rules";

// SCR-TUT-02 — Tạo hồ sơ (FR-03)
export default function NewTutorProfilePage() {
  const router = useRouter();
  const createProfile = useCreateTutorProfile();
  const [submitError, setSubmitError] = useState<unknown>(null);
  const [isLimitReached, setIsLimitReached] = useState(false);

  async function handleSave(values: TutorProfileFormValues) {
    setSubmitError(null);
    try {
      const created = await createProfile.mutateAsync(toUpsertRequest(values));
      if (created) {
        // Thay URL để nút Back không quay lại form trống; trang sửa hiện dải "Đã lưu hồ sơ nháp"
        router.replace(`/tutor/profiles/${created.id}?created=1`);
      }
      return true;
    } catch (err) {
      setSubmitError(err);
      // 409: đã đủ 5 hồ sơ (BR-23) → hiện nút về danh sách
      if (toApiError(err).status === 409) setIsLimitReached(true);
      return false;
    }
  }

  return (
    <div className="py-8 space-y-4 sm:space-y-6">
      <div className="space-y-1">
        <Link href="/tutor/profiles" className="text-sm font-semibold text-primary hover:underline">
          ← Hồ sơ gia sư
        </Link>
        <h1 className="text-2xl font-bold text-on-surface">Tạo hồ sơ</h1>
      </div>

      {isLimitReached ? (
        <Link
          href="/tutor/profiles"
          className="inline-flex min-h-11 items-center rounded-full border border-slate-300 px-4 py-2 text-sm font-semibold text-on-surface hover:bg-surface-container-low"
        >
          Về danh sách hồ sơ
        </Link>
      ) : null}

      <ProfileForm
        defaultValues={EMPTY_PROFILE_FORM}
        readOnly={false}
        submitError={submitError}
        onSave={handleSave}
        onLeave={() => router.push("/tutor/profiles")}
      />
    </div>
  );
}
