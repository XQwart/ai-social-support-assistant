import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";

import AgentActivityList from "@/components/AgentActivity";

import type { Personality } from "@/api/chatApi";
import type { Message } from "@/types";
import { cn } from "@/utils/cn";

interface ChatMessageProps {
  message: Message;
  isStreaming?: boolean;
  personality?: Personality;
  onEdit?: (messageId: string, newText: string) => Promise<void>;
}

const ROLE_LABEL = "Помощник";
const ERROR_LABEL = "Системное сообщение";
const TIME_LOCALE = "ru-RU";
const COPY_RESET_TIMEOUT = 1400;

type FeedbackState = "like" | "dislike" | null;
type FooterAlign = "start" | "center" | "end";
type IconTone = "neutral" | "positive" | "negative";

function formatTimestamp(timestamp: number): string {
  const date = new Date(timestamp);
  const today = new Date();
  const isToday =
    date.getFullYear() === today.getFullYear() &&
    date.getMonth() === today.getMonth() &&
    date.getDate() === today.getDate();

  const time = date.toLocaleTimeString(TIME_LOCALE, { hour: "2-digit", minute: "2-digit" });
  if (isToday) return time;

  const d = String(date.getDate()).padStart(2, "0");
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const y = String(date.getFullYear()).slice(-2);
  return `${d}.${m}.${y} ${time}`;
}

async function copyTextToClipboard(value: string): Promise<void> {
  await navigator.clipboard.writeText(value);
}

function CopyIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.9"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <rect x="9" y="9" width="13" height="13" rx="2.5" ry="2.5" />
      <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
    </svg>
  );
}

function ThumbUpIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.9"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M7 10v10" />
      <path d="M15 5.88 14 10h6.17a2 2 0 0 1 1.95 2.45l-1.1 5A2 2 0 0 1 19.07 19H7V10l4.76-6.35A1.3 1.3 0 0 1 14.1 4.7a1.3 1.3 0 0 1 .9 1.18Z" />
    </svg>
  );
}

function ThumbDownIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.9"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M17 14V4" />
      <path d="M9 18.12 10 14H3.83a2 2 0 0 1-1.95-2.45l1.1-5A2 2 0 0 1 4.93 5H17v9l-4.76 6.35A1.3 1.3 0 0 1 9.9 19.3a1.3 1.3 0 0 1-.9-1.18Z" />
    </svg>
  );
}

function IconActionButton({
  label,
  active = false,
  tone = "neutral",
  onClick,
  children,
}: {
  label: string;
  active?: boolean;
  tone?: IconTone;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      title={label}
      aria-label={label}
      aria-pressed={active}
      onClick={onClick}
      className={cn(
        "inline-flex h-9 w-9 cursor-pointer items-center justify-center rounded-xl transition-all",
        !active && "text-slate-500 hover:bg-slate-900/5 hover:text-slate-700 active:scale-[0.96]",
        active && tone === "positive" && "bg-emerald-50 text-emerald-600 shadow-[0_10px_24px_rgba(16,185,129,0.12)]",
        active && tone === "negative" && "bg-rose-50 text-rose-600 shadow-[0_10px_24px_rgba(244,63,94,0.12)]",
        active && tone === "neutral" && "bg-sky-50 text-sky-600 shadow-[0_10px_24px_rgba(14,165,233,0.16)]"
      )}
    >
      {children}
    </button>
  );
}

function MessageFooter({
  timestamp,
  content,
  align = "start",
  showFeedback = false,
  isStreaming = false,
  onEdit,
}: {
  timestamp: number;
  content: string;
  align?: FooterAlign;
  showFeedback?: boolean;
  isStreaming?: boolean;
  onEdit?: () => void;
}) {
  const [copied, setCopied] = useState(false);
  const [feedback, setFeedback] = useState<FeedbackState>(null);

  useEffect(() => {
    if (!copied) return;
    const timeoutId = window.setTimeout(() => setCopied(false), COPY_RESET_TIMEOUT);
    return () => window.clearTimeout(timeoutId);
  }, [copied]);

  const handleCopy = async () => {
    try {
      await copyTextToClipboard(content);
      setCopied(true);
    } catch (error) {
      console.error("Failed to copy message", error);
    }
  };

  const handleFeedbackToggle = (next: Exclude<FeedbackState, null>) => {
    setFeedback((current) => (current === next ? null : next));
  };

  return (
    <div
      className={cn(
        "mt-2 flex flex-wrap items-center gap-2",
        align === "center" && "justify-center",
        align === "end" && "justify-end",
        align === "start" && "justify-start"
      )}
    >
      <span className="text-[11px] text-slate-400">{formatTimestamp(timestamp)}</span>

      {!isStreaming && (
        <div className="flex items-center gap-0.5">
          <IconActionButton
            label={copied ? "Скопировано" : "Копировать"}
            active={copied}
            onClick={() => void handleCopy()}
          >
            <CopyIcon className="h-[19px] w-[19px]" />
          </IconActionButton>

          {onEdit && (
            <IconActionButton label="Редактировать" onClick={onEdit}>
              <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
              </svg>
            </IconActionButton>
          )}

          {showFeedback && (
            <>
              <IconActionButton
                label="Нравится"
                tone="positive"
                active={feedback === "like"}
                onClick={() => handleFeedbackToggle("like")}
              >
                <ThumbUpIcon className="h-[19px] w-[19px]" />
              </IconActionButton>

              <IconActionButton
                label="Не нравится"
                tone="negative"
                active={feedback === "dislike"}
                onClick={() => handleFeedbackToggle("dislike")}
              >
                <ThumbDownIcon className="h-[19px] w-[19px]" />
              </IconActionButton>
            </>
          )}
        </div>
      )}
    </div>
  );
}

