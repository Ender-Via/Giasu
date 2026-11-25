// Quy tắc ô nhập dùng chung cho SCR-AUTH-01 (đăng nhập) và SCR-AUTH-02 (đăng ký).
// Cùng giới hạn và câu thông báo với validator backend (BR-01, ui-screens.md §4.3).

export const EMAIL_MAX_LENGTH = 254;
const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

// Bỏ khoảng trắng hai đầu cho họ tên, email, số điện thoại; mật khẩu không dùng hàm này.
export function trimValue(value: unknown) {
  return typeof value === "string" ? value.trim() : value;
}

export const EMAIL_VALIDATE = {
  required: (value: string) => value.trim().length > 0 || "Vui lòng nhập email",
  maxLength: (value: string) =>
    value.trim().length <= EMAIL_MAX_LENGTH || "Email không được vượt quá 254 ký tự",
  format: (value: string) => EMAIL_PATTERN.test(value.trim()) || "Email không đúng định dạng",
};
