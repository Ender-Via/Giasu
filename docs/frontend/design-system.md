# Design system — Gia Sư Kết Nối

## 0. Về tài liệu này

Giao diện dùng chung của frontend: màu, chữ, khoảng cách, component dùng chung, quy tắc
responsive và truy cập. Bộ component và token màu được chuẩn hóa cho dự án Gia Sư theo nhận diện prototype EJS,
mô tả đúng `src/app/globals.css`, `src/app/layout.tsx`, `src/components/` hiện có.
Chỗ còn ghi "mẫu" là khuôn nên theo khi làm màn hình đầu tiên của loại đó.

Ba tài liệu frontend chia việc như sau:

| Tài liệu | Trả lời câu hỏi |
| :---- | :---- |
| `frontend/ui-screens.md` | Màn hình hiện gì, gọi API nào, bấm nút thì làm gì |
| File này | Hiện bằng component nào, màu gì, cỡ nào, trên điện thoại ra sao |
| `frontend/frontend-conventions.md` | Viết code thế nào: thư mục, tên, gọi API, form, danh sách cấm |
| `frontend/frontend-architecture.md` | Frontend được dựng thế nào: công nghệ, routing, state, xác thực, cách chạy |

Khi lệch nhau: FR, BR, D đúng trước hết; về hành vi thì `ui-screens.md` đúng, về hình thức thì
file này đúng. Dự án không có Figma; bố cục từng màn hình là wireframe dạng chữ trong
`ui-screens.md`.

Sửa `app/layout.tsx` hay `app/globals.css` (gồm token màu) phải được Lead đồng ý. Component trong
`src/components/` do người phụ trách bộ component dùng chung làm hoặc duyệt (`onboarding-guide.md`
§8.2); người khác cần thêm hay sửa thì báo trước.

---

## 1. Nguyên tắc

1. **Dùng component có sẵn trước.** Dự án không dùng thư viện UI nào, chỉ Tailwind 4 và component
   tự viết trong `src/components/`. Không cài thư viện UI, icon hay tiện ích ghép class (D03).
   Thiếu component mà từ hai vai trò trở lên cần thì thêm vào `src/components/`; chỉ một màn hình
   dùng thì đặt trong `_components/` của màn hình đó.
2. **Màu lấy từ token (§3.1) hoặc bảng tông (§3.2).** Không gõ mã màu hex, không tự chọn màu
   Tailwind ngoài hai bảng này. Riêng xám `slate` được dùng cho viền và nền trung tính như các
   component đang làm.
3. **Không ghi đè màu, padding hay bo góc của component dùng chung bằng `className`.** Khi hai lớp
   Tailwind cùng đặt một thuộc tính, lớp nào thắng phụ thuộc thứ tự trong file CSS sinh ra, không
   phụ thuộc thứ tự trong `className`. Ví dụ truyền `bg-amber-50` vào `Button variant="outline"`
   thì nền vẫn trắng vì `bg-surface-container-lowest` của variant thắng. Cần kiểu mới thì thêm
   variant vào component. `className` chỉ dùng cho bố cục: `w-full`, `flex-1`, `shrink-0`,
   `min-h-11`, margin, ẩn hiện theo breakpoint.
4. **Desktop trước, nhưng dùng được ở 375px.** Riêng các màn gia sư và phụ huynh mở hằng tuần
   trên điện thoại — tìm tin, ứng tuyển, ghi nhận và xác nhận buổi học, thông báo — thao tác chính
   phải bấm được bằng một ngón tay (`ui-screens.md` §4.6).
5. **Chữ giao diện là tiếng Việt**, dùng đúng thuật ngữ ở `frontend-conventions.md` §6.

---

## 2. Chữ

Font duy nhất là **Be Vietnam Pro**, nạp bằng `next/font/google` trong `app/layout.tsx` (D03),
subset `vietnamese` và `latin`, gắn vào `--font-sans`. Chỉ nạp bốn độ đậm 400, 500, 600, 700, nên
chỉ dùng `font-normal`, `font-medium`, `font-semibold`, `font-bold`; `font-light` hay
`font-extrabold` sẽ bị trình duyệt giả lập, nét xấu. Thẻ `<html>` có `lang="vi"`.

