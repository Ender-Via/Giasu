import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/axios";
import type { ApiResponse } from "@/types/auth";
import type {
  CreateStudentVerificationRequest,
  StudentVerificationResponse,
} from "@/types/student-verification";

export const STUDENT_VERIFICATIONS_QUERY_KEY = ["student-verifications"] as const;
export const MY_STUDENT_VERIFICATION_QUERY_KEY = ["student-verifications", "mine"] as const;

// Yêu cầu xác thực gần nhất của gia sư, null khi chưa gửi lần nào (FR-02).
// Dùng ở SCR-TUT-03 và dải xác thực của SCR-TUT-01.
export function useMyStudentVerification() {
  return useQuery<StudentVerificationResponse | null>({
    queryKey: MY_STUDENT_VERIFICATION_QUERY_KEY,
    queryFn: async () => {
      const res = await apiClient.get<ApiResponse<StudentVerificationResponse | null>>(
        "/api/student-verifications/mine"
      );
      return res.data.data ?? null;
    },
  });
}

// Gửi yêu cầu xác thực (FR-02): multipart university, studentCode, file. Ghi đè Content-Type như
// useUploadEvidences để axios không đổi FormData thành JSON. Ghi xong làm mới cả tutor-profiles vì
// dải xác thực ở SCR-TUT-01 đọc trạng thái này (frontend-conventions.md §3.2).
export function useCreateStudentVerification() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: CreateStudentVerificationRequest) => {
      const formData = new FormData();
      formData.append("university", body.university);
      formData.append("studentCode", body.studentCode);
      formData.append("file", body.file);
      const res = await apiClient.post<ApiResponse<StudentVerificationResponse>>(
        "/api/student-verifications",
        formData,
        { headers: { "Content-Type": "multipart/form-data" } }
      );
      return res.data.data;
    },
    onSettled: () => {
      void queryClient.invalidateQueries({ queryKey: STUDENT_VERIFICATIONS_QUERY_KEY });
      void queryClient.invalidateQueries({ queryKey: ["tutor-profiles"] });
    },
  });
}
