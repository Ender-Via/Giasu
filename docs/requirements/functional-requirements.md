# Yêu cầu chức năng

## 0. Về tài liệu này

Yêu cầu chức năng theo module. Mã `FR-01`–`FR-36` **giữ nguyên** như biểu mẫu OOAD (sheet P2_05)
để file kế hoạch và biểu mẫu truy vết được. Biểu mẫu chỉ có một dòng cho mỗi FR; file này là bản
đủ để code.

**Viết dần theo sprint.** Mỗi module được viết chi tiết trước sprint backend của nó một sprint
(thẻ `[Docs]` trong file kế hoạch). Module chưa viết chi tiết nằm ở §9: chỉ có mô tả từ biểu mẫu,
**chưa được code** cho tới khi có bản chi tiết.

Khuôn mỗi FR:

- **Tác nhân** · **Ưu tiên** (Cao / Trung bình / Thấp, theo biểu mẫu).
- **Mô tả** — một câu.
- **Luồng chính** — các bước.
- **Quy tắc** — mã BR, D áp dụng; trạng thái hợp lệ ở `business/business-rules.md` §2.
- **Phân quyền & phạm vi** — ai gọi được, ngoài phạm vi trả gì, giá trị nào server tự đặt.
- **API dự kiến** — route theo `api/api-conventions.md`; tên có thể đổi khi backend làm xong,
  bản đã có ghi ở `api/da-trien-khai.md`.
- **Nghiệm thu** — mã AC ở `acceptance-criteria.md`. **Màn hình** — mã SCR ở
  `frontend/ui-screens.md`.

---

## 1. Quy tắc xuyên suốt

- **CC-01 — Theo vai trò:** chức năng chỉ dành cho tác nhân được liệt kê; vai trò khác → 403.
  Ma trận đầy đủ: `business/user-roles.md` §3.
- **CC-02 — Không tự mở rộng:** chức năng không có trong tài liệu này thì không làm (D17).
- **CC-03 — Backend là nơi quyết định:** vai trò, phạm vi, dữ liệu vào đều kiểm lại ở mỗi request
  (BR-SCOPE-01). Giao diện ẩn nút không phải là chặn.
- **CC-04 — Giá trị server tự đặt, không nhận từ client:** người thao tác, chủ sở hữu bản ghi,
  thời điểm tạo/duyệt/gửi, trạng thái, `expires_at`, số tiền học phí, người nhận thông báo.
- **CC-05 — Không xóa cứng dữ liệu nghiệp vụ.** "Quản lý" = Tạo + Sửa + Xem. Chỉ có hai thao tác
  gỡ: minh chứng của hồ sơ chưa duyệt (BR-26) và tin đã lưu (FR-34).

---

## 2. Module AUTH — Tài khoản

### FR-01 — Đăng ký, đăng nhập, đăng xuất theo vai trò
- **Tác nhân:** Khách (đăng ký), mọi vai trò (đăng nhập, đăng xuất) · **Ưu tiên:** Cao
- **Mô tả:** Sinh viên và phụ huynh tự tạo tài khoản; mọi người đăng nhập bằng email và mật khẩu
  và chỉ dùng được chức năng của vai trò mình.
- **Luồng chính — đăng ký:** khách chọn vai trò Gia sư hoặc Phụ huynh → nhập họ tên, số điện
  thoại, email, mật khẩu, đồng ý quy chế → hệ thống tạo tài khoản đang hoạt động cùng hồ sơ vai
  trò (`tutors` hoặc `parents`) và ánh xạ `users.auth_user_id` → giao diện tự đăng nhập. Phần này
  thuộc thẻ S01-04, chưa triển khai trong nền FastAPI.
- **Luồng chính — đăng nhập:** Next.js gửi email + mật khẩu tới Supabase Auth, nhận access token,
  gọi `GET /api/auth/me`; backend xác minh token và trả vai trò nghiệp vụ → giao diện chuyển cổng.
- **Luồng chính — đăng xuất:** frontend kết thúc phiên Supabase local và xóa access token khỏi
  bộ nhớ; access token đã phát hết hiệu lực theo `exp` (D06).
