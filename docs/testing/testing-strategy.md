# Chiến lược kiểm thử

## 0. Về tài liệu này

Kiểm gì, bằng gì, ca kiểm bám vào mã nào, dữ liệu test lấy ở đâu, phải kiểm gì trước khi mở hay
duyệt PR. SV4 giữ file này (thẻ S02-09); khung dưới đây lấy từ dự án Nhà trẻ, thêm phần xUnit mà
bên đó chưa có.

### 0.1 Các loại kiểm thử

| Loại | Công cụ | Phạm vi | Ai viết |
| :-- | :-- | :-- | :-- |
| Unit test | xUnit, `backend/GiaSu.Tests` | Mỗi `BR-xx` trong Service và Validator | Người làm thẻ backend; SV4 bổ sung ca biên |
| Kiểm thử API | Postman Collection, chạy bằng Runner hoặc `newman` | Mỗi endpoint: đúng, dữ liệu sai, sai vai trò, ngoài phạm vi | Người làm thẻ backend; SV4 gom và dọn |
| Kiểm thử giao diện | Kiểm tay theo checklist §3.3 | Mỗi màn hình SCR | Người làm thẻ frontend; người review chạy lại |
| Nghiệm thu | AC trong `requirements/acceptance-criteria.md` | Mỗi AC là một kịch bản | Kịch bản theo vai trò ở S12 |

CI (`.github/workflows/ci.yml`) chạy `dotnet build -warnaserror`, `dotnet test`, `npm run lint`,
`npm run build` cho mọi PR.

### 0.2 Gắn ca kiểm với mã

- Mỗi AC của thẻ có **ít nhất một ca kiểm** trước khi merge: unit test, request Postman, hoặc kiểm tay.
- Mục "Đã test thế nào" của PR liệt kê theo mã AC: mỗi dòng là mã AC, đã làm gì, ra kết quả gì.
  AC không kiểm được thì ghi lý do.
- Tên unit test nói điều kiện và kết quả, kèm mã trong chú thích:
  `public void Gui_duyet_khi_chua_co_minh_chung_thi_bi_tu_choi() // AC-PROFILE-06, BR-04`.
- Postman: tên folder có mã module (`PROFILE — Hồ sơ gia sư (FR-03, FR-04, FR-36)`), tên request
  `<mã AC> - <mô tả> (<status>)`, ví dụ `AC-PROFILE-02 - Tạo hồ sơ thứ 6 (409)`.
- Cuối kỳ (S13), SV4 chép các ca này sang sheet P4T_01 thành `TC-xx`, mỗi TC ghi mã FR/AC.

### 0.3 Dữ liệu test trên database dùng chung

Cả nhóm dùng chung một database, nên:

- Mỗi vai trò có một tài khoản test cố định (biến môi trường của Postman Collection): `admin@giasu.local`,
  `giasu.test@giasu.local`, `phuhuynh.test@giasu.local`. Không khóa, không đổi mật khẩu các tài
  khoản này.
- Ưu tiên ca không ghi dữ liệu: xem danh sách, 400, 401, 403, 404.
- Bản ghi tạo ra khi test có tên bắt đầu bằng `[TEST]` (tiêu đề hồ sơ, tiêu đề tin, họ tên học
  sinh). Tài khoản tạo thêm để thử đăng ký dùng email `test.<tên>.<số>@giasu.local`.
- Thao tác gửi thông báo tới người thật hoặc không hoàn tác được (duyệt, từ chối, ghi nhận thanh
  toán) chỉ làm trên dữ liệu `[TEST]`.
- `POST /api/auth/login` và `/register` giới hạn 5 lần/phút/IP; gặp 429 thì chờ hết phút.

---

## 1. Lệnh

```bash
dotnet test backend/GiaSu.slnx
npx newman run docs/testing/GiaSu.postman_collection.json -e docs/testing/local.postman_environment.json
cd frontend && npm run lint && npm run build
```

Collection và environment do SV4 tạo ở thẻ S01-09; environment **không** chứa mật khẩu thật của
tài khoản cá nhân, chỉ tài khoản test.

---

## 2. Backend

### 2.1 Unit test

- Test Service bằng repository giả viết tay (class nhỏ cài interface trong `GiaSu.Tests`), không
  thêm thư viện mock khi chưa hỏi GitHub owner (D03).
- Mỗi `BR-xx` của thẻ: một ca đúng, một ca vi phạm, và ca biên (đúng giới hạn, vượt 1). Ví dụ
  BR-23: có 4 hồ sơ tạo được, có 5 hồ sơ thì 409.
- Validator test bằng cách gọi thẳng `Validate(...)` như `LoginRequestValidatorTests`.

### 2.2 Postman

