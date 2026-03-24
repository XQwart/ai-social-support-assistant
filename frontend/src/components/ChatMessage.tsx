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
const TIME_FORMAT: Intl.DateTimeFormatOptions = {
  hour: "2-digit",
  minute: "2-digit",
};

function formatTime(timestamp: number): string {
  return new Date(timestamp).toLocaleTimeString(TIME_LOCALE, TIME_FORMAT);
}

function MarkdownContent({ content }: { content: string }) {
  return (
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
  );
}

function SystemMessage({ message }: { message: Message }) {
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

export default function ChatMessage({
  message,
  shouldAnimate,
}: ChatMessageProps) {
  const isUser = message.role === "user";
  const isError = message.error === true;

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
          "max-w-[88%] md:max-w-[78%]",
          !isUser && "flex items-start gap-3"
        )}
      >
        {!isUser && (
          <AssistantAvatar variant={isError ? "error" : "default"} />
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
                "mb-1 text-[11px] font-semibold tracking-[0.12em]",
                isError ? "text-rose-400" : "text-emerald-600/90"
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
                {(displayed, done) =>
                  done ? (
                    <MarkdownContent content={message.content} />
                  ) : (
                    <span className="inline-block max-w-full whitespace-pre-wrap">
                      {displayed}
                      <span className="typing-cursor" aria-hidden="true" />
                    </span>
                  )
                }
              </TypingAnimation>
            ) : (
              <MarkdownContent content={message.content} />
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