- **Quy tắc:** BR-01; D05, D06, D08.
- **Phân quyền & phạm vi:**
  - Đăng ký và đăng nhập là hai luồng **duy nhất** không cần Bearer token; Supabase Auth giới hạn
    5 lần/phút/IP theo cấu hình project (D08).
  - Vai trò ngoài `Tutor`, `Parent` khi đăng ký → 400. Email đã có → **409** "Email đã được sử
    dụng.".
  - Sai email, sai mật khẩu, tài khoản bị khóa: **cùng** 401 "Email hoặc mật khẩu không đúng.".
  - Không có "quên mật khẩu" trong MVP (D17).
- **API dự kiến:** Supabase Auth `signInWithPassword`/`signOut` · `GET /api/auth/me` (đã có) ·
  đăng ký và tạo hồ sơ nghiệp vụ ở S01-04 (chưa triển khai).
- **Nghiệm thu:** AC-AUTH-01 … AC-AUTH-08 · **Màn hình:** SCR-AUTH-01, SCR-AUTH-02.

---

## 3. Module VERIFY — Xác thực sinh viên

### FR-02 — Xác thực sinh viên
- **Tác nhân:** Gia sư (gửi), Admin (duyệt) · **Ưu tiên:** Cao
- **Mô tả:** Gia sư nộp minh chứng là sinh viên; Admin đối chiếu và cấp huy hiệu "Đã xác thực".
- **Luồng chính:**
  1. Gia sư nhập tên trường, mã số sinh viên, tải lên đúng 1 tệp minh chứng (ảnh thẻ sinh viên
     hoặc giấy xác nhận sinh viên) → yêu cầu ở `Pending`.
  2. Admin xem danh sách yêu cầu `Pending` (cũ nhất trước), mở một yêu cầu, xem tệp qua URL ký.
  3. Admin duyệt → `Verified`, hoặc từ chối kèm lý do → `Rejected`. Gia sư nhận thông báo.
- **Quy tắc:** BR-03, BR-05; §2.2 của business-rules; D16, D36.
- **Phân quyền & phạm vi:**
  - Gia sư chỉ xem yêu cầu của mình: `mine` lấy theo `sub`, không nhận id; API theo id chỉ dành
    cho Admin. Đang có yêu cầu `Pending` hoặc đã `Verified` mà gửi tiếp → 409.
  - Tên trường 2–150 ký tự; mã số sinh viên 3–20 ký tự, chỉ chữ và số. Tệp ≤ 5 MB, JPG/PNG/PDF.
  - Admin duyệt hoặc từ chối yêu cầu không ở `Pending` → 409. Từ chối thiếu lý do hoặc lý do quá
    500 ký tự → 400 (BR-05).
  - Người duyệt và thời điểm duyệt do server đặt.
- **API dự kiến:**
  - Gia sư: `GET /api/student-verifications/mine` (yêu cầu gần nhất, hoặc `data: null`) ·
    `POST /api/student-verifications` (multipart: `university`, `studentCode`, `file`) → 201.
  - Admin: `GET /api/student-verifications?status=&page=&pageSize=` ·
    `GET /api/student-verifications/{id}` (kèm `evidenceUrl` ký 60 phút) ·
    `POST /api/student-verifications/{id}/approve` · `POST /api/student-verifications/{id}/reject`
    `{ reason }`.
- **Nghiệm thu:** AC-VERIFY-01 … AC-VERIFY-07 · **Màn hình:** SCR-TUT-03, SCR-ADM-03.

---

## 4. Module PROFILE — Hồ sơ gia sư

