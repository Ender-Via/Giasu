# Tiêu chí nghiệm thu

## 0. Về tài liệu này

Mỗi tiêu chí là một kịch bản **Cho trước / Khi / Thì** kiểm được bằng một thao tác cụ thể (Postman,
xUnit hoặc bấm tay). Dùng cho ba việc:

- Backend viết unit test và request Postman theo AC của thẻ.
- Frontend tự kiểm màn hình theo AC ghi ở dòng "Yêu cầu" của mục SCR.
- Mô tả PR, mục "Đã test thế nào", liệt kê theo mã AC (`testing/testing-strategy.md` §0.2).
  Cuối kỳ, SV4 chép sang sheet P4T_01 thành TC.

Quy ước:

- Mã `AC-<MODULE>-<số>`; số đã cấp không dùng lại.
- Mọi phản hồi, kể cả lỗi, theo khuôn `ApiResponse<T>` (D04) — ngầm hiểu cho mọi tiêu chí.
- Tiêu chí bảo mật viết ở dạng phủ định (sai vai trò, ngoài phạm vi, giá trị client không được
  quyết), vì đó là cách chứng minh kiểm soát có thật.
- Dòng **Truy vết** ghi theo thứ tự `FR | BR/D | UC | NFR`.

AC của module chưa viết chi tiết (`functional-requirements.md` §9) được thêm cùng thẻ `[Docs]` viết
module đó.

---

## 1. AUTH — Tài khoản

### AC-AUTH-01 — Đăng ký thành công
- **Cho trước:** Email `sv.moi@example.com` chưa có trong hệ thống.
- **Khi:** Gửi đăng ký vai trò `Tutor` với họ tên, số điện thoại `0912345678`, mật khẩu `MatKhau123`, `acceptTerms = true`.
- **Thì:** 201; có một dòng `users` vai trò Gia sư, đang hoạt động, mật khẩu không lưu dạng thô; có một dòng `tutors` với `verification_status = Unverified`. Đăng nhập bằng email và mật khẩu đó thành công.
- **Truy vết:** FR-01 | BR-01 | UC-01 | NFR-02

### AC-AUTH-02 — Đăng ký sai dữ liệu
- **Cho trước:** Lần lượt: (a) mật khẩu `12345678` không có chữ; (b) số điện thoại `123`; (c) `acceptTerms = false`; (d) vai trò `Admin`; (e) họ tên 1 ký tự.
- **Khi:** Gửi đăng ký với từng trường hợp.
- **Thì:** Cả năm đều 400 với `errors` tiếng Việt chỉ đúng trường sai; không tạo tài khoản nào.
- **Truy vết:** FR-01 | BR-01 | UC-01 | NFR-06

### AC-AUTH-03 — Email đã dùng
- **Cho trước:** Đã có tài khoản `Giasu@Example.com`.
- **Khi:** Đăng ký với `giasu@example.com` (khác hoa thường).
- **Thì:** 409 "Email đã được sử dụng."; không tạo tài khoản.
- **Truy vết:** FR-01 | BR-01 | UC-01

### AC-AUTH-04 — Đăng nhập sai không lộ lý do
- **Cho trước:** (a) email không tồn tại; (b) email đúng, sai mật khẩu; (c) tài khoản đã bị khóa.
- **Khi:** Đăng nhập với từng trường hợp.
- **Thì:** Cả ba trả 401 với **cùng** câu "Email hoặc mật khẩu không đúng."; không cấp token.
- **Truy vết:** FR-01 | D06 | UC-01 | NFR-02

### AC-AUTH-05 — Giới hạn tần suất
- **Cho trước:** Một IP đã gọi `POST /api/auth/login` 5 lần trong 1 phút.
- **Khi:** Gọi lần thứ 6 trong cùng phút, kể cả đúng mật khẩu. Lặp lại với `POST /api/auth/register`.
- **Thì:** 429, body theo `ApiResponse<T>`; không cấp token, không tạo tài khoản.
- **Truy vết:** FR-01 | D08 | UC-01 | NFR-02

### AC-AUTH-06 — Sai vai trò bị chặn
- **Cho trước:** Token của một Phụ huynh.
- **Khi:** Gọi một API chỉ dành cho Gia sư (`GET /api/tutor-profiles/mine`) và một API chỉ dành cho Admin (`GET /api/student-verifications`).
- **Thì:** Cả hai 403 "Bạn không có quyền thực hiện hành động này."; không trả dữ liệu.
- **Truy vết:** FR-01 | BR-SCOPE-05 | UC-01 | NFR-02

### AC-AUTH-07 — Không có token hợp lệ
- **Cho trước:** Một API bất kỳ ngoài đăng ký và đăng nhập.
- **Khi:** Gọi (a) không có token; (b) token hết hạn; (c) token sửa claim `role` thành `Admin`.
- **Thì:** Cả ba 401; không thực hiện thao tác.
- **Truy vết:** FR-01 | D06 | UC-01 | NFR-02

