# Quy tắc nghiệp vụ và trạng thái

Nguồn yêu cầu gốc là biểu mẫu OOAD (sheet P2_05 FR/NFR, P2_06 User Story, P3A_01 Use Case).
File này chỉ ghi phần **biểu mẫu chưa đủ để code**: module, trạng thái, quy tắc có mã `BR-xx`.
Chỗ nào biểu mẫu và file này khác nhau thì theo file này cùng `DECISIONS.md`.

---

## 1. Module, yêu cầu và người phụ trách

| Module | FR | UC | Backend | Frontend |
| :-- | :-- | :-- | :-- | :-- |
| **AUTH** Tài khoản, đăng ký, đăng nhập | FR-01 | UC-01 | SV1 | SV2 |
| **VERIFY** Xác thực sinh viên | FR-02 | UC-18 | SV1 | Tutor: SV2 · Admin: SV4 |
| **PROFILE** Hồ sơ gia sư, minh chứng, trạng thái nhận dạy | FR-03, FR-04, FR-36 | UC-02, UC-13 | SV3 | SV2 |
| **REQUEST** Tin tìm gia sư, học sinh, gia hạn | FR-05, FR-06, FR-35 | UC-14, UC-17 | SV3 | SV4 |
| **SEARCH** Tìm kiếm, matching, lưu tin | FR-07, FR-08, FR-34 | UC-03, UC-12 | SV3 | SV2 |
| **APPLY** Ứng tuyển, tuyển chọn, dạy thử | FR-09 – FR-13 | UC-04, UC-15 | SV3 | Tutor: SV2 · Parent: SV4 |
| **CHAT** Hội thoại | FR-14 | UC-05 | SV1 | SV2 (dùng chung) |
| **ROADMAP** Lộ trình học | FR-15 – FR-17 | UC-06 | SV3 | Tutor: SV2 · Parent: SV4 |
| **SESSION** Buổi học, xác nhận, đổi lịch | FR-18 – FR-20 | UC-07 | SV3 | Tutor: SV2 · Parent: SV4 |
| **PROGRESS** Kiểm tra, báo cáo tiến độ, cảnh báo | FR-21 – FR-23 | UC-08 | SV1 | Tutor: SV2 · Parent: SV4 |
| **TUITION** Học phí, thanh toán | FR-24 – FR-26 | UC-16 | SV3 | Tutor: SV2 · Parent: SV4 |
| **REVIEW** Đánh giá, điểm uy tín, gắn cờ | FR-27 – FR-29 | UC-09 | SV1 | SV4 |
| **VIOLATION** Báo cáo vi phạm, chế tài | FR-30, FR-31 | UC-10 | SV1 | Gửi: SV2 · Admin: SV4 |
| **NOTI** Thông báo, cấu hình email | FR-32 | UC-11 | SV1 | SV2 (dùng chung) |
| **DASH** Thống kê quản trị | FR-33 | UC-19 | SV1 | SV4 |
| **ADMIN-REVIEW** Duyệt hồ sơ, duyệt tin | FR-04, FR-06 | UC-02, UC-14 | SV1 | SV4 |

Mã thẻ trong file kế hoạch, tiêu đề PR và tên nhánh dùng tên module ở cột đầu.

---

## 2. Trạng thái chính thức (D32)

Lưu chuỗi tiếng Anh; cột "Hiển thị" là chữ frontend in ra. Mũi tên là chuyển trạng thái **hợp lệ
duy nhất**; chuyển khác → **409**.

### 2.1 Hồ sơ gia sư `TutorProfile.Status`
| Giá trị | Hiển thị |
| :-- | :-- |
| `Draft` | Nháp |
| `PendingReview` | Chờ duyệt |
| `Approved` | Đã duyệt |
| `Rejected` | Bị từ chối |

`Draft → PendingReview → Approved | Rejected`; `Rejected → PendingReview` (sửa rồi gửi lại);
`Approved → PendingReview` khi gia sư sửa nội dung chuyên môn.

Trạng thái nhận dạy `TutorProfile.Availability`: `Accepting` (Đang nhận thêm học sinh), `Full`
(Đã đủ lịch), `Paused` (Tạm ngừng). Chỉ hồ sơ `Approved` + `Accepting` hiện cho phụ huynh tìm.

