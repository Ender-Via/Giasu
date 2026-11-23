"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  ReactNode,
} from "react";
import { apiClient, setAuthToken, toApiError, ApiError } from "@/lib/axios";
import { supabase } from "@/lib/supabase";
import type { ApiResponse, Role } from "@/types/auth";

interface AuthUser {
  userId: string;
  fullName: string;
  role: Role;
}

interface AuthContextValue {
  user: AuthUser | null;
  token: string | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const clearSession = useCallback(() => {
    setToken(null);
    setUser(null);
    setAuthToken(null);
  }, []);

  const loadBusinessProfile = useCallback(async (accessToken: string) => {
    setAuthToken(accessToken);
    const res = await apiClient.get<ApiResponse<AuthUser>>("/api/auth/me");
    if (!res.data.success || !res.data.data) {
      throw new ApiError(
        res.data.message ?? "Không tìm thấy hồ sơ tài khoản.",
        res.data.errors,
        null
      );
    }

    setToken(accessToken);
    setUser(res.data.data);
  }, []);

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
    try {
      const { data, error } = await supabase.auth.signInWithPassword({ email, password });
      if (error) {
        throw new ApiError(
          "Email hoặc mật khẩu không đúng.",
          null,
          error.status ?? 401
        );
      }
      if (!data.session) {
        throw new ApiError("Đăng nhập thất bại.", null, 401);
      }

      await loadBusinessProfile(data.session.access_token);
    } catch (err) {
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
