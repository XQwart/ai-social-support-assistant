export type MessageRole = "user" | "assistant" | "system";

export type AsyncStatus = "idle" | "loading" | "ready" | "error";

export type AgentActionKind =
  | "thinking"
  | "rag"
  | "web_search"
  | "fetch_page"
  | "memory";

export type AgentActivityStatus = "running" | "done";

export interface AgentRagInput {
  query?: string | null;
  region?: string | null;
}

export interface AgentWebSearchInput {
  query?: string | null;
}

export interface AgentFetchPageInput {
  urls?: string[];
}

export type AgentActionInput =
  | AgentRagInput
  | AgentWebSearchInput
  | AgentFetchPageInput
  | Record<string, never>;

export interface AgentActivity {
  id: string;
  kind: AgentActionKind;
  status: AgentActivityStatus;
  text?: string;
  input?: AgentActionInput;
  ok?: boolean;
}

export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: number;
  error?: boolean;
  activities?: AgentActivity[];
}

export interface StreamingFinalMessage {
  id: string;
  role: "assistant";
  content: string;
  timestamp: number;
}

export interface StreamingResponse {
  buffer: string;
  content: string;
  phaseId: string | null;
  phaseStartOffset: number;
  activities: AgentActivity[];
  streamComplete: boolean;
  finalMessage: StreamingFinalMessage | null;
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
  streaming?: StreamingResponse | null;
}
