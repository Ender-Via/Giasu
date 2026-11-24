# Tiêu chí nghiệm thu

## 0. Về tài liệu này

Mỗi tiêu chí là một kịch bản **Cho trước / Khi / Thì** kiểm được bằng một thao tác cụ thể (Postman,
pytest hoặc bấm tay). Dùng cho ba việc:

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

AC của module chưa viết chi tiết (`functional-requirements.md` §10) được thêm cùng thẻ `[Docs]` viết
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
- **Khi:** (a), (b) đăng nhập qua Supabase; (c) đăng nhập đúng rồi gọi `/api/auth/me`.
- **Thì:** Giao diện hiển thị cùng câu "Email hoặc mật khẩu không đúng."; tài khoản khóa không
  nhận được hồ sơ nghiệp vụ và không vào cổng vai trò.
- **Truy vết:** FR-01 | D06 | UC-01 | NFR-02

### AC-AUTH-05 — Giới hạn tần suất
- **Cho trước:** Project Supabase đã cấu hình Auth 5 lần/phút/IP và một IP đã thử 5 lần.
- **Khi:** Gọi Supabase Auth lần thứ 6 trong cùng phút; lặp lại với luồng đăng ký S01-04.
- **Thì:** Supabase trả 429; frontend hiển thị thời gian chờ; không tạo hồ sơ nghiệp vụ.
- **Truy vết:** FR-01 | D08 | UC-01 | NFR-02

### AC-AUTH-06 — Sai vai trò bị chặn
- **Cho trước:** Token của một Phụ huynh.
- **Khi:** Gọi một API chỉ dành cho Gia sư (`GET /api/tutor-profiles/mine`) và một API chỉ dành cho Admin (`GET /api/student-verifications`).
- **Thì:** Cả hai 403 "Bạn không có quyền thực hiện hành động này."; không trả dữ liệu.
- **Truy vết:** FR-01 | BR-SCOPE-05 | UC-01 | NFR-02

### AC-AUTH-07 — Không có token hợp lệ
- **Cho trước:** `GET /api/auth/me` hoặc API nghiệp vụ.
- **Khi:** Gọi (a) không có token; (b) token hết hạn; (c) token bị sửa hoặc ký bằng khóa khác.
- **Thì:** Cả ba 401; không thực hiện thao tác.
- **Truy vết:** FR-01 | D06 | UC-01 | NFR-02

### AC-AUTH-08 — Đăng xuất xóa phiên local
- **Cho trước:** Gia sư đã đăng nhập trên frontend.
- **Khi:** Bấm Đăng xuất rồi mở lại trang cần xác thực.
- **Thì:** Supabase session và token trong bộ nhớ bị xóa, frontend về `/login`, Axios không gửi
  Bearer token. Access token đã chép ra ngoài chỉ hết hiệu lực theo `exp` (D06).
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

---

## 5. REQUEST — Học sinh và tin tìm gia sư

### AC-REQUEST-01 — Thêm và sửa học sinh
- **Cho trước:** Phụ huynh chưa có học sinh.
- **Khi:** Thêm học sinh `  Nguyễn Minh An  `, lớp 9; rồi sửa lớp thành 10.
- **Thì:** Thêm 201, họ tên lưu đã bỏ khoảng trắng hai đầu; sửa 200; `GET /api/students/mine` trả đúng một học sinh, lớp 10.
- **Truy vết:** FR-05 | D24 | UC-14

### AC-REQUEST-02 — Học sinh sai dữ liệu
- **Cho trước:** Phụ huynh đang đăng nhập.
- **Khi:** Thêm học sinh với (a) họ tên 1 ký tự; (b) lớp 0; (c) lớp 13.
- **Thì:** Cả ba 400 với `errors` chỉ đúng trường sai; không tạo học sinh.
- **Truy vết:** FR-05 | D24 | UC-14 | NFR-06

