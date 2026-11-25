import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/axios";
import type { ApiResponse } from "@/types/auth";
import type { SubjectResponse } from "@/types/catalog";

export const SUBJECTS_QUERY_KEY = ["subjects"] as const;

// Danh mục môn học (BR-24), mọi vai trò đọc được. Ít khi đổi nên giữ 30 phút mới tải lại.
export function useSubjects() {
  return useQuery({
    queryKey: SUBJECTS_QUERY_KEY,
    queryFn: async () => {
      const res = await apiClient.get<ApiResponse<SubjectResponse[]>>("/api/subjects");
      return res.data.data ?? [];
    },
    staleTime: 30 * 60 * 1000,
  });
}
