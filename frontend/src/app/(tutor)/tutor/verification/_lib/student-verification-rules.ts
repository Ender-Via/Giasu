// Quy tắc ô nhập của SCR-TUT-03 (FR-02), cùng câu thông báo với validator backend.

export interface VerificationFormValues {
  university: string;
  studentCode: string;
  files: FileList | null;
}

export const VERIFICATION_DEFAULT_VALUES: VerificationFormValues = {
  university: "",
  studentCode: "",
  files: null,
};

const STUDENT_CODE_PATTERN = /^[A-Za-z0-9]{3,20}$/;

export const UNIVERSITY_VALIDATE = {
  length: (value: string) => {
    const length = value.trim().length;
    return (length >= 2 && length <= 150) || "Tên trường từ 2 đến 150 ký tự";
  },
};

export const STUDENT_CODE_VALIDATE = {
  format: (value: string) =>
    STUDENT_CODE_PATTERN.test(value.trim()) ||
    "Mã số sinh viên từ 3 đến 20 ký tự, chỉ gồm chữ và số",
};