### AC-REQUEST-03 — Phạm vi học sinh
- **Cho trước:** Phụ huynh A có học sinh S; phụ huynh B; một Gia sư.
- **Khi:** B sửa S; B đăng tin với `studentId` của S; Gia sư gọi `POST /api/students`.
- **Thì:** Lần lượt 404 "Không tìm thấy học sinh.", 404 "Không tìm thấy học sinh." (không tạo tin), 403.
- **Truy vết:** FR-05 | BR-SCOPE-03, BR-SCOPE-05 | UC-14 | NFR-02

### AC-REQUEST-04 — Đăng tin thành công
- **Cho trước:** Phụ huynh có học sinh S lớp 11.
- **Khi:** Đăng tin cho S: môn Toán, `UpperSecondary`, `Offline`, TP. Hồ Chí Minh, Phường Bến Thành, 2 buổi/tuần, 150.000–250.000 đ, yêu cầu "Sinh viên năm 3 trở lên, dạy tối thứ 3, thứ 6.". Body có thêm `status: "Recruiting"`, `expiresAt`.
- **Thì:** 201; tin ở `PendingReview`, `expiresAtUtc = null` (server bỏ qua hai trường client gửi); mọi Admin đang hoạt động có một thông báo `ModerationQueue`; tin **không** có trong `GET /api/tutor-requests/search`.
- **Truy vết:** FR-05 | BR-06, CC-04 | UC-14 | NFR-04

### AC-REQUEST-05 — Tin sai dữ liệu
- **Cho trước:** Phụ huynh có học sinh.
- **Khi:** Đăng tin lần lượt với (a) `minFee = 300000`, `maxFee = 200000`; (b) `minFee = 40000`; (c) `sessionsPerWeek = 8`; (d) hình thức `Offline` không có phường/xã; (e) `province = "Quận 1"`; (f) `subjectId` không có trong danh mục; (g) yêu cầu 2001 ký tự.
- **Thì:** Cả bảy 400 với `errors` chỉ đúng trường sai; không tạo tin.
- **Truy vết:** FR-05 | BR-06, BR-24, D37 | UC-14 | NFR-06

### AC-REQUEST-06 — Tin online không cần khu vực
- **Cho trước:** Phụ huynh có học sinh.
- **Khi:** Đăng tin hình thức `Online`, không có tỉnh, phường; rồi đăng tin `Online` khác có gửi kèm tỉnh, phường, địa chỉ.
- **Thì:** Cả hai 201; cả hai tin có `province`, `ward`, `address` là `null`.
- **Truy vết:** FR-05 | BR-06, D37 | UC-14

### AC-REQUEST-07 — Sửa tin đang tuyển
- **Cho trước:** Tin `Recruiting` có 2 phiếu `Pending`.
- **Khi:** Phụ huynh đổi học phí tối đa rồi lưu.
- **Thì:** 200; tin về `PendingReview`, biến mất khỏi kết quả tìm kiếm của gia sư; 2 phiếu vẫn `Pending`; Admin có thông báo `ModerationQueue`. Admin duyệt lại thì `expiresAtUtc` = thời điểm duyệt lại + 30 ngày.
- **Truy vết:** FR-05, FR-06 | D33, BR-07 | UC-14

### AC-REQUEST-08 — Không sửa tin đã kết thúc
- **Cho trước:** Một tin `Hired`, một tin `Closed`.
- **Khi:** Phụ huynh sửa từng tin.
- **Thì:** Cả hai 409; nội dung tin không đổi.
- **Truy vết:** FR-05 | §2.3 business-rules | UC-14

### AC-REQUEST-09 — Đóng tin
- **Cho trước:** Tin `Recruiting` có phiếu P1 `Pending`, P2 `Viewed`, P3 `TrialInvited`, P4 `Withdrawn`; một tin khác ở `PendingReview`.
- **Khi:** Phụ huynh đóng tin thứ nhất, rồi đóng tin `PendingReview`.
- **Thì:** Lần đầu 200: tin `Closed`, P1 và P2 `Rejected`, P3 `NotHired`, P4 vẫn `Withdrawn`; gia sư của P1, P2, P3 mỗi người một thông báo `ApplicationStatus`; `audit_logs` có dòng cho tin và cho từng phiếu đổi trạng thái. Lần sau 409, tin vẫn `PendingReview`.
- **Truy vết:** FR-05 | §2.3, §2.4 business-rules, BR-22 | UC-14 | NFR-03, NFR-04