### FR-03 — Nhiều hồ sơ gia sư, một hồ sơ mặc định
- **Tác nhân:** Gia sư · **Ưu tiên:** Cao
- **Mô tả:** Gia sư tạo tối đa 5 hồ sơ theo nhóm môn/cấp học và chọn một hồ sơ làm mặc định.
- **Luồng chính:** tạo hồ sơ (lưu ở `Draft`) → sửa → đặt một hồ sơ làm mặc định.
- **Quy tắc:** BR-02, BR-04, BR-23, BR-24, BR-25.
- **Phân quyền & phạm vi:** Chỉ hồ sơ của mình; hồ sơ người khác → 404. Hồ sơ thứ 6 → 409. Sửa hồ
  sơ `PendingReview` → 409. Hồ sơ đầu tiên tự là mặc định; đặt mặc định hồ sơ khác thì bỏ mặc
  định hồ sơ cũ trong cùng transaction. Các API ở đây chỉ dành cho Gia sư; Admin xem hồ sơ qua
  API của module ADMIN-REVIEW (viết ở S02), Phụ huynh qua API của APPLY (FR-11).
- **API dự kiến:** `GET /api/tutor-profiles/mine` · `GET /api/tutor-profiles/{id}` ·
  `POST /api/tutor-profiles` → 201 · `PUT /api/tutor-profiles/{id}` ·
  `POST /api/tutor-profiles/{id}/set-default` · `GET /api/subjects` (danh mục môn, mọi vai trò).
- **Nghiệm thu:** AC-PROFILE-01 … AC-PROFILE-04 · **Màn hình:** SCR-TUT-01, SCR-TUT-02.

### FR-04 — Minh chứng và gửi duyệt hồ sơ
- **Tác nhân:** Gia sư (gửi), Admin (duyệt — xem module ADMIN-REVIEW, viết chi tiết ở S02)
  · **Ưu tiên:** Cao
- **Mô tả:** Gia sư đính kèm minh chứng năng lực rồi gửi hồ sơ cho Admin duyệt.
- **Luồng chính:** tải lên minh chứng (bảng điểm, chứng chỉ, giấy khen) → gửi duyệt → hồ sơ
  `PendingReview` → Admin nhận thông báo.
- **Quy tắc:** BR-03, BR-04, BR-26; D16.
- **Phân quyền & phạm vi:** Thêm/gỡ minh chứng khi hồ sơ không ở `Draft`/`Rejected` → 409. Quá
  5 tệp → 409; tệp sai định dạng hay quá 5 MB → 400. Gửi duyệt khi thiếu điều kiện BR-04 → 400 kèm
  danh sách điều còn thiếu trong `errors`. Gửi duyệt hồ sơ không ở `Draft`/`Rejected` → 409.
  Gia sư chỉ nhận lại URL ký của tệp thuộc hồ sơ của mình.
- **API dự kiến:** `POST /api/tutor-profiles/{id}/evidences` (multipart, trường `files`, 1–5 tệp)
  → 201 · `DELETE /api/tutor-profiles/{id}/evidences/{evidenceId}` ·
  `POST /api/tutor-profiles/{id}/submit`.
- **Nghiệm thu:** AC-PROFILE-05 … AC-PROFILE-08 · **Màn hình:** SCR-TUT-02.

### FR-36 — Trạng thái sẵn sàng nhận dạy
- **Tác nhân:** Gia sư · **Ưu tiên:** Cao
- **Mô tả:** Gia sư đặt mỗi hồ sơ ở `Accepting`, `Full` hoặc `Paused`.
- **Quy tắc:** §2.1 business-rules; BR-25 (không phải duyệt lại).
- **Phân quyền & phạm vi:** Chỉ hồ sơ của mình; giá trị khác ba giá trị trên → 400. Đổi được ở mọi
  trạng thái duyệt; chỉ có tác dụng hiển thị khi hồ sơ `Approved`.
- **API dự kiến:** `PUT /api/tutor-profiles/{id}/availability` `{ availability }`.
- **Nghiệm thu:** AC-PROFILE-09 · **Màn hình:** SCR-TUT-01.

---

## 5. Module NOTI — Thông báo

### FR-32 — Thông báo trong ứng dụng và cấu hình email
- **Tác nhân:** Mọi vai trò · **Ưu tiên:** Cao
- **Mô tả:** Hệ thống tạo thông báo khi có sự kiện ở `business-rules.md` §4; người dùng xem, đánh
  dấu đã đọc, và bật/tắt email từng loại.
