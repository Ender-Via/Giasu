// Hook gọi API thông báo (FR-32). Dùng ở chuông của khung trang, SCR-COM-01 và SCR-COM-02 của cả
// ba vai trò nên đặt ở src/lib (frontend-conventions.md §1).
import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/axios";
import type { ApiResponse } from "@/types/auth";
import type {
  NotificationPageResponse,
  NotificationPreferencesResponse,
  UnreadCountResponse,
  UpdateNotificationPreferencesRequest,
} from "@/types/notification";

export const NOTIFICATIONS_PAGE_SIZE = 20;

// Mọi query thông báo chung tiền tố này: ghi xong làm mới một lần là trúng cả danh sách lẫn số
// chưa đọc của chuông (frontend-conventions.md §3.2)
export const NOTIFICATIONS_QUERY_KEY = ["notifications"] as const;
export const UNREAD_COUNT_QUERY_KEY = ["notifications", "unread-count"] as const;
export const notificationsQueryKey = (params: { unreadOnly: boolean; page: number }) =>
  ["notifications", params] as const;
export const NOTIFICATION_PREFERENCES_QUERY_KEY = ["notification-preferences"] as const;

// Danh sách thông báo của mình, mới nhất trước, phân trang ở server (SCR-COM-01)
export function useNotifications(unreadOnly: boolean, page: number) {
  return useQuery({
    queryKey: notificationsQueryKey({ unreadOnly, page }),
    queryFn: async () => {
      const res = await apiClient.get<ApiResponse<NotificationPageResponse>>(
        "/api/notifications",
        { params: { unreadOnly, page, pageSize: NOTIFICATIONS_PAGE_SIZE } }
      );
      const result =
        res.data.data ?? { items: [], page, pageSize: NOTIFICATIONS_PAGE_SIZE, totalCount: 0 };
      const totalPages = Math.max(1, Math.ceil(result.totalCount / NOTIFICATIONS_PAGE_SIZE));
      // Dữ liệu vừa co lại khiến trang đang xem vượt quá tổng số trang: tải ngay trang cuối
      // hợp lệ (frontend-conventions.md §3.4) để không bị kẹt ở trang rỗng.
      if (page > totalPages) {
        const fallbackRes = await apiClient.get<ApiResponse<NotificationPageResponse>>(
          "/api/notifications",
          { params: { unreadOnly, page: totalPages, pageSize: NOTIFICATIONS_PAGE_SIZE } }
        );
        return (
          fallbackRes.data.data ?? {
            items: [],
            page: totalPages,
            pageSize: NOTIFICATIONS_PAGE_SIZE,
            totalCount: result.totalCount,
          }
        );
      }
      return result;
    },
    placeholderData: keepPreviousData,
  });
}

// Số thông báo chưa đọc. Chuông tải lại mỗi 60 giây (ui-screens.md §4.1 [7]); màn hình
// SCR-COM-01 dùng cùng query nên không gọi thêm.
export function useUnreadCount(refetchInterval?: number) {
  return useQuery({
    queryKey: UNREAD_COUNT_QUERY_KEY,
    queryFn: async () => {
      const res = await apiClient.get<ApiResponse<UnreadCountResponse>>(
        "/api/notifications/unread-count"
      );
      return res.data.data?.count ?? 0;
    },
    refetchInterval,
  });
}

function useInvalidateNotifications() {
  const queryClient = useQueryClient();
  return () => queryClient.invalidateQueries({ queryKey: NOTIFICATIONS_QUERY_KEY });
}

// Đánh dấu một thông báo đã đọc; bấm là ghi, không hỏi lại (ui-screens.md §4.3)
export function useMarkNotificationRead() {
  const invalidate = useInvalidateNotifications();
  return useMutation({
    mutationFn: async (id: string) => {
      await apiClient.post<ApiResponse<null>>(`/api/notifications/${id}/read`);
    },
    onSettled: invalidate,
  });
}

export function useMarkAllNotificationsRead() {
  const invalidate = useInvalidateNotifications();
  return useMutation({
    mutationFn: async () => {
      await apiClient.post<ApiResponse<null>>("/api/notifications/read-all");
    },
    onSettled: invalidate,
  });
}

// Cấu hình email theo loại; backend chỉ trả các loại thuộc vai trò (SCR-COM-02)
export function useNotificationPreferences() {
  return useQuery({
    queryKey: NOTIFICATION_PREFERENCES_QUERY_KEY,
    queryFn: async () => {
      const res = await apiClient.get<ApiResponse<NotificationPreferencesResponse>>(
        "/api/notification-preferences"
      );
      return res.data.data?.items ?? [];
    },
  });
}

export function useUpdateNotificationPreferences() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: UpdateNotificationPreferencesRequest) => {
      const res = await apiClient.put<ApiResponse<NotificationPreferencesResponse>>(
        "/api/notification-preferences",
        body
      );
      return res.data.data?.items ?? [];
    },
    onSuccess: (items) => {
      queryClient.setQueryData(NOTIFICATION_PREFERENCES_QUERY_KEY, items);
    },
    onSettled: () =>
      queryClient.invalidateQueries({ queryKey: NOTIFICATION_PREFERENCES_QUERY_KEY }),
  });
}