- Collection chạy đúng thứ tự: folder 0 đăng nhập 3 vai trò và lưu token vào biến; folder cuối là
  ca giới hạn tần suất.
- Mỗi endpoint mới: ca đúng, ca 400, ca sai vai trò (403); đụng bản ghi cụ thể thì thêm ca ngoài
  phạm vi (404).
- Request ghi dữ liệu để trong folder riêng, đặt tên `W — ...`, chỉ ghi dữ liệu `[TEST]`.

---

## 3. Frontend

### 3.1 Công cụ

Chrome hoặc Edge với DevTools: Device toolbar (375×812, 1280), Network → Slow 3G / Offline,
Lighthouse → Accessibility. Kiểm cuộn ngang bằng Console:
`document.documentElement.scrollWidth > document.documentElement.clientWidth` phải là `false`.

### 3.2 Dữ liệu giả khi API chưa có

Màn hình có API ghi "(chờ Sxx-yy)" trong mục SCR thì dựng giao diện với dữ liệu giả trước:

- Kiểu dữ liệu viết trước trong `src/types/` theo dòng "API" của SCR và FR.
- Dữ liệu giả ở `_lib/<tài-nguyên>-mock.ts`; hook trong `_lib/*-api.ts` giữ đúng tên và kiểu trả
  về như khi có API, chỉ `queryFn` trả dữ liệu giả, kèm chú thích
  `// DỮ LIỆU GIẢ: thay bằng apiClient khi có <endpoint>`.
- Thử rỗng và lỗi bằng cách cho `queryFn` giả trả `[]` hoặc `throw`.
- **Không merge khi còn dữ liệu giả.** Muốn xin góp ý sớm thì mở PR Draft, ghi rõ phần nào còn giả.

### 3.3 Checklist kiểm một màn hình

Người làm chạy hết trước khi mở PR; người review chạy lại. Mục nào không kiểm được thì ghi lý do
vào PR.

**A. Build** — [ ] `npm run lint`, `npm run build` sạch.

**B. Đúng đặc tả**
- [ ] Đủ các vùng trong khối Bố cục và bảng Vùng của mục SCR.
- [ ] Từng dòng trong Hành vi: bấm thử, xem Network gửi đúng endpoint, tham số, body.
- [ ] Câu rỗng, câu lỗi, nhãn đúng `ui-screens.md`; giá trị liệt kê dùng nhãn tiếng Việt.
- [ ] Ngày giờ theo giờ Việt Nam; tiền định dạng `vi-VN`.
- [ ] Không có mã FR, BR, AC hay id kỹ thuật trên giao diện.

**C. Ba trạng thái**
- [ ] Đang tải: Slow 3G, tải lại trang, thấy vòng quay hoặc hàng chờ.
- [ ] Lỗi lần đầu: Offline rồi tải lại, thấy lỗi kèm "Thử lại"; bật mạng, bấm "Thử lại" có dữ liệu.
- [ ] Lỗi khi tải lại: đang có dữ liệu thì chuyển Offline rồi làm mới; dữ liệu cũ vẫn còn, có cảnh báo.
- [ ] Rỗng: dùng tài khoản hoặc bộ lọc không có bản ghi, thấy đúng câu rỗng.

**D. Lỗi từ backend**
- [ ] Ít nhất một lỗi 4xx thật hiện đúng `message` của backend (ví dụ 409: cùng thao tác ở hai tab).
- [ ] Ghi thành công: có dải thành công, dữ liệu trên màn hình đổi theo.
- [ ] 401: đăng xuất ở tab khác rồi thao tác ở tab này, phải về `/login`.

**E. Điện thoại** — [ ] 375 px không cuộn ngang, bảng thành thẻ, nút chính cao ≥ 44 px.
[ ] 1280 px đúng bố cục desktop.

**F. Truy cập** — [ ] Tab qua mọi nút và ô, thấy viền focus; hộp thoại đóng bằng Esc.
[ ] Mọi ô có nhãn.

**G. Phân quyền** — [ ] Đăng nhập vai trò khác rồi mở thẳng URL màn hình, phải bị đưa về cổng
của vai trò đó.

### 3.4 Review PR frontend

- Merge thử `develop` vào nhánh PR ở máy mình, `npm run build`, rồi đi checklist §3.3 với mục SCR.
- Ghi góp ý dạng "file:dòng — đặc tả nói gì — code làm gì".
- Chia "cần sửa trước khi merge" (lệch đặc tả, lỗi hành vi, thiếu trạng thái) và "nên sửa" (hình
  thức, gọn code).

---

## 4. Kịch bản người dùng (S12)

Mỗi vai trò một kịch bản trọn vòng đời, chạy trên bản `develop` sau khi đóng băng; lỗi ghi vào tab
"Lỗi" của file kế hoạch. Kịch bản viết ở thẻ S12 theo AC đã có.
