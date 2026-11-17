export type Role = "Admin" | "Tutor" | "Parent";

export interface LoginResponseData {
  token: string;
  expiresAtUtc: string;
  userId: string;
  fullName: string;
  role: Role;
}

export interface ApiResponse<T> {
  success: boolean;
  data: T | null;
  message: string | null;
  errors: string[] | null;
}