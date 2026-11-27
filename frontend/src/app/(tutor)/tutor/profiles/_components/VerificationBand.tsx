"use client";

import Link from "next/link";
import { Badge, Icons } from "@/components";
import {
  VERIFICATION_STATUS_LABELS,
  VERIFICATION_STATUS_TONES,
  type TutorVerificationStatus,
} from "@/types/student-verification";
import { useMyStudentVerification } from "../../verification/_lib/student-verifications-api";

// SCR-TUT-01 [2] — dải trạng thái xác thực sinh viên (D36). Lỗi tải chỉ ẩn dải này,
// không chặn danh sách hồ sơ.
export function VerificationBand() {
  const { data, isPending, isError } = useMyStudentVerification();

  if (isPending || isError) return null;

  const status: TutorVerificationStatus = data?.status ?? "Unverified";

  return (
    <div className="rounded-2xl border border-slate-200/90 bg-surface-container-lowest p-4 flex flex-wrap items-center gap-x-3 gap-y-2 text-sm">
      <span className="font-semibold text-on-surface">Xác thực sinh viên:</span>
      <Badge
        tone={VERIFICATION_STATUS_TONES[status]}
        icon={status === "Verified" ? <Icons.Check /> : undefined}
      >
        {VERIFICATION_STATUS_LABELS[status]}
      </Badge>
      {status === "Unverified" ? (
        <>
          <span className="text-on-surface-variant">Xác thực để có huy hiệu tin cậy.</span>
          <Link href="/tutor/verification" className="font-semibold text-primary hover:underline">
            Xác thực ngay →
          </Link>
        </>
      ) : null}
      {status === "Rejected" ? (
        <Link href="/tutor/verification" className="font-semibold text-primary hover:underline">
          Gửi lại →
        </Link>
      ) : null}
      {status === "Pending" ? (
        <span className="text-on-surface-variant">Đang chờ Admin duyệt.</span>
      ) : null}
    </div>
  );
}
