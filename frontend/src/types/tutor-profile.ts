// Kiểu phản chiếu DTO hồ sơ gia sư của backend (FR-03, FR-04, FR-36).
import type { BadgeTone } from "@/components";
import type { EducationLevel, SubjectResponse, TeachingMode } from "./catalog";

export type TutorProfileStatus = "Draft" | "PendingReview" | "Approved" | "Rejected";
export type Availability = "Accepting" | "Full" | "Paused";

export const TUTOR_PROFILE_STATUS_LABELS: Record<TutorProfileStatus, string> = {
  Draft: "Nháp",
  PendingReview: "Chờ duyệt",
  Approved: "Đã duyệt",
  Rejected: "Bị từ chối",
};

// Tông nhãn theo design-system.md §3.2
export const TUTOR_PROFILE_STATUS_TONES: Record<TutorProfileStatus, BadgeTone> = {
  Draft: "neutral",
  PendingReview: "warning",
  Approved: "positive",
  Rejected: "danger",
};

export const AVAILABILITY_LABELS: Record<Availability, string> = {
  Accepting: "Đang nhận thêm học sinh",
  Full: "Đã đủ lịch",
  Paused: "Tạm ngừng",
};

export interface TutorProfileEvidenceResponse {
  id: string;
  fileName: string;
  contentType: string;
  sizeBytes: number;
  uploadedAtUtc: string;
  // URL ký 60 phút (D16); null khi backend chưa cấp được
  url: string | null;
}

export interface TutorProfileResponse {
  id: string;
  title: string;
  subjects: SubjectResponse[];
  educationLevel: EducationLevel;
  teachingMode: TeachingMode;
  province: string;
  teachingWards: string[];
  expectedFeePerSession: number;
  description: string | null;
  status: TutorProfileStatus;
  availability: Availability;
  isDefault: boolean;
  rejectReason: string | null;
  evidenceCount: number;
  submittedAtUtc: string | null;
  createdAtUtc: string;
  updatedAtUtc: string;
}

export interface TutorProfileDetailResponse extends TutorProfileResponse {
  evidences: TutorProfileEvidenceResponse[];
}

// Body của POST /api/tutor-profiles và PUT /api/tutor-profiles/{id}
export interface TutorProfileUpsertRequest {
  title: string;
  subjectIds: number[];
  educationLevel: EducationLevel;
  teachingMode: TeachingMode;
  province: string;
  teachingWards: string[];
  expectedFeePerSession: number;
  description: string | null;
}