### AC-REQUEST-10 — Phạm vi tin
- **Cho trước:** Tin T của phụ huynh A; phụ huynh B.
- **Khi:** B gọi xem, sửa, đóng T; B gọi `GET /api/tutor-requests/mine`.
- **Thì:** Xem, sửa, đóng đều 404 "Không tìm thấy tin."; danh sách của B không có T.
- **Truy vết:** FR-05 | BR-SCOPE-03, BR-SCOPE-05 | UC-14 | NFR-02

---

## 6. ADMIN-REVIEW — Duyệt hồ sơ và tin

### AC-ADMIN-REVIEW-01 — Danh sách hồ sơ chờ duyệt
- **Cho trước:** Hồ sơ H1 gửi duyệt lúc 08:00, H2 lúc 09:00 (cả hai `PendingReview`); H3 `Draft`; H4 `Approved`.
- **Khi:** Admin gọi `GET /api/tutor-profiles` không có `status`, rồi `status=Draft`.
- **Thì:** Lần đầu trả đúng H1 rồi H2 (cũ nhất trước), không có H3, H4; lần sau 400.
- **Truy vết:** FR-04 | §2.1 business-rules | UC-02

### AC-ADMIN-REVIEW-02 — Duyệt hồ sơ
- **Cho trước:** Hồ sơ H `PendingReview` có 2 minh chứng, trước đó từng bị từ chối với lý do "Thiếu bảng điểm.".
- **Khi:** Admin mở chi tiết H rồi duyệt.
- **Thì:** Chi tiết có 2 `evidences[].url` mở được trong 60 phút, khối `tutor` có `verificationStatus`, `rejectReason` là lý do cũ. Sau khi duyệt: H `Approved`, `rejectReason = null`, `reviewedBy` là Admin đó; gia sư nhận `ModerationResult`; `audit_logs` có dòng `PendingReview → Approved`; gia sư dùng được H để ứng tuyển (AC-APPLY-01).
- **Truy vết:** FR-04 | BR-22, D16, D36 | UC-02 | NFR-04

### AC-ADMIN-REVIEW-03 — Từ chối hồ sơ phải có lý do
- **Cho trước:** Hồ sơ H `PendingReview`.
- **Khi:** Admin từ chối với (a) không có lý do; (b) lý do chỉ có khoảng trắng; (c) lý do 501 ký tự; (d) lý do "Minh chứng IELTS mờ.".
- **Thì:** (a), (b), (c) 400 và H vẫn `PendingReview`; (d) 200, H `Rejected` kèm lý do, gia sư nhận `ModerationResult`, sửa và gửi lại được.
- **Truy vết:** FR-04 | BR-05 | UC-02 | NFR-06

### AC-ADMIN-REVIEW-04 — Không duyệt hồ sơ sai trạng thái
- **Cho trước:** Hồ sơ H1 `Approved`; hồ sơ H2 `PendingReview`.
- **Khi:** Admin duyệt H1; hai Admin gửi cùng lúc, một người duyệt H2, người kia từ chối H2.
- **Thì:** H1: 409, không đổi. H2: đúng một request 200, request kia 409; `audit_logs` chỉ có một dòng cho H2.
- **Truy vết:** FR-04 | §2.1 business-rules, BR-22 | UC-02 | NFR-03

