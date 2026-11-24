# Yêu cầu chức năng

## 0. Về tài liệu này

Yêu cầu chức năng theo module. Mã `FR-01`–`FR-36` **giữ nguyên** như biểu mẫu OOAD (sheet P2_05)
để file kế hoạch và biểu mẫu truy vết được. Biểu mẫu chỉ có một dòng cho mỗi FR; file này là bản
đủ để code.

**Viết dần theo sprint.** Mỗi module được viết chi tiết trước sprint backend của nó một sprint
(thẻ `[Docs]` trong file kế hoạch). Module chưa viết chi tiết nằm ở §10: chỉ có mô tả từ biểu mẫu,
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
  API của module ADMIN-REVIEW (§7), Phụ huynh qua API của APPLY (FR-11).
- **API dự kiến:** `GET /api/tutor-profiles/mine` · `GET /api/tutor-profiles/{id}` ·
  `POST /api/tutor-profiles` → 201 · `PUT /api/tutor-profiles/{id}` ·
  `POST /api/tutor-profiles/{id}/set-default` · `GET /api/subjects` (danh mục môn, mọi vai trò).
- **Nghiệm thu:** AC-PROFILE-01 … AC-PROFILE-04 · **Màn hình:** SCR-TUT-01, SCR-TUT-02.

### FR-04 — Minh chứng và gửi duyệt hồ sơ
- **Tác nhân:** Gia sư (gửi), Admin (duyệt — FR-04 phần Admin ở §7)
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

## 6. Module REQUEST — Học sinh và tin tìm gia sư

### FR-05 — Học sinh và tin tìm gia sư
- **Tác nhân:** Phụ huynh (Admin xem qua FR-06) · **Ưu tiên:** Cao
- **Mô tả:** Phụ huynh khai báo học sinh rồi đăng tin tìm gia sư cho từng học sinh; tin chỉ hiện
  với gia sư sau khi Admin duyệt.
- **Luồng chính — học sinh:** thêm học sinh (họ tên, lớp đang học) → sửa khi cần. Không có xóa
  (CC-05).
- **Luồng chính — đăng tin:**
  1. Phụ huynh chọn học sinh, môn, cấp học, hình thức dạy, khu vực, số buổi/tuần, khoảng học
     phí/buổi, nhập yêu cầu với gia sư → gửi.
  2. Hệ thống kiểm BR-06, lưu tin ở `PendingReview` (tin không có bản nháp, US-05), báo
     `ModerationQueue` cho mọi Admin đang hoạt động.
  3. Admin duyệt hoặc từ chối (FR-06).
- **Luồng chính — sửa tin:** theo trạng thái hiện tại:

  | Trạng thái | Sửa được | Sau khi lưu |
  | :-- | :-- | :-- |
  | `PendingReview` | ✓ | Giữ `PendingReview` |
  | `Rejected` | ✓ | `PendingReview`, báo `ModerationQueue` cho Admin; lý do từ chối cũ giữ lại để Admin đối chiếu |
  | `Recruiting` | ✓ | `PendingReview`, báo `ModerationQueue` cho Admin, ẩn khỏi tìm kiếm tới khi duyệt lại; `expires_at` đặt lại khi duyệt (D33); phiếu ứng tuyển đã có giữ nguyên |
  | `Hired`, `Closed` | — → 409 | — |

- **Luồng chính — đóng tin:** chỉ `Recruiting → Closed`. Trong cùng transaction, phiếu ứng tuyển
  còn mở của tin chuyển theo §2.4 business-rules: `Pending`, `Viewed` → `Rejected`;
  `TrialInvited` → `NotHired`. Mỗi gia sư bị ảnh hưởng nhận thông báo `ApplicationStatus`. Tin đã
  đóng không mở lại.
