# Vai trò và phân quyền

## 0. Về tài liệu này

Ba vai trò, mỗi vai trò làm được gì và trên dữ liệu nào. Đứng thứ hai trong thứ tự ưu tiên tài
liệu (`docs/README.md`), cùng hạng với `business-rules.md`: FR, AC, màn hình và code phải khớp ma
trận §3. Backend là nơi thực thi; giao diện ẩn nút không được coi là đã chặn (BR-SCOPE-01).

---

## 1. Các vai trò

| Vai trò | Claim `role` | Nhãn hiển thị | Ai | Tự đăng ký |
| :-- | :-- | :-- | :-- | :-- |
| Quản trị viên | `Admin` | Quản trị viên | Người vận hành nền tảng | Không — chỉ seed hoặc Admin tạo |
| Sinh viên/Gia sư | `Tutor` | Gia sư | Sinh viên nhận dạy kèm | Có (`/register`) |
| Phụ huynh | `Parent` | Phụ huynh | Người tìm gia sư cho con | Có (`/register`) |

Học sinh **không** có tài khoản; là bản ghi `Student` do phụ huynh quản lý (D24).
Một tài khoản đúng một vai trò, không đổi vai trò sau khi đăng ký.

---

## 2. Phạm vi dữ liệu

| Mã | Quy tắc |
| :-- | :-- |
| BR-SCOPE-01 | Mọi kiểm tra vai trò và phạm vi nằm ở backend, chạy lại ở **mỗi** request. Định danh người thao tác lấy từ claim `sub`, không nhận từ body hay query (D07). |
| BR-SCOPE-02 | **Gia sư** chỉ thao tác trên: hồ sơ gia sư, yêu cầu xác thực, phiếu ứng tuyển, tin đã lưu **của mình**; lộ trình, buổi học, học phí, đánh giá của quan hệ dạy-học **mình là gia sư**. Xem được mọi tin `Recruiting` (công khai cho gia sư). |
| BR-SCOPE-03 | **Phụ huynh** chỉ thao tác trên: học sinh, tin tìm gia sư **của mình**; phiếu ứng tuyển **vào tin của mình**; lộ trình, buổi học, học phí, đánh giá của quan hệ dạy-học **mình là phụ huynh**. Xem được hồ sơ gia sư đã ứng tuyển vào tin của mình. |
| BR-SCOPE-04 | **Admin** xem và xử lý mọi hồ sơ, tin, yêu cầu xác thực, báo cáo vi phạm, số liệu thống kê. Admin **không** sửa nội dung hồ sơ, tin, lộ trình, buổi học, học phí của người dùng — chỉ duyệt, từ chối, xử lý vi phạm. |
| BR-SCOPE-05 | Cách từ chối: sai vai trò → **403** ngay ở `[Authorize]`, trước khi xét bản ghi. Đúng vai trò nhưng bản ghi không tồn tại hoặc ngoài phạm vi → **404**, cùng một message, để không lộ bản ghi nào có thật. |
| BR-SCOPE-06 | Hội thoại chat chỉ hai bên của phiếu ứng tuyển đọc và ghi (D26). Admin chỉ đọc tin nhắn khi xử lý báo cáo vi phạm có liên quan tới hội thoại đó (FR-30). |

---

## 3. Ma trận vai trò – quyền

Chú thích: `–` = bị cấm (403). *(của mình)*, *(tin của mình)*, *(quan hệ của mình)* = chỉ bản ghi
thuộc phạm vi §2, ngoài phạm vi → 404. *(tổng hợp)* = chỉ số liệu tổng hợp.

