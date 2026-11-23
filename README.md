# Gia Sư Kết Nối — SE100 Nhóm 01

Nền tảng tìm việc gia sư và quản lý quá trình dạy cho ba vai trò: **Sinh viên/Gia sư**,
**Phụ huynh**, **Quản trị viên**. Vòng đời nghiệp vụ vẫn giữ nguyên: hồ sơ → tin tìm gia sư →
ứng tuyển → dạy thử → lộ trình → buổi học → tiến độ → học phí → đánh giá → xử lý vi phạm.

| Thành phần | Công nghệ |
| :-- | :-- |
| Backend | Python, FastAPI, SQLAlchemy 2, Alembic, PyJWT |
| Database | PostgreSQL trên Supabase |
| Xác thực | Supabase Auth; backend xác minh access token qua JWKS |
| Tệp | Supabase Storage, bucket private (D16) |
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS 4 |
| Gọi API | Axios, TanStack Query, React Hook Form |
| Test / CI | pytest, Ruff, Postman; GitHub Actions |

## Luồng đăng nhập đã triển khai

1. Next.js gọi `supabase.auth.signInWithPassword()` và để Supabase quản lý phiên/refresh token.
2. Axios gửi access token trong `Authorization: Bearer <token>`.
3. FastAPI xác minh chữ ký, `iss`, `aud`, `exp` bằng JWKS của project.
4. `GET /api/auth/me` dùng claim `sub` để tìm `users.auth_user_id`, kiểm `is_active`, rồi trả
   `{ userId, fullName, role }` trong khuôn `ApiResponse<T>`.

Backend không nhận mật khẩu và không tự phát JWT. Đăng ký/tạo hồ sơ nghiệp vụ là thẻ tiếp theo
**S01-04**, chưa nằm trong phạm vi nền hiện tại.

## Cài đặt lần đầu

Cần: **Python 3.10+** (CI dùng 3.12), **uv 0.9.0**, **Node.js 20.9+**, **Git** và PostgreSQL
hoặc Supabase CLI cho môi trường local.

```bash
git clone <URL repo> GiaSu
cd GiaSu
git checkout develop

cd backend
cp .env.example .env
uv sync --locked --all-groups

cd ../frontend
cp .env.example .env.local
npm ci
```

Các biến cần cấu hình:

- Backend: `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_JWT_AUDIENCE`,
  `SUPABASE_JWT_ALGORITHMS`, `CORS_ALLOWED_ORIGINS`, `SUPABASE_SECRET_KEY`,
  `SUPABASE_STORAGE_BUCKET`.
- Frontend: `NEXT_PUBLIC_API_BASE_URL`, `NEXT_PUBLIC_SUPABASE_URL`,
  `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`.

Project phải dùng signing key bất đối xứng `ES256` hoặc `RS256` để backend xác minh qua JWKS.
Project legacy còn dùng `HS256` cần chuyển signing key trước khi triển khai backend này.

Chỉ dùng publishable/anon key ở frontend. Không commit password database, service-role key, access
token hoặc refresh token.

## Chạy

```bash
cd backend
uv run uvicorn app.main:app --reload --port 5015
```

API ở `http://localhost:5015`; OpenAPI ở `http://localhost:5015/docs`.

```bash
cd frontend
npm run dev
```

Frontend ở `http://localhost:3000`.

## Kiểm thử trước PR

```bash
cd backend
uv run ruff check .
uv run pytest

cd ../frontend
npm run lint
npm run build
```

CI còn dựng PostgreSQL 16, tạo schema `auth.users` tối thiểu, chạy baseline `InitialAuth`, chèn một
bản ghi cũ rồi nâng lên migration Supabase để chứng minh dữ liệu được giữ nguyên.

## Migration

- `0001_initial_auth` là baseline Alembic tương đương migration EF Core `InitialAuth` đã có.
- `0002_supabase_auth_mapping` thêm `users.auth_user_id` nullable + unique + FK đến
  `auth.users.id`, đồng thời cho phép `credential_reference` nullable. Các cột/row cũ được giữ lại.
- DB mới/local Supabase: `uv run alembic upgrade head`.
- DB dùng chung đã có `InitialAuth`: sau khi đối chiếu schema và PR đã merge, chạy
  `uv run alembic stamp 0001_initial_auth` rồi `uv run alembic upgrade head`.

Không tự chạy migration khi app khởi động. Không stamp/upgrade DB dùng chung trước khi PR được
duyệt và merge (D11).

## Cấu trúc

```text
backend/
  app/api/             Router FastAPI, ánh xạ HTTP.
  app/services/        Quy tắc nghiệp vụ.
  app/repositories/    Truy vấn SQLAlchemy và lọc phạm vi.
  app/db/              Model và session PostgreSQL.
  app/core/            Cấu hình, xác minh JWT Supabase.
  app/schemas/         DTO Pydantic và ApiResponse.
  migrations/          Alembic revisions.
  tests/               pytest.
frontend/src/
  app/(admin|tutor|parent)/  Màn hình theo vai trò.
  context/                   Phiên Supabase + hồ sơ nghiệp vụ.
  lib/                       Supabase client, Axios.
docs/                        Tài liệu nhóm.
```

## Thành viên

| | Vai trò | Phụ trách |
| :-- | :-- | :-- |
| SV1 Trần Quý Lộc | **Lead** + Backend | Điều phối, Supabase; backend nền tảng và quản trị |
| SV2 Nguyễn Trí Kiệt | **GitHub owner** + Frontend | Git, tài liệu, biểu mẫu; frontend Gia sư, chat, thông báo |
| SV3 Trần Nguyên Lân | Backend + Database | ERD, tuyển dụng, lộ trình, buổi học, học phí |
| SV4 Nguyễn Anh Kiệt | Frontend + Testing | Frontend Phụ huynh/Admin, pytest, Postman |