- **Quy tắc:** BR-06, BR-22, BR-24; §2.3, §2.4 business-rules; D24, D33, D37.
- **Phân quyền & phạm vi:**
  - Chỉ Phụ huynh tạo, sửa, đóng; chỉ trên học sinh và tin của mình. `parent_id` lấy từ tài
    khoản đang đăng nhập (CC-04). Học sinh, tin của người khác → 404 "Không tìm thấy học sinh." /
    "Không tìm thấy tin.". `studentId` trong body không thuộc mình → 404 "Không tìm thấy học sinh.".
  - Học sinh: `fullName` 2–100 ký tự sau khi bỏ khoảng trắng hai đầu; `gradeLevel` số nguyên
    1–12 (lớp đang học).
  - Tin:
    - `subjectId` phải có trong danh mục `subjects` (BR-24); `educationLevel`, `teachingMode` đúng
      giá trị liệt kê §2.9.
    - Hình thức `Offline` hoặc `Both`: `province` thuộc danh mục D37, `ward` 1–100 ký tự.
      Hình thức `Online`: server bỏ qua `province`, `ward`, `address` client gửi và lưu `null`.
    - `address` (số nhà, đường) không bắt buộc, ≤ 200 ký tự; chỉ phụ huynh chủ tin và Admin xem
      được, không trả cho gia sư ở FR-07.
    - `sessionsPerWeek` 1–7; `minFee`, `maxFee` số nguyên 50.000–2.000.000, `minFee ≤ maxFee`.
    - `requirements` bắt buộc, ≤ 2000 ký tự sau khi bỏ khoảng trắng hai đầu.
    - Sai một trong các điều trên → 400, `errors` liệt kê từng trường.
  - `status`, `expires_at`, `reject_reason`, `submitted_at`, `reviewed_by`, `reviewed_at` do
    server đặt. Không có kiểm từ khóa tự động; tin đòi đặt cọc, phí giữ chỗ do Admin phát hiện và
    từ chối (BR-06, FR-06).
  - Không giới hạn số học sinh và số tin trong MVP.
- **API dự kiến:**
  - Học sinh: `GET /api/students/mine` (thêm trước lên trước) · `POST /api/students` → 201 ·
    `PUT /api/students/{id}`.
  - Tin: `GET /api/tutor-requests/mine?status=&studentId=&page=&pageSize=` (mới cập nhật trước;
    mỗi tin kèm `studentName`, `studentGradeLevel`, `subjectName`, `openApplicationCount`,
    `rejectReason`, `expiresAtUtc`) · `GET /api/tutor-requests/{id}` · `POST /api/tutor-requests`
    → 201 · `PUT /api/tutor-requests/{id}` · `POST /api/tutor-requests/{id}/close`.
  - `GET /api/tutor-requests/{id}` dùng chung ba vai trò, phạm vi khác nhau: Phụ huynh chỉ tin của
    mình; Admin mọi tin (FR-06); Gia sư chỉ tin `Recruiting` và không có `address`, thông tin phụ
    huynh (FR-07).
  - `openApplicationCount` = số phiếu `Pending` + `Viewed` + `TrialInvited` của tin.
- **Nghiệm thu:** AC-REQUEST-01 … AC-REQUEST-10 · **Màn hình:** SCR-PAR-01, SCR-PAR-02, SCR-PAR-03.

---

## 7. Module ADMIN-REVIEW — Duyệt hồ sơ và tin

Hai FR dưới đây cùng một khuôn: danh sách chờ duyệt cũ nhất trước → mở chi tiết → duyệt hoặc từ
chối kèm lý do. Admin chỉ duyệt, không sửa nội dung (BR-SCOPE-04).

### FR-04 (phần Admin) — Duyệt hồ sơ gia sư
- **Tác nhân:** Admin · **Ưu tiên:** Cao
- **Mô tả:** Admin đối chiếu nội dung và minh chứng của hồ sơ chờ duyệt, rồi duyệt để gia sư dùng
  hồ sơ ứng tuyển, hoặc từ chối kèm lý do để gia sư sửa và gửi lại. Phần gia sư gửi duyệt ở §4.