| Dùng cho | Lớp | Có sẵn ở |
| :---- | :---- | :---- |
| Tiêu đề trang, mỗi trang đúng một `<h1>` | `text-2xl font-bold text-on-surface` | SCR-TUT-01 |
| Mô tả dưới tiêu đề | `text-sm text-on-surface-variant` | SCR-TUT-01 |
| Tiêu đề hộp thoại | `text-lg font-bold text-on-surface` | `ConfirmDialog` |
| Tiêu đề khối, trạng thái rỗng | `text-base font-bold text-on-surface` | `EmptyState` |
| Nhãn ô nhập | `text-sm font-semibold text-on-surface` | `Form` |
| Nội dung, ô nhập, ô bảng | `text-sm text-on-surface` | `Form`, `Table` |
| Chữ phụ, nhãn trạng thái, lỗi dưới ô | `text-xs` | `Form` |
| Số liệu lớn trên thẻ thống kê | `text-2xl font-bold` | |

---

## 3. Màu

### 3.1 Token

Khai báo trong `@theme` của `app/globals.css`, dùng như màu Tailwind: `bg-primary`,
`text-on-surface`, `border-outline`, `bg-primary-fixed/40`...

| Token | Giá trị | Dùng cho |
| :---- | :---- | :---- |
| `primary` | `#00288e` | Nút chính, liên kết, viền khi focus |
| `on-primary` | `#ffffff` | Chữ trên nền `primary` hoặc `primary-container` |
| `primary-container` | `#1e40af` | Mục menu đang mở, ô chữ cái đầu của người dùng (`DashboardLayout`) |
| `primary-fixed` | `#dde1ff` | Nền nhạt của tông chính / tích cực, thường kèm độ trong `/30`–`/70` |
| `on-primary-fixed` | `#001453` | Chữ trên nền `primary-fixed` |
| `secondary` | `#4b41e1` | Tông thông tin, nhãn phụ (Indigo) |
| `secondary-fixed` | `#e2dfff` | Nền nhạt tông secondary |
| `on-secondary-fixed` | `#0f0069` | Chữ trên nền `secondary-fixed` |
| `surface` | `#faf8ff` | Nền trang |
| `surface-container-low` | `#f2f3ff` | Nền khối phụ, đầu bảng, hover |
| `surface-container` | `#eaedff` | Nền khối |
| `surface-container-lowest` | `#ffffff` | Nền thẻ, ô nhập, hộp thoại |
| `on-surface` | `#131b2e` | Chữ chính |
| `on-surface-variant` | `#444653` | Chữ phụ |
| `outline` | `#757684` | Màu nhạt nhất còn được dùng cho chữ cần đọc; placeholder dùng `outline/70` |
| `error` | `#ba1a1a` | Lỗi, tông nguy hiểm, viền ô nhập sai |
| `error-container` | `#ffdad6` | Nền của lỗi và tông nguy hiểm |
| `on-error-container` | `#93000a` | Chữ trên nền `error-container` |

Chưa có token cho tông cảnh báo; tạm dùng `amber` của Tailwind như §3.2. Thêm token mới phải sửa
`globals.css`, cần GitHub owner đồng ý.

Viền và nền trung tính dùng `slate` như component đang có: viền khối `border-slate-200/90`, viền ô
nhập `border-slate-300`, nền ô bị khóa `bg-slate-100`.

### 3.2 Tông trạng thái

Mọi nhãn trạng thái, dù ở màn hình nào, chọn một trong năm tông dưới đây theo ý nghĩa của giá trị,
không theo sở thích của từng màn hình.

