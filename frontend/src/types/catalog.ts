// Giá trị liệt kê dùng chung (business-rules.md §2.9, ui-screens.md §4.4).
// Lưu tiếng Anh, hiển thị tiếng Việt.

export type EducationLevel = "Primary" | "LowerSecondary" | "UpperSecondary" | "Other";
export type TeachingMode = "Offline" | "Online" | "Both";

export const EDUCATION_LEVEL_LABELS: Record<EducationLevel, string> = {
  Primary: "Tiểu học",
  LowerSecondary: "THCS",
  UpperSecondary: "THPT",
  Other: "Khác",
};

export const TEACHING_MODE_LABELS: Record<TeachingMode, string> = {
  Offline: "Tại nhà",
  Online: "Trực tuyến",
  Both: "Cả hai",
};

// GET /api/subjects (BR-24)
export interface SubjectResponse {
  id: number;
  name: string;
  code: string;
}
