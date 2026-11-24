# Màn hình và điều hướng

## 0. Về tài liệu này

Mỗi màn hình hiện gì, gọi API nào, bấm nút thì làm gì. Frontend code theo đúng mục SCR của màn
hình; người review đối chiếu với mục đó. Cuối kỳ, bảng §3 và các mục SCR được chép sang sheet
**P3D_05_MauGiaoDien** (mã `UI-xx` của biểu mẫu ghi ở cột cuối bảng §3).

**Viết dần theo sprint.** Màn hình được viết chi tiết trước sprint frontend của nó một sprint
(thẻ `[Docs]` trong file kế hoạch). Màn hình có ghi "chưa viết" ở §3 thì **chưa code**, kể cả
khi đã có khung `UnderConstruction`.

Giao diện tham khảo: prototype EJS 20 màn hình (`views/pages/ui01…ui20` ở repo cũ `D:\Giasu`).
Prototype chỉ để tham khảo bố cục; chỗ nào prototype khác tài liệu này thì theo tài liệu này
(ví dụ prototype có "Quên mật khẩu", "Ghi nhớ đăng nhập", học phí theo giờ — không làm).

Đọc cùng: `frontend/design-system.md` (hình thức), `frontend/frontend-conventions.md` (cách viết
code), `requirements/acceptance-criteria.md` (kiểm gì trước khi mở PR).

---

## 1. Mã màn hình và khuôn mô tả

### 1.1 Mã màn hình

`SCR-<NHÓM>-<số>`:

| Nhóm | Route group | Tiền tố URL | Vai trò |
| :-- | :-- | :-- | :-- |
| `AUTH` | `(auth)` | — | Chưa đăng nhập |
| `TUT` | `(tutor)` | `/tutor` | `Tutor` |
| `PAR` | `(parent)` | `/parent` | `Parent` |
| `ADM` | `(admin)` | `/admin` | `Admin` |
| `COM` | mỗi vai trò một route, dùng chung một component | `/<vai-trò>/...` | Nhiều vai trò |

Màn hình `COM` có một component trong `src/components/screens/`; `page.tsx` của mỗi vai trò chỉ
render component đó (`frontend-conventions.md` §1). Mã đã cấp không đổi, màn hình bị bỏ thì mã
không dùng lại.

### 1.2 Khuôn mô tả một màn hình

```markdown
### SCR-XXX-NN — Tên màn hình

- **Mục đích:** một câu: ai dùng để làm gì
- **Route:** `/...` · **Vai trò:** ...
- **Yêu cầu:** FR-.. · UC-.. · AC-..
- **API:** endpoint, ghi "(chờ Sxx-yy)" nếu backend chưa có trên develop

**Bố cục** — wireframe chữ, các vùng đánh số [1], [2]...
**Vùng** — bảng # | Thành phần | Dữ liệu | API
**Trạng thái** — chỉ ghi chỗ khác §4.2
**Hành vi** — từng thao tác: kiểm tra phía client, gọi API nào, thành công/thất bại thì sao
**Quy tắc liên quan** — BR, D mà giao diện phải thể hiện
```

Wireframe chỉ cho biết các vùng nằm đâu và chứa gì, không quyết màu hay cỡ chữ. Chữ mẫu (họ tên,
số tiền, ngày) là ví dụ.

---

## 2. Điều hướng

### 2.1 Vào app, đăng nhập, đăng xuất

```text
Mở một URL bất kỳ
   │
   ▼
Đang khôi phục phiên? ── có ──▶ vòng quay
   │ không
   ▼
Có phiên? ── không ──▶ /login (SCR-AUTH-01) ⇄ /register (SCR-AUTH-02)
   │ có                        │ đăng nhập / đăng ký thành công
   ▼                           ▼
"/" chuyển tới /<role viết thường> ──▶ trang đầu của vai trò (bảng 2.2)
```

- Chỉ `src/app/page.tsx` chọn trang theo vai trò. Đăng nhập xong, đăng ký xong và layout gặp
  sai vai trò đều chỉ `router.replace("/")`.
- Mở `/login` hay `/register` khi đã có phiên → về `/`.
- Layout mỗi vai trò bọc `RoleGuard`: đang khôi phục phiên → vòng quay; không có phiên →
  `/login`; sai vai trò → `/`. Không có trang "Không có quyền".
- **Đăng xuất:** nút ở đầu trang gọi `logout()` → Supabase `signOut({ scope: "local" })` rồi xóa phiên ở máy.
  Có hiệu lực trên mọi thiết bị (D06).
- **Hết hạn phiên:** timer theo `expiresAtUtc` chỉ xóa phiên ở máy, không gọi API.
- **Bị thu hồi phiên:** API nào trả 401 thì interceptor xóa phiên và tải lại `/login`.

### 2.2 Bản đồ màn hình theo vai trò

| Vai trò | Tên cổng | `/<vai-trò>` chuyển tới | Menu, theo thứ tự |
| :-- | :-- | :-- | :-- |
| `Tutor` | Cổng Gia Sư | `/tutor/profiles` | SCR-TUT-01 Hồ sơ gia sư · SCR-TUT-03 Xác thực sinh viên · SCR-TUT-04 Tìm tin tuyển · SCR-TUT-06 Ứng tuyển của tôi · SCR-TUT-07 Lộ trình và buổi học · SCR-TUT-09 Học phí · SCR-COM-03 Tin nhắn · SCR-COM-01 Thông báo |
| `Parent` | Cổng Phụ Huynh | `/parent/jobs` | SCR-PAR-01 Học sinh của tôi · SCR-PAR-02 Tin tìm gia sư · SCR-PAR-06 Lộ trình và buổi học · SCR-PAR-08 Học phí · SCR-COM-03 Tin nhắn · SCR-COM-01 Thông báo |
| `Admin` | Cổng Quản Trị | `/admin/dashboard` | SCR-ADM-01 Tổng quan · SCR-ADM-02 Duyệt hồ sơ gia sư · SCR-ADM-03 Xác thực sinh viên · SCR-ADM-04 Duyệt tin · SCR-ADM-05 Báo cáo vi phạm · SCR-COM-01 Thông báo |

Màn hình không có trên menu, mở từ màn hình khác: SCR-TUT-02, SCR-TUT-05, SCR-TUT-08, SCR-PAR-03,
SCR-PAR-04, SCR-PAR-05, SCR-PAR-07, SCR-COM-02, SCR-COM-04.

Menu khai báo trong `src/app/(<nhóm>)/layout.tsx`. **Khung hiện tại thiếu** mục "Xác thực sinh
viên" (Gia sư và Admin) và "Học sinh của tôi" (Phụ huynh); thẻ S01 "[FE] Rà khung" bổ sung theo
bảng này.

### 2.3 Thứ tự dữ liệu giữa các màn hình

