# Phần đã triển khai

Danh sách những gì **đã có trên `develop`**. Tài liệu FR, SCR mô tả thiết kế đích; thứ gì không có
ở đây thì coi là chưa có và kiểm code trước. Mỗi PR backend thêm hoặc sửa mục của mình ngay trong
PR đó (checklist `api-conventions.md` §9).

| Mục | Endpoint | Ghi chú | Thẻ / PR |
| :-- | :-- | :-- | :-- |
| Auth — đăng nhập | `POST /api/auth/login` | 5 lần/phút/IP (D08); sai email, sai mật khẩu, tài khoản khóa cùng 401 | S01-01 |
| Auth — người dùng hiện tại | `GET /api/auth/me` | Trả `userId`, `fullName`, `role` | S01-01 |
| Auth — đăng xuất | `POST /api/auth/logout` | Tăng `token_version`, mọi token cũ hết hiệu lực (D06) | S01-01 |
| Schema | bảng `roles`, `users` | Migration `InitialAuth`; seed 3 vai trò; seed Admin `admin@giasu.local` khi bảng `users` trống | S01-01 |
| Hạ tầng chung | — | `ApiResponse<T>`, `GlobalExceptionHandler`, `ActiveUserMiddleware`, `SecurityHeadersMiddleware`, CORS, Swagger (Development) | S01-01 |
