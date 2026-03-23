import type { Message } from "@/types";
import TypingAnimation from "@/components/TypingAnimation";
import { cn } from "@/utils/cn";

interface ChatMessageProps {
  message: Message;
  shouldAnimate: boolean;
}

function formatTime(timestamp: number): string {
  return new Date(timestamp).toLocaleTimeString("ru-RU", {
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function ChatMessage({
  message,
  shouldAnimate,
}: ChatMessageProps) {
  const isUser = message.role === "user";
  const isSystem = message.role === "system";
  const isError = message.error === true;

  // Системное сообщение (сжатие контекста и т.д.) — центрированный информационный блок
  if (isSystem) {
    return (
      <div className="fade-in-up flex w-full justify-center py-1">
        <div className="inline-flex max-w-[90%] items-center gap-2 rounded-full border border-slate-200/60 bg-white/50 px-4 py-2 text-[12px] text-slate-500 shadow-[0_2px_8px_rgba(15,23,42,0.03)] backdrop-blur-xl">
          <svg
            width="14"
            height="14"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="shrink-0 text-slate-400"
          >
            <circle cx="12" cy="12" r="10" />
            <path d="M12 16v-4" />
            <path d="M12 8h.01" />
          </svg>
          <span>{message.content}</span>
        </div>
      </div>
    );
  }

  return (
    <div
      className={cn(
        "fade-in-up flex w-full",
        isUser ? "justify-end" : "justify-start"
      )}
    >
      <div
        className={cn(
          "max-w-[88%] md:max-w-[78%]",
          !isUser && "flex items-start gap-3"
        )}
      >
        {!isUser && (
          <div
            className={cn(
              "mt-1 flex h-9 w-9 shrink-0 items-center justify-center rounded-2xl border text-xs font-semibold shadow-[0_6px_18px_rgba(15,23,42,0.05)] backdrop-blur-xl",
              isError
                ? "border-rose-200/70 bg-white/70 text-rose-500"
                : "border-white/70 bg-white/70 text-emerald-600"
            )}
          >
            ИИ
          </div>
        )}

        <div
          className={cn(
            "rounded-[24px] px-4 py-3.5 shadow-[0_10px_30px_rgba(15,23,42,0.05)]",
            isUser
              ? "rounded-br-[8px] bg-[linear-gradient(135deg,#14b883_0%,#0ea5a4_100%)] text-white"
              : isError
                ? "rounded-bl-[8px] border border-rose-100/80 bg-white/78 text-slate-800 backdrop-blur-2xl"
                : "rounded-bl-[8px] border border-white/80 bg-white/74 text-slate-800 backdrop-blur-2xl"
          )}
        >
          {!isUser && (
            <div
              className={cn(
                "mb-1 text-[11px] font-semibold uppercase tracking-[0.12em]",
                isError ? "text-rose-400" : "text-emerald-600/90"
              )}
            >
              {isError ? "Системное сообщение" : "Помощник"}
            </div>
          )}

          <div
            className={cn(
              "whitespace-pre-wrap break-words text-[15px] leading-7",
              isUser ? "text-white/98" : "text-slate-800"
            )}
          >
            {!isUser && shouldAnimate && !isError ? (
              <TypingAnimation text={message.content} speed={10} />
            ) : (
              message.content
            )}
          </div>

          <div
            className={cn(
              "mt-2 text-[11px]",
              isUser ? "text-white/70" : "text-slate-400"
            )}
          >
            {formatTime(message.timestamp)}
          </div>
        </div>
      </div>
    </div>
  );
}