| Màn hình | Cần có trước | Chưa có thì hiện |
| :-- | :-- | :-- |
| SCR-TUT-01 nút "Gửi duyệt" | Hồ sơ đủ điều kiện BR-04, có ≥ 1 minh chứng (SCR-TUT-02) | Nút khóa, kèm dòng "Cần bổ sung: ..." liệt kê điều còn thiếu |
| SCR-ADM-02 danh sách chờ duyệt | Gia sư gửi duyệt hồ sơ (SCR-TUT-01) | Rỗng: "Chưa có hồ sơ nào chờ duyệt." |
| SCR-ADM-03 danh sách chờ xác thực | Gia sư gửi xác thực (SCR-TUT-03) | Rỗng: "Chưa có yêu cầu xác thực nào." |
| SCR-PAR-03 đăng tin | Phụ huynh có ít nhất một học sinh (SCR-PAR-01) | Ô chọn học sinh rỗng, kèm liên kết "Thêm học sinh" |
| SCR-TUT-04 có tin để tìm | Admin duyệt tin (SCR-ADM-04) | Rỗng theo SCR-TUT-04 |
| SCR-TUT-04 Matching Score | Gia sư có hồ sơ `Approved` | Không có cột điểm phù hợp, kèm dòng nhắc hoàn thiện hồ sơ |

---

## 3. Bảng tổng hợp

| Mã | Tên | Route | FR | Sprint FE | Người làm | Đặc tả | UI biểu mẫu |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| SCR-AUTH-01 | Đăng nhập | `/login` | FR-01 | đã có, sửa ở S02 | SV2 | **đã viết** | UI-01 |
| SCR-AUTH-02 | Đăng ký | `/register` | FR-01 | S02 | SV2 | **đã viết** | UI-01 |
| SCR-TUT-01 | Hồ sơ gia sư | `/tutor/profiles` | FR-03, FR-04, FR-36 | S03 | SV2 | **đã viết** | UI-02 |
| SCR-TUT-02 | Tạo / sửa hồ sơ | `/tutor/profiles/new`, `/tutor/profiles/[id]` | FR-03, FR-04 | S03 | SV2 | **đã viết** | UI-02 |
| SCR-TUT-03 | Xác thực sinh viên | `/tutor/verification` | FR-02 | S03 | SV2 | **đã viết** | UI-02 |
| SCR-TUT-04 | Tìm tin tuyển | `/tutor/jobs` | FR-07, FR-08, FR-34 | S05 | SV2 | chưa viết (S03) | UI-03 |
| SCR-TUT-05 | Chi tiết tin | `/tutor/jobs/[id]` | FR-07, FR-09 | S05 | SV2 | chưa viết (S03) | UI-19 |
| SCR-TUT-06 | Ứng tuyển của tôi | `/tutor/applications` | FR-09, FR-10 | S05 | SV2 | chưa viết (S03) | UI-04 |
| SCR-TUT-07 | Lộ trình và buổi học | `/tutor/roadmaps` | FR-15–FR-18 | S07 | SV2 | chưa viết (S05) | UI-08 |
| SCR-TUT-08 | Chi tiết lộ trình | `/tutor/roadmaps/[id]` | FR-15–FR-23 | S07–S09 | SV2 | chưa viết (S05) | UI-08, UI-09, UI-10 |
| SCR-TUT-09 | Học phí | `/tutor/tuition` | FR-24, FR-26 | S10 | SV2 | chưa viết (S07) | UI-11 |
| SCR-PAR-01 | Học sinh của tôi | `/parent/students` | FR-05 | S04 | SV4 | chưa viết (S02) | UI-05 |
| SCR-PAR-02 | Tin tìm gia sư | `/parent/jobs` | FR-05, FR-35 | S04 | SV4 | chưa viết (S02) | UI-05 |
| SCR-PAR-03 | Đăng / sửa tin | `/parent/jobs/new`, `/parent/jobs/[id]/edit` | FR-05 | S04 | SV4 | chưa viết (S02) | UI-05 |
| SCR-PAR-04 | Ứng viên của tin | `/parent/jobs/[id]` | FR-11–FR-13 | S06 | SV4 | chưa viết (S04) | UI-06 |
| SCR-PAR-05 | Hồ sơ ứng viên | `/parent/candidates/[applicationId]` | FR-11, FR-28 | S06 | SV4 | chưa viết (S04) | UI-20 |
| SCR-PAR-06 | Lộ trình và buổi học | `/parent/roadmaps` | FR-15–FR-19 | S07 | SV4 | chưa viết (S05) | UI-08 |
| SCR-PAR-07 | Chi tiết lộ trình | `/parent/roadmaps/[id]` | FR-15–FR-23 | S07–S10 | SV4 | chưa viết (S05) | UI-09, UI-10 |
| SCR-PAR-08 | Học phí | `/parent/payments` | FR-24, FR-25 | S09 | SV4 | chưa viết (S07) | UI-11 |
| SCR-ADM-01 | Tổng quan | `/admin/dashboard` | FR-33 | S11 | SV4 | chưa viết (S08) | UI-18 |
| SCR-ADM-02 | Duyệt hồ sơ gia sư | `/admin/tutor-profiles` | FR-04 | S04 | SV4 | chưa viết (S02) | UI-15 |
| SCR-ADM-03 | Xác thực sinh viên | `/admin/student-verifications` | FR-02 | S03 | SV4 | **đã viết** | UI-15 |
| SCR-ADM-04 | Duyệt tin | `/admin/jobs` | FR-06 | S04 | SV4 | chưa viết (S02) | UI-16 |
| SCR-ADM-05 | Báo cáo vi phạm | `/admin/violations` | FR-29–FR-31 | S07, S11 | SV4 | chưa viết (S05) | UI-17 |
| SCR-COM-01 | Thông báo | `/<vai-trò>/notifications` | FR-32 | S03 | SV2 | **đã viết** | UI-14 |
| SCR-COM-02 | Cài đặt email | `/<vai-trò>/notifications/settings` | FR-32 | S03 | SV2 | **đã viết** | UI-14 |
| SCR-COM-03 | Tin nhắn | `/tutor/chat`, `/parent/chat` | FR-14 | S06 | SV2 | chưa viết (S04) | UI-07 |
| SCR-COM-04 | Báo cáo vi phạm | `/tutor/reports/new`, `/parent/reports/new` | FR-30 | S06 | SV2 | chưa viết (S04) | UI-13 |

Cột "Đặc tả": "chưa viết (Sxx)" = sprint của thẻ `[Docs]` sẽ viết mục đó. Đánh giá (FR-27) nằm
trong SCR-TUT-08 và SCR-PAR-07.

---

## 4. Quy ước chung cho mọi màn hình

### 4.1 Khung trang

Mọi màn hình trừ `AUTH` nằm trong `DashboardLayout`, bọc ngoài bằng `RoleGuard`.

