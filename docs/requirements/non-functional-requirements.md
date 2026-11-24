# Yêu cầu phi chức năng

## 0. Về tài liệu này

Sáu NFR của biểu mẫu (sheet P2_05) giữ nguyên mã, thêm cách đo và cách kiểm. Mỗi NFR có ít nhất
một cách kiểm cụ thể để SV4 viết thành TC ở P4T_01.

---

## 1. Danh sách

| Mã | Yêu cầu | Đo / kiểm thế nào | Ưu tiên |
| :-- | :-- | :-- | :-- |
| NFR-01 | Thao tác thông thường phản hồi đủ nhanh | 95% request đọc/ghi thông thường ≤ 3 giây trên DB dùng chung, đo bằng Postman Runner 50 lượt cho các API danh sách chính (tin, hồ sơ, thông báo). Danh sách có phân trang ở server, mặc định 20, tối đa 100 | Nên có |
| NFR-02 | Kiểm soát truy cập theo vai trò và bảo vệ tài khoản | Mọi endpoint có dependency xác minh Supabase JWT và vai trò nghiệp vụ; Postman/pytest có ca sai vai trò → 403, ngoài phạm vi → 404; backend không nhận/lưu mật khẩu mới; khóa `users.is_active` có hiệu lực ở request kế tiếp (AC-AUTH-04 … AC-AUTH-08) | Bắt buộc |
| NFR-03 | Dữ liệu nhất quán khi đổi trạng thái, buổi học, thanh toán | Chuyển trạng thái dùng cập nhật có điều kiện (`WHERE status = ...`) trong transaction; hai request cùng lúc chỉ một cái thành công (AC-PROFILE-03); không tính học phí buổi chưa `Completed`; một kỳ một giao dịch (BR-18) | Bắt buộc |
| NFR-04 | Truy vết thao tác quan trọng | `audit_logs` có người thực hiện, thời điểm, trạng thái trước và sau cho mọi chuyển trạng thái ở BR-22 | Nên có |
| NFR-05 | Hiển thị nhất quán với dữ liệu hiện tại | Sau thao tác ghi thành công, màn hình làm mới query liên quan; tải lại trang không thấy trạng thái cũ; mọi vùng dữ liệu đủ 3 trạng thái đang tải / lỗi / rỗng | Bắt buộc |
| NFR-06 | Kiểm tra dữ liệu ở cả giao diện và máy chủ | Schema Pydantic cho mọi request; form frontend lặp đúng giới hạn và câu thông báo của backend; gọi thẳng API bằng Postman với dữ liệu sai vẫn 400 | Bắt buộc |

---

## 2. Bảo mật tối thiểu

Gom từ D06–D09, D16 để người review có một checklist:

- [ ] Không lộ exception hay stack trace ra client; handler FastAPI trả lỗi 500 bằng câu chung.
- [ ] Log không chứa mật khẩu, token, connection string, nội dung tệp minh chứng.
- [ ] Không secret nào trong repo; backend đọc biến môi trường; frontend chỉ có API URL, Supabase URL
  và publishable key. Service-role key không bao giờ vào frontend.
- [ ] Tệp minh chứng ở bucket private, chỉ trả URL ký 60 phút sau khi kiểm phạm vi (D16).
- [ ] CORS chỉ mở cho origin frontend; header `nosniff` và `DENY` (D09).
- [ ] Id trên route không bao giờ là căn cứ phân quyền; phạm vi lấy từ tài khoản nghiệp vụ ánh xạ qua `sub` (D07).

---

## 3. Khả năng sử dụng

- Giao diện tiếng Việt, dùng được ở 375 px và 1280 px, nút thao tác chính cao ≥ 44 px
  (`frontend/design-system.md` §6).
- Thao tác không hoàn tác được (gửi duyệt, từ chối, rút phiếu, nhận gia sư, ghi nhận thanh toán,
  báo cáo vi phạm) luôn qua hộp thoại xác nhận nêu rõ hậu quả (`frontend/ui-screens.md` §4.3).
