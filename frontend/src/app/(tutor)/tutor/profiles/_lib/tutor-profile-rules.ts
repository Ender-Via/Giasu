// Quy tắc ô nhập của SCR-TUT-02, cùng giới hạn và câu thông báo với validator backend (BR-04).
import { PROVINCES } from "@/lib/provinces";
import type { EducationLevel, TeachingMode } from "@/types/catalog";
import type { TutorProfileResponse, TutorProfileUpsertRequest } from "@/types/tutor-profile";

export const MAX_PROFILES = 5; // BR-23
export const MAX_SUBJECTS = 5;
export const MAX_WARDS = 5;
export const MAX_WARD_LENGTH = 100;
export const MAX_DESCRIPTION_LENGTH = 2000;
export const MIN_FEE = 50_000;
export const MAX_FEE = 2_000_000;
export const FEE_STEP = 1_000;

export interface TutorProfileFormValues {
  title: string;
  // Checkbox trả chuỗi; đổi sang số khi gửi
  subjectIds: string[];
  educationLevel: EducationLevel | "";
  teachingMode: TeachingMode | "";
  province: string;
  teachingWards: { value: string }[];
  // Giữ dạng chuỗi để ô trống không thành 0
  expectedFeePerSession: string;
  description: string;
}

export const EMPTY_PROFILE_FORM: TutorProfileFormValues = {
  title: "",
  subjectIds: [],
  educationLevel: "",
  teachingMode: "",
  province: "",
  teachingWards: [{ value: "" }],
  expectedFeePerSession: "",
  description: "",
};

export function parseFee(value: string): number | null {
  const digits = value.replace(/[.\s]/g, "");
  if (!/^\d+$/.test(digits)) return null;
  return Number(digits);
}

export const TITLE_VALIDATE = {
  length: (value: string) => {
    const length = value.trim().length;
    return (length >= 10 && length <= 150) || "Tiêu đề từ 10 đến 150 ký tự";
  },
};

export const SUBJECTS_VALIDATE = {
  count: (value: string[] | false) => {
    const count = Array.isArray(value) ? value.length : 0;
    return (count >= 1 && count <= MAX_SUBJECTS) || "Chọn từ 1 đến 5 môn";
  },
};

export const EDUCATION_LEVEL_VALIDATE = {
  required: (value: string) => value !== "" || "Vui lòng chọn cấp học",
};

export const TEACHING_MODE_VALIDATE = {
  required: (value: string) => value !== "" || "Vui lòng chọn hình thức dạy",
};

export const PROVINCE_VALIDATE = {
  required: (value: string) =>
    (PROVINCES as readonly string[]).includes(value) || "Vui lòng chọn tỉnh/thành",
};

export const WARD_VALIDATE = {
  length: (value: string) =>
    value.trim().length <= MAX_WARD_LENGTH || "Mỗi phường/xã không quá 100 ký tự",
};

export const FEE_VALIDATE = {
  range: (value: string) => {
    const fee = parseFee(value);
    return (
      (fee !== null && fee >= MIN_FEE && fee <= MAX_FEE && fee % FEE_STEP === 0) ||
      "Học phí từ 50.000 đến 2.000.000 đồng, làm tròn đến nghìn"
    );
  },
};

export const DESCRIPTION_VALIDATE = {
  length: (value: string) =>
    value.trim().length <= MAX_DESCRIPTION_LENGTH || "Giới thiệu không quá 2000 ký tự",
};

// Ô phường/xã đầu tiên: thêm điều kiện cần ít nhất một phường/xã, trừ khi chỉ dạy Online
export const FIRST_WARD_VALIDATE = {
  ...WARD_VALIDATE,
  required: (_value: string, values: TutorProfileFormValues) =>
    values.teachingMode === "Online" ||
    cleanWards(values.teachingWards).length > 0 ||
    "Nhập ít nhất một phường/xã",
};

// Phường/xã đã nhập, bỏ ô trống và trùng lặp như backend
export function cleanWards(wards: { value: string }[]): string[] {
  return Array.from(new Set(wards.map((ward) => ward.value.trim()).filter(Boolean)));
}

