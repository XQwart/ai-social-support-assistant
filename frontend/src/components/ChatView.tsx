import { useEffect, useRef } from "react";
import ChatMessage from "@/components/ChatMessage";
import LoadingDots from "@/components/LoadingDots";
import type { Chat } from "@/types";

interface ChatViewProps {
  chat: Chat;
  isLoading: boolean;
  animatedMessageId: string | null;
}

export default function ChatView({
  chat,
  isLoading,
  animatedMessageId,
}: ChatViewProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) {
      return;
    }

    container.scrollTo({
      top: container.scrollHeight,
      behavior: "smooth",
    });
  }, [chat.messages, isLoading]);

  return (
    <div
      ref={containerRef}
      className="custom-scrollbar flex-1 overflow-y-auto px-3 pb-4 pt-24 md:px-5 md:pt-28"
    >
      <div className="mx-auto flex w-full max-w-4xl flex-col gap-1">
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
