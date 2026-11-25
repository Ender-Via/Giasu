"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useForm, useWatch } from "react-hook-form";
import { useAuth } from "@/context/AuthContext";
import { toApiError } from "@/lib/axios";
import { Button, Input, Checkbox, ApiErrorAlert, LoadingSpinner, Icons } from "@/components";
import type { SelfRegisterRole } from "@/types/auth";
import { EMAIL_MAX_LENGTH, EMAIL_VALIDATE, trimValue } from "../login/_lib/auth-rules";
import { useRegister } from "./_lib/register-api";
import {
  ACCEPT_TERMS_VALIDATE,
  CONFIRM_PASSWORD_VALIDATE,
  FULL_NAME_VALIDATE,
  normalizeFullName,
  normalizeFullNameValue,
  PASSWORD_VALIDATE,
  PHONE_VALIDATE,
  REGISTER_DEFAULT_VALUES,
  ROLE_VALIDATE,
  type RegisterFormValues,
} from "./_lib/register-rules";

const ROLE_OPTIONS: { value: SelfRegisterRole; title: string; description: string }[] = [
  { value: "Tutor", title: "Sinh viên / Gia sư", description: "Tìm lớp, nhận dạy" },
  { value: "Parent", title: "Phụ huynh", description: "Đăng tin tìm gia sư" },
];