### 2.2 Xác thực sinh viên `StudentVerification.Status`
`Pending` (Chờ xác thực) → `Verified` (Đã xác thực) | `Rejected` (Bị từ chối, kèm lý do).
Gia sư được gửi lại sau khi bị từ chối.

### 2.3 Tin tìm gia sư `TutorRequest.Status`
| Giá trị | Hiển thị |
| :-- | :-- |
| `PendingReview` | Chờ duyệt |
| `Rejected` | Bị từ chối |
| `Recruiting` | Đang tuyển |
| `Hired` | Đã tuyển |
| `Closed` | Đã đóng |

`PendingReview → Recruiting | Rejected`; `Rejected → PendingReview`; `Recruiting → Hired` (nhận
gia sư chính thức) | `Closed` (phụ huynh đóng tin); sửa tin `Recruiting` → `PendingReview` (D33).

### 2.4 Phiếu ứng tuyển `TutorApplication.Status`
| Giá trị | Hiển thị |
| :-- | :-- |
| `Pending` | Đang chờ xử lý |
| `Viewed` | Đã xem |
| `TrialInvited` | Mời dạy thử |
| `Hired` | Nhận dạy chính thức |
| `NotHired` | Không nhận |
| `Rejected` | Bị từ chối |
| `Withdrawn` | Đã rút |

`Pending → Viewed` (phụ huynh mở chi tiết phiếu); `Pending | Viewed → TrialInvited | Rejected`;
`TrialInvited → Hired | NotHired`; `Pending | Viewed → Withdrawn` (gia sư rút).
Một phiếu `Hired` → tin sang `Hired`, các phiếu còn mở khác của tin đó → `Rejected`.

### 2.5 Lộ trình `LearningRoadmap.Status`
`Draft` (Nháp) → `PendingParent` (Chờ phụ huynh duyệt) → `Active` (Đang học) | `Draft` (cần sửa);
`Active → Ended` (Đã kết thúc).

### 2.6 Buổi học `ClassSession.Status`
| Giá trị | Hiển thị |
| :-- | :-- |
| `Scheduled` | Đã lên lịch |
| `PendingConfirm` | Chờ phụ huynh xác nhận |
| `Completed` | Đã hoàn thành |
| `Disputed` | Đang khiếu nại |
| `Cancelled` | Đã hủy |

`Scheduled → PendingConfirm` (gia sư ghi nhận buổi) → `Completed` (phụ huynh xác nhận hoặc tự
xác nhận sau 48 giờ) | `Disputed` (phụ huynh khiếu nại); `Disputed → Completed | Cancelled`
(hai bên thống nhất hoặc Admin xử lý); `Scheduled → Cancelled` (D22).

### 2.7 Kỳ học phí `TuitionInvoice.Status`
`Unpaid` (Chưa thanh toán) → `Paid` (Đã thanh toán); `Unpaid → Overdue` (Quá hạn) → `Paid`.

### 2.8 Báo cáo vi phạm `ViolationReport.Status`
`Submitted` (Đã gửi) → `NeedMoreEvidence` (Cần bổ sung) → `Submitted`;
`Submitted → Resolved` (Đã xử lý, có chế tài) | `Dismissed` (Bác bỏ, có lý do).

---

## 3. Quy tắc `BR-xx`

