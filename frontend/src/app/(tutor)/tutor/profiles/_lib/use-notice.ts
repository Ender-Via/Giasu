import { useCallback, useEffect, useState } from "react";

export interface Notice {
  message: string;
  role: "status" | "alert";
}

// Dải báo kết quả ghi phía trên nội dung (ui-screens.md §4.2): thành công tự ẩn sau 6 giây,
// lỗi không tự ẩn. Dùng cùng NoticeBanner.
export function useNotice(initial: Notice | null = null) {
  const [notice, setNotice] = useState<Notice | null>(initial);

  useEffect(() => {
    if (!notice || notice.role !== "status") return;
    const timer = setTimeout(() => setNotice(null), 6000);
    return () => clearTimeout(timer);
  }, [notice]);

  const showSuccess = useCallback((message: string) => setNotice({ message, role: "status" }), []);
  const showError = useCallback((message: string) => setNotice({ message, role: "alert" }), []);
  const clear = useCallback(() => setNotice(null), []);

  return { notice, showSuccess, showError, clear };
}