### AC-ADMIN-REVIEW-05 — Duyệt tin
- **Cho trước:** Tin T `PendingReview`.
- **Khi:** Admin mở chi tiết T rồi duyệt lúc 10:00 ngày 23/11/2026 (giờ Việt Nam).
- **Thì:** Chi tiết có `address`, khối `parent` (họ tên, email, số điện thoại), họ tên và lớp học sinh. Sau khi duyệt: T `Recruiting`, `expiresAtUtc` = 10:00 ngày 23/12/2026 giờ Việt Nam (tính bằng UTC); phụ huynh nhận `ModerationResult`; T xuất hiện trong tìm kiếm của gia sư.
- **Truy vết:** FR-06 | D33, BR-07, BR-22 | UC-14 | NFR-04

### AC-ADMIN-REVIEW-06 — Từ chối tin
- **Cho trước:** Tin T `PendingReview` có yêu cầu "Chuyển 200k phí nhận lớp qua Zalo.".
- **Khi:** Admin từ chối (a) không có lý do; (b) với lý do "Tin yêu cầu phí nhận lớp, vi phạm quy chế.".
- **Thì:** (a) 400, T vẫn `PendingReview`; (b) 200, T `Rejected` kèm lý do, phụ huynh nhận `ModerationResult`, T không xuất hiện trong tìm kiếm.
- **Truy vết:** FR-06 | BR-05, BR-06 | UC-14

### AC-ADMIN-REVIEW-07 — Chỉ Admin duyệt, Admin không sửa
- **Cho trước:** Hồ sơ H và tin T đều `PendingReview`; một Gia sư; một Phụ huynh; một Admin.
- **Khi:** Gia sư gọi `POST /api/tutor-profiles/{H}/approve` và `GET /api/tutor-profiles?status=PendingReview`; Phụ huynh gọi `POST /api/tutor-requests/{T}/approve`; Admin gọi `PUT /api/tutor-requests/{T}` và `POST /api/tutor-requests/{T}/close`.
- **Thì:** Cả năm 403; H, T không đổi.
- **Truy vết:** FR-04, FR-06 | BR-SCOPE-04, BR-SCOPE-05 | UC-02, UC-14 | NFR-02

---

## 7. SEARCH — Tìm tin, điểm phù hợp, lưu tin

### AC-SEARCH-01 — Chỉ tin đang tuyển
- **Cho trước:** Tin T1 `Recruiting`, T2 `PendingReview`, T3 `Rejected`, T4 `Hired`, T5 `Closed`.
- **Khi:** Gia sư tìm không lọc; rồi mở chi tiết lần lượt T1 … T5.
- **Thì:** Kết quả chỉ có T1; chi tiết T1 200 và không có `address`, thông tin phụ huynh, họ tên học sinh; T2 … T5 đều 404 "Không tìm thấy tin.".
- **Truy vết:** FR-07 | BR-07, BR-SCOPE-02 | UC-03 | NFR-02

### AC-SEARCH-02 — Lọc
- **Cho trước:** Các tin `Recruiting`: A Toán · `Offline` · TP. Hồ Chí Minh · 150.000–250.000; B Toán · `Online` · 100.000–150.000; C Toán · `Offline` · Hà Nội · 200.000–300.000; D Hóa học · `Both` · TP. Hồ Chí Minh · 200.000–220.000.
- **Khi:** Tìm với (a) `subjectId` = Toán, `province` = TP. Hồ Chí Minh; (b) như (a) thêm `teachingMode=Offline`; (c) `feeFrom=230000`, `feeTo=260000`; (d) `feeFrom=300000`, `feeTo=200000`.
- **Thì:** (a) A, B (B là tin chỉ online); (b) chỉ A; (c) A, C; (d) 400.
- **Truy vết:** FR-07 | D37 | UC-03 | NFR-06

### AC-SEARCH-03 — Tính Matching Score
- **Cho trước:** Hồ sơ mặc định `Approved` của gia sư và bốn tin như bảng ví dụ ở FR-08.
- **Khi:** Gia sư tìm với `sort=match`.
- **Thì:** Bốn tin có điểm lần lượt 100, 50, 40, 25 và theo đúng thứ tự đó; chi tiết tin thứ hai có `matchingBreakdown { subject: 50, area: 0, fee: 0 }`. Tin có phường "  ben thanh" vẫn được 30 điểm khu vực như "Phường Bến Thành".
- **Truy vết:** FR-08 | D25 | UC-03