- **Luồng chính:**
  1. Admin xem danh sách hồ sơ `PendingReview`, gửi duyệt sớm nhất trước.
  2. Mở một hồ sơ: nội dung hồ sơ, minh chứng (URL ký 60 phút, D16), thông tin gia sư (họ tên,
     email, số điện thoại, trạng thái xác thực sinh viên — D36), lý do từ chối lần trước nếu có.
  3. Duyệt → `Approved`; hoặc từ chối kèm lý do → `Rejected`.
  4. Gia sư nhận thông báo `ModerationResult`; `audit_logs` ghi một dòng (BR-22).
- **Quy tắc:** BR-05, BR-22, BR-25; §2.1 business-rules; D16, D36.
- **Phân quyền & phạm vi:**
  - Chỉ Admin; vai trò khác → 403.
  - Duyệt hoặc từ chối hồ sơ không ở `PendingReview` → 409. Chuyển trạng thái là cập nhật có điều
    kiện (`api-conventions.md` §2.1): hai Admin xử lý cùng lúc thì chỉ một người thành công, người
    kia nhận 409.
  - Từ chối: `reason` bắt buộc, 1–500 ký tự sau khi bỏ khoảng trắng hai đầu → sai thì 400 (BR-05).
    Duyệt không nhận lý do và xóa `reject_reason` cũ.
  - `reviewed_by`, `reviewed_at` do server đặt.
  - Lọc `status` chỉ nhận `PendingReview`, `Approved`, `Rejected` (mặc định `PendingReview`);
    hồ sơ `Draft` không hiện với Admin → 400 khi lọc `Draft`.
- **API dự kiến:** `GET /api/tutor-profiles?status=&page=&pageSize=` (tab `PendingReview` sắp
  `submittedAtUtc` tăng dần; hai tab còn lại `reviewedAtUtc` giảm dần) ·
  `GET /api/tutor-profiles/{id}` (Admin xem mọi hồ sơ; Gia sư chỉ hồ sơ của mình — FR-03; kèm
  `evidences[].url` ký 60 phút và khối `tutor` gồm `fullName`, `email`, `phone`,
  `verificationStatus`) · `POST /api/tutor-profiles/{id}/approve` ·
  `POST /api/tutor-profiles/{id}/reject` `{ reason }`.
- **Nghiệm thu:** AC-ADMIN-REVIEW-01 … AC-ADMIN-REVIEW-04, AC-ADMIN-REVIEW-07 · **Màn hình:**
  SCR-ADM-02.

### FR-06 — Duyệt tin tìm gia sư
- **Tác nhân:** Admin · **Ưu tiên:** Cao
- **Mô tả:** Admin kiểm nội dung tin trước khi tin hiện với gia sư, từ chối tin ảo hoặc đòi đặt
  cọc, phí giữ chỗ.
- **Luồng chính:**
  1. Admin xem danh sách tin `PendingReview`, gửi duyệt sớm nhất trước.
  2. Mở một tin: toàn bộ nội dung kể cả `address`, học sinh (họ tên, lớp), phụ huynh (họ tên,
     email, số điện thoại), lý do từ chối lần trước nếu có.
  3. Duyệt → `Recruiting`, `expires_at = thời điểm duyệt + 30 ngày` (D33); hoặc từ chối kèm lý do
     → `Rejected`. Tin có yêu cầu đặt cọc, phí giữ chỗ, phí nhận lớp phải bị từ chối (BR-06).
  4. Phụ huynh nhận thông báo `ModerationResult`; `audit_logs` ghi một dòng.
- **Quy tắc:** BR-05, BR-06, BR-22; §2.3 business-rules; D33.
- **Phân quyền & phạm vi:** Như FR-04 phần Admin: chỉ Admin (403); tin không ở `PendingReview` →
  409, hai Admin cùng lúc chỉ một người thành công; lý do từ chối 1–500 ký tự (400); duyệt xóa
  `reject_reason` cũ; `reviewed_by`, `reviewed_at`, `expires_at` do server đặt. Lọc `status` nhận
  mọi giá trị §2.3 (mặc định `PendingReview`). Admin không có API sửa hay đóng tin.
