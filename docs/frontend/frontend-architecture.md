# Kiến trúc Frontend — Gia Sư Kết Nối

## 0. Về tài liệu này

Frontend được tổ chức thế nào: công nghệ, thư mục, routing và chặn quyền, cách lấy dữ liệu, state,
xác thực, biến môi trường và cách chạy cho 3 vai trò `Admin`, `Tutor`, `Parent`.

| Tài liệu | Trả lời câu hỏi |
| :---- | :---- |
| File này | Frontend được dựng thế nào, dữ liệu và phiên đăng nhập đi qua đâu |
| `frontend/ui-screens.md` | Màn hình hiện gì, gọi API nào, bấm nút thì làm gì |
| `frontend/design-system.md` | Hiện bằng component nào, màu gì, cỡ nào |
| `frontend/frontend-conventions.md` | Viết code thế nào: thư mục một màn hình, tên, query key, form, danh sách cấm |

---

## 1. Công nghệ

| Thành phần | Phiên bản | Ghi chú |
| :---- | :---- | :---- |
| Next.js | 16.3.5 | App Router. Build bằng Turbopack, mặc định của Next.js 16 |
| React | 19.2.8 | |
| TypeScript | 5 | `strict: true`; alias `@/*` → `src/*` |
| Tailwind CSS | 4 | Qua `@tailwindcss/postcss`; token màu trong `app/globals.css` (`design-system.md` §3) |
| TanStack Query | 5 | Mọi đọc và ghi dữ liệu (D03) |
| React Hook Form | 7 | Mọi form (D03) |
| Axios | 1 | Một instance duy nhất `apiClient` (§5) |
| ESLint | 9 | `eslint-config-next` (core-web-vitals và typescript) |
| Node.js | 20.9 trở lên | Next.js 16 không chạy trên bản cũ hơn |

Font Be Vietnam Pro nạp qua `next/font/google`; biểu tượng là SVG viết thẳng trong `Icons.tsx`;
không nạp gì từ CDN (D03). Không thêm package khi chưa hỏi GitHub owner (D03): dự án không có thư viện UI,
thư viện ngày giờ, store toàn cục hay thư viện test.

---

## 2. Thư mục

```text
frontend/
├── .env.example                  ← mẫu biến môi trường, chép thành .env.local (§7)
└── src/
    ├── app/
    │   ├── layout.tsx            ← khung HTML, font, bọc <Providers>; sửa phải được GitHub owner đồng ý
    │   ├── providers.tsx         ← QueryClientProvider + AuthProvider
    │   ├── globals.css           ← Tailwind và token màu; sửa phải được GitHub owner đồng ý
    │   ├── page.tsx              ← trang chủ: chuyển hướng theo vai trò (§3)
    │   ├── (auth)/login, register ← SCR-AUTH-01, SCR-AUTH-02
    │   └── (<nhóm>)/             ← (admin) (tutor) (parent)
    │       ├── layout.tsx        ← menu của vai trò, bọc DashboardLayout và RoleGuard
    │       └── <vai-trò>/<màn-hình>/
    │           ├── page.tsx
    │           ├── _components/  ← component chỉ màn hình này dùng
    │           └── _lib/         ← hook TanStack Query, quy tắc kiểm tra ô nhập
    ├── components/               ← component dùng chung, xuất qua index.ts (design-system.md §5)
    │   └── screens/              ← màn hình dùng chung nhiều vai trò (SCR-COM-*)
    ├── context/AuthContext.tsx   ← phiên đăng nhập (§6)
    ├── lib/
    │   └── axios.ts              ← apiClient, ApiError, toApiError (§5)
    └── types/                    ← kiểu phản chiếu DTO của backend
```

Tổ chức theo vai trò rồi theo màn hình: mỗi màn hình tự chứa component và hook của nó. Code dùng từ
hai vai trò trở lên mới đưa lên `src/components/`, `src/lib/`, `src/types/`
(`frontend-conventions.md` §1). Ai phụ trách thư mục nào: `onboarding/team-workflow.md` §2.