```text
┌──────────────────┬──────────────────────────────────────────────────────────────┐
│ [1] Gia Sư Kết   │ [3] ☰  Tên cổng / Tên màn hình        [7] 🔔 3  [4] Họ tên [5]│
│     Nối          │                                                Vai trò   ⏻  │
│     Tên cổng     ├──────────────────────────────────────────────────────────────┤
│ [2] Menu         │ [6] Nội dung màn hình                                        │
└──────────────────┴──────────────────────────────────────────────────────────────┘
```

| # | Thành phần | Dữ liệu |
| :-- | :-- | :-- |
| 1 | Thương hiệu, tên cổng, tên nhóm | Bảng 2.2 |
| 2 | Menu | Mục đang mở tô màu, `aria-current="page"`. Từ `lg` cố định bên trái; nhỏ hơn thì là ngăn kéo mở bằng [3] |
| 3 | Nút "Mở menu" (dưới `lg`), đường dẫn (từ `sm`) | Tên mục menu đang mở; trang không có trên menu thì lấy tên mục cha |
| 4 | Người dùng | `user.fullName`, nhãn vai trò tiếng Việt |
| 5 | Đăng xuất | Dưới `sm` chỉ còn biểu tượng |
| 6 | Nội dung | Màn hình đang mở |
| 7 | Chuông thông báo | Số chưa đọc từ `GET /api/notifications/unread-count`, tải lại mỗi 60 giây và khi đổi trang; 0 thì không hiện số, > 99 hiện "99+". Bấm → SCR-COM-01. Thuộc thẻ NOTI (SCR-COM-01) |

### 4.2 Trạng thái và lỗi

Mỗi vùng có dữ liệu từ API có đủ ba trạng thái (NFR-05), dùng `StateFeedback.tsx`, `Table.tsx`:

| Trạng thái | Khi nào | Hiển thị | Component |
| :-- | :-- | :-- | :-- |
| Đang tải | Lần tải đầu (`isPending`) | Vòng quay "Đang tải ..."; bảng thì hàng chờ | `LoadingSpinner`, `TableLoading` |
| Lỗi | Lỗi khi chưa có dữ liệu | `message` qua `toApiError`, nút "Thử lại" | `ErrorAlert`, `TableError` |
| Rỗng | Danh sách rỗng | Một câu nói vì sao rỗng, kèm bước tiếp theo | `EmptyState`, `TableEmpty` |

Đã có dữ liệu mà lần tải lại lỗi thì giữ dữ liệu cũ, hiện cảnh báo phía trên.

Lỗi luôn đọc qua `toApiError(err)`, hiện `message` của backend, không `if/else` theo mã:

| Mã | Giao diện làm gì |
| :-- | :-- |
| 400 | Có `errors` thì liệt kê từng dòng (trong form: một khung phía trên các ô); không có thì hiện `message` |
| 401 | Interceptor tự xử lý |
| 403 | Hiện thông báo, không đăng xuất |
| 404 | Bản ghi không tồn tại hoặc ngoài phạm vi; hiện message, tải lại danh sách |
| 409 | Xung đột trạng thái, thường do dữ liệu vừa đổi; hiện message, tải lại dữ liệu liên quan |
| 429 | Chỉ ở `AUTH` |
| 500 | Message chung của backend |

Ghi thành công → dải `role="status"` phía trên nội dung, tự ẩn sau 6 giây, có nút đóng. Ghi thất
bại → dải `role="alert"` cùng chỗ, **không tự ẩn**.

### 4.3 Form

- React Hook Form; kiểm tra phía client lặp đúng giới hạn và câu thông báo của validator backend;
  lỗi hiện dưới ô. Họ tên, email, tiêu đề, mô tả đo độ dài sau khi bỏ khoảng trắng hai đầu; mật
  khẩu không bỏ.
- Ô chọn giá trị liệt kê bắt đầu rỗng, không chọn sẵn.
- Đang gửi thì khóa nút gửi. Chỉ đóng hộp thoại hay xóa form khi gửi thành công.
- Thao tác không hoàn tác được luôn qua `ConfirmDialog` nêu đối tượng và hậu quả: gửi duyệt hồ
  sơ, lưu thay đổi hồ sơ đã duyệt, gỡ minh chứng, gửi xác thực, duyệt/từ chối (Admin), rút phiếu,
  mời dạy thử, nhận/không nhận gia sư, đóng tin, xác nhận/khiếu nại buổi học, ghi nhận thanh toán,
  gửi báo cáo vi phạm, áp chế tài.
- Ngoại lệ bấm một lần là ghi: đổi trạng thái nhận dạy, đặt hồ sơ mặc định, lưu tin, đánh dấu
  thông báo đã đọc — đều đổi lại được ngay.
- Rời trang khi form có thay đổi chưa lưu → hỏi "Bạn có thay đổi chưa lưu. Rời trang?" (sự kiện
  `beforeunload` và khi bấm "Hủy").

### 4.4 Hiển thị dữ liệu

Giá trị liệt kê lưu tiếng Anh, hiển thị tiếng Việt; bảng nhãn khai báo một chỗ trong
`src/types/<tài-nguyên>.ts`. Danh sách đầy đủ và tông màu: `business/business-rules.md` §2,
`frontend/design-system.md` §3.2.

| Loại | Giá trị → nhãn |
| :-- | :-- |
| Vai trò | `Admin` → Quản trị viên · `Tutor` → Gia sư · `Parent` → Phụ huynh |
| Hồ sơ | `Draft` → Nháp · `PendingReview` → Chờ duyệt · `Approved` → Đã duyệt · `Rejected` → Bị từ chối |
| Nhận dạy | `Accepting` → Đang nhận thêm học sinh · `Full` → Đã đủ lịch · `Paused` → Tạm ngừng |
| Xác thực | `Unverified` → Chưa xác thực · `Pending` → Chờ xác thực · `Verified` → Đã xác thực · `Rejected` → Bị từ chối |
| Cấp học | `Primary` → Tiểu học · `LowerSecondary` → THCS · `UpperSecondary` → THPT · `Other` → Khác |
| Hình thức dạy | `Offline` → Tại nhà · `Online` → Trực tuyến · `Both` → Cả hai |

**Ngày giờ.** Trường kết thúc bằng `Utc` hiển thị theo giờ Việt Nam dạng `dd/MM/yyyy HH:mm`.
Trường chỉ có ngày hiển thị `dd/MM/yyyy`, không đổi múi giờ. Thông báo trong 24 giờ hiện tương
đối ("5 phút trước", "3 giờ trước"), cũ hơn hiện ngày giờ.

**Tiền.** Định dạng `vi-VN`, đơn vị đồng, ví dụ `200.000 ₫`; học phí luôn ghi "/buổi".