export function toUpsertRequest(values: TutorProfileFormValues): TutorProfileUpsertRequest {
  const teachingMode = values.teachingMode as TeachingMode;
  const description = values.description.trim();
  return {
    title: values.title.trim(),
    subjectIds: values.subjectIds.map(Number),
    educationLevel: values.educationLevel as EducationLevel,
    teachingMode,
    province: values.province,
    // Chỉ dạy Online thì không gửi phường/xã (BR-04)
    teachingWards: teachingMode === "Online" ? [] : cleanWards(values.teachingWards),
    expectedFeePerSession: parseFee(values.expectedFeePerSession) ?? 0,
    description: description === "" ? null : description,
  };
}

export function toFormValues(profile: TutorProfileResponse): TutorProfileFormValues {
  return {
    title: profile.title,
    subjectIds: profile.subjects.map((subject) => String(subject.id)),
    educationLevel: profile.educationLevel,
    teachingMode: profile.teachingMode,
    province: profile.province,
    teachingWards:
      profile.teachingWards.length > 0
        ? profile.teachingWards.map((value) => ({ value }))
        : [{ value: "" }],
    expectedFeePerSession: String(profile.expectedFeePerSession),
    description: profile.description ?? "",
  };
}

// Điều còn thiếu để gửi duyệt, tính phía client cho dòng "Cần bổ sung" (SCR-TUT-01 hành vi 4),
// khớp với missing_submission_requirements ở backend (BR-04).
// Các trường khác đã bị chặn khi lưu; backend vẫn là nơi quyết định cuối (400 kèm errors).
export function getMissingSubmitRequirements(profile: TutorProfileResponse): string[] {
  const missing: string[] = [];
  if (profile.subjects.length === 0) {
    missing.push("môn dạy");
  }
  if (profile.teachingMode !== "Online" && profile.teachingWards.length === 0) {
    missing.push("phường/xã");
  }
  if (!profile.description?.trim()) {
    missing.push("giới thiệu, kinh nghiệm");
  }
  if (profile.evidenceCount === 0) {
    missing.push("minh chứng");
  }
  return missing;
}

export function canSubmit(profile: TutorProfileResponse): boolean {
  return profile.status === "Draft" || profile.status === "Rejected";
}

// BR-26: thêm, gỡ minh chứng khi Draft hoặc Rejected
export function canEditEvidences(profile: TutorProfileResponse): boolean {
  return profile.status === "Draft" || profile.status === "Rejected";
}

// Kiểm tệp phía client trước khi gửi (ui-screens.md §4.5, D16)
const ALLOWED_TYPES = ["image/jpeg", "image/png", "application/pdf"];
const ALLOWED_EXTENSIONS = [".jpg", ".jpeg", ".png", ".pdf"];
export const MAX_FILE_BYTES = 5 * 1024 * 1024;
export const MAX_EVIDENCES = 5; // BR-03

export function validateEvidenceFiles(files: File[], remainingSlots: number): string[] {
  const errors: string[] = [];
  if (files.length > remainingSlots) {
    errors.push(
      remainingSlots === 0
        ? "Hồ sơ đã đủ 5 minh chứng."
        : `Chỉ còn ${remainingSlots} chỗ cho minh chứng, bạn đã chọn ${files.length} tệp.`
    );
  }
  for (const file of files) {
    const name = file.name.toLowerCase();
    const typeOk =
      ALLOWED_TYPES.includes(file.type) || ALLOWED_EXTENSIONS.some((ext) => name.endsWith(ext));
    if (!typeOk) {
      errors.push(`Tệp '${file.name}' không phải JPG, PNG hoặc PDF.`);
    } else if (file.size > MAX_FILE_BYTES) {
      errors.push(`Tệp '${file.name}' vượt quá 5 MB.`);
    }
  }
  return errors;
}

// 1258291 → "1,2 MB"; 819200 → "800 KB"
export function formatFileSize(bytes: number): string {
  if (bytes >= 1024 * 1024) {
    return `${(bytes / (1024 * 1024)).toLocaleString("vi-VN", { maximumFractionDigits: 1 })} MB`;
  }
  return `${Math.max(1, Math.round(bytes / 1024)).toLocaleString("vi-VN")} KB`;
}