| Tông | Ý nghĩa | Nền và chữ | Chấm |
| :---- | :---- | :---- | :---- |
| Tích cực | Việc đã xong, đang ổn | `bg-primary-fixed/40 text-primary` | `bg-primary` |
| Cảnh báo | Cần để ý nhưng không phải lỗi | `bg-amber-100 text-amber-800` | `bg-amber-600` |
| Nguy hiểm | Sai, vi phạm, sự việc xấu | `bg-error-container text-on-error-container` | `bg-error` |
| Trung tính | Chưa có, chưa làm, đã tắt | `bg-slate-100 text-outline` | `bg-outline` |
| Thông tin | Phân loại, không mang đánh giá | `bg-surface-container-low text-secondary` | không có |

Gán tông cho các giá trị liệt kê ở `ui-screens.md` §4.4 và `business/business-rules.md` §2:

| Giá trị | Tông |
| :---- | :---- |
| Hồ sơ `Approved`, tin `Recruiting`, xác thực `Verified`, buổi học `Completed`, học phí `Paid`, phiếu `Hired` | Tích cực |
| Hồ sơ/tin `PendingReview`, xác thực `Pending`, buổi học `PendingConfirm`, học phí `Unpaid`, phiếu `TrialInvited`, nhận dạy `Full` | Cảnh báo |
| Hồ sơ/tin/xác thực `Rejected`, học phí `Overdue`, buổi học `Disputed`, phiếu `Rejected` / `NotHired` | Nguy hiểm |
| Hồ sơ `Draft`, xác thực `Unverified`, phiếu `Withdrawn`, tin `Closed`, buổi học `Cancelled`, nhận dạy `Paused` | Trung tính |
| Nhận dạy `Accepting`, phiếu `Pending` / `Viewed`, tin `Hired`, vai trò, cấp học, môn học | Thông tin |
| Hồ sơ mặc định (★ Mặc định), huy hiệu "Đã xác thực" | Tích cực, kèm `Icons.Check` |

Nút bấm không mang tông trạng thái. Ví dụ nút "Duyệt" dùng `primary`, nút "Từ chối"
dùng `outline`; muốn nút có màu riêng thì thêm variant vào `Button` (§1 mục 3).

---

## 4. Khoảng cách, bo góc, bóng

| Thành phần | Lớp | Ghi chú |
| :---- | :---- | :---- |
| Lề ngang của nội dung | `px-6 lg:px-8` | Đã có trong `<main>` của `DashboardLayout`; màn hình không thêm lề ngang |
| Gốc của một trang | `py-8 space-y-6` | Màn hình nhiều thẻ trên điện thoại được thu còn `space-y-4 sm:space-y-6` |
| Khối, thẻ, bộ lọc | `rounded-3xl border border-slate-200/90 bg-surface-container-lowest p-4 shadow-sm` | Thẻ lặp dày trong danh sách (mỗi hồ sơ, mỗi thông báo một thẻ) được dùng `rounded-2xl p-3` |
| Dải thông báo | `rounded-2xl border p-4` | Màu theo tông; hành vi ở `ui-screens.md` §4.2 |
| Ô nhập | `rounded-2xl` | Có sẵn trong `Form` |
| Nút, nhãn trạng thái | `rounded-full` | Có sẵn trong `Button` |
| Hộp thoại | `rounded-3xl p-6 shadow-2xl` | Có sẵn trong `Modal` |
| Khoảng cách trong form, bộ lọc | `gap-3` | Nhãn và ô cách nhau `space-y-1.5` (có sẵn trong `Form`) |
| Nút đứng cạnh nhau | `gap-2` trở lên | Trên điện thoại không sát hơn 8px |

Bóng chỉ dùng `shadow-xs`, `shadow-sm` cho khối và `shadow-2xl` cho hộp thoại; không dùng bóng có
màu.

---

## 5. Component dùng chung

Tất cả xuất qua `src/components/index.ts`: `import { Button, Input, Table } from "@/components"`.