- **API dự kiến:** `GET /api/tutor-requests?status=&page=&pageSize=` (tab `PendingReview` sắp
  `submittedAtUtc` tăng dần; tab khác `reviewedAtUtc` giảm dần) · `GET /api/tutor-requests/{id}`
  (Admin xem mọi tin, kèm khối `parent`) · `POST /api/tutor-requests/{id}/approve` ·
  `POST /api/tutor-requests/{id}/reject` `{ reason }`.
- **Nghiệm thu:** AC-ADMIN-REVIEW-05 … AC-ADMIN-REVIEW-07 · **Màn hình:** SCR-ADM-04.

---

## 8. Module SEARCH — Tìm tin, điểm phù hợp, lưu tin

### FR-07 — Tìm và lọc tin tìm gia sư
- **Tác nhân:** Gia sư · **Ưu tiên:** Cao
- **Mô tả:** Gia sư xem các tin đang tuyển, lọc theo môn, cấp học, khu vực, hình thức, học phí;
  mặc định tin phù hợp nhất lên đầu.
- **Luồng chính:** mở danh sách → chọn bộ lọc → hệ thống trả tin `Recruiting` khớp bộ lọc, mỗi tin
  kèm Matching Score (FR-08) → mở chi tiết một tin để ứng tuyển (FR-09) hoặc lưu (FR-34).
- **Bộ lọc** (đều không bắt buộc, kết hợp bằng AND):

  | Tham số | Ý nghĩa |
  | :-- | :-- |
  | `subjectId` | Đúng môn của tin |
  | `educationLevel` | Đúng cấp học của tin |
  | `teachingMode` | Chỉ nhận `Offline` (tin `Offline` hoặc `Both`) hoặc `Online` (tin `Online` hoặc `Both`) |
  | `province` | Tin có tỉnh/thành đó, **cộng** tin chỉ dạy `Online` (không gắn khu vực). Muốn bỏ tin online thì lọc thêm `teachingMode=Offline` |
  | `ward` | Chỉ dùng cùng `province`; khớp khi phường/xã của tin trùng sau khi chuẩn hóa như FR-08 |
  | `feeFrom`, `feeTo` | Khoảng `[minFee, maxFee]` của tin giao với khoảng lọc |
  | `sort` | `match` (mặc định): điểm giảm dần, cùng điểm thì duyệt mới nhất trước; `newest`: duyệt mới nhất trước |

- **Dữ liệu mỗi tin:** `id`, `subjectName`, `educationLevel`, `studentGradeLevel`, `teachingMode`,
  `province`, `ward`, `sessionsPerWeek`, `minFee`, `maxFee`, `requirements`, `approvedAtUtc`,
  `matchingScore` (số hoặc `null`), `isSaved`, `hasOpenApplication` (gia sư đang có phiếu
  `Pending`/`Viewed`/`TrialInvited` vào tin). **Không** trả họ tên học sinh, `address`, thông tin
  phụ huynh.
- **Quy tắc:** BR-07; D25, D37.
- **Phân quyền & phạm vi:**
  - Chỉ Gia sư; vai trò khác → 403. Chỉ tin `Recruiting` (BR-07).
  - Chi tiết `GET /api/tutor-requests/{id}` với Gia sư: tin không tồn tại hoặc không `Recruiting`
    → 404 "Không tìm thấy tin.". Chi tiết có thêm `matchingBreakdown { subject, area, fee }`.
  - Bộ lọc sai (`subjectId` không có trong danh mục, `province` ngoài D37, `teachingMode = Both`,
    `ward` khi thiếu `province`, `feeFrom > feeTo`, `sort` lạ, `pageSize` > 100) → 400.
  - Không có kết quả → 200, `items` rỗng (SSD-04).
