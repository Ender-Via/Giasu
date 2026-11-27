"use client";

import { useState } from "react";
import { useForm, useWatch } from "react-hook-form";
import {
  ApiErrorAlert,
  Badge,
  Button,
  ConfirmDialog,
  ErrorAlert,
  Icons,
  Input,
  LoadingSpinner,
  NoticeBanner,
} from "@/components";
import { toApiError } from "@/lib/axios";
import { formatVietnamDateTime } from "@/lib/datetime";
import {
  VERIFICATION_STATUS_LABELS,
  VERIFICATION_STATUS_TONES,
  type TutorVerificationStatus,
} from "@/types/student-verification";
import { formatFileSize, validateEvidenceFiles } from "../profiles/_lib/tutor-profile-rules";
import { useNotice } from "../profiles/_lib/use-notice";
import {
  useCreateStudentVerification,
  useMyStudentVerification,
} from "./_lib/student-verifications-api";
import {
  STUDENT_CODE_VALIDATE,
  UNIVERSITY_VALIDATE,
  VERIFICATION_DEFAULT_VALUES,
  type VerificationFormValues,
} from "./_lib/student-verification-rules";

// Tệp minh chứng: đúng 1 tệp, JPG/PNG/PDF, ≤ 5 MB (FR-02, D16)
const FILE_VALIDATE = {
  file: (value: FileList | null) => {
    const files = value ? Array.from(value) : [];
    if (files.length !== 1) return "Vui lòng chọn một tệp minh chứng";
    const errors = validateEvidenceFiles(files, 1);
    return errors.length === 0 || errors[0];
  },
};