| Component | Dùng khi | Props chính | Lưu ý |
| :---- | :---- | :---- | :---- |
| `Button` | Mọi nút | `variant`: `primary` (hành động chính, mỗi khu vực một nút), `secondary`, `outline` (hành động phụ), `danger` (xóa, vô hiệu hóa), `ghost` (hành động nhẹ như "Xóa bộ lọc"); `size`: `sm`, `md` (mặc định), `lg`; `isLoading` (hiện vòng quay và tự khóa); `icon` | Mặc định `type="button"`; nút gửi form phải ghi `type="submit"`. `sm` cao khoảng 30px, `md` khoảng 36px: nút thao tác chính trên điện thoại thêm `min-h-11` |
| `Input`, `Textarea`, `Select`, `Checkbox` (`Form.tsx`) | Mọi ô nhập | `label` (tự gắn `htmlFor`), `error` (hiện dưới ô, đặt `aria-invalid`), `helperText`, `required` (dấu `*`). `Input`: `prefixIcon`, `suffixIcon`. `Textarea`: `showCount`, `currentValue` để đếm ký tự. `Select`: `options`, `placeholder` (một lựa chọn rỗng bị khóa, dùng cho ô bắt đầu rỗng — `ui-screens.md` §4.3) | Có `forwardRef`, dùng thẳng với `register` của React Hook Form |
| `Modal` | Hộp thoại có form hay nội dung | `isOpen`, `onClose`, `title`, `description`, `size` (`sm`, `md`, `lg`, `xl`), `closeOnBackdropClick`, `closeOnEscape`, `showCloseButton` | Khóa cuộn trang khi mở. Chưa giữ và trả focus (§7) |
| `ConfirmDialog` | Xác nhận thao tác không hoàn tác được (`ui-screens.md` §4.3) | `variant`: `primary`, `warning`, `danger`; `title`, `message` (ReactNode), `confirmText`, `cancelText`, `isLoading`, `onConfirm` | Đang gửi thì khóa cả nút Hủy và không đóng được. Lỗi API hiện ngay trong `message`; chỉ đóng khi thành công  |
| `Table`, `TableHeader`, `TableBody`, `TableRow`, `TableHead`, `TableCell` | Danh sách nhiều cột trên màn rộng | `Table` có `containerClassName` | Khung đã có `overflow-x-auto`, nhưng dưới `xl` phải đổi sang thẻ (§6) |
| `TableLoading`, `TableEmpty`, `TableError` | Ba trạng thái bên trong bảng | `colSpan` bắt buộc; `TableLoading`: `rowCount` (mặc định 5); `TableEmpty`: `title`, `message`, `actionText`, `onAction`; `TableError`: `message`, `onRetry` | |
| `LoadingSpinner`, `EmptyState`, `ErrorAlert` (`StateFeedback.tsx`) | Ba trạng thái ngoài bảng, và lỗi tải lại phía trên dữ liệu cũ | `LoadingSpinner`: `label`; `EmptyState`: `title`, `message`, `icon`, `actionText`, `onAction`; `ErrorAlert`: `title`, `message`, `onRetry` | |
| `Pagination` | Phân trang | `currentPage`, `totalPages`, `onPageChange`, `totalItems`, `pageSize`, `siblingCount` | Có dòng "Hiển thị a - b trong n kết quả" khi truyền `totalItems` và `pageSize` |
| `Icons` | Mọi biểu tượng | `Alert`, `Check`, `Close`, `Refresh`, `Spinner`, `Empty`, `Info`, `Trash`, `ChevronLeft`, `ChevronRight`, `Menu`, `Logout`, `User`, `School`, `Clock`, `Heart`, `Camera`, `Activity`, `FileText`, `Clipboard`, `Tool` | SVG viết thẳng, nét theo `currentColor` nên đổi màu bằng `text-*`. Cỡ 20px (`Menu` 24, `Logout` và `Refresh` 18, `Empty` 40). Thiếu biểu tượng (ví dụ chưa có kính lúp cho ô tìm) thì thêm vào `Icons.tsx`, không vẽ SVG riêng trong màn hình, không nạp từ CDN (D03) |
| `DashboardLayout`, `RoleGuard` | Chỉ trong `layout.tsx` của mỗi vai trò | | Khung trang ở `ui-screens.md` §4.1 |
| `UnderConstruction` | Trang chưa làm | | |

### 5.1 Khuôn chưa thành component

Các khuôn dưới đây đang viết thẳng trong màn hình. Khi vai trò thứ hai cần thì gom thành component
trong `src/components/`.