- **API dự kiến:** `GET /api/tutor-requests/search?subjectId=&educationLevel=&teachingMode=&province=&ward=&feeFrom=&feeTo=&sort=&page=&pageSize=`
  → `{ items, page, pageSize, totalCount, scoringProfileId }` · `GET /api/tutor-requests/{id}`.
  `scoringProfileId` là hồ sơ dùng để tính điểm (FR-08), `null` khi không tính được.
- **Nghiệm thu:** AC-SEARCH-01, AC-SEARCH-02, AC-SEARCH-05, AC-SEARCH-08 · **Màn hình:**
  SCR-TUT-04, SCR-TUT-05 (viết ở S03).

### FR-08 — Matching Score
- **Tác nhân:** Hệ thống tính, Gia sư xem · **Ưu tiên:** Cao
- **Mô tả:** Điểm 0–100 giữa hồ sơ mặc định của gia sư và từng tin, để gia sư ưu tiên tin hợp với
  mình. Cách tính theo D25; mục này chốt các chi tiết D25 chưa nói.
- **Hồ sơ dùng để tính:** hồ sơ mặc định của gia sư, **chỉ khi** hồ sơ đó `Approved`. Không thỏa
  → `matchingScore = null` cho mọi tin và `sort=match` sắp như `newest`.
- **Cách tính** (cộng ba phần):

  | Phần | Điểm | Điều kiện |
  | :-- | :-- | :-- |
  | Môn | 50 | Môn của tin nằm trong các môn của hồ sơ; không thì 0 |
  | Khu vực | 30 | Hình thức của tin và của hồ sơ đều thuộc {`Online`, `Both`} |
  | | 30 | Không thỏa dòng trên, nhưng cùng `province` và `ward` của tin trùng một giá trị `teaching_wards` của hồ sơ sau khi chuẩn hóa |
  | | 15 | Chỉ cùng `province` |
  | | 0 | Còn lại |
  | Học phí | 20 | `minFee ≤ expected_fee_per_session ≤ maxFee` |
  | | 10 | Ngoài khoảng, nhưng lệch so với mốc gần nhất (`minFee` hoặc `maxFee`) không quá 20% của mốc đó |
  | | 0 | Còn lại |

  **Chuẩn hóa phường/xã:** bỏ khoảng trắng hai đầu, gộp khoảng trắng liên tiếp, chữ thường, bỏ dấu
  (`đ` → `d`), bỏ tiền tố `phường `, `xã `, `p. `, `p.` ở đầu. Ví dụ "Phường Bến Thành" và
  "  ben thanh" trùng nhau.

  **Ví dụ** — hồ sơ: Toán, Vật lý · `Both` · TP. Hồ Chí Minh · Phường Bến Thành · 200.000 ₫/buổi.

  | Tin | Môn | Khu vực | Học phí | Tổng |
  | :-- | :-- | :-- | :-- | :-- |
  | Toán · `Offline` · TP. Hồ Chí Minh, Phường Bến Thành · 150.000–250.000 | 50 | 30 | 20 | **100** |
  | Hóa học · `Offline` · TP. Hồ Chí Minh, Phường Sài Gòn · 100.000–180.000 | 0 | 15 | 10 (lệch 20.000 = 11% của 180.000) | **25** |
  | Tiếng Anh · `Online` · 220.000–300.000 | 0 | 30 | 10 (lệch 20.000 = 9% của 220.000) | **40** |
  | Toán · `Offline` · Hà Nội, Phường Cửa Nam · 300.000–400.000 | 50 | 0 | 0 (lệch 100.000 = 33%) | **50** |

- **Quy tắc:** D25, D37.
- **Phân quyền & phạm vi:** Điểm chỉ trả trong kết quả FR-07 cho gia sư đang gọi, tính trên hồ sơ
  của chính gia sư đó. Không lưu điểm, tính khi gọi API (bỏ tác vụ nền SSD-58). Không có API tính
  điểm cho hồ sơ khác hồ sơ mặc định, hay cho hồ sơ của người khác.
