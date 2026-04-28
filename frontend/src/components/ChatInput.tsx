import { useEffect, useRef, useState } from "react";
import { cn } from "@/utils/cn";

const WORD_LIMIT = 3500;

function countWords(value: string): number {
  return value.trim().split(/\s+/).filter(Boolean).length;
}

interface ChatInputProps {
  onSend: (message: string) => Promise<boolean>;
  isLoading: boolean;
  placeholder?: string;
  mode?: "hero" | "dock";
  autoFocus?: boolean;
  isAuthenticated?: boolean;
  onAuthRequired?: () => void;
  theme?: "light" | "dark";
}

export default function ChatInput({
  onSend,
  isLoading,
  placeholder = "Введите ваш вопрос",
  mode = "dock",
  autoFocus = false,
  isAuthenticated = true,
  onAuthRequired,
  theme = "light",
}: ChatInputProps) {
  const [value, setValue] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [validationError, setValidationError] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const isBusy = isLoading || isSubmitting;

  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;
    if (!value) {
      textarea.style.height = "";
      return;
    }
    textarea.style.height = "auto";
    textarea.style.height = `${Math.min(textarea.scrollHeight, 160)}px`;
  }, [value]);

  useEffect(() => {
    if (autoFocus) {
      textareaRef.current?.focus();
    }
  }, [autoFocus]);

  const submit = async () => {
    const trimmed = value.trim();
    if (!trimmed || isBusy) return;

    const wordCount = countWords(trimmed);
    if (wordCount > WORD_LIMIT) {
      setValidationError(`Сообщение не должно превышать ${WORD_LIMIT} слов.`);
      return;
    }

    if (!isAuthenticated) {
      onAuthRequired?.();
      return;
    }

    setValidationError("");
    setIsSubmitting(true);

    try {
      const didSend = await onSend(trimmed);
      if (didSend) {
        setValue("");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const wordCount = countWords(value);
  const canSend = value.trim().length > 0 && !isBusy && wordCount <= WORD_LIMIT;
  const isDark = theme === "dark";

  return (
    <div
      className={cn(
        "w-full",
        mode === "hero"
          ? "mx-auto max-w-[760px]"
          : "px-3 pb-[max(env(safe-area-inset-bottom),0.75rem)] pt-3 md:px-5 md:pb-4"
      )}
    >
      <div
        className={cn(
          mode === "dock" && "mx-auto w-full max-w-4xl",
          "relative flex min-h-[44px] items-center gap-2 overflow-hidden rounded-[22px] border px-3 py-1.5 shadow-[0_10px_35px_rgba(15,23,42,0.05)] backdrop-blur-2xl transition-all sm:min-h-[58px] sm:gap-3 sm:rounded-[28px] sm:px-4 sm:py-2.5",
          isDark
            ? mode === "hero"
              ? "border-white/10 bg-[rgba(10,24,20,0.82)]"
              : "border-white/10 bg-[rgba(10,24,20,0.9)] shadow-[0_16px_40px_rgba(0,0,0,0.24)]"
            : mode === "hero"
              ? "border-white/80 bg-white/84"
              : "border-white/84 bg-white/86 shadow-[0_16px_40px_rgba(15,23,42,0.08)]"
        )}
      >
        <div
          className="pointer-events-none absolute inset-0 opacity-70"
          aria-hidden="true"
          style={{
            background: isDark
              ? mode === "hero"
                ? "linear-gradient(180deg, rgba(255,255,255,0.06) 0%, rgba(255,255,255,0.02) 100%)"
                : "linear-gradient(180deg, rgba(255,255,255,0.08) 0%, rgba(255,255,255,0.02) 100%)"
              : mode === "hero"
                ? "linear-gradient(180deg, rgba(255,255,255,0.56) 0%, rgba(255,255,255,0.12) 100%)"
                : "linear-gradient(180deg, rgba(255,255,255,0.68) 0%, rgba(255,255,255,0.18) 100%)",
          }}
        />

        <div className="relative z-10 flex flex-1 items-center gap-3">
          <textarea
            ref={textareaRef}
            value={value}
            rows={1}
            placeholder={placeholder}
            disabled={isBusy}
            onChange={(event) => {
              setValue(event.target.value);
              if (validationError) setValidationError("");
            }}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                void submit();
              }
            }}
            className={cn(
              "custom-scrollbar block max-h-40 min-h-[22px] flex-1 resize-none bg-transparent py-1 align-middle outline-none sm:min-h-[24px] sm:py-[8px]",
              isDark
                ? "text-[14px] leading-5 text-slate-100 placeholder:text-slate-500 sm:text-[15px] sm:leading-6"
                : "text-[14px] leading-5 text-slate-800 placeholder:text-slate-400 sm:text-[15px] sm:leading-6",
              mode === "hero" ? "md:text-base" : ""
            )}
            aria-label="Поле ввода сообщения"
          />

          <button
            type="button"
            onClick={() => void submit()}
            aria-disabled={!canSend}
            className={cn(
              "relative z-10 inline-flex h-9 w-9 shrink-0 cursor-pointer items-center justify-center self-end rounded-xl transition-all sm:h-11 sm:w-11 sm:self-auto sm:rounded-2xl",
              canSend
                ? "bg-[linear-gradient(135deg,#12b981,#0ea5a4)] text-white shadow-[0_10px_30px_rgba(16,185,129,0.34)] hover:scale-[1.03] hover:shadow-[0_14px_34px_rgba(16,185,129,0.38)] active:scale-[0.97]"
                : isDark
                  ? "bg-white/8 text-slate-500 hover:scale-[1.03] hover:bg-white/12 hover:text-slate-300 hover:shadow-[0_10px_24px_rgba(0,0,0,0.14)] active:scale-[0.97]"
                  : "bg-slate-200/82 text-slate-400 hover:scale-[1.03] hover:bg-slate-300/85 hover:text-slate-500 hover:shadow-[0_10px_24px_rgba(148,163,184,0.18)] active:scale-[0.97]"
            )}
            aria-label="Отправить сообщение"
          >
            {isBusy ? (
              <span className="inline-flex items-center gap-1">
                <span className="loading-dot" />
                <span className="loading-dot" style={{ animationDelay: "120ms" }} />
                <span className="loading-dot" style={{ animationDelay: "240ms" }} />
              </span>
            ) : (
              <svg
                width="18"
                height="18"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.4"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M22 2L11 13" />
                <path d="M22 2L15 22L11 13L2 9L22 2Z" />
              </svg>
            )}
          </button>
        </div>
      </div>

      {(validationError || wordCount > WORD_LIMIT) && (
        <div className={cn("mt-2 px-2 text-xs", isDark ? "text-rose-300" : "text-rose-600")}>
          {validationError || `Превышен лимит: ${wordCount}/${WORD_LIMIT} слов.`}
        </div>
      )}

      {mode === "hero" && (
        <div className="mt-3 hidden text-center text-xs text-slate-500 sm:block">
          Enter — отправить, Shift + Enter — новая строка
        </div>
      )}
    </div>
  );
}
