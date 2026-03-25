import { useEffect, useRef } from "react";

import ChatMessage from "@/components/ChatMessage";
import LoadingDots from "@/components/LoadingDots";

import type { Chat } from "@/types";

interface ChatViewProps {
  chat: Chat;
  isLoading: boolean;
  animatedMessageId: string | null;
}

const AUTO_SCROLL_THRESHOLD = 120;

function isNearBottom(node: HTMLDivElement): boolean {
  return node.scrollHeight - node.scrollTop - node.clientHeight <= AUTO_SCROLL_THRESHOLD;
}

export default function ChatView({
  chat,
  isLoading,
  animatedMessageId,
}: ChatViewProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);
  const shouldAutoScrollRef = useRef(true);

  const scrollToBottom = (behavior: ScrollBehavior = "auto") => {
    const container = containerRef.current;
    if (!container) return;

    container.scrollTo({
      top: container.scrollHeight,
      behavior,
    });
  };

  useEffect(() => {
    const frameId = window.requestAnimationFrame(() => {
      shouldAutoScrollRef.current = true;
      scrollToBottom("auto");
    });

    return () => window.cancelAnimationFrame(frameId);
  }, [chat.id]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const handleScroll = () => {
      shouldAutoScrollRef.current = isNearBottom(container);
    };

    handleScroll();
    container.addEventListener("scroll", handleScroll, { passive: true });

    return () => container.removeEventListener("scroll", handleScroll);
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
      }
    });

    observer.observe(content);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (!shouldAutoScrollRef.current) return;
    scrollToBottom(chat.messages.length > 0 ? "smooth" : "auto");
  }, [chat.messages.length, isLoading, animatedMessageId]);

  return (
    <div
      ref={containerRef}
      className="custom-scrollbar min-h-0 flex-1 overflow-y-auto px-3 pb-6 pt-24 md:px-5 md:pb-8 md:pt-28"
      style={{ scrollPaddingBottom: "2rem" }}
    >
      <div ref={contentRef} className="mx-auto flex w-full max-w-4xl flex-col gap-4">
        {chat.messages.map((message) => (
          <ChatMessage
            key={message.id}
            message={message}
            shouldAnimate={message.id === animatedMessageId}
          />
        ))}

        {isLoading && <LoadingDots />}
      </div>
    </div>
  );
}