- **API dự kiến:** trong FR-07 (`matchingScore`, `matchingBreakdown`, `scoringProfileId`).
- **Nghiệm thu:** AC-SEARCH-03, AC-SEARCH-04 · **Màn hình:** SCR-TUT-04 (viết ở S03).

### FR-34 — Lưu tin để xem sau
- **Tác nhân:** Gia sư · **Ưu tiên:** Cao
- **Mô tả:** Gia sư lưu tin đang tuyển vào danh sách riêng và bỏ lưu khi không cần.
- **Luồng chính:** mở tin → Lưu → tin vào danh sách đã lưu; mở danh sách đã lưu → mở lại tin hoặc
  bỏ lưu.
- **Quy tắc:** BR-07; CC-05 (tin đã lưu là một trong hai thứ được xóa cứng).
- **Phân quyền & phạm vi:**
  - Chỉ Gia sư (403); chỉ danh sách của mình (`tutor_id` lấy từ tài khoản).
  - Lưu tin không tồn tại hoặc không `Recruiting` → 404 "Không tìm thấy tin." (SSD-50).
  - Lưu tin đã lưu → 200, không tạo dòng thứ hai. Bỏ lưu tin chưa lưu → 200.
  - Tin đã lưu rồi rời `Recruiting` vẫn nằm trong danh sách, với `isAvailable = false`; không trả
    trạng thái cụ thể của tin cho gia sư. Gia sư tự bỏ lưu, hệ thống không tự xóa.
- **API dự kiến:** `GET /api/saved-tutor-requests?page=&pageSize=` (lưu mới nhất trước; mỗi dòng
  có `savedAtUtc`, `isAvailable` và các trường tóm tắt của FR-07 trừ `matchingScore`) ·
  `PUT /api/saved-tutor-requests/{requestId}` · `DELETE /api/saved-tutor-requests/{requestId}`.
- **Nghiệm thu:** AC-SEARCH-06, AC-SEARCH-07, AC-SEARCH-08 · **Màn hình:** SCR-TUT-04, SCR-TUT-05
  (viết ở S03).

---

## 9. Module APPLY — Ứng tuyển và rút phiếu

FR-11 – FR-13 (phụ huynh xem ứng viên, mời dạy thử, nhận gia sư) viết ở S03, xem §10.

### FR-09 — Ứng tuyển
- **Tác nhân:** Gia sư · **Ưu tiên:** Cao
- **Mô tả:** Gia sư gửi phiếu ứng tuyển vào một tin đang tuyển, dùng một hồ sơ đã duyệt của mình.
- **Luồng chính:**
  1. Từ chi tiết tin, gia sư chọn một hồ sơ `Approved` của mình và viết lời giới thiệu → gửi.
  2. Hệ thống kiểm theo thứ tự dưới đây, tạo phiếu `Pending`, báo `NewApplication` cho phụ huynh
     chủ tin, ghi `audit_logs`.
  3. Gia sư theo dõi phiếu ở danh sách ứng tuyển của mình.
