// Quy tắc ô nhập của SCR-AUTH-02, lặp đúng giới hạn và câu thông báo của validator backend (BR-01).
import type { SelfRegisterRole } from "@/types/auth";

export interface RegisterFormValues {
  // Chuỗi rỗng = chưa chọn vai trò (ui-screens.md §4.3: ô chọn bắt đầu rỗng)
  role: SelfRegisterRole | "";
  fullName: string;
  phone: string;
  email: string;
  password: string;
  confirmPassword: string;
  acceptTerms: boolean;
}

export const REGISTER_DEFAULT_VALUES: RegisterFormValues = {
  role: "",
  fullName: "",
  phone: "",
  email: "",
  password: "",
  confirmPassword: "",
  acceptTerms: false,
};

const PHONE_PATTERN = /^0\d{9}$/;
const HAS_LETTER = /\p{L}/u;
const HAS_DIGIT = /\d/;

export const ROLE_VALIDATE = {
  required: (value: RegisterFormValues["role"]) => value !== "" || "Vui lòng chọn vai trò",
};

export const FULL_NAME_VALIDATE = {
  length: (value: string) => {
    const length = value.trim().length;
    return (length >= 2 && length <= 100) || "Họ tên từ 2 đến 100 ký tự";
  },
};

export const PHONE_VALIDATE = {
  format: (value: string) =>
    PHONE_PATTERN.test(value.trim()) || "Số điện thoại gồm 10 chữ số, bắt đầu bằng 0",
};

// Mật khẩu không bỏ khoảng trắng (ui-screens.md §4.3)
export const PASSWORD_VALIDATE = {
  strength: (value: string) =>
    (value.length >= 8 &&
      value.length <= 128 &&
      HAS_LETTER.test(value) &&
      HAS_DIGIT.test(value)) ||
    "Mật khẩu từ 8 đến 128 ký tự, có cả chữ và số",
};

// "Nhập lại" chỉ kiểm phía client, không gửi lên
export const CONFIRM_PASSWORD_VALIDATE = {
  match: (value: string, values: RegisterFormValues) =>
    value === values.password || "Mật khẩu nhập lại không khớp",
};

export const ACCEPT_TERMS_VALIDATE = {
  accepted: (value: boolean) => value === true || "Bạn cần đồng ý quy chế để tiếp tục",
};
