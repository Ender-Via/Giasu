export type Role = "Admin" | "Tutor" | "Parent";

export interface ApiResponse<T> {
  success: boolean;
  data: T | null;
  message: string | null;
  errors: string[] | null;
}
