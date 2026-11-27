import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/axios";
import type { ApiResponse } from "@/types/auth";
import type {
  Availability,
  TutorProfileDetailResponse,
  TutorProfileEvidenceResponse,
  TutorProfileResponse,
  TutorProfileUpsertRequest,
} from "@/types/tutor-profile";

// Mọi query của hồ sơ dùng chung tiền tố này để ghi xong làm mới một lần là trúng cả danh sách
// lẫn chi tiết (frontend-conventions.md §3.1, §3.2)
export const TUTOR_PROFILES_QUERY_KEY = ["tutor-profiles"] as const;
export const MY_TUTOR_PROFILES_QUERY_KEY = ["tutor-profiles", "mine"] as const;
export const tutorProfileQueryKey = (id: string) => ["tutor-profiles", id] as const;

// Danh sách hồ sơ của gia sư đang đăng nhập (FR-03)
export function useMyTutorProfiles() {
  return useQuery({
    queryKey: MY_TUTOR_PROFILES_QUERY_KEY,
    queryFn: async () => {
      const res = await apiClient.get<ApiResponse<TutorProfileResponse[]>>(
        "/api/tutor-profiles/mine"
      );
      return res.data.data ?? [];
    },
  });
}

// Chi tiết một hồ sơ kèm minh chứng và URL ký (FR-03, FR-04). 404 là kết quả bình thường khi
// hồ sơ không thuộc mình nên không thử lại (frontend-conventions.md §3.3)
export function useTutorProfile(id: string) {
  return useQuery({
    queryKey: tutorProfileQueryKey(id),
    queryFn: async () => {
      const res = await apiClient.get<ApiResponse<TutorProfileDetailResponse>>(
        `/api/tutor-profiles/${id}`
      );
      return res.data.data;
    },
    retry: false,
  });
}

function useInvalidateTutorProfiles() {
  const queryClient = useQueryClient();
  return () => queryClient.invalidateQueries({ queryKey: TUTOR_PROFILES_QUERY_KEY });
}

export function useCreateTutorProfile() {
  const invalidate = useInvalidateTutorProfiles();
  return useMutation({
    mutationFn: async (body: TutorProfileUpsertRequest) => {
      const res = await apiClient.post<ApiResponse<TutorProfileResponse>>(
        "/api/tutor-profiles",
        body
      );
      return res.data.data;
    },
    onSettled: invalidate,
  });
}

export function useUpdateTutorProfile(id: string) {
  const queryClient = useQueryClient();
  const invalidate = useInvalidateTutorProfiles();
  return useMutation({
    mutationFn: async (body: TutorProfileUpsertRequest) => {
      const res = await apiClient.put<ApiResponse<TutorProfileResponse>>(
        `/api/tutor-profiles/${id}`,
        body
      );
      return res.data.data;
    },
    onSuccess: (updated) => {
      if (!updated) return;
      queryClient.setQueryData<TutorProfileDetailResponse>(
        tutorProfileQueryKey(id),
        (old) => (old ? { ...old, ...updated } : old)
      );
    },
    onSettled: invalidate,
  });
}

// Đổi trạng thái nhận dạy (FR-36): bấm là ghi, không làm hồ sơ phải duyệt lại (BR-25)
export function useSetAvailability() {
  const invalidate = useInvalidateTutorProfiles();
  return useMutation({
    mutationFn: async ({ id, availability }: { id: string; availability: Availability }) => {
      const res = await apiClient.put<ApiResponse<TutorProfileResponse>>(
        `/api/tutor-profiles/${id}/availability`,
        { availability }
      );
      return res.data.data;
    },
    onSettled: invalidate,
  });
}

// Đặt hồ sơ mặc định (BR-02)
export function useSetDefaultProfile() {
  const invalidate = useInvalidateTutorProfiles();
  return useMutation({
    mutationFn: async (id: string) => {
      const res = await apiClient.post<ApiResponse<TutorProfileResponse>>(
        `/api/tutor-profiles/${id}/set-default`
      );
      return res.data.data;
    },
    onSettled: invalidate,
  });
}

// Gửi duyệt (FR-04); backend trả 400 kèm danh sách điều còn thiếu nếu chưa đủ BR-04
export function useSubmitProfile() {
  const invalidate = useInvalidateTutorProfiles();
  return useMutation({
    mutationFn: async (id: string) => {
      const res = await apiClient.post<ApiResponse<TutorProfileResponse>>(
        `/api/tutor-profiles/${id}/submit`
      );
      return res.data.data;
    },
    onSettled: invalidate,
  });
}

// Tải minh chứng: multipart, trường files (FR-04, D16). Không đặt Content-Type bằng tay;
// interceptor của apiClient gỡ header JSON cho FormData để trình duyệt tự gắn boundary (ui-screens.md §4.5).
export function useUploadEvidences(profileId: string) {
  const invalidate = useInvalidateTutorProfiles();
  return useMutation({
    mutationFn: async (files: File[]) => {
      const formData = new FormData();
      files.forEach((file) => formData.append("files", file));
      const res = await apiClient.post<ApiResponse<TutorProfileEvidenceResponse[]>>(
        `/api/tutor-profiles/${profileId}/evidences`,
        formData
      );
      return res.data.data ?? [];
    },
    onSettled: invalidate,
  });
}

// Gỡ minh chứng, chỉ khi hồ sơ Draft hoặc Rejected (BR-26)
export function useRemoveEvidence(profileId: string) {
  const invalidate = useInvalidateTutorProfiles();
  return useMutation({
    mutationFn: async (evidenceId: string) => {
      await apiClient.delete<ApiResponse<null>>(
        `/api/tutor-profiles/${profileId}/evidences/${evidenceId}`
      );
    },
    onSettled: invalidate,
  });
}