### AC-SEARCH-04 — Không có hồ sơ để tính điểm
- **Cho trước:** Gia sư có hồ sơ mặc định ở `PendingReview` (hồ sơ khác của gia sư thì `Approved`).
- **Khi:** Tìm với `sort=match`.
- **Thì:** 200; mọi tin `matchingScore = null`, `scoringProfileId = null`; tin xếp duyệt mới nhất trước.
- **Truy vết:** FR-08 | D25 | UC-03

### AC-SEARCH-05 — Không có kết quả
- **Cho trước:** Không có tin `Recruiting` nào môn Tiếng Nhật.
- **Khi:** Tìm với `subjectId` = Tiếng Nhật.
- **Thì:** 200, `items` rỗng, `totalCount = 0`.
- **Truy vết:** FR-07 | BR-07 | UC-03

### AC-SEARCH-06 — Lưu và bỏ lưu tin
- **Cho trước:** Tin T `Recruiting`, gia sư chưa lưu.
- **Khi:** Lưu T hai lần; xem danh sách đã lưu; tin T được tuyển (`Hired`); xem lại danh sách; bỏ lưu T hai lần.
- **Thì:** Hai lần lưu đều 200, danh sách có đúng một dòng T, `isAvailable = true`, kết quả tìm kiếm có `isSaved = true`; sau khi T `Hired` danh sách vẫn có T với `isAvailable = false`; hai lần bỏ lưu đều 200 và danh sách rỗng.
- **Truy vết:** FR-34 | BR-07 | UC-12

### AC-SEARCH-07 — Không lưu được tin không còn hiển thị
- **Cho trước:** Tin T `Closed`; tin U không tồn tại.
- **Khi:** Gia sư lưu T, lưu U.
- **Thì:** Cả hai 404 "Không tìm thấy tin."; không có dòng nào trong danh sách đã lưu.
- **Truy vết:** FR-34 | BR-07 | UC-12

### AC-SEARCH-08 — Phân quyền tìm kiếm và tin đã lưu
- **Cho trước:** Gia sư A đã lưu tin T; gia sư B; một Phụ huynh.
- **Khi:** Phụ huynh gọi `GET /api/tutor-requests/search` và `PUT /api/saved-tutor-requests/{T}`; B gọi `GET /api/saved-tutor-requests`.
- **Thì:** Hai request của Phụ huynh 403; danh sách của B rỗng, không có T.
- **Truy vết:** FR-07, FR-34 | BR-SCOPE-02, BR-SCOPE-05 | UC-03, UC-12 | NFR-02

---

## 8. APPLY — Ứng tuyển và rút phiếu

### AC-APPLY-01 — Ứng tuyển thành công
- **Cho trước:** Tin T `Recruiting`; gia sư có hồ sơ H `Approved`, chưa xác thực sinh viên, 0 phiếu đang chờ.
- **Khi:** Ứng tuyển T bằng H với lời giới thiệu 50 ký tự; body có thêm `status: "Hired"`.
- **Thì:** 201; phiếu ở `Pending` (server bỏ qua `status` client gửi); phụ huynh chủ T nhận `NewApplication`; `GET /api/tutor-applications/mine` có phiếu, `openCount = 1`; tìm kiếm trả T với `hasOpenApplication = true`.
- **Truy vết:** FR-09 | BR-08, CC-04, D36 | UC-04 | NFR-04

### AC-APPLY-02 — Tối đa 5 phiếu đang chờ
- **Cho trước:** Gia sư có 3 phiếu `Pending`, 2 phiếu `Viewed`, 4 phiếu `TrialInvited`.
- **Khi:** Ứng tuyển tin thứ 10; rồi rút một phiếu `Pending` và ứng tuyển lại tin thứ 10.
- **Thì:** Lần đầu 409 "Bạn đã có 5 phiếu đang chờ xử lý. …", không tạo phiếu; sau khi rút, lần sau 201 (phiếu `TrialInvited` không tính vào hạn mức).
- **Truy vết:** FR-09, FR-10 | BR-08, D21 | UC-04