- **Nhãn trạng thái:** `inline-flex items-center gap-1.5 whitespace-nowrap rounded-full px-2.5 py-1
  text-xs font-semibold` cộng nền và chữ theo tông §3.2, chấm `h-1.5 w-1.5 rounded-full` có
  `aria-hidden="true"`. Nên gom ngay thành `src/components/Badge.tsx` với prop `tone` (thẻ S01 "[FE] Đổi design system"),
  vì cả ba vai trò đều có nhãn trạng thái.
- **Dải thông báo thành công và lỗi:** `role="status"` hoặc `role="alert"`, nút đóng là nút chỉ có
  `Icons.Close` với `aria-label="Đóng thông báo"`. 
- **Lỗi API trong form:** liệt kê `errors` nếu có, không thì hiện `message`. Đã có `src/components/ApiErrorAlert.tsx`.

---

## 6. Responsive

- Breakpoint là mặc định của Tailwind: `sm` 640px, `md` 768px, `lg` 1024px, `xl` 1280px, `2xl`
  1536px. Không thêm breakpoint riêng.
- Khung trang: từ `lg` menu cố định bên trái, rộng 288px; nhỏ hơn thì menu thành ngăn kéo
  (`ui-screens.md` §4.1).
- Bảng nhiều cột: bảng từ `xl`, mỗi bản ghi một thẻ dưới `xl` . Mốc là `xl` chứ
  không phải `lg`, vì từ `lg` menu đã chiếm 288px.
- Vùng bấm của thao tác chính trên điện thoại cao ít nhất 44px (`min-h-11`); hai nút cạnh nhau cách
  ít nhất 8px.
- Trên điện thoại, nội dung chính lên trước: thu gọn thẻ thống kê thành hàng nhãn nhỏ, ẩn bộ lọc
  trùng chức năng với thứ khác đã có trên màn hình.
- Thử mỗi màn hình ở 375px và ở màn rộng (1280px trở lên). Ở 375px trang không được cuộn ngang.

---

## 7. Truy cập

- Mọi ô nhập có nhãn: prop `label` của `Form`, hoặc `aria-label` khi giao diện không có chỗ cho
  nhãn (ô tìm, ô lọc). Placeholder không thay được nhãn.
- Nút chỉ có biểu tượng phải có `aria-label`.
- Trạng thái không chỉ thể hiện bằng màu: nhãn luôn có chữ; chấm và biểu tượng trang trí có
  `aria-hidden="true"`.
- `role="status"` cho thông báo thành công, `role="alert"` cho lỗi.
- `aria-current="page"` cho mục menu và trang đang mở; đã có trong `DashboardLayout` và
  `Pagination`.
- Nút bật tắt một bộ lọc có `aria-pressed`.
- Nhóm nút thao tác trên cùng một đối tượng (ví dụ nút Duyệt và Từ chối của một yêu cầu) bọc trong
  `role="group"` có `aria-label` nêu đối tượng.
- Không bỏ viền focus mà không thay bằng `ring`. `Button` và `Form` đã có `focus-visible:ring-2`
  và `focus:ring-2`.
- Chữ cần đọc không nhạt hơn `outline`.
- **Hạn chế đã biết:** `Modal` chưa giữ focus bên trong hộp thoại, chưa tự focus phần tử đầu tiên
  và chưa trả focus về nút đã mở. Đây là việc của bộ component dùng chung. Trong lúc chờ, hộp thoại
  có form đặt `autoFocus` cho ô đầu tiên.

---

## 8. Chỗ code hiện chưa theo tài liệu này

- `DashboardLayout` chưa có chuông thông báo (`ui-screens.md` §4.1 [7]) — làm cùng thẻ SCR-COM-01.
- *Ghi chú hoàn thành:* Thẻ S01-08 đã cập nhật nhận diện Gia sư (TutorConnect) theo prototype EJS, chuẩn hóa màu sắc trang Đăng nhập (SCR-AUTH-01) theo token và bổ sung component `Badge.tsx` dùng chung.