// SCR-AUTH-02 — Đăng ký (FR-01, AC-AUTH-01, AC-AUTH-02, AC-AUTH-03, AC-AUTH-05)
export default function RegisterPage() {
  const { user, isLoading, login } = useAuth();
  const router = useRouter();
  const registerMutation = useRegister();

  const [submitError, setSubmitError] = useState<unknown>(null);
  const [cooldownSeconds, setCooldownSeconds] = useState<number>(0);
  const [showPassword, setShowPassword] = useState<boolean>(false);

  const {
    register,
    handleSubmit,
    setFocus,
    control,
    formState: { errors, isSubmitting },
  } = useForm<RegisterFormValues>({
    defaultValues: REGISTER_DEFAULT_VALUES,
    mode: "onTouched",
  });

  const selectedRole = useWatch({ control, name: "role" });

  // Đã có phiên thì về "/" để trang chủ chọn cổng theo vai trò (ui-screens.md §2.1)
  useEffect(() => {
    if (!isLoading && user) {
      router.replace("/");
    }
  }, [user, isLoading, router]);

  // Bị giới hạn tần suất (429, D08): khóa form và đếm ngược 60 giây trên nút, như SCR-AUTH-01
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

  async function onSubmit(values: RegisterFormValues) {
    if (cooldownSeconds > 0 || values.role === "") return;
    setSubmitError(null);

    const email = values.email.trim();
    const password = values.password;

    try {
      await registerMutation.mutateAsync({
        role: values.role,
        fullName: normalizeFullName(values.fullName),
        phone: values.phone.trim(),
        email,
        password,
        acceptTerms: values.acceptTerms,
      });
    } catch (err: unknown) {
      const error = toApiError(err);
      if (error.status === 429) {
        setCooldownSeconds(60);
      }
      setSubmitError(err);
      // 409 email đã dùng: giữ dữ liệu, đưa con trỏ về ô Email (AC-AUTH-03)
      if (error.status === 409) {
        setFocus("email");
      }
      return;
    }

    // Tạo tài khoản xong thì tự đăng nhập (FR-01). Bước này lỗi (ví dụ 429) thì sang /login
    // kèm dải báo tạo tài khoản thành công.
    try {
      await login(email, password);
      router.replace("/");
    } catch {
      router.replace("/login?registered=1");
    }
  }

  if (isLoading || user) {
    return (
      <main className="flex min-h-screen items-center justify-center p-4 bg-surface">
        <LoadingSpinner label="Đang kiểm tra phiên đăng nhập..." />
      </main>
    );
  }

  const isLocked = cooldownSeconds > 0;
  const isButtonDisabled = isSubmitting || isLocked;

  return (
    <main className="flex min-h-screen items-center justify-center p-4 sm:p-6 bg-surface">
      <div className="w-full max-w-xl rounded-3xl border border-slate-200/90 bg-surface-container-lowest p-6 sm:p-8 shadow-sm">
        <div className="space-y-1 mb-6 text-center sm:text-left">
          <div className="inline-flex items-center gap-2 mb-2 text-primary">
            <div className="w-8 h-8 rounded-full bg-primary-container text-on-primary flex items-center justify-center">
              <Icons.School />
            </div>
            <span className="font-bold text-lg leading-none">Gia Sư Kết Nối</span>
          </div>
          <h1 className="text-2xl font-bold text-on-surface">Tạo tài khoản</h1>
        </div>

        {/* [1] Lỗi từ server */}
        {submitError ? (
          <div className="mb-4">
            <ApiErrorAlert error={submitError} />
          </div>
        ) : null}

        <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
          {/* [2] Chọn vai trò: hai thẻ chọn một, bắt đầu chưa chọn */}
          <div className="space-y-1.5">
            <p id="role-label" className="block text-sm font-semibold text-on-surface">
              Bạn tham gia với vai trò:<span className="ml-1 text-error">*</span>
            </p>
            <div
              role="radiogroup"
              aria-labelledby="role-label"
              aria-required="true"
              aria-invalid={errors.role ? "true" : "false"}
              aria-describedby={errors.role ? "role-error" : undefined}
              className="grid grid-cols-1 sm:grid-cols-2 gap-3"
            >
              {ROLE_OPTIONS.map((option) => (
                <label
                  key={option.value}
                  className={`flex min-h-11 items-start gap-3 rounded-2xl border p-4 transition-colors has-[:checked]:border-primary has-[:checked]:bg-primary-fixed/30 has-[:focus-visible]:ring-2 has-[:focus-visible]:ring-primary/40 ${
                    errors.role ? "border-error" : "border-slate-300"
                  } ${
                    isLocked
                      ? "cursor-not-allowed opacity-60"
                      : "cursor-pointer hover:bg-surface-container-low"
                  }`}
                >
                  <input
                    type="radio"
                    value={option.value}
                    disabled={isLocked}
                    className="mt-1 h-4 w-4 shrink-0 accent-primary"
                    {...register("role", { validate: ROLE_VALIDATE })}
                  />
                  <span className="flex flex-col">
                    <span className="text-sm font-bold text-on-surface">{option.title}</span>
                    <span className="text-xs text-on-surface-variant">{option.description}</span>
                  </span>
                </label>
              ))}
            </div>
            {errors.role ? (
              <p id="role-error" className="text-xs text-error font-medium">
                {errors.role.message}
              </p>
            ) : null}
          </div>

          {/* [3] Họ và tên */}
          <Input
            id="fullName"
            label="Họ và tên"
            required
            autoComplete="name"
            disabled={isLocked}
            placeholder="Nguyễn Văn A"
            error={errors.fullName?.message}
            {...register("fullName", {
              setValueAs: normalizeFullNameValue,
              validate: FULL_NAME_VALIDATE,
            })}
          />

          {/* [4] Số điện thoại — không đặt maxLength={10} để dán số có khoảng trắng đầu/cuối không bị cắt mất ký tự */}
          <Input
            id="phone"
            type="tel"
            inputMode="numeric"
            label="Số điện thoại"
            required
            autoComplete="tel"
            disabled={isLocked}
            placeholder="0912345678"
            error={errors.phone?.message}
            {...register("phone", { setValueAs: trimValue, validate: PHONE_VALIDATE })}
          />

          {/* [5] Email; vai trò Gia sư có gợi ý dùng email sinh viên */}
          <Input
            id="email"
            type="email"
            label="Email"
            required
            autoComplete="email"
            maxLength={EMAIL_MAX_LENGTH}
            disabled={isLocked}
            placeholder="hoten@example.com"
            error={errors.email?.message}
            helperText={
              selectedRole === "Tutor"
                ? "Nên dùng email sinh viên để xác thực nhanh hơn."
                : undefined
            }
            {...register("email", { setValueAs: trimValue, validate: EMAIL_VALIDATE })}
          />

          {/* [6] Mật khẩu, nhập lại */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              id="password"
              type={showPassword ? "text" : "password"}
              label="Mật khẩu"
              required
              autoComplete="new-password"
              disabled={isLocked}
              placeholder="••••••••"
              error={errors.password?.message}
              suffixAction={
                <button
                  type="button"
                  onClick={() => setShowPassword((prev) => !prev)}
                  disabled={isLocked}
                  aria-label={showPassword ? "Ẩn mật khẩu" : "Hiện mật khẩu"}
                  aria-pressed={showPassword}
                  aria-controls="password confirmPassword"
                  className="flex h-8 w-8 items-center justify-center rounded-full text-on-surface-variant transition-colors cursor-pointer hover:bg-surface-container-low hover:text-on-surface focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {showPassword ? <Icons.EyeOff /> : <Icons.Eye />}
                </button>
              }
              {...register("password", {
                validate: PASSWORD_VALIDATE,
                deps: "confirmPassword",
              })}
            />
            <Input
              id="confirmPassword"
              type={showPassword ? "text" : "password"}
              label="Nhập lại mật khẩu"
              required
              autoComplete="new-password"
              disabled={isLocked}
              placeholder="••••••••"
              error={errors.confirmPassword?.message}
              {...register("confirmPassword", { validate: CONFIRM_PASSWORD_VALIDATE })}
            />
          </div>

          {/* [7] Đồng ý quy chế */}
          <Checkbox
            id="acceptTerms"
            required
            disabled={isLocked}
            label="Tôi đồng ý Quy chế hoạt động và cam kết không thu hoặc đóng phí giữ chỗ, phí cọc."
            error={errors.acceptTerms?.message}
            {...register("acceptTerms", { validate: ACCEPT_TERMS_VALIDATE })}
          />

          {/* [8] Nút gửi */}
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
                ? "Đang tạo tài khoản..."
                : isLocked
                ? `Thử lại sau (${cooldownSeconds}s)`
                : "Tạo tài khoản"}
            </Button>
          </div>
        </form>

        {/* [9] Liên kết sang đăng nhập */}
        <p className="mt-6 text-center text-sm text-on-surface-variant">
          Đã có tài khoản?{" "}
          <Link href="/login" className="font-semibold text-primary hover:underline">
            Đăng nhập
          </Link>
        </p>
      </div>
    </main>
  );
}
