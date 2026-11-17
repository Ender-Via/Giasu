# DECISIONS — Nền tảng tìm việc gia sư (SE100 – Nhóm 01)

Mỗi quyết định có một mã `Dxx`. Code, commit, PR và tài liệu trích mã này thay vì giải thích lại.
Trong mọi tài liệu: **Lead** là SV1 Trần Quý Lộc (nhóm trưởng), **GitHub owner** là SV2 Nguyễn
Trí Kiệt (giữ repo và tài liệu). Chỉ GitHub owner thêm hoặc sửa quyết định. Thấy code và quyết
định mâu thuẫn thì báo GitHub owner, không tự chọn.

Bảng này cũng là nguồn cho sheet **P3D_03_QuyetDinhTK** của biểu mẫu OOAD. Các quyết định D20–D35
sửa mâu thuẫn trong biểu mẫu; mỗi quyết định đó được ghi thành một CR ở sheet **P2_07_ThayDoiYC**.

---

## 1. Nền tảng

### D01 — Kiến trúc
Khối đơn (monolith) **phân 4 lớp**: `Domain` ← `Application` ← `Infrastructure`, `API`.
Phụ thuộc đi một chiều; `Domain` không tham chiếu lớp nào. Frontend tách riêng, chỉ nói chuyện
với backend qua REST API.
- Lý do: đủ tách trách nhiệm cho môn OOAD, dễ học, dễ test; nhóm đã chạy mô hình này ở dự án Nhà trẻ.
- Đánh đổi: không scale độc lập từng phần.

### D02 — Repo và tài liệu
Một repo duy nhất gồm `backend/`, `frontend/`, `docs/`. Tài liệu nằm cùng repo để PR trích được
đúng phiên bản tài liệu. Chỉ GitHub owner sửa `docs/` (CODEOWNERS); GitHub owner được cấu hình bypass branch
protection để commit tài liệu thẳng lên `develop` bằng commit `docs: ...`.
GitHub owner cũng giữ git (nhánh, branch protection, merge `develop` → `main`), `CODEOWNERS` và biểu
mẫu OOAD trên Drive.

### D03 — Công nghệ
| Phần | Chọn |
| :-- | :-- |
| Backend | ASP.NET Core 10 Web API, EF Core 10, FluentValidation, Serilog, Swagger |
| Database | PostgreSQL trên Supabase, **cả nhóm dùng chung một database** |
| Frontend | Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS 4 |
| Gọi API | Axios (`apiClient`), TanStack Query, React Hook Form |
| Test | xUnit (`backend/GiaSu.Tests`), Postman Collection |

Không thêm package mới khi chưa hỏi GitHub owner.

### D04 — Khuôn response
Mọi response, kể cả lỗi, đều là `ApiResponse<T>`:
```json
{ "success": true, "data": { }, "message": null, "errors": null }
```
Lỗi validate: `errors` là danh sách message tiếng Việt. Frontend chỉ đọc lỗi qua `toApiError()`.

### D05 — Vai trò
Ba vai trò, claim `role` là hằng số tiếng Anh trong `GiaSu.Domain.Constants.Roles`:
`Admin` (id 1), `Tutor` (id 2, Sinh viên/Gia sư), `Parent` (id 3, Phụ huynh).
Học sinh **không** đăng nhập; là dữ liệu do Phụ huynh quản lý (xem D24).

### D06 — Xác thực
JWT HS256, sống 10 giờ, claim `sub`, `role`, `tv` (token version). `ActiveUserMiddleware` kiểm
mỗi request: tài khoản còn hoạt động, vai trò chưa đổi, `tv` khớp `users.token_version`.
Đăng xuất, đổi vai trò, khóa tài khoản đều tăng `token_version` để token cũ mất hiệu lực ngay.
Mật khẩu băm bằng `PasswordHasher<T>` (NFR-02). Frontend giữ token trong bộ nhớ, `localStorage`
chỉ để khôi phục phiên.

### D07 — Phạm vi dữ liệu: 404 chứ không phải 403
Đúng vai trò nhưng bản ghi không thuộc mình (tin của phụ huynh khác, lộ trình của người khác)
→ **404**. Sai vai trò → **403**. Không để người dùng dò được bản ghi nào tồn tại.
Phạm vi lấy từ `sub` trong token, không bao giờ từ id client gửi lên.

### D08 — Chống dò mật khẩu
`POST /api/auth/login` giới hạn **5 lần/phút/IP** (trả 429). Thay cho quy tắc "khóa tài khoản
15 phút sau 5 lần sai" trong SSD-01/SSD-27 (khóa tài khoản để người khác cố tình khóa hộ được).

### D09 — Header bảo mật
Mọi response có `X-Content-Type-Options: nosniff` và `X-Frame-Options: DENY`.

### D10 — CI
GitHub Actions (`.github/workflows/ci.yml`) chạy cho mọi PR: backend `build -warnaserror` +
`dotnet test`, frontend `lint` + `build`. PR chỉ merge khi CI xanh.