---

## 3. Routing và chặn quyền

- **Route group theo vai trò.** Tên trong ngoặc như `(tutor)` không vào URL, chỉ để mỗi vai trò có
  `layout.tsx` riêng. Thư mục con ngay dưới tạo tiền tố URL bằng claim `role` viết thường:
  `(tutor)/tutor/profiles/page.tsx` → `/tutor/profiles`. Tiền tố là bắt buộc vì nhiều vai
  trò có trang cùng tên.
- **Trang chủ `src/app/page.tsx`** là nơi duy nhất chọn trang theo vai trò: chờ khôi phục phiên xong
  (`isLoading` = `false`), chưa đăng nhập thì sang `/login`, đã đăng nhập thì sang
  `/<role viết thường>`. Trang đăng nhập sau khi thành công và layout gặp sai vai trò đều chỉ
  `router.replace("/")`.
- **`RoleGuard`** bọc nội dung trong `layout.tsx` của mỗi vai trò, nhận `allowedRole`. Đang khôi
  phục phiên thì hiện vòng quay; không có phiên thì sang `/login`; sai vai trò thì về `/`. Không có
  trang "Không có quyền" riêng.
- Chặn ở giao diện chỉ để điều hướng. Quyền thật do backend kiểm tra ở mọi request (dependency
  `get_current_auth_user`, service kiểm `users.is_active`, phạm vi dữ liệu trả 404).
- Bản đồ màn hình, menu và hành vi điều hướng: `ui-screens.md` §2.

---

## 4. Render và lấy dữ liệu

- Trang có gọi API hay dùng hook là Client Component (`"use client"`). Trang khung chỉ hiện
  `UnderConstruction` không cần.
- Dữ liệu nghiệp vụ chỉ lấy ở trình duyệt qua `apiClient` bọc trong TanStack Query. Ngoại lệ duy
  nhất là `supabase.auth` cho đăng nhập/đăng xuất/refresh phiên; frontend không nói chuyện thẳng
  với PostgreSQL hay bảng/Storage Supabase (D01).
- Next.js dựng sẵn khung trang tĩnh lúc build (`○ (Static)` trong kết quả `npm run build`); dữ liệu
  điền vào sau khi trang chạy ở trình duyệt.

---

## 5. Gọi API

- **`apiClient`** trong `src/lib/axios.ts` là Axios instance duy nhất: `baseURL` lấy từ
  `NEXT_PUBLIC_API_BASE_URL` (mặc định `http://localhost:5015`), header JSON.
  - Interceptor request gắn `Authorization: Bearer <token>` từ biến token trong bộ nhớ.
  - Interceptor response: gặp 401 thì kết thúc phiên Supabase local, xóa token và tải lại hẳn trang
    `/login` bằng `window.location.replace`; tải lại hẳn để xóa sạch cache dữ liệu của phiên cũ.
    Riêng `/api/auth/me` trong `login()` đặt `skipAuthRedirect`: `AuthContext` tự đăng xuất rồi giữ
    nguyên trang để hiện đúng lỗi tài khoản khóa hoặc chưa có hồ sơ.
- **Khuôn response** của backend là `ApiResponse<T>` `{ success, data, message, errors }`, kể cả khi
  lỗi (D04); kiểu này ở `src/types/auth.ts`.
- **Lỗi** đọc qua `toApiError(err)` → `ApiError { message, errors, status }`. Cách hiện từng mã:
  `ui-screens.md` §4.2.
- **Kiểu dữ liệu** viết tay trong `src/types/`, phản chiếu record DTO của backend, giữ nguyên tên
  trường camelCase của JSON. Đối chiếu với OpenAPI (`http://localhost:5015/docs`) khi backend
  đã có; trước đó theo dòng "API" của mục SCR và FR. Không sinh kiểu từ OpenAPI (cần thêm package,
  D03).
