import { useMutation } from "@tanstack/react-query";
import { apiClient } from "@/lib/axios";
import type { ApiResponse, RegisterRequest, RegisterResponseData } from "@/types/auth";

// POST /api/auth/register (FR-01). Không có query nào đọc tài khoản trước khi đăng nhập
// nên không cần làm mới cache sau khi ghi.
export function useRegister() {
  return useMutation({
    mutationFn: async (body: RegisterRequest) => {
      const res = await apiClient.post<ApiResponse<RegisterResponseData>>(
        "/api/auth/register",
        body
      );
      return res.data.data;
    },
  });
}
