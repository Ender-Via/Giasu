# Quy ước code Frontend — Gia Sư Kết Nối

## 0. Về tài liệu này

Cách viết code frontend để mọi màn hình theo cùng một khuôn (bộ khung `apiClient`, `AuthContext`,
component dùng chung).

Đọc cùng:

- `frontend/ui-screens.md` — màn hình hiện gì và làm gì. Hành vi ghi ở đó, file này không chép lại.
- `frontend/design-system.md` — màu, chữ, component dùng chung, responsive, truy cập.
- `frontend/frontend-architecture.md` — công nghệ, thư mục, routing, state, xác thực, cách chạy.
- `testing/testing-strategy.md` §3 — kiểm một màn hình trước khi mở PR.

**Module mẫu:** chưa có. Màn hình đầu tiên làm xong (SCR-TUT-01, thư mục
`src/app/(tutor)/tutor/profiles/`) sẽ thành khuôn cho các màn sau, theo thứ tự:
`page.tsx` → `_components/` → `_lib/tutor-profiles-api.ts`, `_lib/tutor-profile-rules.ts` →
`src/types/user.ts`.

---

## 1. Thư mục của một màn hình

```text
src/app/(<nhóm>)/<vai-trò>/<màn-hình>/
├── page.tsx                  ← ghép các phần, giữ state của trang (bộ lọc, trang, hộp thoại đang mở)
├── _components/              ← component chỉ màn hình này dùng
└── _lib/
    ├── <tài-nguyên>-api.ts   ← hook TanStack Query và query key
    └── <tài-nguyên>-rules.ts ← quy tắc kiểm tra ô nhập, hàm thuần
src/types/<tài-nguyên>.ts     ← kiểu phản chiếu DTO backend, bảng nhãn tiếng Việt của enum
```

- Thư mục bắt đầu bằng `_` không thành route.
- Làm màn hình thì thay `page.tsx` đã có, không tạo route ngoài `ui-screens.md`
  (`ui-screens.md` §3).
- Code dùng lại giữa các màn hình đặt theo phạm vi dùng:

  | Dùng ở | Đặt ở |
  | :---- | :---- |
  | Một màn hình | `_components/`, `_lib/` của màn hình đó |
  | Nhiều màn hình cùng một vai trò | `_lib/` của màn hình đầu tiên dùng nó; màn hình sau import từ đó |
  | Từ hai vai trò trở lên | `src/components/` (component), `src/lib/` (hàm), `src/types/` (kiểu) |
  | Cả một màn hình dùng chung (`SCR-COM-*`) | `src/components/screens/<Tên>Screen.tsx`; `page.tsx` của mỗi vai trò chỉ render component đó |

  Ví dụ hàm định dạng ngày theo giờ Việt Nam và `normalizeForSearch` dùng ở nhiều vai trò, nên thuộc
  `src/lib/`; gặp bản đang nằm trong `_lib/` của một màn hình thì chuyển lên khi sửa tới.

---

## 2. Đặt tên

| Loại | Quy ước | Ví dụ |
| :---- | :---- | :---- |
| File component | PascalCase, trùng tên component chính trong file | `UserFormModal.tsx` |
| File trong `_lib/` | kebab-case theo tài nguyên | `tutor-profiles-api.ts`, `tutor-profile-rules.ts` |
| Hook đọc | `use` + tài nguyên | `useUsers`, `useHomeroomChildren` |
| Hook ghi | `use` + động từ + tài nguyên | `useCreateUser`, `useChangeRole` |
| Query key | Hằng `XXX_QUERY_KEY`, hoặc hàm `xxxQueryKey(params)` khi có tham số | `USERS_QUERY_KEY` |
| Kiểu DTO | Trùng tên record của backend | `UserResponse`, `CreateUserRequest` |
| Bảng nhãn enum | `XXX_LABELS: Record<Enum, string>`, đặt cạnh kiểu trong `src/types/` | Riêng vai trò là `ROLE_VIETNAMESE_LABELS` trong `DashboardLayout.tsx` |
| Trường dữ liệu | Đúng tên JSON của backend (camelCase), không đổi tên khi nhận về | `checkInTimeUtc`, `healthNotes` |

