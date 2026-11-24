"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useForm } from "react-hook-form";
import { useAuth } from "@/context/AuthContext";
import { toApiError } from "@/lib/axios";
import { Button, Input, ApiErrorAlert, LoadingSpinner, Icons, NoticeBanner } from "@/components";
import { EMAIL_MAX_LENGTH, EMAIL_VALIDATE, trimValue } from "./_lib/auth-rules";

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

  // Bộ đếm ngược thời gian chờ khi gặp lỗi HTTP 429 (D08). Bộ đếm chỉ hiện trên nút;
  // thông báo lỗi lấy message từ API và được xóa khi hết giờ chờ để không còn nhắc "đợi".
  useEffect(() => {
    if (cooldownSeconds <= 0) return;

    const timer = setTimeout(() => {
      if (cooldownSeconds === 1) {
        setSubmitError(null);
      }
      setCooldownSeconds(cooldownSeconds - 1);
    }, 1000);

    return () => clearTimeout(timer);
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

        {/* Dải báo khi đăng ký xong nhưng tự đăng nhập lỗi (SCR-AUTH-02 hành vi 3) */}
        <Suspense fallback={null}>
          <RegisteredNotice />
        </Suspense>

        {/* Thông báo lỗi từ server (SCR-AUTH-01 [1]) */}
        {submitError ? (
          <div className="mb-4">
            <ApiErrorAlert error={submitError} />
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
            maxLength={EMAIL_MAX_LENGTH}
            {...register("email", { setValueAs: trimValue, validate: EMAIL_VALIDATE })}
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
            suffixAction={
              <button
                type="button"
                onClick={() => setShowPassword((prev) => !prev)}
                disabled={isButtonDisabled}
                aria-label={showPassword ? "Ẩn mật khẩu" : "Hiện mật khẩu"}
                aria-pressed={showPassword}
                aria-controls="password"
                className="flex h-8 w-8 items-center justify-center rounded-full text-on-surface-variant transition-colors cursor-pointer hover:bg-surface-container-low hover:text-on-surface focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary disabled:cursor-not-allowed disabled:opacity-50"
              >
                {showPassword ? <Icons.EyeOff /> : <Icons.Eye />}
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
              {isSubmitting
                ? "Đang đăng nhập..."
                : cooldownSeconds > 0
                ? `Thử lại sau (${cooldownSeconds}s)`
                : "Đăng nhập"}
            </Button>
          </div>
        </form>

        {/* Liên kết Đăng ký (SCR-AUTH-01 [5]) */}
        <p className="mt-6 text-center text-sm text-on-surface-variant">
          Chưa có tài khoản?{" "}
          <Link href="/register" className="font-semibold text-primary hover:underline">
            Đăng ký
          </Link>
        </p>
      </div>
    </main>
  );
}

// Đọc cờ ?registered=1 do SCR-AUTH-02 gắn khi tạo tài khoản xong mà bước tự đăng nhập lỗi.
// Tách component riêng để bọc Suspense, trang vẫn dựng tĩnh được (useSearchParams).
// Dải thành công tự ẩn sau 6 giây (ui-screens.md §4.2); ẩn bằng cách bỏ cờ khỏi URL.
function RegisteredNotice() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const isRegistered = searchParams.get("registered") === "1";

  useEffect(() => {
    if (!isRegistered) return;
    const timer = setTimeout(() => router.replace("/login"), 6000);
    return () => clearTimeout(timer);
  }, [isRegistered, router]);

  if (!isRegistered) return null;

  return (
    <div className="mb-4">
      <NoticeBanner
        message="Tạo tài khoản thành công, vui lòng đăng nhập."
        onClose={() => router.replace("/login")}
      />
    </div>
  );
}
