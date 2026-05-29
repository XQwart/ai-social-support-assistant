import type { Chat, Message, StreamingResponse } from "@/types";

export const TYPEWRITER_INTERVAL_MS = 12;
export const TYPEWRITER_CHARS_PER_TICK = 3;

interface TypewriterStep {
  chat: Chat;
  finalized: Message | null;
}

function advanceContent(
  streaming: StreamingResponse,
  hidden: boolean,
  charsPerTick: number
): string {
  const { buffer, content } = streaming;
  if (content.length > buffer.length) {
    return buffer;
  }
  if (content === buffer) {
    return content;
  }
  if (hidden) {
    return buffer;
  }
  return buffer.slice(0, content.length + charsPerTick);
}

function buildFinalMessage(
  streaming: StreamingResponse,
  fallback: StreamingResponse["finalMessage"]
): Message | null {
  if (!fallback) return null;
  return {
    id: fallback.id,
    role: fallback.role,
    content: fallback.content,
    timestamp: fallback.timestamp,
  };
}

export function advanceTypewriterChat(
  chat: Chat,
  hidden: boolean,
  charsPerTick: number = TYPEWRITER_CHARS_PER_TICK
): TypewriterStep {
  const streaming = chat.streaming;
  if (!streaming) return { chat, finalized: null };

  const nextContent = advanceContent(streaming, hidden, charsPerTick);
  const reachedEnd =
    streaming.streamComplete && nextContent === streaming.buffer;

  if (reachedEnd && streaming.finalMessage) {
    const finalized = buildFinalMessage(streaming, streaming.finalMessage);
    return { chat, finalized };
  }

  if (nextContent === streaming.content) {
    return { chat, finalized: null };
  }

  return {
    chat: { ...chat, streaming: { ...streaming, content: nextContent } },
    finalized: null,
  };
}

export function hasActiveTypewriter(chat: Chat): boolean {
  return !!chat.streaming;
}