### AC-AUTH-08 — Đăng xuất làm token cũ hết hiệu lực
- **Cho trước:** Gia sư đã đăng nhập, đã chép token ra Postman.
- **Khi:** Gọi `POST /api/auth/logout`, rồi dùng token cũ gọi `GET /api/auth/me`.
- **Thì:** Request sau trả 401. Đăng nhập lại cấp token mới dùng được bình thường.
- **Truy vết:** FR-01 | D06 | UC-01 | NFR-02

---

## 2. VERIFY — Xác thực sinh viên

### AC-VERIFY-01 — Gửi yêu cầu xác thực
- **Cho trước:** Gia sư `Unverified`.
- **Khi:** Gửi tên trường, mã số sinh viên `22520001`, một ảnh JPG 1 MB.
- **Thì:** 201; yêu cầu ở `Pending`; `GET /api/student-verifications/mine` trả yêu cầu đó; mọi tài khoản Admin có một thông báo mới.
- **Truy vết:** FR-02 | BR-03 | UC-18 | NFR-04

### AC-VERIFY-02 — Không gửi trùng
- **Cho trước:** Gia sư có yêu cầu `Pending` (hoặc đã `Verified`).
- **Khi:** Gửi thêm một yêu cầu.
- **Thì:** 409; không tạo yêu cầu mới.
- **Truy vết:** FR-02 | §2.2 business-rules | UC-18

### AC-VERIFY-03 — Tệp không hợp lệ
- **Cho trước:** (a) tệp 6 MB; (b) tệp `.docx`; (c) không có tệp.
- **Khi:** Gửi yêu cầu xác thực.
- **Thì:** Cả ba 400; không tạo yêu cầu, không có tệp nào lên Storage.
- **Truy vết:** FR-02 | BR-03, D16 | UC-18 | NFR-06

### AC-VERIFY-04 — Admin duyệt
- **Cho trước:** Một yêu cầu `Pending`.
- **Khi:** Admin mở chi tiết rồi duyệt.
- **Thì:** Chi tiết có `evidenceUrl` mở được trong 60 phút; sau khi duyệt yêu cầu là `Verified`, `tutors.verification_status = Verified`, gia sư nhận thông báo loại `ModerationResult`; `audit_logs` có một dòng `Pending → Verified` ghi người duyệt.
- **Truy vết:** FR-02 | D16, BR-22 | UC-18 | NFR-04

### AC-VERIFY-05 — Admin từ chối phải có lý do
- **Cho trước:** Một yêu cầu `Pending`.
- **Khi:** Admin từ chối (a) không có lý do; (b) lý do 501 ký tự; (c) lý do hợp lệ.
- **Thì:** (a), (b) 400 và yêu cầu vẫn `Pending`; (c) 200, yêu cầu `Rejected`, gia sư thấy lý do và gửi lại được.
- **Truy vết:** FR-02 | BR-05 | UC-18

### AC-VERIFY-06 — Phạm vi
- **Cho trước:** Gia sư A, gia sư B, một Phụ huynh.
- **Khi:** Gia sư A gọi `GET /api/student-verifications/{id của B}`; Phụ huynh gọi `POST /api/student-verifications`; Admin duyệt một yêu cầu đã `Verified`.
- **Thì:** Lần lượt 403 (A gọi API của Admin), 403, 409.
- **Truy vết:** FR-02 | BR-SCOPE-02, BR-SCOPE-05 | UC-18 | NFR-02

### AC-VERIFY-07 — Gia sư chỉ thấy yêu cầu của mình
- **Cho trước:** Gia sư A có yêu cầu `Rejected`; gia sư B có yêu cầu `Pending`; gia sư C chưa gửi yêu cầu nào.
- **Khi:** Lần lượt A, B, C gọi `GET /api/student-verifications/mine`.
- **Thì:** A nhận đúng yêu cầu của A kèm lý do từ chối; B nhận đúng yêu cầu của B; C nhận 200 với `data: null`. Không ai nhận được yêu cầu của người khác.
- **Truy vết:** FR-02 | BR-SCOPE-01, BR-SCOPE-02 | UC-18 | NFR-02

---

## 3. PROFILE — Hồ sơ gia sư

### AC-PROFILE-01 — Tạo hồ sơ
- **Cho trước:** Gia sư chưa có hồ sơ.
- **Khi:** Tạo hồ sơ với tiêu đề, 2 môn, cấp THPT, hình thức `Both`, tỉnh và 2 phường, học phí 200.000 đ.
- **Thì:** 201; hồ sơ ở `Draft`, `availability = Accepting`, `isDefault = true` vì là hồ sơ đầu tiên.
- **Truy vết:** FR-03 | BR-02, BR-23 | UC-02

### AC-PROFILE-02 — Giới hạn 5 hồ sơ
- **Cho trước:** Gia sư đã có 5 hồ sơ.
- **Khi:** Tạo hồ sơ thứ 6.
- **Thì:** 409; vẫn 5 hồ sơ.
- **Truy vết:** FR-03 | BR-23 | UC-02

