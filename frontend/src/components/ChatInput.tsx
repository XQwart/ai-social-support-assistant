import { useEffect, useRef, useState } from "react";
import { cn } from "@/utils/cn";

interface ChatInputProps {
  onSend: (message: string) => void;
  isLoading: boolean;
  placeholder?: string;
  mode?: "hero" | "dock";
  autoFocus?: boolean;
  isAuthenticated?: boolean;
  onAuthRequired?: () => void;
}

export default function ChatInput({
  onSend,
  isLoading,
  placeholder = "Введите ваш вопрос",
  mode = "dock",
  autoFocus = false,
  isAuthenticated = true,
  onAuthRequired,
}: ChatInputProps) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) {
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

  const submit = () => {
    const trimmed = value.trim();
    if (!trimmed || isLoading) return;

    if (!isAuthenticated) {
      onAuthRequired?.();
      return;
    }

    onSend(trimmed);
    setValue("");
  };

  const canSend = value.trim().length > 0 && !isLoading;

  return (
    <div
      className={cn(
        "w-full",
        mode === "hero"
          ? "mx-auto max-w-[760px]"
          : "mx-auto max-w-4xl px-3 pb-3 pt-3 md:px-4 md:pb-4"
      )}
    >
      <div
        className={cn(
          "relative flex min-h-[58px] items-center gap-3 overflow-hidden rounded-[28px] border px-4 py-2.5 shadow-[0_10px_35px_rgba(15,23,42,0.05)] backdrop-blur-2xl transition-all",
          mode === "hero"
            ? "bg-white/84 border-white/80"
            : "bg-white/76 border-white/72"
        )}
      >
        <div
          className="pointer-events-none absolute inset-0 opacity-70"
          aria-hidden="true"
          style={{
            background:
              "linear-gradient(180deg, rgba(255,255,255,0.56) 0%, rgba(255,255,255,0.12) 100%)",
          }}
        />

        <div className="relative z-10 flex flex-1 items-center gap-3">
          <textarea
            ref={textareaRef}
            value={value}
            rows={1}
            placeholder={placeholder}
            disabled={isLoading}
            onChange={(event) => setValue(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                submit();
              }
            }}
            className={cn(
              "custom-scrollbar block max-h-40 min-h-[24px] flex-1 resize-none bg-transparent py-[8px] align-middle outline-none",
              "text-[15px] leading-6 text-slate-800 placeholder:text-slate-400",
              mode === "hero" ? "md:text-base" : ""
            )}
            aria-label="Поле ввода сообщения"
          />

          <button
            type="button"
            onClick={submit}
            aria-disabled={!canSend}
            className={cn(
              "relative z-10 inline-flex h-11 w-11 shrink-0 cursor-pointer items-center justify-center rounded-2xl transition-all",
              canSend
                ? "bg-[linear-gradient(135deg,#12b981,#0ea5a4)] text-white shadow-[0_10px_30px_rgba(16,185,129,0.34)] hover:scale-[1.03] hover:shadow-[0_14px_34px_rgba(16,185,129,0.38)] active:scale-[0.97]"
                : "bg-slate-200/82 text-slate-400 hover:scale-[1.03] hover:bg-slate-300/85 hover:text-slate-500 hover:shadow-[0_10px_24px_rgba(148,163,184,0.18)] active:scale-[0.97]"
            )}
            aria-label="Отправить сообщение"
          >
            {isLoading ? (
              <span className="inline-flex items-center gap-1">
                <span className="loading-dot" />
                <span
                  className="loading-dot"
                  style={{ animationDelay: "120ms" }}
                />
                <span
                  className="loading-dot"
                  style={{ animationDelay: "240ms" }}
                />
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

      {mode === "hero" && (
        <div className="mt-3 text-center text-xs text-slate-500">
          Enter — отправить, Shift + Enter — новая строка
        </div>
      )}
    </div>
  );
}
