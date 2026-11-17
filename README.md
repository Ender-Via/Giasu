# Gia Sư Kết Nối — SE100 Nhóm 01

Nền tảng tìm việc gia sư và quản lý quá trình dạy cho sinh viên. Ba vai trò: **Sinh viên/Gia sư**,
**Phụ huynh**, **Quản trị viên**. Quản lý trọn vòng đời: hồ sơ → tin tìm gia sư → ứng tuyển →
dạy thử → lộ trình học → buổi học → tiến độ → học phí → đánh giá → xử lý vi phạm.

| Thành phần | Công nghệ |
| :-- | :-- |
| Backend | ASP.NET Core 10, EF Core 10, FluentValidation, Serilog |
| Database | PostgreSQL (Supabase, cả nhóm dùng chung) |
| Xác thực | JWT Bearer HS256 |
| Frontend | Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS 4 |
| Gọi API | Axios, TanStack Query, React Hook Form |
| Test / CI | xUnit, Postman; GitHub Actions |

## Cài đặt lần đầu

Cần: **.NET SDK 10**, **Node.js 20.9+**, **Git**, công cụ EF:

```bash
dotnet tool install --global dotnet-ef
```

Clone và chuyển sang nhánh tích hợp:

```bash
git clone <URL repo> GiaSu
cd GiaSu
git checkout develop
```

### Secret backend
Chuỗi kết nối và khóa JWT **không** nằm trong repo. Xin SV1 Lộc (quản trị Supabase) gửi riêng, rồi chạy trong thư mục
`backend/GiaSu.API`:

```bash
dotnet user-secrets set "ConnectionStrings:DefaultConnection" "Host=...;Port=5432;Database=postgres;Username=...;Password=...;SSL Mode=Require"
dotnet user-secrets set "Jwt:Key" "<chuỗi ngẫu nhiên tối thiểu 32 ký tự>"
dotnet user-secrets set "Supabase:Url" "https://<mã-project>.supabase.co"
dotnet user-secrets set "Supabase:ServiceKey" "<service key>"
```

Thiếu `Jwt:Key` thì backend dừng ngay lúc khởi động. Hai giá trị `Supabase:*` chỉ cần từ khi có
chức năng tải tệp minh chứng.

### Frontend
```bash
cd frontend
cp .env.example .env.local
npm install
```

## Chạy

```bash
dotnet run --project backend/GiaSu.API
```
API ở `http://localhost:5015`, Swagger ở `http://localhost:5015/swagger`.
Tài khoản seed khi bảng `users` trống: `admin@giasu.local` / `Admin@123456`.

```bash
cd frontend && npm run dev
```
Giao diện ở `http://localhost:3000`.

Kiểm trước khi mở PR (CI chạy đúng các lệnh này):

```bash
dotnet build backend/GiaSu.slnx -warnaserror
dotnet test backend/GiaSu.slnx
cd frontend && npm run lint && npm run build
```

Migration (đọc D11 trong `docs/DECISIONS.md` trước):

```bash
dotnet ef migrations add <TenMigration> --project backend/GiaSu.Infrastructure --startup-project backend/GiaSu.API --output-dir Persistence/Migrations
dotnet ef database update --project backend/GiaSu.Infrastructure --startup-project backend/GiaSu.API
```

## Cấu trúc

```
backend/
  GiaSu.Domain/          Entity và hằng số. Không tham chiếu project nào khác.
  GiaSu.Application/     DTO, interface, service (logic nghiệp vụ), validator.
  GiaSu.Infrastructure/  DbContext, cấu hình Fluent API, migration, repository, dịch vụ ngoài.
  GiaSu.API/             Controller, middleware, Program.cs.
  GiaSu.Tests/           Unit test xUnit.
frontend/src/
  app/(admin|tutor|parent)/  Màn hình theo vai trò, khung và menu đã dựng sẵn.
  app/(auth)/            Đăng nhập, đăng ký.
  components/            Component dùng chung.
  context/  lib/  types/ Phiên đăng nhập, apiClient, kiểu dữ liệu.
docs/                    Tài liệu của nhóm — đọc docs/README.md trước.
```

## Thành viên

| | Vai trò | Phụ trách |
| :-- | :-- | :-- |
| SV1 Trần Quý Lộc | **Lead** (nhóm trưởng) + Backend | Điều phối nhóm, tiến độ, quản trị Supabase; backend các module nền tảng và quản trị |
| SV2 Nguyễn Trí Kiệt | **GitHub owner** + Frontend | Git, `docs/`, `CODEOWNERS`, biểu mẫu OOAD, merge `main`; màn hình Gia sư, chat, thông báo |
| SV3 Trần Nguyễn Lân | Backend + Database | ERD, tuyển dụng, lộ trình, buổi học, học phí |
| SV4 Nguyễn Anh Kiệt | Frontend + Testing | Màn hình Phụ huynh và Admin, xUnit, Postman |