### D11 — Migration
SV3 (DB) chốt ERD ở Sprint 01. Sau đó người làm module backend tự tạo migration cho bảng của
module mình, nhưng:
- trước khi tạo phải `git merge develop` để snapshot mới nhất; mỗi lúc chỉ **một** migration chưa
  merge trên toàn nhóm — báo trong group trước khi tạo;
- migration do người backend còn lại duyệt trong PR (SV1 ↔ SV3);
- chỉ chạy lên DB dùng chung **sau khi** PR đã merge vào `develop`, người chạy là tác giả PR.

**SV1 Lộc quản trị project Supabase**: tạo DB, cấp connection string riêng từng người, thu hồi khi
cần. Ai cần quyền gì trên Supabase thì xin SV1.

App không tự chạy migration. Không bao giờ `database drop` hay `database update` về migration cũ
trên DB dùng chung.

---

## 2. Cắt phạm vi MVP

### D12 — Chat
Không dùng WebSocket. Tin nhắn lưu DB, frontend **polling 5 giây** khi đang mở hội thoại.
Bỏ SSD-37 (mất kết nối Socket).

### D13 — Email
Thông báo trong ứng dụng là kênh chính. Email đi qua `IEmailSender`; bản MVP chỉ **ghi log**,
không gửi thật. Cấu hình bật/tắt từng loại email vẫn lưu đầy đủ (FR-32).

### D14 — Thanh toán
Không tích hợp cổng thanh toán. Phụ huynh **ghi nhận** đã thanh toán (tiền mặt hoặc chuyển khoản
kèm mã giao dịch), gia sư xác nhận đã nhận. Ghi nhận hai lần cùng một kỳ chỉ tạo một bản ghi
(NFR-03).

### D15 — Tác vụ định kỳ
Dùng `BackgroundService` của .NET, chạy mỗi giờ: nhắc gia hạn tin 30 ngày (FR-35), tự xác nhận
buổi học sau 48 giờ (D27), cảnh báo lệch tiến độ (FR-23), nhắc học phí quá hạn (FR-26), nhắc lịch
học, tính lại điểm uy tín. Không dùng Hangfire/Quartz.

### D16 — Tệp minh chứng
Lưu ở Supabase Storage, bucket **private**, chỉ trả URL ký hạn 60 phút sau khi kiểm phạm vi.
Mỗi tệp ≤ 5 MB, chỉ JPG/PNG/PDF.

### D17 — Ngoài phạm vi MVP
Xuất PDF báo cáo tiến độ (bỏ SSD-43), tin nổi bật trả phí, ký quỹ học phí, ngân hàng đề,
quét nội dung chat tự động bằng từ khóa (SSD-36 chỉ còn: người dùng báo cáo tin nhắn).

---

## 3. Đặt tên (thống nhất biểu mẫu)

### D18 — Tên lớp/bảng dùng chung cho code và tài liệu
| Khái niệm | Tên trong code | Bảng | Ghi chú |
| :-- | :-- | :-- | :-- |
| Tin tìm gia sư | `TutorRequest` | `tutor_requests` | bỏ tên "Tutor Job" |
| Phiếu ứng tuyển | `TutorApplication` | `tutor_applications` | không dùng `Application` vì trùng tên project `GiaSu.Application` |
| Lộ trình học | `LearningRoadmap` | `learning_roadmaps` | bỏ tên "LearningPath" |
| Kế hoạch theo tuần | `RoadmapPlanItem` | `roadmap_plan_items` | thay "LearningPlan" |
| Buổi học | `ClassSession` | `class_sessions` | SSD đang ghi "Lesson" → đổi theo |
| Bài kiểm tra | `Assessment` | `assessments` | |
| Báo cáo tiến độ | `ProgressReport` | `progress_reports` | |
| Kỳ học phí | `TuitionInvoice` | `tuition_invoices` | |
| Giao dịch | `Payment` | `payments` | |
| Đánh giá | `Review` | `reviews` | |
| Báo cáo vi phạm | `ViolationReport` | `violation_reports` | |

Giá trị trạng thái lưu chuỗi tiếng Anh PascalCase (`PendingReview`), frontend hiển thị tiếng Việt.

### D19 — Lớp miền bổ sung
Thêm vào Domain Model (sheet P3A_03): `Student`, `TutorProfileEvidence`, `StudentVerification`,
`SavedTutorRequest`, `RescheduleRequest`, `Notification`, `NotificationPreference`,
`AccountSanction`, `ReputationFlag`. Chi tiết ở `data-model.md`.

---

## 4. Quy tắc nghiệp vụ chốt lại (sửa mâu thuẫn biểu mẫu)

### D20 — Phạm vi so với P1_01
Chat (FR-14) và xác thực sinh viên (FR-02) **nằm trong** phạm vi. Xóa hai mục này khỏi
"Ngoài phạm vi" của P1_01. Xuất PDF vẫn ngoài phạm vi (D17).

### D21 — Giới hạn phiếu ứng tuyển
"Phiếu đang chờ" = phiếu ở trạng thái `Pending` hoặc `Viewed`. Mỗi gia sư tối đa **5** phiếu
đang chờ (FR-09). Kiểm trong cùng transaction với lệnh tạo phiếu để hai request đồng thời không
vượt hạn mức. Rút phiếu (`Withdrawn`) giải phóng hạn mức.

