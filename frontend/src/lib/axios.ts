import axios, { AxiosError } from "axios";
import type { ApiResponse } from "@/types/auth";
import { supabase } from "@/lib/supabase";

declare module "axios" {
  interface AxiosRequestConfig {
    skipAuthRedirect?: boolean;
  }
}

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:5015";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: { "Content-Type": "application/json" },
});

// Supabase quản lý phiên bền vững; Axios chỉ giữ access token hiện tại trong bộ nhớ.
let inMemoryToken: string | null = null;

export function setAuthToken(token: string | null): void {
  inMemoryToken = token;
}

// Request interceptor — đọc từ biến in-memory, không đọc localStorage.
// Với FormData, xóa Content-Type JSON mặc định để Axios/trình duyệt tự gắn boundary (ui-screens.md §4.5).
apiClient.interceptors.request.use((config) => {
  if (inMemoryToken) {
    config.headers.Authorization = `Bearer ${inMemoryToken}`;
  }
  if (config.data instanceof FormData) {
    config.headers.delete("Content-Type");
  }
  return config;
});

// Token đăng nhập do Supabase cấp, nên 401 từ API kết thúc phiên local. Luồng login
// đặt skipAuthRedirect để AuthContext tự dọn phiên và giữ message của /api/auth/me.
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401 && !error.config?.skipAuthRedirect) {
      setAuthToken(null);
      void supabase.auth.signOut({ scope: "local" });
      if (typeof window !== "undefined") {
        // Cố ý tải lại hẳn trang thay vì chuyển trang phía client: interceptor nằm
        // ngoài cây React nên không có router, và tải lại xóa sạch cache dữ liệu của
        // phiên cũ. Dùng replace để nút Back không quay lại trang cần đăng nhập.
        window.location.replace("/login");
      }
    }
    return Promise.reject(error);
  }
);

// --- Đọc lỗi thống nhất từ AxiosError — dùng ở MỌI nơi gọi apiClient ---
// Xử lý luôn cho mọi status (401 sai mật khẩu, 403, 429, 400 validate...),
// không cần if/else theo từng status code ở nơi gọi.
export class ApiError extends Error {
  errors: string[] | null;
  status: number | null;

  constructor(message: string, errors: string[] | null, status: number | null) {
    super(message);
    this.name = "ApiError";
    this.errors = errors;
    this.status = status;
  }
}

export function toApiError(error: unknown): ApiError {
  if (error instanceof ApiError) {
    return error;
  }
  if (axios.isAxiosError(error)) {
    const data = error.response?.data as ApiResponse<unknown> | undefined;
    const message = data?.message ?? "Đã xảy ra lỗi, vui lòng thử lại.";
    return new ApiError(message, data?.errors ?? null, error.response?.status ?? null);
  }
  if (typeof error === "string") {
    return new ApiError(error, null, null);
  }
  if (error instanceof Error) {
    return new ApiError(error.message, null, null);
  }
  return new ApiError("Đã xảy ra lỗi không xác định.", null, null);
}