**Văn bản người dùng nhập** (giới thiệu, lý do, nội dung thông báo) hiển thị văn bản thuần, giữ
xuống dòng (`whitespace-pre-wrap`), không render HTML.

### 4.5 Tệp tải lên

- Chặn phía client trước khi gửi: quá số tệp cho phép, tệp > 5 MB, tệp không phải JPG/PNG/PDF;
  backend vẫn kiểm lại (D16).
- Gửi `multipart/form-data`; không đặt header `Content-Type` bằng tay (để trình duyệt tự gắn
  `boundary`).
- Xem tệp luôn bằng URL ký API trả về, hạn 60 phút; không lưu URL lâu dài. Ảnh tải lỗi (thường do
  URL hết hạn) thì gọi lại API lấy URL mới. PDF mở ở tab mới.

### 4.6 Responsive

- Dùng được ở 375 px và từ 1280 px; không cuộn ngang ở 375 px.
- Bảng nhiều cột: bảng từ `xl`, thẻ dưới `xl`.
- Nút thao tác chính trên điện thoại cao ≥ 44 px (`min-h-11`).

---

## 5. Tài khoản

### SCR-AUTH-01 — Đăng nhập

- **Mục đích:** Mọi người dùng đăng nhập để vào cổng của vai trò mình.
- **Route:** `/login` · **Vai trò:** chưa đăng nhập
- **Yêu cầu:** FR-01 · UC-01 · AC-AUTH-04, AC-AUTH-05
- **API:** Supabase Auth `signInWithPassword`, sau đó `GET /api/auth/me` qua `AuthContext` (đã có)

**Bố cục**

```text
┌────────────────────────────────────┐
│ Đăng nhập                          │
│ Nền tảng tìm gia sư và quản lý ... │
│ [1] (khung lỗi)                    │
│ [2] Email     [                  ] │
│ [3] Mật khẩu  [                  ] │
│ [4] (          Đăng nhập         ) │
│ [5] Chưa có tài khoản? Đăng ký     │
└────────────────────────────────────┘
```

**Vùng**

| # | Thành phần | Dữ liệu | API |
| :-- | :-- | :-- | :-- |
| 1 | Lỗi từ server | `errors` hoặc `message` | — |
| 2 | Email | Bỏ khoảng trắng hai đầu; bắt buộc; ≤ 254 ký tự; đúng định dạng | — |
| 3 | Mật khẩu | Bắt buộc; không bỏ khoảng trắng; nút hiện/ẩn mật khẩu | — |
| 4 | Nút Đăng nhập | "Đang đăng nhập..." khi gửi; "Thử lại sau (Ns)" khi Supabase giới hạn | Supabase Auth → `GET /api/auth/me` |
| 5 | Liên kết | Sang `/register` | — |

**Hành vi**

1. Kiểm tra khi rời ô: "Vui lòng nhập email", "Email không đúng định dạng", "Email không được
   vượt quá 254 ký tự", "Vui lòng nhập mật khẩu".
2. Thành công → `router.replace("/")`.
3. 401 → "Email hoặc mật khẩu không đúng.", giữ chữ đã gõ (AC-AUTH-04).
4. 429 → hiện message, khóa form, nút đếm ngược 60 giây (D08).
5. Supabase trả mã `email_not_confirmed` → "Email chưa được xác nhận. Vui lòng kiểm tra hộp thư.".
6. `/api/auth/me` lỗi → xóa phiên Supabase vừa tạo, giữ trang đăng nhập để hiện message.
7. Không có "Quên mật khẩu", "Ghi nhớ đăng nhập", tài khoản demo (D17).

**Hiện trạng:** [1]–[4] đã theo token và component dùng chung (thẻ S01-08). [5] đang chờ: link
tạm ẩn vì chưa có route `/register`, bật lại cùng SCR-AUTH-02 (S02-07). Chưa kiểm với backend thật
hai ca: đăng nhập thành công của cả ba vai trò, và 429 ở lần gọi thứ sáu trong một phút.

**Quy tắc liên quan** — D06, D08.

---

### SCR-AUTH-02 — Đăng ký

- **Mục đích:** Sinh viên hoặc phụ huynh tự tạo tài khoản rồi vào thẳng cổng của mình.
- **Route:** `/register` · **Vai trò:** chưa đăng nhập
- **Yêu cầu:** FR-01 · UC-01 · AC-AUTH-01, AC-AUTH-02, AC-AUTH-03, AC-AUTH-05
- **API:** `POST /api/auth/register` (chờ S01-04), rồi `login()`

**Bố cục**

```text
┌──────────────────────────────────────────────────────┐
│ Tạo tài khoản                                        │
│ [1] (khung lỗi)                                      │
│ [2] Bạn tham gia với vai trò:                        │
│     ┌───────────────────┐  ┌───────────────────┐     │
│     │ Sinh viên / Gia sư│  │ Phụ huynh         │     │
│     │ Tìm lớp, nhận dạy │  │ Đăng tin tìm gia sư│    │
│     └───────────────────┘  └───────────────────┘     │
│ [3] Họ và tên        [                            ]  │
│ [4] Số điện thoại    [                            ]  │
│ [5] Email            [                            ]  │
│ [6] Mật khẩu         [              ] Nhập lại [   ] │
│ [7] ☐ Tôi đồng ý Quy chế hoạt động và cam kết không  │
│       thu hoặc đóng phí giữ chỗ, phí cọc.            │
│ [8] (              Tạo tài khoản              )      │
│ [9] Đã có tài khoản? Đăng nhập                       │
└──────────────────────────────────────────────────────┘
```

**Vùng**

| # | Thành phần | Dữ liệu | API |
| :-- | :-- | :-- | :-- |
| 1 | Lỗi từ server | `errors` hoặc `message` | — |
| 2 | Chọn vai trò | Hai thẻ chọn một (`role="radiogroup"`), bắt đầu **chưa chọn**; gửi `Tutor` hoặc `Parent` | — |
| 3 | Họ và tên | 2–100 ký tự sau khi bỏ khoảng trắng | — |
| 4 | Số điện thoại | 10 chữ số, bắt đầu bằng 0; bàn phím số (`inputMode="numeric"`) | — |
| 5 | Email | Như SCR-AUTH-01. Vai trò Gia sư thì có gợi ý dưới ô: "Nên dùng email sinh viên để xác thực nhanh hơn." | — |
| 6 | Mật khẩu, nhập lại | 8–128 ký tự, có chữ và số; "Nhập lại" phải trùng (chỉ kiểm phía client, không gửi lên) | — |
| 7 | Đồng ý quy chế | Bắt buộc tick; gửi `acceptTerms: true` | — |
| 8 | Nút gửi | "Đang tạo tài khoản..." khi gửi | `POST /api/auth/register` |
| 9 | Liên kết | Sang `/login` | — |