// SCR-TUT-03 — Xác thực sinh viên (FR-02)
export default function TutorVerificationPage() {
  const { data, isPending, isError, isFetching, error, refetch } = useMyStudentVerification();
  const createVerification = useCreateStudentVerification();
  const { notice, showSuccess, clear } = useNotice();
  const [confirmValues, setConfirmValues] = useState<VerificationFormValues | null>(null);
  const [submitError, setSubmitError] = useState<unknown>(null);

  const {
    register,
    handleSubmit,
    reset,
    control,
    formState: { errors },
  } = useForm<VerificationFormValues>({
    defaultValues: VERIFICATION_DEFAULT_VALUES,
    mode: "onTouched",
  });
  const chosenFiles = useWatch({ control, name: "files" });
  const chosenFile = chosenFiles && chosenFiles.length > 0 ? chosenFiles[0] : null;

  async function confirmSend() {
    if (!confirmValues?.files) return;
    setSubmitError(null);
    try {
      await createVerification.mutateAsync({
        university: confirmValues.university.trim(),
        studentCode: confirmValues.studentCode.trim(),
        file: confirmValues.files[0],
      });
      showSuccess("Đã gửi yêu cầu xác thực.");
      reset(VERIFICATION_DEFAULT_VALUES);
      setConfirmValues(null);
    } catch (err) {
      // 409 (đã có yêu cầu chờ): hiện message, danh sách tự làm mới trong onSettled
      setSubmitError(err);
      setConfirmValues(null);
    }
  }

  if (isPending) {
    return (
      <div className="py-8">
        <LoadingSpinner label="Đang tải trạng thái xác thực..." />
      </div>
    );
  }

  if (data === undefined) {
    return (
      <div className="py-8">
        <ErrorAlert
          title="Không tải được trạng thái xác thực"
          message={toApiError(error).message}
          onRetry={() => void refetch()}
        />
      </div>
    );
  }

  const status: TutorVerificationStatus = data?.status ?? "Unverified";
  const canSend = status === "Unverified" || status === "Rejected";

  return (
    <div className="py-8 space-y-4 sm:space-y-6">
      <div className="space-y-1">
        <h1 className="text-2xl font-bold text-on-surface">Xác thực sinh viên</h1>
        <p className="text-sm text-on-surface-variant">
          Gia sư đã xác thực có huy hiệu &quot;Đã xác thực&quot; trên hồ sơ, giúp phụ huynh tin
          tưởng hơn.
        </p>
      </div>

      {isError && !isFetching ? (
        <ErrorAlert
          title="Không làm mới được trạng thái xác thực"
          message={toApiError(error).message}
          onRetry={() => void refetch()}
        />
      ) : null}

      {notice ? (
        <NoticeBanner message={notice.message} role={notice.role} onClose={clear} />
      ) : null}

      {/* [1] Trạng thái hiện tại */}
      <section className="rounded-3xl border border-slate-200/90 bg-surface-container-lowest p-4 sm:p-6 shadow-sm space-y-3">
        <div className="flex flex-wrap items-center gap-2 text-sm">
          <span className="font-semibold text-on-surface">Trạng thái:</span>
          <Badge
            tone={VERIFICATION_STATUS_TONES[status]}
            icon={status === "Verified" ? <Icons.Check /> : undefined}
          >
            {VERIFICATION_STATUS_LABELS[status]}
          </Badge>
          {data ? (
            <span className="text-on-surface-variant">
              — gửi lúc {formatVietnamDateTime(data.createdAtUtc)}
            </span>
          ) : null}
        </div>
        {data && (status === "Pending" || status === "Verified") ? (
          <p className="text-sm text-on-surface-variant break-words">
            {data.university} · Mã số sinh viên: {data.studentCode}
          </p>
        ) : null}
        {status === "Rejected" && data?.rejectReason ? (
          <div className="rounded-2xl border border-error/30 bg-error-container/40 p-3 flex items-start gap-2 text-sm text-on-error-container">
            <span className="text-error shrink-0 mt-0.5">
              <Icons.Alert />
            </span>
            <p className="whitespace-pre-wrap break-words">
              <span className="font-semibold">Lý do: </span>
              {data.rejectReason}
            </p>
          </div>
        ) : null}
      </section>

      {/* [2] Form gửi, chỉ khi chưa gửi hoặc bị từ chối */}
      {status === "Pending" ? (
        <p className="rounded-2xl border border-amber-200 bg-amber-100 p-4 text-sm font-semibold text-amber-800">
          Yêu cầu đang chờ Admin duyệt. Bạn sẽ nhận thông báo khi có kết quả.
        </p>
      ) : null}
      {status === "Verified" ? (
        <div className="flex items-center gap-2 rounded-2xl border border-primary/20 bg-primary-fixed/30 p-4 text-sm font-semibold text-primary">
          <Icons.Check />
          Đã xác thực sinh viên
        </div>
      ) : null}

      {canSend ? (
        <form
          onSubmit={handleSubmit((values) => {
            setSubmitError(null);
            setConfirmValues(values);
          })}
          noValidate
          className="rounded-3xl border border-slate-200/90 bg-surface-container-lowest p-4 sm:p-6 shadow-sm space-y-4"
        >
          <h2 className="text-lg font-bold text-on-surface">Gửi yêu cầu xác thực</h2>

          {submitError ? <ApiErrorAlert error={submitError} /> : null}

          <Input
            id="university"
            label="Trường đang học"
            required
            placeholder="Trường Đại học Công nghệ Thông tin – ĐHQG-HCM"
            error={errors.university?.message}
            {...register("university", { validate: UNIVERSITY_VALIDATE })}
          />
          <Input
            id="studentCode"
            label="Mã số sinh viên"
            required
            placeholder="22520001"
            error={errors.studentCode?.message}
            {...register("studentCode", { validate: STUDENT_CODE_VALIDATE })}
          />

          <div className="space-y-1.5">
            <p id="verification-file-label" className="block text-sm font-semibold text-on-surface">
              Ảnh thẻ sinh viên hoặc giấy xác nhận
              <span className="ml-1 text-error">*</span>
            </p>
            {/* Ô chọn tệp gốc hiện chữ tiếng Anh của trình duyệt nên ẩn đi, dùng nhãn làm nút */}
            <div>
              <input
                id="verification-file"
                type="file"
                accept=".jpg,.jpeg,.png,.pdf,image/jpeg,image/png,application/pdf"
                aria-labelledby="verification-file-label"
                aria-invalid={errors.files ? "true" : "false"}
                aria-describedby="verification-file-help"
                className="peer sr-only"
                {...register("files", { validate: FILE_VALIDATE })}
              />
              <label
                htmlFor="verification-file"
                className="inline-flex min-h-11 sm:min-h-0 cursor-pointer items-center rounded-full border border-slate-300 bg-surface-container-lowest px-4 py-2 text-sm font-semibold text-on-surface hover:bg-surface-container-low peer-focus-visible:ring-2 peer-focus-visible:ring-primary"
              >
                Chọn tệp
              </label>
            </div>
            <p id="verification-file-help" className="text-xs text-on-surface-variant">
              {chosenFile
                ? `${chosenFile.name} · ${formatFileSize(chosenFile.size)}`
                : "JPG, PNG, PDF · tối đa 5 MB"}
            </p>
            {errors.files ? (
              <p className="text-xs text-error font-medium">{errors.files.message}</p>
            ) : null}
          </div>

          <div className="flex justify-end">
            <Button type="submit" variant="primary" className="min-h-11 sm:min-h-0">
              Gửi yêu cầu
            </Button>
          </div>
        </form>
      ) : null}

      <ConfirmDialog
        isOpen={confirmValues !== null}
        onClose={() => setConfirmValues(null)}
        onConfirm={confirmSend}
        isLoading={createVerification.isPending}
        title="Gửi yêu cầu xác thực?"
        confirmText="Gửi yêu cầu"
        message="Sau khi gửi bạn không sửa được cho tới khi có kết quả."
      />
    </div>
  );
}