| Mã | Quy tắc | Nguồn |
| :-- | :-- | :-- |
| BR-01 | Email đăng nhập là duy nhất, lưu lowercase. Mật khẩu ≥ 8 ký tự, có chữ và số. Tự đăng ký chỉ được chọn `Tutor` hoặc `Parent`; tài khoản `Admin` chỉ do seed/Admin tạo | FR-01 |
| BR-02 | Mỗi gia sư nhiều hồ sơ, đúng **một** hồ sơ mặc định. Đặt mặc định hồ sơ khác thì bỏ mặc định hồ sơ cũ trong cùng transaction | FR-03 |
| BR-03 | Minh chứng: ≤ 5 tệp/hồ sơ, ≤ 5 MB/tệp, JPG/PNG/PDF | D16 |
| BR-04 | Gửi duyệt hồ sơ cần đủ: tiêu đề, môn dạy (≥ 1), cấp học, khu vực, học phí mong muốn, ≥ 1 minh chứng | FR-04 |
| BR-05 | Từ chối hồ sơ, tin, xác thực đều **bắt buộc** lý do (≤ 500 ký tự) | FR-04, FR-06, FR-02 |
| BR-06 | Tin cần: học sinh, môn, cấp học, khu vực (tỉnh + quận/huyện), số buổi/tuần (1–7), học phí/buổi tối thiểu và tối đa (min ≤ max, > 0) | FR-05 |
| BR-07 | Chỉ tin `Recruiting` hiện trong tìm kiếm và nhận ứng tuyển | FR-07, FR-13 |
| BR-08 | Tối đa 5 phiếu `Pending` + `Viewed` mỗi gia sư; không ứng tuyển trùng tin đang có phiếu mở; phải dùng hồ sơ `Approved` | FR-09, D21 |
| BR-09 | Chỉ rút phiếu ở `Pending` hoặc `Viewed` | FR-10 |
| BR-10 | Gia sư bị khóa tính năng ứng tuyển (D23) không tạo được phiếu → **403** kèm thông báo thời hạn khóa | FR-31 |
| BR-11 | Mỗi phiếu `Hired` tạo đúng một quan hệ dạy-học; lộ trình chỉ tạo được cho quan hệ đó | FR-15 |
| BR-12 | Lộ trình cần: mục tiêu, lịch học (thứ + giờ), học phí/buổi, ngày bắt đầu, ≥ 1 mục kế hoạch tuần | FR-16, FR-17 |
| BR-13 | Chỉ lộ trình `Active` mới ghi nhận buổi học | FR-18 |
| BR-14 | Buổi học: giờ kết thúc > giờ bắt đầu; mức tiếp thu 1–5; không ghi nhận buổi ở tương lai | FR-18 |
| BR-15 | Đổi lịch: mỗi bên 1 lần/buổi, trước giờ học ≥ 2 giờ | D22 |
| BR-16 | Điểm kiểm tra thang 0–10, tối đa 2 chữ số thập phân | FR-21 |
| BR-17 | Học phí kỳ = số buổi `Completed` × học phí/buổi của lộ trình; tạo kỳ tự động ngày 1 hằng tháng | D28 |
| BR-18 | Một kỳ chỉ một giao dịch `Paid`; ghi nhận lặp → **409**, không tạo bản ghi thứ hai | D14, NFR-03 |
| BR-19 | Đánh giá khi lộ trình có ≥ 1 buổi `Completed`; mỗi bên 1 đánh giá/lộ trình; phản hồi 1 lần | D29 |
| BR-20 | Báo cáo vi phạm cần: người bị báo cáo, loại (`Fraud`, `NoShow`, `Harassment`, `Payment`, `Other`), mô tả ≥ 20 ký tự, ≤ 5 tệp minh chứng | FR-30 |
| BR-21 | Chế tài theo số vi phạm `Resolved` trong 6 tháng gần nhất | D23 |
| BR-22 | Mọi thay đổi trạng thái hồ sơ, tin, phiếu, thanh toán, vi phạm ghi `audit_logs` (ai, lúc nào, từ → sang) | NFR-04 |

---

## 4. Sự kiện tạo thông báo (FR-32)

| Sự kiện | Người nhận | Loại email |
| :-- | :-- | :-- |
| Hồ sơ/tin/xác thực được duyệt hoặc bị từ chối | Chủ hồ sơ/tin | `ModerationResult` |
| Có phiếu ứng tuyển mới | Phụ huynh chủ tin | `NewApplication` |
| Phiếu đổi trạng thái (mời dạy thử, nhận, không nhận, từ chối) | Gia sư | `ApplicationStatus` |
| Lộ trình gửi duyệt / được đồng ý / bị yêu cầu sửa | Bên còn lại | `Roadmap` |
| Buổi học chờ xác nhận, đề nghị đổi lịch, nhắc lịch trước 24 giờ | Bên liên quan | `Session` |
| Tin đủ 30 ngày chưa tuyển | Phụ huynh | `RequestExpiry` |
| Kỳ học phí mới, quá hạn | Phụ huynh, gia sư | `Tuition` |
| Cảnh báo lệch tiến độ, báo cáo tiến độ mới | Phụ huynh, gia sư | `Progress` |
| Báo cáo vi phạm mới (Admin), kết quả xử lý (hai bên) | Admin / hai bên | `Violation` |
