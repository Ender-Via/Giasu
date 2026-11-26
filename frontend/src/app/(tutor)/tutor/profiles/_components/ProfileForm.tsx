"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useFieldArray, useForm, useWatch } from "react-hook-form";
import {
  ApiErrorAlert,
  Button,
  Checkbox,
  ConfirmDialog,
  ErrorAlert,
  Icons,
  Input,
  LoadingSpinner,
  Select,
  Textarea,
} from "@/components";
import { toApiError } from "@/lib/axios";
import { formatMoney } from "@/lib/format";
import { PROVINCES } from "@/lib/provinces";
import {
  EDUCATION_LEVEL_LABELS,
  TEACHING_MODE_LABELS,
  type EducationLevel,
  type TeachingMode,
} from "@/types/catalog";
import { useSubjects } from "../_lib/subjects-api";
import {
  DESCRIPTION_VALIDATE,
  EDUCATION_LEVEL_VALIDATE,
  FEE_VALIDATE,
  MAX_DESCRIPTION_LENGTH,
  MAX_WARD_LENGTH,
  MAX_WARDS,
  PROVINCE_VALIDATE,
  SUBJECTS_VALIDATE,
  TEACHING_MODE_VALIDATE,
  TITLE_VALIDATE,
  WARD_VALIDATE,
  FIRST_WARD_VALIDATE,
  parseFee,
  type TutorProfileFormValues,
} from "../_lib/tutor-profile-rules";

const EDUCATION_LEVEL_OPTIONS = (
  Object.entries(EDUCATION_LEVEL_LABELS) as [EducationLevel, string][]
).map(([value, label]) => ({ value, label }));
const TEACHING_MODE_OPTIONS = (Object.entries(TEACHING_MODE_LABELS) as [TeachingMode, string][]).map(
  ([value, label]) => ({ value, label })
);
const PROVINCE_OPTIONS = PROVINCES.map((province) => ({ value: province, label: province }));

const UNSAVED_MESSAGE = "Bạn có thay đổi chưa lưu. Rời trang?";

interface ProfileFormProps {
  defaultValues: TutorProfileFormValues;
  readOnly: boolean;
  submitError: unknown;
  // Trả về true khi lưu thành công để form coi giá trị hiện tại là bản đã lưu
  onSave: (values: TutorProfileFormValues) => Promise<boolean>;
  onLeave: () => void;
}

