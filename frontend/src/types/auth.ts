export type Role = "Admin" | "Tutor" | "Parent";

export interface ApiResponse<T> {
  success: boolean;
  data: T | null;
  message: string | null;
  errors: string[] | null;
}

// Vai trò được tự đăng ký; Admin chỉ do seed tạo (BR-01, D05)
export type SelfRegisterRole = Extract<Role, "Tutor" | "Parent">;

// Body của POST /api/auth/register (FR-01, SCR-AUTH-02)
export interface RegisterRequest {
  role: SelfRegisterRole;
  fullName: string;
  phone: string;
  email: string;
  password: string;
  acceptTerms: boolean;
}

// Khớp CurrentUserResponse của backend (GET /api/auth/me và POST /api/auth/register — FR-01)
export interface CurrentUserResponse {
  userId: string;
  fullName: string;
  role: Role;
}