| FR | Chức năng | Admin | Gia sư | Phụ huynh |
| :-- | :-- | :-- | :-- | :-- |
| FR-01 | Đăng ký, đăng nhập, đăng xuất | Đăng nhập, đăng xuất | ✓ | ✓ |
| FR-02 | Xác thực sinh viên | Xem / Duyệt / Từ chối | Gửi / Xem (của mình) | – |
| FR-03 | Hồ sơ gia sư, hồ sơ mặc định | Xem | Tạo / Sửa / Xem (của mình) | Xem (hồ sơ đã ứng tuyển vào tin của mình) |
| FR-04 | Gửi duyệt và duyệt hồ sơ | Duyệt / Từ chối | Gửi duyệt (của mình) | – |
| FR-05 | Đăng tin tìm gia sư, học sinh | Xem | – | Tạo / Sửa / Đóng / Xem (của mình) |
| FR-06 | Duyệt tin | Duyệt / Từ chối | – | – |
| FR-07 | Tìm kiếm, lọc tin | – | Xem (tin `Recruiting`) | – |
| FR-08 | Matching Score | – | Xem | – |
| FR-09 | Ứng tuyển | – | Tạo (của mình) | – |
| FR-10 | Rút phiếu | – | Rút (của mình) | – |
| FR-11 | Xem ứng viên, cập nhật phiếu | – | – | Xem / Đổi trạng thái (tin của mình) |
| FR-12 | Mời dạy thử, quyết định nhận | – | – | Tạo (tin của mình) |
| FR-13 | Tin chuyển Đã tuyển | hệ thống | hệ thống | hệ thống |
| FR-14 | Chat | Xem khi xử lý vi phạm | Tạo / Xem (của mình) | Tạo / Xem (của mình) |
| FR-15–17 | Lộ trình học | – | Tạo / Sửa / Xem (quan hệ của mình) | Xem / Đồng ý / Yêu cầu sửa (quan hệ của mình) |
| FR-18 | Ghi nhận buổi học | – | Tạo (quan hệ của mình) | Xem (quan hệ của mình) |
| FR-19 | Xác nhận buổi học | – | Xem | Xác nhận / Khiếu nại (quan hệ của mình) |
| FR-20 | Đổi lịch | – | Đề nghị / Phản hồi (quan hệ của mình) | Đề nghị / Phản hồi (quan hệ của mình) |
| FR-21 | Bài kiểm tra, điểm | – | Tạo / Xem (quan hệ của mình) | Xem (quan hệ của mình) |
| FR-22–23 | Báo cáo tiến độ, cảnh báo | – | Tạo / Xem (quan hệ của mình) | Xem (quan hệ của mình) |
| FR-24–26 | Học phí, thanh toán | Xem (tổng hợp) | Xem / Xác nhận đã nhận (quan hệ của mình) | Xem / Ghi nhận thanh toán (quan hệ của mình) |
| FR-27 | Đánh giá | – | Tạo / Phản hồi (quan hệ của mình) | Tạo / Phản hồi (quan hệ của mình) |
| FR-28 | Điểm uy tín | Xem | Xem | Xem |
| FR-29 | Cờ cảnh báo | Xem / Xử lý | – | – |
| FR-30 | Báo cáo vi phạm | Xem / Yêu cầu bổ sung | Tạo / Xem (của mình) | Tạo / Xem (của mình) |
| FR-31 | Chế tài | Tạo | – | – |
| FR-32 | Thông báo, cấu hình email | Xem / Cấu hình (của mình) | Xem / Cấu hình (của mình) | Xem / Cấu hình (của mình) |
| FR-33 | Thống kê | Xem (tổng hợp) | – | – |
| FR-34 | Lưu tin | – | Tạo / Bỏ / Xem (của mình) | – |
| FR-35 | Gia hạn tin | – | – | Gia hạn / Sửa (của mình) |
| FR-36 | Trạng thái nhận dạy | – | Sửa (của mình) | – |

**Không vai trò nào được:** sửa phiếu ứng tuyển của người khác; tự đổi trạng thái hồ sơ hay tin
sang `Approved` / `Recruiting`; đánh dấu kỳ học phí `Paid` mà không có bản ghi `payments`; sửa
hay xóa giao dịch, đánh giá, báo cáo vi phạm đã gửi.