### AC-PROFILE-03 — Đúng một hồ sơ mặc định
- **Cho trước:** Hồ sơ A đang mặc định, hồ sơ B không.
- **Khi:** Đặt B làm mặc định.
- **Thì:** B mặc định, A không; gọi hai lần cùng lúc vẫn chỉ đúng một hồ sơ mặc định.
- **Truy vết:** FR-03 | BR-02 | UC-02 | NFR-03

### AC-PROFILE-04 — Phạm vi hồ sơ
- **Cho trước:** Hồ sơ X của gia sư khác.
- **Khi:** Gia sư đang đăng nhập gọi xem, sửa, đặt mặc định, gửi duyệt hồ sơ X.
- **Thì:** Cả bốn 404 "Không tìm thấy hồ sơ."; hồ sơ X không đổi.
- **Truy vết:** FR-03 | BR-SCOPE-02, BR-SCOPE-05 | UC-02 | NFR-02

### AC-PROFILE-05 — Tải minh chứng
- **Cho trước:** Hồ sơ `Draft` có 4 minh chứng.
- **Khi:** (a) tải thêm 1 tệp PDF 2 MB; (b) tải tiếp 1 tệp nữa.
- **Thì:** (a) 201, hồ sơ có 5 minh chứng; (b) 409, vẫn 5 minh chứng.
- **Truy vết:** FR-04 | BR-03 | UC-02

### AC-PROFILE-06 — Gửi duyệt thiếu điều kiện
- **Cho trước:** Hồ sơ `Draft` đủ mọi trường nhưng chưa có minh chứng.
- **Khi:** Gửi duyệt.
- **Thì:** 400, `errors` có "Hồ sơ cần ít nhất một minh chứng."; hồ sơ vẫn `Draft`.
- **Truy vết:** FR-04 | BR-04 | UC-02

### AC-PROFILE-07 — Gửi duyệt thành công và khóa sửa
- **Cho trước:** Hồ sơ `Draft` đủ điều kiện BR-04.
- **Khi:** Gửi duyệt, rồi thử sửa tiêu đề và thêm minh chứng.
- **Thì:** Gửi duyệt 200, hồ sơ `PendingReview`, Admin có thông báo; sửa và thêm minh chứng sau đó đều 409.
- **Truy vết:** FR-04 | BR-25, BR-26 | UC-02

### AC-PROFILE-08 — Sửa hồ sơ đã duyệt
- **Cho trước:** Hồ sơ `Approved`.
- **Khi:** (a) đổi học phí rồi lưu; (b) với một hồ sơ `Approved` khác, chỉ đổi trạng thái nhận dạy.
- **Thì:** (a) hồ sơ về `PendingReview`; (b) hồ sơ vẫn `Approved`.
- **Truy vết:** FR-04, FR-36 | BR-25 | UC-02, UC-13

### AC-PROFILE-09 — Trạng thái nhận dạy
- **Cho trước:** Hồ sơ của mình.
- **Khi:** Đặt `availability` lần lượt `Full`, `Paused`, `Busy`.
- **Thì:** Hai lần đầu 200; `Busy` 400 "Trạng thái nhận dạy không hợp lệ."
- **Truy vết:** FR-36 | §2.1 business-rules | UC-13

---

## 4. NOTI — Thông báo

### AC-NOTI-01 — Xem thông báo của mình
- **Cho trước:** Gia sư có 25 thông báo, 3 chưa đọc; người khác có thông báo riêng.
- **Khi:** Gọi danh sách trang 1, `pageSize = 20`, rồi `unreadOnly = true`.
- **Thì:** Trang 1 có 20 thông báo mới nhất trước, `totalCount = 25`; lọc chưa đọc trả đúng 3; không có thông báo của người khác.
- **Truy vết:** FR-32 | BR-27, BR-SCOPE-01 | UC-11

### AC-NOTI-02 — Đánh dấu đã đọc
- **Cho trước:** 3 thông báo chưa đọc.
- **Khi:** Đánh dấu một cái, rồi "đã đọc tất cả".
- **Thì:** `unread-count` lần lượt 2 rồi 0.
- **Truy vết:** FR-32 | BR-27 | UC-11

### AC-NOTI-03 — Thông báo của người khác
- **Cho trước:** Thông báo N của tài khoản khác.
- **Khi:** Đánh dấu đã đọc N.
- **Thì:** 404; N vẫn chưa đọc.
- **Truy vết:** FR-32 | BR-SCOPE-05 | UC-11 | NFR-02

### AC-NOTI-04 — Tắt email một loại
- **Cho trước:** Gia sư tắt email loại `ModerationResult`.
- **Khi:** Admin từ chối một hồ sơ của gia sư đó.
- **Thì:** Có thông báo trong ứng dụng; log **không** có dòng gửi email cho thông báo đó. Bật lại thì lần sau có dòng log gửi email.
- **Truy vết:** FR-32 | BR-27, D13 | UC-11

### AC-NOTI-05 — Cấu hình không hợp lệ
- **Cho trước:** Gia sư đang đăng nhập.
- **Khi:** Lưu cấu hình với loại `Abc`.
- **Thì:** 400; cấu hình cũ giữ nguyên.
- **Truy vết:** FR-32 | §4 business-rules | UC-11 | NFR-06
