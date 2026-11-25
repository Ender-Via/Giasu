"use client";

import { useRef, useState } from "react";
import { ApiErrorAlert, Button, ConfirmDialog, Icons } from "@/components";
import { toApiError } from "@/lib/axios";
import type {
  TutorProfileDetailResponse,
  TutorProfileEvidenceResponse,
} from "@/types/tutor-profile";
import { useRemoveEvidence, useUploadEvidences } from "../_lib/tutor-profiles-api";
import {
  MAX_EVIDENCES,
  canEditEvidences,
  formatFileSize,
  validateEvidenceFiles,
} from "../_lib/tutor-profile-rules";

interface EvidenceSectionProps {
  profile: TutorProfileDetailResponse;
  onSuccess: (message: string) => void;
}

// SCR-TUT-02 [B] — minh chứng năng lực, chỉ hiện khi hồ sơ đã được lưu (FR-04, BR-03, BR-26)
export function EvidenceSection({ profile, onSuccess }: EvidenceSectionProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const upload = useUploadEvidences(profile.id);
  const removeEvidence = useRemoveEvidence(profile.id);
  const [clientErrors, setClientErrors] = useState<string[]>([]);
  const [uploadError, setUploadError] = useState<unknown>(null);
  const [removeTarget, setRemoveTarget] = useState<TutorProfileEvidenceResponse | null>(null);
  const [removeError, setRemoveError] = useState<unknown>(null);

  const editable = canEditEvidences(profile);
  const remainingSlots = Math.max(0, MAX_EVIDENCES - profile.evidences.length);

  function handleFilesChosen(fileList: FileList | null) {
    const files = fileList ? Array.from(fileList) : [];
    // Cho phép chọn lại đúng tệp vừa chọn ở lần sau
    if (fileInputRef.current) fileInputRef.current.value = "";
    if (files.length === 0) return;

    setUploadError(null);
    const errors = validateEvidenceFiles(files, remainingSlots);
    setClientErrors(errors);
    if (errors.length > 0) return;

    upload.mutate(files, {
      onSuccess: () => onSuccess(`Đã tải lên ${files.length} minh chứng.`),
      onError: (err) => setUploadError(err),
    });
  }

  async function confirmRemove() {
    if (!removeTarget) return;
    try {
      await removeEvidence.mutateAsync(removeTarget.id);
      onSuccess(`Đã gỡ tệp '${removeTarget.fileName}'.`);
      setRemoveTarget(null);
    } catch (err) {
      setRemoveError(err);
    }
  }

  return (
    <section
      aria-labelledby="evidence-heading"
      className="rounded-3xl border border-slate-200/90 bg-surface-container-lowest p-4 sm:p-6 shadow-sm space-y-4"
    >
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 id="evidence-heading" className="text-lg font-bold text-on-surface">
          Minh chứng năng lực
        </h2>
        <span className="text-sm text-on-surface-variant">
          {profile.evidences.length}/{MAX_EVIDENCES} tệp
        </span>
      </div>
      <p className="text-sm text-on-surface-variant">
        Bảng điểm, chứng chỉ, giấy khen. Cần ít nhất một minh chứng để gửi duyệt.
      </p>

      {/* [10] Danh sách minh chứng */}
      {profile.evidences.length === 0 ? (
        <p className="text-sm text-on-surface-variant">Chưa có minh chứng nào.</p>
      ) : (
        <ul className="divide-y divide-slate-200 rounded-2xl border border-slate-200">
          {profile.evidences.map((evidence) => (
            <li
              key={evidence.id}
              className="flex flex-wrap items-center justify-between gap-2 px-3 py-2"
            >
              <div className="min-w-0 flex items-center gap-2">
                <span className="text-on-surface-variant shrink-0">
                  <Icons.FileText />
                </span>
                <span className="truncate text-sm font-medium text-on-surface">
                  {evidence.fileName}
                </span>
                <span className="shrink-0 text-xs text-on-surface-variant">
                  {formatFileSize(evidence.sizeBytes)}
                </span>
              </div>
              <div className="flex items-center gap-2">
                {evidence.url ? (
                  <a
                    href={evidence.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex min-h-11 sm:min-h-0 items-center rounded-full px-3 py-1.5 text-xs font-semibold text-primary hover:bg-surface-container-low focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                  >
                    Xem
                  </a>
                ) : null}
                {editable ? (
                  <Button
                    variant="ghost"
                    size="sm"
                    className="min-h-11 sm:min-h-0"
                    onClick={() => {
                      setRemoveError(null);
                      setRemoveTarget(evidence);
                    }}
                  >
                    Gỡ
                  </Button>
                ) : null}
              </div>
            </li>
          ))}
        </ul>
      )}

      {/* [11] Tải lên: chỉ khi hồ sơ Draft hoặc Rejected (BR-26) */}
      {editable ? (
        <div className="space-y-2">
          {clientErrors.length > 0 ? (
            <div role="alert" className="rounded-2xl border border-error/30 bg-error-container/40 p-3">
              <ul className="list-disc list-inside space-y-0.5 text-xs font-medium text-error">
                {clientErrors.map((message) => (
                  <li key={message}>{message}</li>
                ))}
              </ul>
            </div>
          ) : null}
          {uploadError ? <ApiErrorAlert error={uploadError} /> : null}

          <input
            ref={fileInputRef}
            id="evidence-files"
            type="file"
            multiple
            accept=".jpg,.jpeg,.png,.pdf,image/jpeg,image/png,application/pdf"
            className="sr-only"
            onChange={(event) => handleFilesChosen(event.target.files)}
          />
          <div className="flex flex-wrap items-center gap-3">
            <Button
              variant="outline"
              className="min-h-11 sm:min-h-0"
              isLoading={upload.isPending}
              disabled={remainingSlots === 0}
              onClick={() => fileInputRef.current?.click()}
            >
              + Tải lên minh chứng
            </Button>
            <span className="text-xs text-on-surface-variant">
              JPG, PNG, PDF · tối đa 5 MB mỗi tệp
            </span>
          </div>
        </div>
      ) : null}

      <ConfirmDialog
        isOpen={removeTarget !== null}
        onClose={() => setRemoveTarget(null)}
        onConfirm={confirmRemove}
        isLoading={removeEvidence.isPending}
        variant="danger"
        title="Gỡ minh chứng"
        confirmText="Gỡ"
        message={
          <div className="space-y-3 text-left">
            <p>Gỡ tệp &apos;{removeTarget?.fileName}&apos; khỏi hồ sơ?</p>
            {removeError ? (
              <p role="alert" className="text-sm font-medium text-error">
                {toApiError(removeError).message}
              </p>
            ) : null}
          </div>
        }
      />
    </section>
  );
}
