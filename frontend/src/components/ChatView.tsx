import { useCallback, useEffect, useRef, useState } from "react";

import ChatMessage from "@/components/ChatMessage";
import LoadingDots from "@/components/LoadingDots";

import type { Chat } from "@/types";

interface ChatViewProps {
  chat: Chat;
  isLoading: boolean;
  animatedMessageId: string | null;
}

const AUTO_SCROLL_THRESHOLD = 120;
const SHOW_SCROLL_BUTTON_THRESHOLD = 240;
const UNLOCK_AUTO_SCROLL_THRESHOLD = 8;
const PROGRAMMATIC_SCROLL_TIMEOUT_MS = 420;

function getDistanceFromBottom(node: HTMLDivElement): number {
  return node.scrollHeight - node.scrollTop - node.clientHeight;
}

function isNearBottom(node: HTMLDivElement): boolean {
  return getDistanceFromBottom(node) <= AUTO_SCROLL_THRESHOLD;
}

export default function ChatView({
  chat,
  isLoading,
  animatedMessageId,
}: ChatViewProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);
  const shouldAutoScrollRef = useRef(true);
  const manualScrollLockRef = useRef(false);
  const programmaticScrollRef = useRef(false);
  const programmaticTimeoutRef = useRef<number | null>(null);
  const lastScrollTopRef = useRef(0);
  const [showScrollToBottom, setShowScrollToBottom] = useState(false);

  const releaseProgrammaticScroll = useCallback(() => {
    if (programmaticTimeoutRef.current !== null) {
      window.clearTimeout(programmaticTimeoutRef.current);
    }

    programmaticTimeoutRef.current = window.setTimeout(() => {
      programmaticScrollRef.current = false;
    }, PROGRAMMATIC_SCROLL_TIMEOUT_MS);
  }, []);

  const scrollToBottom = useCallback((behavior: ScrollBehavior = "auto") => {
    const container = containerRef.current;
    if (!container) return;

    programmaticScrollRef.current = true;
    container.scrollTo({
      top: container.scrollHeight,
      behavior,
    });

    releaseProgrammaticScroll();
  }, [releaseProgrammaticScroll]);

  const syncScrollState = useCallback(() => {
    const container = containerRef.current;
    if (!container) return;

    const distanceFromBottom = getDistanceFromBottom(container);
    const isAtBottom = distanceFromBottom <= UNLOCK_AUTO_SCROLL_THRESHOLD;

    if (isAtBottom) {
      manualScrollLockRef.current = false;
      shouldAutoScrollRef.current = true;
    }

    setShowScrollToBottom(distanceFromBottom > SHOW_SCROLL_BUTTON_THRESHOLD);
    lastScrollTopRef.current = container.scrollTop;
  }, []);

  useEffect(() => {
    const frameId = window.requestAnimationFrame(() => {
      shouldAutoScrollRef.current = true;
      manualScrollLockRef.current = false;
      setShowScrollToBottom(false);
      scrollToBottom("auto");
    });

    return () => window.cancelAnimationFrame(frameId);
  }, [chat.id]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    lastScrollTopRef.current = container.scrollTop;

    const handleWheel = (event: WheelEvent) => {
      if (event.deltaY < 0 && !programmaticScrollRef.current) {
        manualScrollLockRef.current = true;
        shouldAutoScrollRef.current = false;
      }
    };

    const handleScroll = () => {
      const currentScrollTop = container.scrollTop;
      const scrolledUp = currentScrollTop < lastScrollTopRef.current - 1;
      const distanceFromBottom = getDistanceFromBottom(container);
      const atBottom = distanceFromBottom <= UNLOCK_AUTO_SCROLL_THRESHOLD;

      if (!programmaticScrollRef.current && scrolledUp) {
        manualScrollLockRef.current = true;
        shouldAutoScrollRef.current = false;
      }

      if (atBottom) {
        manualScrollLockRef.current = false;
        shouldAutoScrollRef.current = true;
      } else if (!manualScrollLockRef.current && isNearBottom(container)) {
        shouldAutoScrollRef.current = true;
      }

      setShowScrollToBottom(distanceFromBottom > SHOW_SCROLL_BUTTON_THRESHOLD);
      lastScrollTopRef.current = currentScrollTop;
    };

    handleScroll();
    container.addEventListener("wheel", handleWheel, { passive: true });
    container.addEventListener("scroll", handleScroll, { passive: true });

    return () => {
      container.removeEventListener("wheel", handleWheel);
      container.removeEventListener("scroll", handleScroll);
    };
  }, []);

  useEffect(() => {
    const container = containerRef.current;
    const content = contentRef.current;

    if (!container || !content || typeof ResizeObserver === "undefined") {
      return;
    }

    const observer = new ResizeObserver(() => {
      if (shouldAutoScrollRef.current) {
        scrollToBottom("auto");
      } else {
        syncScrollState();
      }
    });

    observer.observe(content);
    return () => observer.disconnect();
  }, [scrollToBottom, syncScrollState]);

  useEffect(() => {
    if (!shouldAutoScrollRef.current) return;

    scrollToBottom(chat.messages.length > 0 ? "smooth" : "auto");
  }, [chat.messages.length, isLoading, animatedMessageId, scrollToBottom]);

  useEffect(() => {
    return () => {
      if (programmaticTimeoutRef.current !== null) {
        window.clearTimeout(programmaticTimeoutRef.current);
      }
    };
  }, []);

  return (
    <div className="relative h-full min-h-0 overflow-hidden">
      <div
        ref={containerRef}
        className="custom-scrollbar h-full min-h-0 overflow-y-auto overscroll-contain px-3 pb-28 pt-24 md:px-5 md:pb-32 md:pt-28"
        style={{ scrollPaddingBottom: "9rem" }}
      >
        <div ref={contentRef} className="mx-auto flex w-full max-w-4xl flex-col gap-4">
          {chat.messages.map((message) => (
            <ChatMessage
              key={message.id}
              message={message}
              shouldAnimate={message.id === animatedMessageId}
            />
          ))}

          {isLoading && <LoadingDots chatId={chat.id} />}
        </div>
      </div>

      {showScrollToBottom && (
        <div className="pointer-events-none absolute bottom-4 left-1/2 z-20 -translate-x-1/2 md:bottom-5">
          <button
            type="button"
            onClick={() => {
              manualScrollLockRef.current = false;
              shouldAutoScrollRef.current = true;
              setShowScrollToBottom(false);
              scrollToBottom("smooth");
            }}
            className="pointer-events-auto inline-flex h-14 w-14 items-center justify-center rounded-full border border-white/80 bg-white text-slate-800 shadow-[0_18px_40px_rgba(15,23,42,0.22)] backdrop-blur-2xl transition-all hover:-translate-y-0.5 hover:shadow-[0_22px_46px_rgba(15,23,42,0.26)] active:translate-y-0"
            aria-label="Перейти к последнему сообщению"
            title="К последнему сообщению"
          >
            <svg
              width="22"
              height="22"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M12 5v14" />
              <path d="m19 12-7 7-7-7" />
            </svg>
          </button>
        </div>
      )}
    </div>
  );
}