Chú thích trong code viết tiếng Việt. Code thực hiện một quy tắc thì ghi mã FR, BR, D, AC trong chú
thích; không đưa các mã này lên giao diện.

---

## 3. Gọi API và dữ liệu từ server

- Chỉ gọi qua `apiClient` trong `src/lib/axios.ts`. Không `axios.create()` mới, không `fetch`.
- Mọi đọc và ghi qua TanStack Query (D03). Không tải dữ liệu bằng `useEffect` với `useState`.
- Hook đặt trong `_lib/*-api.ts`. Component không gọi `apiClient` trực tiếp.
- Ghi kiểu cho mọi lời gọi: `apiClient.get<ApiResponse<UserResponse[]>>(...)`, và mở gói trong
  `queryFn`: `return res.data.data ?? []`.
- Tham số lọc truyền qua `params` của axios, không tự ghép chuỗi query.

### 3.1 Query key

- Phần tử đầu là tên tài nguyên, lấy theo đoạn đường dẫn API: `/api/tutor-profiles/mine` →
  `["tutor-profiles", "mine"]`, `/api/notifications?unreadOnly=true&page=2` →
  `["notifications", { unreadOnly: true, page: 2 }]`, `/api/notifications/unread-count` →
  `["notifications", "unread-count"]`.
- Tham số lọc gộp vào một object ở phần tử thứ hai.
- Hai màn hình đọc cùng một tài nguyên dùng cùng tiền tố, để làm mới theo tiền tố là trúng cả hai.

### 3.2 Làm mới sau khi ghi

- Mutation làm mới theo tiền tố tài nguyên trong `onSettled`, kể cả khi lỗi: 404 hay 409 thường do
  người khác vừa đổi dữ liệu, danh sách đang hiện đã cũ. Mọi hook ghi theo cùng
  khuôn này.
- Ghi một tài nguyên mà làm đổi tài nguyên khác đang hiện trên màn hình của cùng người dùng thì làm
  mới cả tài nguyên đó. Thêm dòng vào bảng khi có API mới:

  | Ghi | Làm mới thêm | Vì sao |
  | :---- | :---- | :---- |
  | `student-verifications` (gửi, duyệt, từ chối) | `tutor-profiles` | Dải xác thực ở SCR-TUT-01 đọc trạng thái xác thực |
  | Mọi thao tác Admin duyệt/từ chối | `notifications` | Admin vừa xử lý xong, chuông nên giảm theo nếu có thông báo liên quan |
  | `notifications` (đọc, đọc tất cả) | — | Cùng tiền tố `["notifications"]` đã gồm `unread-count` của chuông |

  Màn hình khác đọc cùng tài nguyên tự được làm mới nhờ cùng tiền tố, không cần ghi vào bảng.

- Muốn dòng vừa ghi đổi ngay, không chờ tải lại xong, thì `setQueryData` bằng bản ghi API trả về.
- Không `await` việc làm mới trong `onSuccess` nếu không muốn nút bị khóa suốt lúc tải lại.

### 3.3 Mặc định của QueryClient và các bẫy đã gặp

`providers.tsx` tạo `new QueryClient()` không cấu hình, nên đang dùng mặc định của TanStack Query:

| Mặc định | Hệ quả | Cách làm |
| :---- | :---- | :---- |
| Query thử lại 3 lần, chờ 1, 2, 4 giây | Lỗi 400, 404, 409 hiện ra sau khoảng 7 giây | Query mà lỗi 4xx là kết quả bình thường (tra cứu theo lựa chọn của người dùng) đặt `retry: false` |
| `staleTime` = 0, tải lại khi quay lại tab | Mạng chập chờn thì lần tải lại có thể lỗi khi đã có dữ liệu | Giữ dữ liệu cũ, chỉ cảnh báo (`ui-screens.md` §4.2): hiện lỗi thay cả danh sách khi `data === undefined`, không dựa riêng vào `isError`. |
| `refetch()` chạy cả khi query đang `enabled: false` | Gọi API khi thiếu tham số, nhận 400 | Kiểm tra điều kiện trước khi gọi `refetch()` |

Lần tải đầu dùng `isPending` (chưa có dữ liệu). `isLoading` là `isPending && isFetching`, nên query
đang tắt có `isLoading` = `false`.