- **Vai trò được gọi** từng endpoint: `business/user-roles.md` §3; phần đã có: `api/da-trien-khai.md`.
- **Hook gọi API** đặt trong `_lib/*-api.ts` của màn hình; query key, làm mới sau khi ghi và mặc định
  của QueryClient ở `frontend-conventions.md` §3.
- **Tệp minh chứng** luôn xem qua URL ký hạn 60 phút do API trả, URL hết hạn thì xin lại (D16);
  frontend không gọi Supabase Storage.

---

## 6. State và xác thực

### 6.1 State

| Loại | Giữ ở đâu | Ghi chú |
| :---- | :---- | :---- |
| Dữ liệu từ server | Cache của TanStack Query | `QueryClient` tạo một lần trong `providers.tsx`, dùng mặc định (`frontend-conventions.md` §3.3). Mất khi tải lại trang |
| Phiên đăng nhập | `AuthContext` | `user` (`userId`, `fullName`, `role`), `token`, `isLoading`, `login()`, `logout()` qua `useAuth()` |
| State của một màn hình | `useState` trong `page.tsx` | Bộ lọc, trang, hộp thoại đang mở; truyền xuống component con qua props |

Không dùng store toàn cục (Redux, Zustand...) và không lưu dữ liệu nghiệp vụ vào `localStorage` hay
`sessionStorage`. Hiện chưa màn hình nào giữ state trên URL. Chưa chốt cách giữ con đang chọn khi
phụ huynh chuyển giữa các màn hình (`ui-screens.md` §10).

### 6.2 Xác thực

| Việc | Cách làm | Quyết định |
| :---- | :---- | :---- |
| Đăng nhập | `login()` gọi `supabase.auth.signInWithPassword()`, rồi gửi access token tới `GET /api/auth/me` để lấy `userId`, `fullName`, `role` | D06 |
| Giữ token | Supabase JS persist session; Axios chỉ giữ access token hiện tại trong bộ nhớ | D06 |
| Khôi phục phiên | `AuthProvider` gọi `supabase.auth.getSession()`, gắn access token rồi gọi `/api/auth/me`; xong mới đặt `isLoading = false` | D06 |
| Hết hạn | Supabase JS tự refresh; sự kiện `TOKEN_REFRESHED` cập nhật Axios và tải lại hồ sơ nghiệp vụ | D06 |
| Đăng xuất | `supabase.auth.signOut({ scope: "local" })`, xóa token/bộ nhớ và về `/login` | D06 |
| Bị khóa | `/api/auth/me` và API nghiệp vụ kiểm `users.is_active`; 401 làm interceptor kết thúc phiên local | D06 |
| Vai trò | Không đọc claim role Supabase; luôn lấy `role` từ `/api/auth/me` | D05, D06 |

Trường `role` từ `/api/auth/me` là chuỗi tiếng Anh (`Admin`, `Tutor`, `Parent`); nhãn tiếng
Việt lấy từ `ROLE_VIETNAMESE_LABELS` trong `DashboardLayout.tsx`.

---

## 7. Biến môi trường, chạy và kiểm tra

- Chép `frontend/.env.example` thành `frontend/.env.local`: `NEXT_PUBLIC_API_BASE_URL`,
  `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`. `.env.local` không commit;
  không dùng service-role key ở trình duyệt.
- Frontend chạy ở cổng 3000. Đổi cổng thì phải thêm origin vào `CORS_ALLOWED_ORIGINS` của backend.

```bash
cd frontend
npm install
npm run dev      # http://localhost:3000
npm run build    # Definition of Done: build sạch
npm run lint
```

- Chưa có công cụ test tự động cho frontend. Trước khi mở PR kiểm tay theo checklist ở
  `testing/testing-strategy.md` §3.3.
- Màn hình đang chờ API thì dựng với dữ liệu giả trước; cách làm ở `testing/testing-strategy.md`
  §3.2.

---

## 8. Quyết định liên quan

D01 (frontend chỉ đi qua API), D03 (công nghệ, không thêm package), D04 (khuôn response), D06 (xác
thực, lưu token, thu hồi phiên), D12 (chat polling), D16 (tệp qua URL ký).
