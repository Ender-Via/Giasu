// Định dạng số liệu theo quy chuẩn tiếng Việt (frontend-conventions.md §6, ui-screens.md §4.4)

/**
 * Số tiền theo vi-VN, đơn vị đồng: 200000 → "200.000 ₫" (ui-screens.md §4.4).
 * Dùng cho học phí/buổi và kỳ học phí.
 */
export function formatMoney(amount: number): string {
  return new Intl.NumberFormat("vi-VN", {
    style: "currency",
    currency: "VND",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount);
}

/**
 * Điểm kiểm tra thang 0–10, tối đa 2 chữ số thập phân (BR-16, FR-21).
 * Ví dụ: 8.5 → "8,5", 10 → "10"
 */
export function formatScore(score: number | null | undefined): string {
  if (score === null || score === undefined) return "—";
  return score.toLocaleString("vi-VN", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  });
}

/**
 * Tỷ lệ phần trăm hoàn thành kế hoạch/tiến độ (FR-22, D35).
 * Ví dụ: 75.5 → "75,5%"
 */
export function formatPercent(percent: number | null | undefined): string {
  if (percent === null || percent === undefined) return "0%";
  return `${percent.toLocaleString("vi-VN", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 1,
  })}%`;
}