**Hành vi**

1. Câu thông báo phía client: "Vui lòng chọn vai trò", "Họ tên từ 2 đến 100 ký tự", "Số điện thoại
   gồm 10 chữ số, bắt đầu bằng 0", "Mật khẩu từ 8 đến 128 ký tự, có cả chữ và số", "Mật khẩu nhập
   lại không khớp", "Bạn cần đồng ý quy chế để tiếp tục".
2. Gửi `{ role, fullName, phone, email, password, acceptTerms }`.
3. 201 → gọi `login(email, password)` → `router.replace("/")`. Nếu bước đăng nhập lỗi (ví dụ 429)
   → chuyển `/login` kèm dải "Tạo tài khoản thành công, vui lòng đăng nhập."
4. 409 → hiện message ("Email đã được sử dụng."), giữ dữ liệu đã nhập, focus ô Email.
5. 400 → liệt kê `errors` ở [1]. 429 → như SCR-AUTH-01.

**Quy tắc liên quan** — BR-01; D05, D08.

---

## 6. Gia sư

### SCR-TUT-01 — Hồ sơ gia sư

- **Mục đích:** Gia sư xem các hồ sơ của mình, biết hồ sơ nào đang công khai, đổi trạng thái nhận
  dạy, đặt mặc định và gửi duyệt.
- **Route:** `/tutor/profiles` (`/tutor` chuyển tới đây) · **Vai trò:** Gia sư
- **Yêu cầu:** FR-03, FR-04, FR-36 · UC-02, UC-13 · AC-PROFILE-01, AC-PROFILE-03, AC-PROFILE-06,
  AC-PROFILE-07, AC-PROFILE-09
- **API:** `GET /api/tutor-profiles/mine`, `GET /api/student-verifications/mine`,
  `PUT /api/tutor-profiles/{id}/availability`, `POST /api/tutor-profiles/{id}/set-default`,
  `POST /api/tutor-profiles/{id}/submit` (chờ S02-05, S02-03)

**Bố cục**

```text
Hồ sơ gia sư                                          [1] ( + Tạo hồ sơ mới ) 2/5
Tạo hồ sơ riêng cho từng nhóm môn/cấp học để phụ huynh tìm thấy bạn.

[2] ┌ Xác thực sinh viên: ● Chưa xác thực — Xác thực để có huy hiệu tin cậy. (Xác thực ngay →) ┐

[3] ┌──────────────────────────────────────────────────────────────────────┐
    │ ★ Mặc định   ● Đã duyệt                                              │
    │ Toán THPT & luyện thi đại học                                        │
    │ Toán, Vật lý · THPT · Cả hai                                          │
    │ TP. Hồ Chí Minh — Phường Bến Thành, Phường Sài Gòn                    │
    │ 200.000 ₫/buổi · 3 minh chứng · Cập nhật 10/11/2026 14:20             │
    │ Nhận dạy: [ Đang nhận thêm học sinh ▾ ]                               │
    │ ( Sửa )                                                               │
    ├──────────────────────────────────────────────────────────────────────┤
    │ ● Bị từ chối                                                          │
    │ Tiếng Anh THCS                                                        │
    │ ⚠ Lý do: Minh chứng IELTS mờ, không đọc được số báo danh.             │
    │ ...                                                                   │
    │ ( Sửa )  ( Đặt làm mặc định )  ( Gửi duyệt lại )                      │
    └──────────────────────────────────────────────────────────────────────┘
```

**Vùng**

| # | Thành phần | Dữ liệu | API |
| :-- | :-- | :-- | :-- |
| 1 | Nút tạo hồ sơ, bộ đếm | Sang SCR-TUT-02 (`/new`). Đủ 5 hồ sơ thì khóa nút, kèm "Tối đa 5 hồ sơ" (BR-23) | — |
| 2 | Dải xác thực sinh viên | Nhãn trạng thái xác thực; `Unverified`/`Rejected` có liên kết "Xác thực ngay"/"Gửi lại"; `Pending` ghi "Đang chờ Admin duyệt"; `Verified` chỉ hiện huy hiệu | `GET /api/student-verifications/mine` |
| 3 | Danh sách hồ sơ | Mỗi hồ sơ một thẻ, hồ sơ mặc định lên đầu, còn lại mới cập nhật trước. Thẻ gồm: nhãn mặc định, nhãn trạng thái duyệt, tiêu đề, môn (nối bằng dấu phẩy), cấp học, hình thức dạy, tỉnh + phường, học phí/buổi, số minh chứng, `updatedAtUtc`, lý do từ chối (khi `Rejected`), ô chọn trạng thái nhận dạy, các nút | `GET /api/tutor-profiles/mine` |

**Trạng thái** — rỗng: "Bạn chưa có hồ sơ nào. Tạo hồ sơ đầu tiên để phụ huynh tìm thấy bạn.",
kèm nút "Tạo hồ sơ". Lỗi tải [2] chỉ ẩn dải [2], không chặn [3].

**Hành vi**

1. **Nút theo trạng thái hồ sơ:**

   | Trạng thái | Sửa | Đặt mặc định | Gửi duyệt |
   | :-- | :-- | :-- | :-- |
   | `Draft` | ✓ | ✓ (nếu chưa mặc định) | ✓ — khóa nếu thiếu điều kiện BR-04 |
   | `PendingReview` | — (hiện "Đang chờ duyệt, chưa sửa được") | ✓ | — |
   | `Approved` | ✓ | ✓ | — |
   | `Rejected` | ✓ | ✓ | ✓ "Gửi duyệt lại" — khóa nếu thiếu BR-04 |

2. **Trạng thái nhận dạy:** đổi ô chọn là ghi ngay `PUT .../availability`, không hỏi lại. Đang
   gửi thì khóa ô của thẻ đó. Lỗi → trả ô về giá trị cũ, hiện dải lỗi. Hồ sơ chưa `Approved`
   có dòng phụ "Chỉ hiển thị cho phụ huynh khi hồ sơ đã duyệt."
3. **Đặt mặc định:** bấm là ghi, thành công thì danh sách tải lại (thẻ mặc định lên đầu).
4. **Gửi duyệt:** nút khóa khi thiếu điều kiện, kèm dòng "Cần bổ sung: minh chứng, phường/xã..."
   tính phía client từ dữ liệu hồ sơ. Bấm → `ConfirmDialog` "Gửi hồ sơ '<tiêu đề>' cho Admin
   duyệt? Trong lúc chờ duyệt bạn không sửa được hồ sơ." → `POST .../submit`. 400 → liệt kê
   `errors` (điều kiện còn thiếu do backend xác định). Thành công → nhãn chuyển "Chờ duyệt".
5. Mọi thao tác ghi xong làm mới query `["tutor-profiles", "mine"]`.

**Quy tắc liên quan** — BR-02, BR-04, BR-23, BR-25; D36.

