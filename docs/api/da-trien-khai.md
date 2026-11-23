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
| Phân quyền theo vai trò | dependency `require_roles(...)` | Sai vai trò 403 "Bạn không có quyền thực hiện hành động này." trước khi xét bản ghi; vai trò đọc từ `users.role_id` | pytest |
| Lỗi validate | handler `RequestValidationError` | 400 giữ đúng câu tiếng Việt của validator trong `errors`; lỗi kiểu/JSON hỏng dùng câu chung | pytest |
| Schema | `tutors`, `parents`, `subjects` (seed 22 môn), `tutor_profiles`, `tutor_profile_subjects`, `tutor_profile_evidences` | Migration `0003`, `0004` nâng từ `0002` và hạ về được; CHECK chặn tỉnh ngoài D37, học phí lẻ, `Rejected` thiếu lý do | PostgreSQL 16 local |
| Danh mục môn | `GET /api/subjects` | Mọi vai trò; thứ tự theo `id` | S01-07 · pytest |
| Hồ sơ gia sư | `GET /api/tutor-profiles/mine` · `GET /api/tutor-profiles/{id}` · `POST /api/tutor-profiles` → 201 · `PUT /api/tutor-profiles/{id}` · `POST .../{id}/set-default` · `PUT .../{id}/availability` · `POST .../{id}/submit` | AC-PROFILE-01 … 09 (trừ phần thông báo Admin); chỉ Gia sư; hồ sơ người khác 404; đồng thời đặt mặc định/tạo hồ sơ/gửi duyệt đã thử trên PostgreSQL | S02-05 · pytest SQLite + PostgreSQL |
| Minh chứng hồ sơ | `POST /api/tutor-profiles/{id}/evidences` (multipart `files`, 1–5 tệp) → 201 · `DELETE .../{id}/evidences/{evidenceId}` | Kiểm magic bytes + đuôi, ≤ 5 MB/tệp (400); quá 5 tệp/hồ sơ, kể cả dồn trong một lượt (409); không giữ khóa DB trong lúc gọi Storage, kiểm lại trạng thái sau khi tải, lỗi thì không lưu bản ghi và dọn tệp; chi tiết hồ sơ trả URL ký 60 phút; body > 26 MB bị chặn 413 kể cả chunked | S02-05 · pytest (Storage giả) |
| Lưu tệp | `SupabaseFileStorage` (`app/core/file_storage.py`) | Upload, xóa, ký URL hàng loạt qua Storage REST; header `apikey` + `Authorization` như SDK | pytest (không gọi mạng) |

Chưa triển khai trong PR nền này:

- `POST /api/auth/register` và việc tạo đồng bộ `auth.users` + `users` + `tutors/parents`: thẻ
  **S01-04** tiếp theo.
- Không còn `POST /api/auth/login` hay `/logout` ở backend; Supabase Auth đảm nhiệm hai thao tác.
- Chưa chạy/stamp migration trên DB Supabase dùng chung và chưa xác minh token với project thật vì
  môi trường làm việc không có cấu hình Supabase.
- Hồ sơ gia sư chưa gửi thông báo cho Admin khi gửi duyệt (AC-PROFILE-07, phần thông báo): chờ
  dịch vụ thông báo của module NOTI.
- `SupabaseFileStorage` chưa thử với bucket thật: cần tạo bucket private (mặc định `evidences`)
  và đặt `SUPABASE_SECRET_KEY` rồi thử tải lên/xem một tệp trên project dùng chung.