const SAFE_PROTOCOLS = ["https:", "http:", "mailto:", "tel:"];

function LinkChip({ href }: { href: string }) {
  const [imgError, setImgError] = useState(false);

  let hostname = "";
  try {
    hostname = new URL(href).hostname.replace(/^www\./, "");
  } catch {
    return null;
  }

  return (
    <a href={href} target="_blank" rel="noopener noreferrer" className="link-chip">
      {!imgError ? (
        <img
          src={`https://icons.duckduckgo.com/ip3/${hostname}.ico`}
          alt=""
          width={13}
          height={13}
          onError={() => setImgError(true)}
        />
      ) : (
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="10" />
          <path d="M2 12h20" />
          <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
        </svg>
      )}
      <span>{hostname}</span>
    </a>
  );
}

function MarkdownContent({
  content,
  isStreaming = false,
}: {
  content: string;
  isStreaming?: boolean;
}) {
  return (
    <div className={cn("min-w-0 markdown-content", isStreaming && "is-streaming")}>
      <ReactMarkdown
        components={{
          p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
          strong: ({ children }) => (
            <strong className="font-semibold">{children}</strong>
          ),
          em: ({ children }) => <em className="italic">{children}</em>,
          ul: ({ children }) => (
            <ul className="mb-2 ml-4 list-disc last:mb-0">{children}</ul>
          ),
          ol: ({ children }) => (
            <ol className="mb-2 ml-4 list-decimal last:mb-0">{children}</ol>
          ),
          li: ({ children }) => <li className="mb-0.5">{children}</li>,
          code: ({ children, className }) => {
            const isBlock = Boolean(className);

            if (isBlock) {
              return (
                <pre className="my-2 overflow-x-auto rounded-lg bg-slate-100 p-3 text-sm">
                  <code>{children}</code>
                </pre>
              );
            }

            return (
              <code className="rounded bg-slate-100 px-1.5 py-0.5 text-sm">
                {children}
              </code>
            );
          },
          h1: ({ children }) => (
            <h1 className="mb-2 mt-3 text-lg font-bold first:mt-0">{children}</h1>
          ),
          h2: ({ children }) => (
            <h2 className="mb-2 mt-3 text-base font-bold first:mt-0">{children}</h2>
          ),
          h3: ({ children }) => (
            <h3 className="mb-1 mt-2 text-sm font-bold first:mt-0">{children}</h3>
          ),
          blockquote: ({ children }) => (
            <blockquote className="my-2 border-l-2 border-emerald-400 pl-3 italic text-slate-600">
              {children}
            </blockquote>
          ),
          a: ({ href }) => {
            let safeHref: string | undefined;
            try {
              const parsed = new URL(href ?? "");
              safeHref = SAFE_PROTOCOLS.includes(parsed.protocol) ? href : undefined;
            } catch {
              safeHref = undefined;
            }
            if (!safeHref) return null;
            return <LinkChip href={safeHref} />;
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}

function SystemMessage({ message }: { message: Message }) {
  return (
    <div className="fade-in-up flex w-full justify-center py-1">
      <div className="flex max-w-[90%] flex-col items-center gap-2">
        <div className="inline-flex items-center gap-2 rounded-full border border-slate-200/60 bg-white/50 px-4 py-2 text-[12px] text-slate-500 shadow-[0_2px_8px_rgba(15,23,42,0.03)] backdrop-blur-xl">
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

        <MessageFooter timestamp={message.timestamp} content={message.content} align="center" />
      </div>
    </div>
  );
}

const PERSONALITY_HEADER: Record<NonNullable<Personality>, string> = {
  default: "text-emerald-600",
  friendly: "text-teal-500",
  professional: "text-blue-600",
};

const PERSONALITY_BORDER: Record<NonNullable<Personality>, string> = {
  default: "border-white/80",
  friendly: "border-teal-200/60",
  professional: "border-slate-300/60",
};

export default function ChatMessage({
  message,
  isStreaming = false,
  personality = "default",
  onEdit,
}: ChatMessageProps) {
  const isUser = message.role === "user";
  const isError = message.error === true;
  const showFeedback = !isUser && !isError;
  const activities = message.activities ?? [];
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState(message.content);
  const [editMinHeight, setEditMinHeight] = useState<number | undefined>();
  const [isSubmittingEdit, setIsSubmittingEdit] = useState(false);
  const editTextareaRef = useRef<HTMLTextAreaElement>(null);
  const textContentRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isEditing || !editTextareaRef.current) return;
    const el = editTextareaRef.current;
    el.style.height = "auto";
    el.style.height = `${el.scrollHeight}px`;
    el.focus();
    el.setSelectionRange(el.value.length, el.value.length);
  }, [isEditing]);

  useEffect(() => {
    if (!isEditing) return;
    const el = editTextareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${el.scrollHeight}px`;
  }, [editValue, isEditing]);

  const handleEditSubmit = async () => {
    const trimmed = editValue.trim();
    if (!trimmed || isSubmittingEdit || !onEdit) return;
    setIsSubmittingEdit(true);
    try {
      await onEdit(message.id, trimmed);
      setIsEditing(false);
    } finally {
      setIsSubmittingEdit(false);
    }
  };

  const handleEditCancel = () => {
    setEditValue(message.content);
    setIsEditing(false);
  };

  if (message.role === "system") {
    return <SystemMessage message={message} />;
  }

  const headerColor = isError ? "text-rose-400" : PERSONALITY_HEADER[personality];
  const bubbleBorder = isError ? "border-rose-100/80" : PERSONALITY_BORDER[personality];

  return (
    <div
      className={cn(
        "fade-in-up flex w-full",
        isUser ? "justify-end" : "justify-start"
      )}
    >
      <div
        className={cn(
          "min-w-0",
          isUser ? "max-w-[92%] md:max-w-[82%]" : "w-full max-w-[92%] md:max-w-[82%]"
        )}
      >
        <div className="min-w-0">
          <div
            className={cn(
              "rounded-[24px] px-4 py-3.5 shadow-[0_10px_30px_rgba(15,23,42,0.05)]",
              isUser
                ? "rounded-br-[8px] bg-[linear-gradient(135deg,#14b883_0%,#0ea5a4_100%)] text-white"
                : cn("rounded-bl-[8px] border bg-white/78 text-slate-800 backdrop-blur-2xl", bubbleBorder)
            )}
          >
            {!isUser && (
              <div
                className={cn(
                  "mb-1.5 text-sm font-semibold tracking-[0.08em] md:text-[15px]",
                  headerColor
                )}
              >
                {isError ? ERROR_LABEL : ROLE_LABEL}
              </div>
            )}

            {!isUser && activities.length > 0 && (
              <AgentActivityList activities={activities} isStreaming={isStreaming} />
            )}

            {isUser && isEditing ? (
              <div className="flex flex-col gap-2">
                <textarea
                  ref={editTextareaRef}
                  value={editValue}
                  onChange={(e) => setEditValue(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      void handleEditSubmit();
                    }
                    if (e.key === "Escape") handleEditCancel();
                  }}
                  disabled={isSubmittingEdit}
                  rows={1}
                  style={{ minHeight: editMinHeight !== undefined ? `${editMinHeight}px` : undefined }}
                  className="w-full resize-none bg-transparent text-[15px] leading-7 text-white/98 outline-none placeholder:text-white/50"
                />
                <div className="flex justify-end gap-2">
                  <button
                    type="button"
                    onClick={handleEditCancel}
                    className="rounded-lg px-3 py-1 text-[13px] font-medium text-white/70 transition-colors hover:text-white/95"
                  >
                    Отмена
                  </button>
                  <button
                    type="button"
                    onClick={() => void handleEditSubmit()}
                    disabled={isSubmittingEdit || !editValue.trim()}
                    className="rounded-lg bg-white/20 px-3 py-1 text-[13px] font-semibold text-white transition-all hover:bg-white/30 disabled:opacity-50"
                  >
                    Отправить
                  </button>
                </div>
              </div>
            ) : (
              <div
                ref={isUser ? textContentRef : undefined}
                className={cn(
                  "break-words text-[15px] leading-7",
                  isUser ? "whitespace-pre-wrap text-white/98" : "text-slate-800"
                )}
              >
                {isUser || isError ? (
                  message.content
                ) : message.content ? (
                  <MarkdownContent content={message.content} isStreaming={isStreaming} />
                ) : isStreaming ? (
                  <div className="mt-1 flex items-center gap-1.5 py-0.5">
                    <span className="loading-dot" />
                    <span className="loading-dot" style={{ animationDelay: "140ms" }} />
                    <span className="loading-dot" style={{ animationDelay: "280ms" }} />
                  </div>
                ) : null}
              </div>
            )}
          </div>

          <MessageFooter
            timestamp={message.timestamp}
            content={message.content}
            align={isUser ? "end" : "start"}
            showFeedback={showFeedback && !isStreaming}
            isStreaming={isStreaming}
            onEdit={isUser && onEdit && !isEditing ? () => {
              setEditValue(message.content);
              setEditMinHeight(textContentRef.current?.offsetHeight);
              setIsEditing(true);
            } : undefined}
          />
        </div>
      </div>
    </div>
  );
}
