import type {
  AgentActivity,
  AgentActionKind,
  Chat,
  StreamingResponse,
} from "@/types";
import type { StreamEvent } from "@/api/chatApi";

const EMPTY_STREAMING: StreamingResponse = {
  buffer: "",
  content: "",
  phaseId: null,
  phaseStartOffset: 0,
  activities: [],
  streamComplete: false,
  finalMessage: null,
};

export function createStreaming(): StreamingResponse {
  return { ...EMPTY_STREAMING, activities: [] };
}

export function ensureStreaming(chat: Chat): StreamingResponse {
  return chat.streaming ?? EMPTY_STREAMING;
}

function upsertActivity(
  activities: AgentActivity[],
  next: AgentActivity
): AgentActivity[] {
  const idx = activities.findIndex((a) => a.id === next.id);
  if (idx === -1) {
    return [...activities, next];
  }
  const copy = [...activities];
  copy[idx] = { ...copy[idx], ...next };
  return copy;
}

function commitThinkingBuffer(
  activities: AgentActivity[],
  phaseId: string,
  text: string
): AgentActivity[] {
  if (!text.trim()) {
    return activities;
  }
  const activity: AgentActivity = {
    id: `thinking-${phaseId}`,
    kind: "thinking",
    status: "done",
    text,
  };
  return [...activities, activity];
}

export function reduceStream(chat: Chat, event: StreamEvent): Chat {
  const streaming = ensureStreaming(chat);

  switch (event.type) {
    case "phase_start":
      return {
        ...chat,
        streaming: {
          ...streaming,
          phaseId: event.phase_id,
          phaseStartOffset: streaming.buffer.length,
        },
      };

    case "token": {
      if (streaming.phaseId !== event.phase_id) {
        return chat;
      }
      return {
        ...chat,
        streaming: {
          ...streaming,
          buffer: streaming.buffer + event.delta,
        },
      };
    }

    case "phase_end": {
      if (streaming.phaseId !== event.phase_id) {
        return chat;
      }

      if (event.role === "thinking") {
        const offset = streaming.phaseStartOffset;
        const thinkingText = streaming.buffer.slice(offset);
        const truncatedBuffer = streaming.buffer.slice(0, offset);
        const truncatedContent =
          streaming.content.length > offset
            ? truncatedBuffer
            : streaming.content;
        return {
          ...chat,
          streaming: {
            ...streaming,
            buffer: truncatedBuffer,
            content: truncatedContent,
            phaseId: null,
            phaseStartOffset: truncatedBuffer.length,
            activities: commitThinkingBuffer(
              streaming.activities,
              event.phase_id,
              thinkingText
            ),
          },
        };
      }

      return {
        ...chat,
        streaming: {
          ...streaming,
          phaseId: null,
          phaseStartOffset: streaming.buffer.length,
        },
      };
    }

    case "action_start": {
      const activity: AgentActivity = {
        id: event.action_id,
        kind: event.kind as AgentActionKind,
        status: "running",
        input: event.input as AgentActivity["input"],
      };
      return {
        ...chat,
        streaming: {
          ...streaming,
          activities: upsertActivity(streaming.activities, activity),
        },
      };
    }

    case "action_end": {
      const existing = streaming.activities.find((a) => a.id === event.action_id);
      const activity: AgentActivity = {
        id: event.action_id,
        kind: (existing?.kind ?? (event.kind as AgentActionKind)) as AgentActionKind,
        status: "done",
        input: existing?.input,
        ok: event.ok,
      };
      return {
        ...chat,
        streaming: {
          ...streaming,
          activities: upsertActivity(streaming.activities, activity),
        },
      };
    }

    default:
      return chat;
  }
}