---

### SCR-TUT-02 — Tạo / sửa hồ sơ

- **Mục đích:** Gia sư nhập nội dung hồ sơ và quản lý minh chứng.
- **Route:** `/tutor/profiles/new` (tạo), `/tutor/profiles/[id]` (sửa) · **Vai trò:** Gia sư
- **Yêu cầu:** FR-03, FR-04 · UC-02 · AC-PROFILE-01, AC-PROFILE-02, AC-PROFILE-04, AC-PROFILE-05,
  AC-PROFILE-07, AC-PROFILE-08
- **API:** `GET /api/subjects`, `GET /api/tutor-profiles/{id}`, `POST /api/tutor-profiles`,
  `PUT /api/tutor-profiles/{id}`, `POST /api/tutor-profiles/{id}/evidences`,
  `DELETE /api/tutor-profiles/{id}/evidences/{evidenceId}` (chờ S02-05)

**Bố cục**

```text
← Hồ sơ gia sư
Sửa hồ sơ  ● Bị từ chối                       [0] ⚠ Lý do từ chối: ...

[A] Thông tin hồ sơ
[1] Tiêu đề              [ Toán THPT & luyện thi đại học              ]
[2] Môn dạy (1–5)        [ ☐ Toán ☐ Vật lý ☐ Hóa học ☐ Tiếng Anh ... ]
[3] Cấp học              [ Chọn cấp học ▾ ]   [4] Hình thức [ Chọn ▾ ]
[5] Tỉnh/thành           [ Chọn tỉnh/thành ▾ ]
[6] Phường/xã (1–5)      [ Phường Bến Thành  ×] [ + Thêm phường/xã ]
[7] Học phí mong muốn    [ 200000 ] ₫/buổi
[8] Giới thiệu, kinh nghiệm [                                  ] 0/2000
                                            ( Hủy )  [9] ( Lưu )

[B] Minh chứng năng lực (tối đa 5)          — chỉ hiện khi hồ sơ đã được lưu
[10] Bang-diem.pdf   1,2 MB   ( Xem )  ( Gỡ )
     Giay-khen.jpg   800 KB   ( Xem )  ( Gỡ )
[11] ( + Tải lên minh chứng )  JPG, PNG, PDF · tối đa 5 MB mỗi tệp
```

**Vùng**

| # | Thành phần | Dữ liệu | API |
| :-- | :-- | :-- | :-- |
| 0 | Nhãn trạng thái, lý do từ chối | Chỉ khi sửa | `GET /api/tutor-profiles/{id}` |
| 1 | Tiêu đề | 10–150 ký tự | — |
| 2 | Môn dạy | Nhiều lựa chọn từ danh mục, 1–5 môn | `GET /api/subjects` |
| 3 | Cấp học | `EducationLevel`, bắt đầu rỗng | — |
| 4 | Hình thức dạy | `TeachingMode`, bắt đầu rỗng | — |
| 5 | Tỉnh/thành | Danh mục 34 tỉnh/thành trong `src/lib/provinces.ts` (D37) | — |
| 6 | Phường/xã | 1–5 ô chữ, mỗi ô ≤ 100 ký tự. Ẩn khi hình thức là `Online` | — |
| 7 | Học phí | Số nguyên 50.000–2.000.000, bội số 1.000; hiện kèm bản định dạng "200.000 ₫" | — |
| 8 | Giới thiệu | ≤ 2000 ký tự, có bộ đếm | — |
| 9 | Nút Lưu | Tạo → `POST`; sửa → `PUT` | xem bên dưới |
| 10 | Danh sách minh chứng | Tên tệp, dung lượng; "Xem" mở URL ký ở tab mới | `GET /api/tutor-profiles/{id}` (trả `evidences[].url`) |
| 11 | Tải lên | Chọn nhiều tệp một lần, không quá số chỗ còn lại | `POST .../evidences` |

**Trạng thái** — hồ sơ không tồn tại hoặc của người khác (404): thay cả trang bằng `EmptyState`
"Không tìm thấy hồ sơ." kèm nút về SCR-TUT-01. Hồ sơ `PendingReview`: mọi ô chỉ đọc, ẩn nút Lưu,
Gỡ, Tải lên, kèm dải "Hồ sơ đang chờ duyệt, chưa sửa được."

**Hành vi**

1. Câu thông báo phía client khớp validator: "Tiêu đề từ 10 đến 150 ký tự", "Chọn từ 1 đến 5 môn",
   "Vui lòng chọn cấp học", "Vui lòng chọn hình thức dạy", "Vui lòng chọn tỉnh/thành", "Nhập ít
   nhất một phường/xã", "Học phí từ 50.000 đến 2.000.000 đồng, làm tròn đến nghìn", "Giới thiệu
   không quá 2000 ký tự".
2. **Tạo:** `POST` → 201 → chuyển `/tutor/profiles/<id mới>` (thay URL bằng `router.replace`) với
   dải "Đã lưu hồ sơ nháp. Tải lên minh chứng rồi gửi duyệt ở trang Hồ sơ gia sư." 409 (đã đủ 5)
   → hiện message, nút về SCR-TUT-01.
3. **Sửa hồ sơ `Approved`:** bấm Lưu → `ConfirmDialog` cảnh báo "Hồ sơ sẽ chuyển sang Chờ duyệt
   và tạm ẩn với phụ huynh cho tới khi Admin duyệt lại." (BR-25). Hồ sơ `Draft`/`Rejected` lưu
   không hỏi.
4. **Tải minh chứng:** kiểm phía client theo §4.5 trước khi gửi; gửi `multipart` trường `files`.
   Đang tải thì khóa [11], hiện vòng quay. Thành công → danh sách [10] tải lại. Chỉ hiện [11] khi
   hồ sơ `Draft` hoặc `Rejected` (BR-26).
5. **Gỡ minh chứng:** `ConfirmDialog` "Gỡ tệp '<tên>' khỏi hồ sơ?" → `DELETE`.
6. **Hủy / mũi tên quay lại:** có thay đổi chưa lưu thì hỏi (§4.3), rồi về SCR-TUT-01.
7. Không có nút Gửi duyệt trên trang này; gửi duyệt ở SCR-TUT-01 để gia sư thấy cả danh sách.

**Quy tắc liên quan** — BR-03, BR-04, BR-23 – BR-26; D16, D37.

---

### SCR-TUT-03 — Xác thực sinh viên

- **Mục đích:** Gia sư gửi minh chứng sinh viên và theo dõi kết quả.
- **Route:** `/tutor/verification` · **Vai trò:** Gia sư
- **Yêu cầu:** FR-02 · UC-18 · AC-VERIFY-01, AC-VERIFY-02, AC-VERIFY-03, AC-VERIFY-05,
  AC-VERIFY-07
