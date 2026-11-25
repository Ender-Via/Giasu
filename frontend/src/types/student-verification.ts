// Kiểu phản chiếu DTO xác thực sinh viên (FR-02). Gia sư và Admin dùng chung.
import type { BadgeTone } from "@/components";

// Trạng thái của một yêu cầu (business-rules.md §2.2)
export type StudentVerificationStatus = "Pending" | "Verified" | "Rejected";
// Trạng thái xác thực của gia sư; "Unverified" = chưa gửi lần nào
export type TutorVerificationStatus = "Unverified" | StudentVerificationStatus;

export const VERIFICATION_STATUS_LABELS: Record<TutorVerificationStatus, string> = {
  Unverified: "Chưa xác thực",
  Pending: "Chờ xác thực",
  Verified: "Đã xác thực",
  Rejected: "Bị từ chối",
};

export const VERIFICATION_STATUS_TONES: Record<TutorVerificationStatus, BadgeTone> = {
  Unverified: "neutral",
  Pending: "warning",
  Verified: "positive",
  Rejected: "danger",
};

// GET /api/student-verifications/mine trả yêu cầu gần nhất hoặc null
export interface StudentVerificationResponse {
  id: string;
  university: string;
  studentCode: string;
  status: StudentVerificationStatus;
  rejectReason: string | null;
  createdAtUtc: string;
  reviewedAtUtc: string | null;
}

// Body multipart của POST /api/student-verifications
export interface CreateStudentVerificationRequest {
  university: string;
  studentCode: string;
  file: File;
}
