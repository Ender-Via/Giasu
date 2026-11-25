"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  ReactNode,
} from "react";
import { useQueryClient } from "@tanstack/react-query";
import { apiClient, setAuthToken, toApiError, ApiError } from "@/lib/axios";
import { supabase } from "@/lib/supabase";
import type { AuthError } from "@supabase/supabase-js";
import type { ApiResponse, CurrentUserResponse } from "@/types/auth";

interface AuthContextValue {
  user: CurrentUserResponse | null;
  token: string | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

function toSignInError(error: AuthError): ApiError {
  if (error.status === 429 || error.code === "over_request_rate_limit") {
    return new ApiError(
      "Bạn đã thử đăng nhập quá nhiều lần. Vui lòng thử lại sau 60 giây.",
      null,
      429
    );
  }

  if (error.code === "email_not_confirmed") {
    return new ApiError(
      "Email chưa được xác nhận. Vui lòng kiểm tra hộp thư.",
      null,
      error.status ?? 400
    );
  }

  return new ApiError("Email hoặc mật khẩu không đúng.", null, 401);
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<CurrentUserResponse | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const queryClient = useQueryClient();

  // Xóa luôn cache TanStack Query để người đăng nhập sau trên cùng tab không thấy dữ liệu
  // của phiên cũ (đăng xuất không tải lại trang như interceptor 401).
  const clearSession = useCallback(() => {
    setToken(null);
    setUser(null);
    setAuthToken(null);
    queryClient.clear();
  }, [queryClient]);

  const loadBusinessProfile = useCallback(
    async (accessToken: string, skipAuthRedirect = false) => {
      setAuthToken(accessToken);
      const res = await apiClient.get<ApiResponse<CurrentUserResponse>>("/api/auth/me", {
        skipAuthRedirect,
      });
      if (!res.data.success || !res.data.data) {
        throw new ApiError(
          res.data.message ?? "Không tìm thấy hồ sơ tài khoản.",
          res.data.errors,
          null
        );
      }

      setToken(accessToken);
      setUser(res.data.data);
    },
    []
  );

  const logout = useCallback(async () => {
    try {
      await supabase.auth.signOut({ scope: "local" });
    } finally {
      clearSession();
    }
  }, [clearSession]);

  useEffect(() => {
    async function restoreSession() {
      const { data, error } = await supabase.auth.getSession();
      if (error) throw error;
      if (!data.session) {
        clearSession();
        return;
      }

      try {
        await loadBusinessProfile(data.session.access_token);
      } catch {
        await supabase.auth.signOut({ scope: "local" });
        clearSession();
      }
    }

    restoreSession()
      .catch(async () => {
        await supabase.auth.signOut({ scope: "local" });
        clearSession();
      })
      .finally(() => setIsLoading(false));

    const { data: listener } = supabase.auth.onAuthStateChange((event, session) => {
      if (event === "SIGNED_OUT" || !session) {
        clearSession();
        return;
      }
      if (event === "TOKEN_REFRESHED") {
        void loadBusinessProfile(session.access_token).catch(clearSession);
      }
    });

    return () => listener.subscription.unsubscribe();
  }, [clearSession, loadBusinessProfile]);

  async function login(email: string, password: string) {
    let signedIn = false;
    try {
      const { data, error } = await supabase.auth.signInWithPassword({ email, password });
      if (error) {
        throw toSignInError(error);
      }
      if (!data.session) {
        throw new ApiError("Đăng nhập thất bại.", null, 401);
      }

      signedIn = true;
      await loadBusinessProfile(data.session.access_token, true);
    } catch (err) {
      if (signedIn) {
        await logout();
      }
      if (err instanceof ApiError) throw err;
      throw toApiError(err);
    }
  }

  return (
    <AuthContext.Provider value={{ user, token, isLoading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth phải được gọi bên trong AuthProvider");
  }
  return context;
}
