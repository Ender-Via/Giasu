"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { useAuth } from "@/context/AuthContext";
import { toApiError } from "@/lib/axios";
import { Button, Input, ApiErrorAlert, LoadingSpinner, Icons } from "@/components";

interface LoginFormValues {
  email: string;
  password: string;
}

export default function LoginPage() {
  const { user, isLoading, login } = useAuth();
  const router = useRouter();

  const [submitError, setSubmitError] = useState<unknown>(null);
  const [cooldownSeconds, setCooldownSeconds] = useState<number>(0);
  const [showPassword, setShowPassword] = useState<boolean>(false);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormValues>({
    defaultValues: {
      email: "",
      password: "",
    },
    mode: "onTouched",
  });

  // Chuyển hướng về trang chủ nếu người dùng đã đăng nhập
  useEffect(() => {
    if (!isLoading && user) {
      router.replace("/");
    }
  }, [user, isLoading, router]);

  // Bộ đếm ngược thời gian chờ khi gặp lỗi HTTP 429 (D08)
  useEffect(() => {
    if (cooldownSeconds <= 0) return;

    const timer = setInterval(() => {
      setCooldownSeconds((prev) => Math.max(0, prev - 1));
    }, 1000);

    return () => clearInterval(timer);
  }, [cooldownSeconds]);

  async function onSubmit(data: LoginFormValues) {
    if (cooldownSeconds > 0) return;
    setSubmitError(null);

    try {
      await login(data.email, data.password);
      router.replace("/");
    } catch (err: unknown) {
      const error = toApiError(err);
      if (error.status === 429) {
        setCooldownSeconds(60);
      }
      setSubmitError(err);
    }
  }

  if (isLoading || user) {
    return (
      <main className="flex min-h-screen items-center justify-center p-4 bg-background">
        <LoadingSpinner label="Đang kiểm tra phiên đăng nhập..." />
      </main>
    );
  }

  const isButtonDisabled = isSubmitting || cooldownSeconds > 0;
  const activeError =
    cooldownSeconds > 0
      ? `Bạn đã thử đăng nhập quá số lần cho phép. Vui lòng thử lại sau ${cooldownSeconds} giây.`
      : submitError;

  return (
    <main className="flex min-h-screen items-center justify-center p-4 sm:p-6 bg-background">
      <div className="w-full max-w-md rounded-3xl border border-slate-200/90 bg-surface-container-lowest p-6 sm:p-8 shadow-sm">
        {/* Tiêu đề & Giới thiệu */}
        <div className="space-y-1 mb-6 text-center sm:text-left">
          <div className="inline-flex items-center gap-2 mb-2 text-primary">
            <div className="w-8 h-8 rounded-full bg-primary-container text-on-primary flex items-center justify-center">
              <Icons.School />
            </div>
            <span className="font-bold text-lg leading-none">Gia Sư Kết Nối</span>
          </div>
          <h1 className="text-2xl font-bold text-on-surface">Đăng nhập</h1>
          <p className="text-sm text-on-surface-variant">
            Nền tảng tìm gia sư và quản lý quá trình dạy học
          </p>
        </div>

        {/* Thông báo lỗi từ server (SCR-AUTH-01 [1]) */}
        {activeError ? (
          <div className="mb-4">
            <ApiErrorAlert error={activeError} />
          </div>
        ) : null}

        <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
          {/* Ô nhập Email (SCR-AUTH-01 [2]) */}
          <Input
            id="email"
            type="email"
            label="Email"
            required
            autoComplete="email"
            disabled={isButtonDisabled}
            placeholder="hoten@example.com"
            error={errors.email?.message}
            {...register("email", {
              setValueAs: (v: string) => (typeof v === "string" ? v.trim() : v),
              required: "Vui lòng nhập email",
              maxLength: {
                value: 254,
                message: "Email không được vượt quá 254 ký tự",
              },
              pattern: {
                value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
                message: "Email không đúng định dạng",
              },
            })}
          />

          {/* Ô nhập Mật khẩu (SCR-AUTH-01 [3]) */}
          <Input
            id="password"
            type={showPassword ? "text" : "password"}
            label="Mật khẩu"
            required
            autoComplete="current-password"
            disabled={isButtonDisabled}
            placeholder="••••••••"
            error={errors.password?.message}
            suffixIcon={
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                tabIndex={-1}
                aria-label={showPassword ? "Ẩn mật khẩu" : "Hiện mật khẩu"}
                className="text-outline hover:text-on-surface transition-colors p-1 cursor-pointer"
              >
                {showPassword ? (
                  <svg width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                    <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" />
                    <line x1="1" y1="1" x2="23" y2="23" />
                  </svg>
                ) : (
                  <svg width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                    <circle cx="12" cy="12" r="3" />
                  </svg>
                )}
              </button>
            }
            {...register("password", {
              required: "Vui lòng nhập mật khẩu",
            })}
          />

          {/* Nút Đăng nhập (SCR-AUTH-01 [4]) */}
          <div className="pt-2">
            <Button
              type="submit"
              variant="primary"
              size="lg"
              className="w-full min-h-11 rounded-full font-bold shadow-sm"
              isLoading={isSubmitting}
              disabled={isButtonDisabled}
            >
              {cooldownSeconds > 0
                ? `Thử lại sau (${cooldownSeconds}s)`
                : "Đăng nhập"}
            </Button>
          </div>
        </form>

        {/* Liên kết Đăng ký (SCR-AUTH-01 [5]) */}
        <div className="mt-6 pt-4 border-t border-slate-100 text-center text-sm text-on-surface-variant">
          <span>Chưa có tài khoản? </span>
          <Link
            href="/register"
            className="font-semibold text-primary hover:underline transition-colors"
          >
            Đăng ký ngay
          </Link>
        </div>
      </div>
    </main>
  );
}