### 3.4 Phân trang

Phân trang ở đâu tùy endpoint (`api/api-conventions.md` §2.1):

| Endpoint | Phân trang ở | Cách làm |
| :---- | :---- | :---- |
| Trả `{ items, page, pageSize, totalCount }` (hiện có `GET /api/notifications`) | Server | Gửi `page` và `pageSize` qua `params`; số trang tính từ `totalCount`. Đưa `page` vào query key; thêm `placeholderData: keepPreviousData` để trang cũ còn hiện trong lúc tải trang mới |
| Trả toàn bộ danh sách | Client | Lọc và tìm trên toàn bộ danh sách trước, rồi mới cắt trang bằng `slice`, để bộ lọc áp lên mọi bản ghi chứ không chỉ trang đang xem |

Quy tắc chung:

- **Cỡ trang mặc định là 20 bản ghi**, trùng mặc định `pageSize` của backend. Màn hình cần cỡ khác thì
  ghi ở mục SCR trong `ui-screens.md`.
- **Không phân trang** danh sách có giới hạn tự nhiên mà người dùng cần nhìn hết một lượt, như cả lớp
  (hồ sơ của gia sư — tối đa 5; học sinh của phụ huynh).
- Đổi bộ lọc, ô tìm hay cách xem thì về trang 1.
- Trang đang xem lớn hơn số trang (dữ liệu vừa ít đi sau khi tải lại hay sau khi lọc) thì hiện trang
  cuối: `Math.min(page, totalPages)`.
- Chỉ hiện `Pagination` khi có hơn một trang và đã có dữ liệu; lúc đang tải lần đầu hay lỗi thay cả
  danh sách thì không hiện.
- Giữ thứ tự backend trả về; không tự sắp xếp lại trừ khi mục SCR ghi.
- Bảng trên màn rộng và thẻ trên màn hẹp dùng chung một trang và một `Pagination`.
- Cột số thứ tự (nếu có) đánh liền qua các trang: `(page - 1) * pageSize + index + 1`.

---

## 4. Form

- Mọi form dùng React Hook Form (D03). Ô nhập dùng component của `Form.tsx` với `register`.
- Quy tắc kiểm tra đặt trong `_lib/*-rules.ts`, dạng `{ validate: { ... } }`, cùng giới hạn và cùng
  câu thông báo với validator backend. Khuôn: `user-rules.ts`. Bỏ khoảng trắng hai đầu theo
  `ui-screens.md` §4.3.
- Lỗi từ API trong form hiện một khung phía trên các ô (khuôn `ApiErrorAlert`). Backend chỉ trả danh
  sách câu, không gắn với tên trường, nên không gán lỗi API vào từng ô.
- Khóa nút gửi khi mutation `isPending`; chỉ đóng hộp thoại và xóa form trong `onSuccess`.
- Ô chọn giá trị liệt kê bắt đầu rỗng: `Select` có `placeholder`.

---

## 5. Lỗi

- Luôn đọc lỗi qua `toApiError(err)`: có `errors` thì liệt kê từng dòng, không có thì hiện `message`.
  `toApiError` đã có câu dự phòng khi backend không trả `message`.
- Không rẽ nhánh theo mã HTTP để tự viết câu thông báo, không thay `message` của backend bằng câu viết
  cứng. Cần hành động khác nhau theo tình huống (ví dụ 404 thì tải lại danh sách) thì làm cùng một
  việc cho mọi lỗi, như làm mới cả hai query.
- Cách hiện từng mã: `ui-screens.md` §4.2. 401 do interceptor xử lý, màn hình không làm gì.

---

## 6. Ngày giờ, chữ và từ ngữ

**Ngày giờ** hiển thị theo `ui-screens.md` §4.4. Khi viết code:

- "Hôm nay" lấy bằng `new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Ho_Chi_Minh" })
  .format(new Date())`, ra `yyyy-MM-dd`. Không dùng `new Date().toISOString().slice(0, 10)`: đó là
  ngày theo UTC, trước 7 giờ sáng giờ Việt Nam sẽ ra ngày hôm qua.
