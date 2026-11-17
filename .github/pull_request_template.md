<!-- Tiêu đề PR = tiêu đề thẻ trong file kế hoạch, ví dụ: [BE][FR-09] API ứng tuyển, giới hạn 5 phiếu chờ -->

## Làm gì
<!-- 1–3 câu: chức năng nào, cho vai trò nào -->

## Endpoint / màn hình
<!-- Backend: METHOD /api/...   Frontend: /tutor/... (UI-xx) -->
-

## Mã yêu cầu
<!-- FR-xx, UC-xx, quy tắc BR-xx, quyết định Dxx đã áp dụng -->

## Đã test thế nào
<!-- Mỗi dòng một kịch bản: điều kiện → kết quả thấy được. Ghi rõ cái gì CHƯA kiểm được -->
- [ ] Ca đúng:
- [ ] Ca dữ liệu sai (400):
- [ ] Ca sai vai trò (403) / ngoài phạm vi (404):
- [ ] Backend: `dotnet build -warnaserror` + `dotnet test` sạch / Frontend: `npm run build` + `npm run lint` sạch

## Thẻ kế hoạch
<!-- Mã thẻ trong file kế hoạch, ví dụ S03-BE-02 -->