- **API:** `GET /api/student-verifications/mine`, `POST /api/student-verifications` (chờ S02-03)

**Bố cục**

```text
Xác thực sinh viên
Gia sư đã xác thực có huy hiệu "Đã xác thực" trên hồ sơ, giúp phụ huynh tin tưởng hơn.

[1] Trạng thái: ● Bị từ chối — gửi lúc 12/11/2026 09:15
    ⚠ Lý do: Ảnh thẻ bị che mất mã số sinh viên.

[2] Gửi yêu cầu xác thực
    Trường đang học      [ Trường Đại học Công nghệ Thông tin – ĐHQG-HCM ]
    Mã số sinh viên      [ 22520001 ]
    Ảnh thẻ sinh viên hoặc giấy xác nhận  ( Chọn tệp )  the-sv.jpg 1,1 MB
    JPG, PNG, PDF · tối đa 5 MB
                                                  ( Gửi yêu cầu )
```

**Vùng**

| # | Thành phần | Dữ liệu | API |
| :-- | :-- | :-- | :-- |
| 1 | Trạng thái hiện tại | Nhãn trạng thái; `createdAtUtc`; khi `Rejected` có lý do; khi `Pending`/`Verified` có trường, mã số sinh viên đã gửi | `GET /api/student-verifications/mine` |
| 2 | Form gửi | Trường (2–150 ký tự), mã số sinh viên (3–20 ký tự, chữ và số), đúng 1 tệp | `POST /api/student-verifications` |

**Trạng thái** — `data: null` (chưa gửi lần nào): [1] ghi "Chưa xác thực". Form [2] chỉ hiện khi
`Unverified` hoặc `Rejected`; `Pending` thay [2] bằng "Yêu cầu đang chờ Admin duyệt. Bạn sẽ nhận
thông báo khi có kết quả."; `Verified` thay bằng huy hiệu "Đã xác thực sinh viên".

**Hành vi**

1. Câu thông báo phía client: "Tên trường từ 2 đến 150 ký tự", "Mã số sinh viên từ 3 đến 20 ký
   tự, chỉ gồm chữ và số", "Vui lòng chọn một tệp minh chứng", cùng các câu tệp ở §4.5.
2. Gửi → `ConfirmDialog` "Gửi yêu cầu xác thực? Sau khi gửi bạn không sửa được cho tới khi có kết
   quả." → `POST` multipart (`university`, `studentCode`, `file`).
3. 201 → làm mới `["student-verifications", "mine"]`, dải thành công. 409 (đã có yêu cầu chờ) →
   hiện message và làm mới.
4. Không có nút xem lại tệp đã gửi: gia sư không cần, và bớt một chỗ phải cấp URL ký.

**Quy tắc liên quan** — BR-03, BR-05; D16, D36.

---

### Màn hình Gia sư chưa viết

SCR-TUT-04 … SCR-TUT-09 — xem bảng §3, cột "Đặc tả".

---

## 7. Phụ huynh

Chưa có màn hình nào thuộc S01–S03. SCR-PAR-01 … SCR-PAR-03 viết ở thẻ `[Docs]` S02 (frontend
làm ở S04).

---

## 8. Quản trị viên

### SCR-ADM-03 — Xác thực sinh viên

- **Mục đích:** Admin đối chiếu minh chứng sinh viên và duyệt hoặc từ chối.
- **Route:** `/admin/student-verifications` · **Vai trò:** Admin
- **Yêu cầu:** FR-02 · UC-18 · AC-VERIFY-04, AC-VERIFY-05, AC-VERIFY-06
- **API:** `GET /api/student-verifications?status=&page=&pageSize=`,
  `GET /api/student-verifications/{id}`, `POST .../{id}/approve`, `POST .../{id}/reject`
  (chờ S02-03)

**Bố cục**

```text
Xác thực sinh viên
[1] ( Chờ xác thực 5 ) ( Đã xác thực ) ( Bị từ chối )                 ( Làm mới )
[2] ┌──────────────┬──────────────────────┬───────────┬──────────────────┬─────────┐
    │ Gia sư       │ Trường / MSSV        │ Gửi lúc   │ Trạng thái       │         │
    ├──────────────┼──────────────────────┼───────────┼──────────────────┼─────────┤
    │ Nguyễn Văn A │ ĐH CNTT – ĐHQG-HCM   │ 12/11 09:15│ ● Chờ xác thực  │ ( Xem ) │
    │ a@gm.uit...  │ 22520001             │           │                  │         │
    └──────────────┴──────────────────────┴───────────┴──────────────────┴─────────┘
[3] < 1 2 3 >   Hiển thị 1 - 20 trong 45 kết quả

[4] Hộp thoại "Yêu cầu xác thực"
    Nguyễn Văn A · a@gm.uit.edu.vn · 0912345678
    Trường: ĐH CNTT – ĐHQG-HCM · MSSV: 22520001 · Gửi lúc 12/11/2026 09:15
    [ ảnh minh chứng / nút "Mở tệp PDF" ]
    ( Từ chối )                                       ( Duyệt )
```

**Vùng**

| # | Thành phần | Dữ liệu | API |
| :-- | :-- | :-- | :-- |
| 1 | Tab trạng thái | `Pending` (mặc định, có số đếm từ `totalCount`), `Verified`, `Rejected`; `aria-pressed` | — |
| 2 | Bảng / thẻ | Họ tên, email, trường, mã số sinh viên, `createdAtUtc`, nhãn trạng thái. Tab `Pending` sắp **cũ nhất trước**; hai tab còn lại mới duyệt trước, thêm cột người duyệt và `reviewedAtUtc` | `GET /api/student-verifications?status=` |
| 3 | Phân trang | Server, 20/trang | — |
| 4 | Hộp thoại chi tiết | Thông tin gia sư, số điện thoại, minh chứng: ảnh hiện thẳng; PDF có nút mở tab mới. Tab `Rejected` hiện thêm lý do | `GET /api/student-verifications/{id}` |

**Trạng thái** — rỗng theo tab: "Chưa có yêu cầu nào chờ xác thực." / "Chưa có yêu cầu nào đã
xác thực." / "Chưa có yêu cầu nào bị từ chối."

**Hành vi**

1. Đổi tab → về trang 1.
2. **Duyệt:** `ConfirmDialog` (variant `primary`) "Xác thực sinh viên Nguyễn Văn A? Gia sư sẽ có
   huy hiệu Đã xác thực." → `POST .../approve`.
3. **Từ chối:** mở form trong hộp thoại, ô "Lý do" bắt buộc, ≤ 500 ký tự, có bộ đếm; câu gợi ý
   dưới ô: "Lý do sẽ gửi cho gia sư, nêu rõ cần bổ sung gì." → `POST .../reject` `{ reason }`.
