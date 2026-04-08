export type MessageRole = "user" | "assistant" | "system";

export type AsyncStatus = "idle" | "loading" | "ready" | "error";

export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: number;
  error?: boolean;
}

export interface Chat {
  id: string;
  title: string;
  createdAt: number;
  updatedAt: number;
  messages: Message[];
  historyStatus: AsyncStatus;
  historyError: string | null;
  messagesOffset: number;
  hasOlderMessages: boolean;
  isHistoryHydrated: boolean;
  pendingMessageText: string | null;
  sendError: string | null;
}