- **Quy tắc:** BR-07, BR-08, BR-10, BR-22; D21, D36.
- **Phân quyền & phạm vi:** kiểm theo thứ tự, gặp lỗi đầu tiên thì dừng:
  1. Không phải Gia sư → 403.
  2. `introduction` bắt buộc, 20–1000 ký tự sau khi bỏ khoảng trắng hai đầu → sai thì 400.
  3. Gia sư đang bị khóa tính năng ứng tuyển (BR-10, có hiệu lực khi FR-31 xong) → 403 kèm ngày
     hết khóa.
  4. Tin không tồn tại hoặc ở `PendingReview`/`Rejected` → 404 "Không tìm thấy tin.". Hồ sơ không
     tồn tại hoặc không thuộc mình → 404 "Không tìm thấy hồ sơ.".
  5. Tin ở `Hired`/`Closed` → 409 "Tin không còn nhận ứng tuyển.". Hồ sơ không `Approved` → 409
     "Chỉ ứng tuyển được bằng hồ sơ đã duyệt.".
  6. Gia sư đã có phiếu mở (`Pending`, `Viewed`, `TrialInvited`) vào tin này → 409 "Bạn đã ứng
     tuyển tin này.".
  7. Gia sư đã có 5 phiếu `Pending` + `Viewed` → 409 "Bạn đã có 5 phiếu đang chờ xử lý. Rút bớt
     phiếu hoặc chờ phụ huynh phản hồi.". Bước 6–7 và lệnh tạo phiếu chạy trong cùng transaction,
     khóa dòng `tutors` của gia sư (`SELECT … FOR UPDATE`) để hai request đồng thời không vượt hạn
     mức (D21).
  - `tutor_id`, `status`, thời điểm tạo do server đặt. Trạng thái xác thực sinh viên không chặn
    ứng tuyển (D36). Trạng thái nhận dạy của hồ sơ không chặn ứng tuyển.
  - Sau khi phiếu đóng (`Withdrawn`, `Rejected`, `NotHired`) gia sư ứng tuyển lại cùng tin được,
    vẫn qua đủ các bước trên (BR-08 chỉ cấm trùng phiếu mở).
- **API dự kiến:** `POST /api/tutor-applications` `{ requestId, profileId, introduction }` → 201
  `{ id, status }` · `GET /api/tutor-applications/mine?status=&page=&pageSize=` → `{ items, page,
  pageSize, totalCount, openCount }` (mới cập nhật trước; mỗi phiếu kèm `profileTitle`, tóm tắt
  tin như FR-07 và `requestAvailable`; `openCount` = số phiếu `Pending` + `Viewed`) ·
  `GET /api/tutor-applications/{id}` (chỉ phiếu của mình, ngoài phạm vi → 404).
- **Nghiệm thu:** AC-APPLY-01 … AC-APPLY-06, AC-APPLY-09 · **Màn hình:** SCR-TUT-05, SCR-TUT-06
  (viết ở S03).

### FR-10 — Rút phiếu ứng tuyển
- **Tác nhân:** Gia sư · **Ưu tiên:** Cao
- **Mô tả:** Gia sư rút phiếu khi phụ huynh chưa mời dạy thử.
- **Luồng chính:** mở danh sách ứng tuyển → chọn phiếu → xác nhận rút → phiếu `Withdrawn`, hạn
  mức 5 phiếu đang chờ được giải phóng (D21).
- **Quy tắc:** BR-09, BR-22; §2.4 business-rules; D21.
- **Phân quyền & phạm vi:**
  - Chỉ Gia sư (403); phiếu của gia sư khác → 404 "Không tìm thấy phiếu ứng tuyển.".
  - Phiếu không ở `Pending`/`Viewed` → 409 "Chỉ rút được phiếu đang chờ xử lý hoặc đã xem." Phiếu
    `TrialInvited` thì hai bên trao đổi qua chat (SSD-34).
  - Cập nhật có điều kiện: phụ huynh mời dạy thử cùng lúc gia sư rút thì chỉ một bên thành công.
  - Không gửi thông báo cho phụ huynh (`business-rules.md` §4 không có sự kiện này); danh sách ứng
    viên của phụ huynh hiện phiếu đã rút.
- **API dự kiến:** `POST /api/tutor-applications/{id}/withdraw`.
- **Nghiệm thu:** AC-APPLY-07 … AC-APPLY-09 · **Màn hình:** SCR-TUT-06 (viết ở S03).

---

## 10. Module chưa viết chi tiết

Mô tả lấy từ biểu mẫu P2_05 cùng các quyết định đã chốt. Cột "Viết ở" là sprint của thẻ `[Docs]`
viết bản chi tiết; chưa có bản chi tiết thì **chưa code**.

| FR | Module | Mô tả ngắn | Quyết định đã chốt | Viết ở |
| :-- | :-- | :-- | :-- | :-- |
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