// SCR-TUT-02 [A] — form nội dung hồ sơ, dùng chung cho tạo và sửa
export function ProfileForm({
  defaultValues,
  readOnly,
  submitError,
  onSave,
  onLeave,
}: ProfileFormProps) {
  const router = useRouter();
  const subjectsQuery = useSubjects();
  const [isLeaveConfirmOpen, setIsLeaveConfirmOpen] = useState(false);
  const [pendingHref, setPendingHref] = useState<string | null>(null);
  const {
    register,
    control,
    handleSubmit,
    reset,
    getValues,
    formState: { errors, isDirty, isSubmitting },
  } = useForm<TutorProfileFormValues>({ defaultValues, mode: "onTouched" });
  const { fields, append, remove } = useFieldArray({ control, name: "teachingWards" });

  const teachingMode = useWatch({ control, name: "teachingMode" });
  const feeInput = useWatch({ control, name: "expectedFeePerSession" });
  const description = useWatch({ control, name: "description" });
  const isOnline = teachingMode === "Online";
  const parsedFee = parseFee(feeInput);

  // Hỏi trước khi đóng tab, tải lại hoặc bấm liên kết rời trang (← Hồ sơ gia sư, menu) khi có
  // thay đổi chưa lưu (ui-screens.md §4.3, SCR-TUT-02 hành vi 6)
  useEffect(() => {
    if (!isDirty || readOnly) return;
    const handleBeforeUnload = (event: BeforeUnloadEvent) => {
      event.preventDefault();
    };
    const handleClickCapture = (event: MouseEvent) => {
      if (
        event.defaultPrevented ||
        event.button !== 0 ||
        event.metaKey ||
        event.ctrlKey ||
        event.shiftKey ||
        event.altKey
      ) {
        return;
      }
      const anchor = (event.target as Element | null)?.closest("a[href]") as
        | HTMLAnchorElement
        | null;
      if (!anchor || (anchor.target && anchor.target !== "_self") || anchor.hasAttribute("download")) {
        return;
      }
      const targetUrl = new URL(anchor.href, window.location.href);
      if (targetUrl.origin !== window.location.origin) return;
      if (targetUrl.pathname + targetUrl.search === window.location.pathname + window.location.search) {
        return;
      }
      event.preventDefault();
      event.stopPropagation();
      setPendingHref(targetUrl.pathname + targetUrl.search + targetUrl.hash);
      setIsLeaveConfirmOpen(true);
    };
    window.addEventListener("beforeunload", handleBeforeUnload);
    window.addEventListener("click", handleClickCapture, true);
    return () => {
      window.removeEventListener("beforeunload", handleBeforeUnload);
      window.removeEventListener("click", handleClickCapture, true);
    };
  }, [isDirty, readOnly]);

  async function onSubmit(values: TutorProfileFormValues) {
    const saved = await onSave(values);
    if (saved) reset(getValues());
  }

  function handleLeave() {
    if (isDirty && !readOnly) {
      setPendingHref(null);
      setIsLeaveConfirmOpen(true);
    } else {
      onLeave();
    }
  }

  return (
    <form
      onSubmit={handleSubmit(onSubmit)}
      noValidate
      className="rounded-3xl border border-slate-200/90 bg-surface-container-lowest p-4 sm:p-6 shadow-sm space-y-4"
    >
      <h2 className="text-lg font-bold text-on-surface">Thông tin hồ sơ</h2>

      {submitError ? <ApiErrorAlert error={submitError} /> : null}

      <fieldset disabled={readOnly} className="space-y-4 min-w-0">
        {/* [1] Tiêu đề */}
        <Input
          id="title"
          label="Tiêu đề"
          required
          placeholder="Toán THPT & luyện thi đại học"
          error={errors.title?.message}
          {...register("title", { validate: TITLE_VALIDATE })}
        />

        {/* [2] Môn dạy, 1–5 môn từ danh mục */}
        <div className="space-y-1.5">
          <p id="subjects-label" className="text-sm font-semibold text-on-surface">
            Môn dạy (1–5)<span className="ml-1 text-error">*</span>
          </p>
          {subjectsQuery.isPending ? (
            <LoadingSpinner label="Đang tải danh mục môn..." />
          ) : subjectsQuery.isError ? (
            <ErrorAlert
              title="Không tải được danh mục môn"
              message={toApiError(subjectsQuery.error).message}
              onRetry={() => void subjectsQuery.refetch()}
            />
          ) : (
            <div
              role="group"
              aria-labelledby="subjects-label"
              className="grid grid-cols-2 gap-2 sm:grid-cols-3"
            >
              {subjectsQuery.data.map((subject) => (
                <Checkbox
                  key={subject.id}
                  value={String(subject.id)}
                  label={subject.name}
                  {...register("subjectIds", { validate: SUBJECTS_VALIDATE })}
                />
              ))}
            </div>
          )}
          {errors.subjectIds ? (
            <p className="text-xs text-error font-medium">{errors.subjectIds.message}</p>
          ) : null}
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {/* [3] Cấp học */}
          <Select
            id="educationLevel"
            label="Cấp học"
            required
            placeholder="Chọn cấp học"
            options={EDUCATION_LEVEL_OPTIONS}
            error={errors.educationLevel?.message}
            {...register("educationLevel", { validate: EDUCATION_LEVEL_VALIDATE })}
          />
          {/* [4] Hình thức dạy */}
          <Select
            id="teachingMode"
            label="Hình thức dạy"
            required
            placeholder="Chọn hình thức"
            options={TEACHING_MODE_OPTIONS}
            error={errors.teachingMode?.message}
            {...register("teachingMode", { validate: TEACHING_MODE_VALIDATE })}
          />
        </div>

        {/* [5] Tỉnh/thành (D37) */}
        <Select
          id="province"
          label="Tỉnh/thành"
          required
          placeholder="Chọn tỉnh/thành"
          options={PROVINCE_OPTIONS}
          error={errors.province?.message}
          {...register("province", { validate: PROVINCE_VALIDATE })}
        />

        {/* [6] Phường/xã 1–5 ô; ẩn khi chỉ dạy Online */}
        {!isOnline ? (
          <div className="space-y-1.5">
            <p className="text-sm font-semibold text-on-surface">
              Phường/xã (1–5)<span className="ml-1 text-error">*</span>
            </p>
            <div className="space-y-2">
              {fields.map((field, index) => (
                <div key={field.id} className="flex items-start gap-2">
                  <div className="flex-1 min-w-0">
                    <Input
                      aria-label={`Phường/xã ${index + 1}`}
                      placeholder="Phường Bến Thành"
                      maxLength={MAX_WARD_LENGTH}
                      error={errors.teachingWards?.[index]?.value?.message}
                      {...register(`teachingWards.${index}.value` as const, {
                        // Ô đầu tiên mang thêm lỗi "cần ít nhất một phường/xã"
                        validate: index === 0 ? FIRST_WARD_VALIDATE : WARD_VALIDATE,
                      })}
                    />
                  </div>
                  {fields.length > 1 ? (
                    <button
                      type="button"
                      onClick={() => remove(index)}
                      aria-label={`Bỏ phường/xã ${index + 1}`}
                      className="mt-1 flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-on-surface-variant hover:bg-surface-container-low hover:text-on-surface focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary cursor-pointer"
                    >
                      <Icons.Close />
                    </button>
                  ) : null}
                </div>
              ))}
            </div>
            {fields.length < MAX_WARDS ? (
              <Button variant="ghost" size="sm" onClick={() => append({ value: "" })}>
                + Thêm phường/xã
              </Button>
            ) : null}
          </div>
        ) : null}

        {/* [7] Học phí mong muốn */}
        <Input
          id="expectedFeePerSession"
          label="Học phí mong muốn mỗi buổi (đồng)"
          required
          inputMode="numeric"
          placeholder="200000"
          error={errors.expectedFeePerSession?.message}
          helperText={parsedFee !== null ? `${formatMoney(parsedFee)}/buổi` : undefined}
          {...register("expectedFeePerSession", { validate: FEE_VALIDATE })}
        />

        {/* [8] Giới thiệu, kinh nghiệm */}
        <Textarea
          id="description"
          label="Giới thiệu, kinh nghiệm"
          rows={5}
          showCount
          maxLength={MAX_DESCRIPTION_LENGTH}
          helperText="Không bắt buộc khi lưu nháp, nhưng cần có trước khi gửi duyệt."
          currentValue={description}
          error={errors.description?.message}
          {...register("description", { validate: DESCRIPTION_VALIDATE })}
        />
      </fieldset>

      {/* [9] Nút */}
      <div className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
        <Button variant="outline" className="min-h-11 sm:min-h-0" onClick={handleLeave}>
          {readOnly ? "Quay lại" : "Hủy"}
        </Button>
        {!readOnly ? (
          <Button
            type="submit"
            variant="primary"
            className="min-h-11 sm:min-h-0"
            isLoading={isSubmitting}
          >
            Lưu
          </Button>
        ) : null}
      </div>

      <ConfirmDialog
        isOpen={isLeaveConfirmOpen}
        onClose={() => {
          setIsLeaveConfirmOpen(false);
          setPendingHref(null);
        }}
        onConfirm={() => {
          const target = pendingHref;
          setIsLeaveConfirmOpen(false);
          setPendingHref(null);
          if (target) {
            router.push(target);
          } else {
            onLeave();
          }
        }}
        variant="warning"
        title="Rời trang?"
        message={UNSAVED_MESSAGE}
        confirmText="Rời trang"
        cancelText="Ở lại"
      />
    </form>
  );
}