- **Luồng chính:** module nghiệp vụ gọi `INotificationService.NotifyAsync(recipientId, type,
  title, message, link)` → service ghi `notifications` → nếu người nhận bật email loại đó thì gọi
  `IEmailSender` (MVP chỉ ghi log — D13).
- **Quy tắc:** BR-27; D13.
- **Phân quyền & phạm vi:**
  - Chỉ xem và đánh dấu thông báo của chính mình; thông báo người khác → 404.
  - Không có API cho client **tạo** thông báo.
  - Mặc định mọi loại email **bật**; chưa có dòng `notification_preferences` coi như bật.
  - `link` là đường dẫn tương đối trong frontend (ví dụ `/tutor/profiles`), không phải URL ngoài.
- **API dự kiến:** `GET /api/notifications?unreadOnly=&page=&pageSize=` →
  `{ items, page, pageSize, totalCount }` · `GET /api/notifications/unread-count` → `{ count }` ·
  `POST /api/notifications/{id}/read` · `POST /api/notifications/read-all` ·
  `GET /api/notification-preferences` · `PUT /api/notification-preferences`
  `{ items: [{ type, emailEnabled }] }`.
- **Nghiệm thu:** AC-NOTI-01 … AC-NOTI-05 · **Màn hình:** SCR-COM-01, SCR-COM-02.

---

## 9. Module chưa viết chi tiết

Mô tả lấy từ biểu mẫu P2_05 cùng các quyết định đã chốt. Cột "Viết ở" là sprint của thẻ `[Docs]`
viết bản chi tiết; chưa có bản chi tiết thì **chưa code**.

| FR | Module | Mô tả ngắn | Quyết định đã chốt | Viết ở |
| :-- | :-- | :-- | :-- | :-- |
| FR-05 | REQUEST | Phụ huynh tạo học sinh và tin tìm gia sư | D24, D33, BR-06 | S02 |
| FR-06 | ADMIN-REVIEW | Admin duyệt tin trước khi công khai | BR-05, D33 | S02 |
| FR-04 (Admin) | ADMIN-REVIEW | Admin duyệt hồ sơ gia sư | BR-05, BR-25 | S02 |
| FR-07 | SEARCH | Tìm và lọc tin theo môn, khu vực, học phí | BR-07 | S02 |
| FR-08 | SEARCH | Matching Score giữa hồ sơ và tin | D25 | S02 |
| FR-34 | SEARCH | Lưu tin để xem sau | — | S02 |
| FR-09, FR-10 | APPLY | Ứng tuyển, rút phiếu, tối đa 5 phiếu đang chờ | D21, BR-08..10 | S02 |
| FR-11 – FR-13 | APPLY | Phụ huynh xem ứng viên, mời dạy thử, nhận/không nhận | §2.4 business-rules | S03 |
| FR-14 | CHAT | Chat theo phiếu ứng tuyển, polling | D12, D26 | S03 |
| FR-30 | VIOLATION | Gửi báo cáo vi phạm kèm minh chứng | BR-20 | S03 |
| FR-35 | REQUEST | Nhắc và gia hạn tin sau 30 ngày | D15, D33 | S03 |
| FR-31 | VIOLATION | Admin xử lý, chế tài | D23, BR-21 | S04 |
| FR-15 – FR-17 | ROADMAP | Lộ trình, kế hoạch tuần, phụ huynh đồng ý | D34, BR-11, BR-12 | S04 |
| FR-18 – FR-20 | SESSION | Ghi nhận buổi, xác nhận/khiếu nại, đổi lịch | D22, D27, BR-13..15 | S05 |
| FR-21 | PROGRESS | Bài kiểm tra, nhập điểm | BR-16 | S05 |
| FR-22, FR-23 | PROGRESS | Báo cáo tiến độ tuần, cảnh báo lệch | D35 | S06 |
| FR-24 – FR-26 | TUITION | Kỳ học phí, ghi nhận thanh toán, quá hạn | D14, D28, BR-17, BR-18 | S06 |
| FR-27 – FR-29 | REVIEW | Đánh giá, điểm uy tín, gắn cờ | D29–D31, BR-19 | S07 |
| FR-33 | DASH | Thống kê quản trị | — | S07 |