### D22 — Đổi lịch buổi học
Theo FR-20: **mỗi bên** đề nghị đổi lịch tối đa **1 lần** cho cùng một buổi; đề nghị phải gửi
trước giờ học **ít nhất 2 giờ**. Bên kia chấp nhận thì đổi lịch, từ chối thì giữ lịch cũ. Một bên
cần đổi lần thứ hai → buổi chuyển `Cancelled`. Sửa SSD-10, SSD-40 theo quy tắc này.

### D23 — Chế tài vi phạm
Theo FR-31: 2 vi phạm trong 6 tháng → cảnh cáo; vi phạm thứ 3 → khóa tính năng ứng tuyển/đăng tin
**30–90 ngày** (Admin chọn); vi phạm nghiêm trọng → khóa vĩnh viễn. Sửa SSD-13 (đang ghi 7–30 ngày).

### D24 — Học sinh
Phụ huynh tạo hồ sơ `Student` (họ tên, lớp đang học) trước khi đăng tin. Mỗi tin và mỗi lộ trình
gắn một học sinh. Một quan hệ gia sư–học sinh có đúng một lộ trình (FR-15).

### D25 — Matching Score (FR-08)
Thang 0–100: **môn khớp 50** + **khu vực khớp 30** (cùng quận/huyện 30, cùng tỉnh 15)
+ **học phí 20** (mức gia sư mong muốn nằm trong khoảng của tin 20, lệch ≤ 20% thì 10).
Tính khi gọi API tìm kiếm, không lưu sẵn; bỏ tác vụ nền SSD-58.

### D26 — Chat mở khi nào
Chỉ mở hội thoại khi phiếu ứng tuyển ở `Viewed`, `TrialInvited` hoặc `Hired`, hoặc khi đã có lộ
trình. Mỗi phiếu ứng tuyển một hội thoại.

### D27 — Xác nhận buổi học
Phụ huynh xác nhận hoặc khiếu nại trong **48 giờ** sau giờ kết thúc; quá hạn hệ thống tự xác nhận
(giữ SSD-09/SSD-39, bổ sung vào FR-19). Chỉ buổi `Completed` được tính học phí (NFR-03).

### D28 — Học phí
Trả sau: mỗi tháng là một kỳ; số tiền = số buổi `Completed` trong tháng × học phí/buổi đã chốt
trong lộ trình. Hạn thanh toán = ngày 7 tháng sau; quá hạn → `Overdue` và nhắc. Vì trả sau nên
không có tiền trả trước để hoàn: phần "hoàn học phí chưa dạy" của FR-26 **không áp dụng** (CR).

### D29 — Đánh giá
Được đánh giá khi lộ trình có ≥ 1 buổi `Completed` (FR-27). 1–5 sao, nhận xét ≤ 1000 ký tự,
mỗi bên đánh giá một lần cho mỗi lộ trình, người được đánh giá phản hồi một lần. Đánh giá hiển
thị ngay; bỏ quy tắc 14 ngày của SSD-12.

### D30 — Điểm uy tín (FR-28)
Thang 0–100 = `50 × (sao trung bình / 5)` + `30 × tỷ lệ buổi hoàn thành` + `20 × (1 − min(số lần
bị xử lý vi phạm, 5) / 5)`. Chưa có đánh giá thì phần sao tính 0,8. Tính lại khi có đánh giá mới
hoặc vi phạm mới, và mỗi đêm (D15).

### D31 — Gắn cờ (FR-29)
Tạo cờ cho Admin khi gia sư có ≥ 5 đánh giá và > 30% là 1 sao, hoặc bị báo cáo loại `Fraud`.
Cờ không tự khóa tài khoản; Admin quyết định.

### D32 — Trạng thái dùng chung
Danh sách trạng thái chính thức ở `business-rules.md` §2. Không tự thêm trạng thái mới
(ví dụ "Bản nháp" trong SSD-02, "Không hợp lệ" trong SSD-56) khi chưa có trong danh sách đó.

### D33 — Tin hết hạn
Tin `Recruiting` có `expires_at = duyệt + 30 ngày`. Đến hạn chưa tuyển: nhắc phụ huynh (FR-35).
Gia hạn: cộng thêm 30 ngày. Sửa nội dung tin đã duyệt → quay lại `PendingReview`.

### D34 — Lộ trình
Gia sư tạo lộ trình (`Draft`) → gửi (`PendingParent`) → phụ huynh đồng ý (`Active`) hoặc yêu cầu
sửa (`Draft`, kèm góp ý). Bỏ trạng thái "Thảo luận" của SSD-08.

### D35 — Báo cáo tiến độ (FR-22)
Hệ thống tự tổng hợp theo **tuần** (Chủ nhật hằng tuần) cho mỗi lộ trình `Active`; gia sư có thể
tạo thêm theo khoảng ngày tùy chọn. Cảnh báo lệch tiến độ khi kế hoạch tuần đã qua ≥ 2 tuần mà
nội dung chưa đánh dấu hoàn thành (FR-23).
