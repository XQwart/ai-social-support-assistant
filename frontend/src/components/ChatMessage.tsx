import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";

import { AssistantAvatar } from "@/components/AssistantAvatar";
import TypingAnimation from "@/components/TypingAnimation";

import type { Message } from "@/types";
import { cn } from "@/utils/cn";

interface ChatMessageProps {
  message: Message;
  shouldAnimate: boolean;
}

const ROLE_LABEL = "Помощник";
const ERROR_LABEL = "Системное сообщение";
const TYPING_SPEED = 10;
const TIME_LOCALE = "ru-RU";
const COPY_RESET_TIMEOUT = 1400;

const TIME_FORMAT: Intl.DateTimeFormatOptions = {
  hour: "2-digit",
  minute: "2-digit",
};

type FeedbackState = "like" | "dislike" | null;
type FooterAlign = "start" | "center" | "end";
type IconTone = "neutral" | "positive" | "negative";

function formatTime(timestamp: number): string {
  return new Date(timestamp).toLocaleTimeString(TIME_LOCALE, TIME_FORMAT);
}

async function copyTextToClipboard(value: string): Promise<void> {
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(value);
    return;
  }

  const textarea = document.createElement("textarea");
  textarea.value = value;
  textarea.setAttribute("readonly", "");
  textarea.style.position = "fixed";
  textarea.style.opacity = "0";
  textarea.style.pointerEvents = "none";
  textarea.style.top = "0";
  textarea.style.left = "0";

  document.body.appendChild(textarea);
  textarea.focus();
  textarea.select();
  document.execCommand("copy");
  document.body.removeChild(textarea);
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
        "inline-flex h-9 w-9 items-center justify-center rounded-xl transition-all cursor-pointer",
        !active && "text-slate-500 hover:bg-slate-900/5 hover:text-slate-700 active:scale-[0.96]",
        active && tone === "positive" && "bg-emerald-50 text-emerald-600 shadow-[0_10px_24px_rgba(16,185,129,0.12)]",
        active && tone === "negative" && "bg-rose-50 text-rose-600 shadow-[0_10px_24px_rgba(244,63,94,0.12)]",
        active && tone === "neutral" && "bg-emerald-50 text-emerald-600 shadow-[0_10px_24px_rgba(16,185,129,0.12)]"
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
}: {
  timestamp: number;
  content: string;
  align?: FooterAlign;
  showFeedback?: boolean;
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
      <span className="text-[11px] text-slate-400">{formatTime(timestamp)}</span>

      <div className="flex items-center gap-0.5">
        <IconActionButton
          label={copied ? "Скопировано" : "Копировать"}
          active={copied}
          onClick={() => void handleCopy()}
        >
          <CopyIcon className="h-[19px] w-[19px]" />
        </IconActionButton>

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
    </div>
  );
}

function MarkdownContent({
  content,
  showCursor = false,
}: {
  content: string;
  showCursor?: boolean;
}) {
  return (
    <div className="min-w-0">
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
          a: ({ href, children }) => (
            <a
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              className="text-emerald-600 underline decoration-emerald-300 underline-offset-2 hover:text-emerald-700"
            >
              {children}
            </a>
          ),
        }}
      >
        {content}
      </ReactMarkdown>

      {showCursor && <span className="typing-cursor ml-1 inline-block align-baseline" aria-hidden="true" />}
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

export default function ChatMessage({
  message,
  shouldAnimate,
}: ChatMessageProps) {
  const isUser = message.role === "user";
  const isError = message.error === true;
  const showFeedback = !isUser && !isError;

  if (message.role === "system") {
    return <SystemMessage message={message} />;
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
          "max-w-[92%] min-w-0 md:max-w-[82%]",
          !isUser && "flex items-start gap-4"
        )}
      >
        {!isUser && (
          <AssistantAvatar className="mt-0.5" variant={isError ? "error" : "default"} />
        )}

        <div className="min-w-0">
          <div
            className={cn(
              "rounded-[24px] px-4 py-3.5 shadow-[0_10px_30px_rgba(15,23,42,0.05)]",
              isUser
                ? "rounded-br-[8px] bg-[linear-gradient(135deg,#14b883_0%,#0ea5a4_100%)] text-white"
                : isError
                ? "rounded-bl-[8px] border border-rose-100/80 bg-white/82 text-slate-800 backdrop-blur-2xl"
                : "rounded-bl-[8px] border border-white/80 bg-white/78 text-slate-800 backdrop-blur-2xl"
            )}
          >
            {!isUser && (
              <div
                className={cn(
                  "mb-1.5 text-sm font-semibold tracking-[0.08em] md:text-[15px]",
                  isError ? "text-rose-400" : "text-emerald-600"
                )}
              >
                {isError ? ERROR_LABEL : ROLE_LABEL}
              </div>
            )}

            <div
              className={cn(
                "break-words text-[15px] leading-7",
                isUser ? "whitespace-pre-wrap text-white/98" : "text-slate-800"
              )}
            >
              {isUser ? (
                message.content
              ) : isError ? (
                message.content
              ) : shouldAnimate ? (
                <TypingAnimation text={message.content} speed={TYPING_SPEED}>
                  {(displayed, done) => (
                    <MarkdownContent
                      content={done ? message.content : displayed}
                      showCursor={!done}
                    />
                  )}
                </TypingAnimation>
              ) : (
                <MarkdownContent content={message.content} />
              )}
            </div>
          </div>

          <MessageFooter
            timestamp={message.timestamp}
            content={message.content}
            align={isUser ? "end" : "start"}
            showFeedback={showFeedback}
          />
        </div>
      </div>
    </div>
  );
}