4. Thành công → đóng hộp thoại, dải thành công, làm mới danh sách (yêu cầu rời tab Chờ).
   409 (người khác vừa xử lý) → hiện message, đóng hộp thoại, làm mới.
5. Nút Duyệt/Từ chối chỉ có ở yêu cầu `Pending`.
6. Ảnh minh chứng tải lỗi → gọi lại chi tiết để lấy URL mới (§4.5).

**Quy tắc liên quan** — BR-05, BR-22, BR-SCOPE-04; D16.

---

### Màn hình Admin chưa viết

SCR-ADM-01, SCR-ADM-02, SCR-ADM-04, SCR-ADM-05 — xem bảng §3.

---

## 9. Dùng chung

### SCR-COM-01 — Thông báo

- **Mục đích:** Người dùng xem thông báo của mình và đi tới chỗ cần xử lý.
- **Route:** `/tutor/notifications`, `/parent/notifications`, `/admin/notifications` · **Vai trò:**
  mọi vai trò
- **Yêu cầu:** FR-32 · UC-11 · AC-NOTI-01, AC-NOTI-02, AC-NOTI-03
- **API:** `GET /api/notifications?unreadOnly=&page=&pageSize=`,
  `GET /api/notifications/unread-count`, `POST /api/notifications/{id}/read`,
  `POST /api/notifications/read-all` (chờ S02-02)
- **Code:** `src/components/screens/NotificationsScreen.tsx`; ba `page.tsx` chỉ render component
  này. Chuông ở khung trang (§4.1 [7]) thuộc cùng thẻ.

**Bố cục**

```text
Thông báo                        [1] ( Tất cả ) ( Chưa đọc 3 )   [2] ( Đánh dấu đã đọc tất cả )
                                                                  [3] Cài đặt email →
[4] ● Hồ sơ gia sư đã được duyệt                                   5 phút trước
      Hồ sơ "Toán THPT & luyện thi đại học" đã được duyệt và hiển thị với phụ huynh.
    ─────────────────────────────────────────────────────────────────────────
      Yêu cầu xác thực bị từ chối                                  12/11/2026 09:15
      Ảnh thẻ bị che mất mã số sinh viên.
[5] < 1 2 >
```

**Vùng**

| # | Thành phần | Dữ liệu | API |
| :-- | :-- | :-- | :-- |
| 1 | Bộ lọc | Tất cả / Chưa đọc (`unreadOnly=true`); số chưa đọc lấy từ `unread-count` | `GET .../unread-count` |
| 2 | Đánh dấu tất cả | Khóa khi số chưa đọc = 0 | `POST .../read-all` |
| 3 | Liên kết | Sang SCR-COM-02 | — |
| 4 | Danh sách | Mới nhất trước. Mỗi dòng: chấm chưa đọc + chữ đậm nếu `isRead = false`, `title`, `message` (văn bản thuần), thời gian (§4.4) | `GET /api/notifications` |
| 5 | Phân trang | Server, 20/trang | — |

**Trạng thái** — rỗng: "Bạn chưa có thông báo nào." / lọc Chưa đọc: "Bạn đã đọc hết thông báo."

**Hành vi**

1. Bấm một thông báo: chưa đọc thì gọi `POST .../{id}/read` (không chờ xong mới chuyển trang);
   có `link` thì `router.push(link)`, không có thì chỉ đánh dấu đã đọc.
2. Đánh dấu tất cả: bấm là ghi, không hỏi lại.
3. Mọi thao tác ghi làm mới tiền tố `["notifications"]` (gồm cả `unread-count` của chuông).
4. Không có nút xóa thông báo (BR-27).

**Quy tắc liên quan** — BR-27, BR-SCOPE-01.

---

### SCR-COM-02 — Cài đặt email

- **Mục đích:** Người dùng chọn loại thông báo nào được gửi thêm qua email.
- **Route:** `/<vai-trò>/notifications/settings` · **Vai trò:** mọi vai trò
- **Yêu cầu:** FR-32 · UC-11 · AC-NOTI-04, AC-NOTI-05
- **API:** `GET /api/notification-preferences`, `PUT /api/notification-preferences` (chờ S02-02)
- **Code:** `src/components/screens/NotificationSettingsScreen.tsx`.

**Bố cục**

```text
← Thông báo
Cài đặt email
Thông báo trong ứng dụng luôn được gửi. Tắt một loại ở đây chỉ ngừng gửi email loại đó.

[1] Kết quả duyệt hồ sơ, tin, xác thực             [ ● Bật ]
    Có ứng viên mới                                [ ● Bật ]
    ...
[2]                                           ( Hủy )  ( Lưu )
```

**Vùng**

| # | Thành phần | Dữ liệu | API |
| :-- | :-- | :-- | :-- |
| 1 | Danh sách loại | Mỗi dòng: nhãn tiếng Việt, công tắc `emailEnabled`. Chỉ hiện các loại liên quan tới vai trò (bảng bên dưới) | `GET /api/notification-preferences` |
| 2 | Lưu | Gửi **toàn bộ** danh sách | `PUT /api/notification-preferences` |

| Loại `type` | Nhãn | Gia sư | Phụ huynh | Admin |
| :-- | :-- | :-- | :-- | :-- |
| `ModerationResult` | Kết quả duyệt hồ sơ, tin, xác thực | ✓ | ✓ | |
| `NewApplication` | Có ứng viên mới | | ✓ | |
| `ApplicationStatus` | Thay đổi trạng thái ứng tuyển | ✓ | | |
| `Roadmap` | Lộ trình học | ✓ | ✓ | |
| `Session` | Buổi học và nhắc lịch | ✓ | ✓ | |
| `RequestExpiry` | Tin sắp hết hạn | | ✓ | |
| `Tuition` | Học phí | ✓ | ✓ | |
| `Progress` | Tiến độ học tập | ✓ | ✓ | |
| `Violation` | Báo cáo vi phạm | ✓ | ✓ | ✓ |
| `ModerationQueue` | Có hồ sơ, tin, yêu cầu xác thực mới cần duyệt | | | ✓ |

**Hành vi**

1. Công tắc chỉ đổi trên màn hình; bấm Lưu mới gửi. Có thay đổi chưa lưu mà rời trang → hỏi (§4.3).
2. Thành công → dải "Đã lưu cài đặt email.". 400 → liệt kê `errors`.

**Quy tắc liên quan** — BR-27; D13; `business/business-rules.md` §4.

---

### SCR-COM-03, SCR-COM-04

Chưa viết — xem bảng §3.

---

## 10. Còn mở

1. Gia sư có nhiều hồ sơ: khi ứng tuyển chọn hồ sơ nào hiện cho phụ huynh — viết ở SCR-TUT-05 (S03).
2. Phụ huynh có nhiều học sinh: bộ chọn học sinh dùng chung giữa các màn hình — viết ở
   SCR-PAR-01 (S02).