- Trường kết thúc bằng `Utc` định dạng bằng `Intl.DateTimeFormat("vi-VN", { timeZone:
  "Asia/Ho_Chi_Minh", ... })`, không theo múi giờ của máy.
- Trường chỉ có ngày (`yyyy-MM-dd`) không đổi múi giờ: tách chuỗi, hoặc tạo `Date` từ
  `` `${date}T00:00:00+07:00` `` rồi định dạng theo `Asia/Ho_Chi_Minh`.

**Ngôn ngữ.** Giao diện chỉ có tiếng Việt, không dùng thư viện i18n; chữ viết thẳng trong component.

**Từ ngữ:**

| Dùng | Không dùng |
| :---- | :---- |
| gia sư | thầy, cô, giáo viên, tutor |
| học sinh | con, bé, học viên |
| phụ huynh | cha mẹ, khách hàng |
| tin tìm gia sư, tin | bài đăng, job, lớp |
| phiếu ứng tuyển, ứng tuyển | đơn, apply |
| hồ sơ gia sư | profile, CV |
| buổi học | tiết, ca |
| lộ trình học | kế hoạch, path, roadmap |
| học phí (theo buổi) | tiền công, lương |
| Quản trị viên | Admin (trên giao diện) |

Động từ trên nút:

| Nút | Dùng khi |
| :---- | :---- |
| Lưu | Ghi một form |
| Hủy | Đóng form hay hộp thoại, không ghi |
| Đóng | Đóng hộp thoại chỉ xem |
| Thử lại | Gọi lại sau khi tải lỗi |
| Làm mới | Người dùng chủ động tải lại dữ liệu mới nhất |
| Xóa bộ lọc | Đưa mọi bộ lọc về mặc định; một màn hình chỉ dùng một tên cho việc này |

Văn bản người dùng nhập (ghi chú, lưu ý, mô tả) hiển thị dạng văn bản thuần, giữ xuống dòng bằng
`whitespace-pre-wrap`. Không đưa lên giao diện mã FR, BR, D, AC hay id kỹ thuật.

---

## 7. Style

- Viết bằng lớp Tailwind 4 trong `className`. Không CSS module, không `style` inline trừ giá trị phải
  tính lúc chạy.
- Màu, chữ, khoảng cách theo `design-system.md`. Không ghi đè màu, padding, bo góc của component
  dùng chung (`design-system.md` §1 mục 3).
- Ghép lớp có điều kiện bằng template string; không thêm `clsx` hay thư viện tương tự (D03).

---

## 8. Danh sách cấm

- Dùng `any`; ép kiểu bằng `as` để lách lỗi kiểu.
- `axios.create()` mới, `fetch`, hay gọi `apiClient` trong component.
- Rẽ nhánh theo mã HTTP để tự viết câu lỗi.
- Mã màu hex, màu Tailwind ngoài bảng của `design-system.md`, ghi đè lớp của component dùng chung.
- Thêm package khi chưa hỏi GitHub owner (D03), kể cả thư viện ngày giờ, icon, UI hay ghép class.
- Lưu dữ liệu nghiệp vụ vào `localStorage` hay `sessionStorage`. Chỉ `AuthContext` lưu token để
  khôi phục phiên (D06).
- Ghi số điện thoại, mã số sinh viên, URL ký của tệp ra `console`, hoặc đưa dữ liệu cá nhân vào URL (NFR-02).
- `dangerouslySetInnerHTML`.
- Sửa `app/layout.tsx`, `app/globals.css` khi chưa có GitHub owner đồng ý; sửa `src/components/` mà không
  báo người phụ trách bộ component.
- Tạo route ngoài `ui-screens.md`.
- Mã FR, BR, D, AC trên giao diện.

---

## 9. Trước khi mở PR

- `npm run build` sạch (Definition of Done). Chạy `npm run lint`, file mình sửa không thêm cảnh báo.
- Kiểm tay theo checklist ở `testing/testing-strategy.md` §3.3: đúng đặc tả, ba trạng thái, lỗi từ
  backend, điện thoại, truy cập, phân quyền.
- Ghi kết quả vào mục "Đã test thế nào" của PR theo mã AC (`testing/testing-strategy.md` §0.2).
- Không còn dữ liệu giả trong code (`testing/testing-strategy.md` §3.2).
