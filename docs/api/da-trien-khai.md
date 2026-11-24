# Phần đã triển khai

Danh sách những gì đã được kiểm chứng trong nhánh chuyển FastAPI. Tài liệu FR/SCR mô tả thiết kế
đích; thứ không có ở đây vẫn coi là chưa triển khai.

| Mục | Endpoint / thành phần | Đã kiểm chứng | Phạm vi |
| :-- | :-- | :-- | :-- |
| Auth — hồ sơ hiện tại | `GET /api/auth/me` | JWT đúng trả `userId`, `fullName`, `role`; thiếu/sai/hết hạn 401; tài khoản khóa 401 cùng thông báo đăng nhập sai; chưa có hồ sơ nghiệp vụ 404 | pytest local |
| Auth — frontend | Supabase `signInWithPassword` → Bearer token → `/api/auth/me` | TypeScript, ESLint và Next.js production build thành công | local build |
| Xác minh token | JWKS của `${SUPABASE_URL}/auth/v1/.well-known/jwks.json` | Kiểm chữ ký, `iss`, `aud`, `exp`, `sub`; test dùng cặp khóa RSA cục bộ, không gọi Supabase thật | pytest local |
| Schema | `roles`, `users.auth_user_id` | Alembic nâng từ baseline `InitialAuth`, giữ row/hash/token_version cũ, tạo unique index và FK `auth.users.id` | PostgreSQL 16 local |
| Hạ tầng chung | — | `ApiResponse<T>`, lỗi HTTP theo cùng khuôn, CORS, header `nosniff`/`DENY`, OpenAPI `/docs` | pytest/lint |

Chưa triển khai trong PR nền này:

- `POST /api/auth/register` và việc tạo đồng bộ `auth.users` + `users` + `tutors/parents`: thẻ
  **S01-04** tiếp theo.
- Không còn `POST /api/auth/login` hay `/logout` ở backend; Supabase Auth đảm nhiệm hai thao tác.
- Chưa chạy/stamp migration trên DB Supabase dùng chung và chưa xác minh token với project thật vì
  môi trường làm việc không có cấu hình Supabase.