### AC-APPLY-03 — Hai request đồng thời không vượt hạn mức
- **Cho trước:** Gia sư có 4 phiếu `Pending`; hai tin `Recruiting` X, Y.
- **Khi:** Gửi cùng lúc hai request ứng tuyển X và Y.
- **Thì:** Đúng một request 201, request kia 409; gia sư có đúng 5 phiếu `Pending`.
- **Truy vết:** FR-09 | D21 | UC-04 | NFR-03

### AC-APPLY-04 — Không ứng tuyển trùng
- **Cho trước:** Gia sư có phiếu `TrialInvited` vào tin T; phiếu `Withdrawn` vào tin U (U vẫn `Recruiting`).
- **Khi:** Ứng tuyển T; ứng tuyển U.
- **Thì:** T: 409 "Bạn đã ứng tuyển tin này."; U: 201, phiếu mới `Pending`.
- **Truy vết:** FR-09 | BR-08 | UC-04

### AC-APPLY-05 — Hồ sơ không hợp lệ
- **Cho trước:** Tin T `Recruiting`; gia sư có hồ sơ H1 `Draft`; hồ sơ H2 `Approved` của gia sư khác.
- **Khi:** Ứng tuyển T bằng H1; bằng H2.
- **Thì:** H1: 409 "Chỉ ứng tuyển được bằng hồ sơ đã duyệt."; H2: 404 "Không tìm thấy hồ sơ.". Không tạo phiếu.
- **Truy vết:** FR-09 | BR-08, BR-SCOPE-02 | UC-04 | NFR-02

### AC-APPLY-06 — Tin không nhận ứng tuyển và lời giới thiệu sai
- **Cho trước:** Tin T1 `Hired`, T2 `PendingReview`, T3 `Recruiting`; gia sư có hồ sơ `Approved`.
- **Khi:** Ứng tuyển T1, T2; ứng tuyển T3 với lời giới thiệu 19 ký tự, rồi 1001 ký tự.
- **Thì:** T1: 409 "Tin không còn nhận ứng tuyển."; T2: 404 "Không tìm thấy tin."; T3: cả hai 400. Không tạo phiếu.
- **Truy vết:** FR-09 | BR-07 | UC-04 | NFR-06

### AC-APPLY-07 — Rút phiếu
- **Cho trước:** Phiếu P1 `Pending`, P2 `Viewed` của gia sư.
- **Khi:** Rút P1, rút P2, rồi rút lại P1.
- **Thì:** Hai lần đầu 200, phiếu `Withdrawn`, `openCount` giảm 2; `audit_logs` có hai dòng; lần thứ ba 409. Phụ huynh không nhận thông báo.
- **Truy vết:** FR-10 | BR-09, D21, BR-22 | UC-04

### AC-APPLY-08 — Không rút phiếu đã qua bước mời dạy thử
- **Cho trước:** Phiếu P3 `TrialInvited`, P4 `Hired`, P5 `Rejected` của gia sư.
- **Khi:** Rút từng phiếu.
- **Thì:** Cả ba 409 "Chỉ rút được phiếu đang chờ xử lý hoặc đã xem."; trạng thái không đổi.
- **Truy vết:** FR-10 | BR-09 | UC-04

### AC-APPLY-09 — Phạm vi phiếu
- **Cho trước:** Phiếu P của gia sư A; gia sư B; một Phụ huynh có tin `Recruiting`.
- **Khi:** B xem P và rút P; Phụ huynh gọi `POST /api/tutor-applications`.
- **Thì:** B nhận 404 "Không tìm thấy phiếu ứng tuyển." cho cả hai, P không đổi; Phụ huynh nhận 403.
- **Truy vết:** FR-09, FR-10 | BR-SCOPE-02, BR-SCOPE-05 | UC-04 | NFR-02
