import { getApiBase } from "@/api/base";
import type { Chat, Message } from "@/types";
import { ApiError } from "@/api/errors";
import { AUTH_TOKEN_KEY, refreshRequest } from "@/api/authApi";

const API_BASE = getApiBase();

let refreshPromise: Promise<string> | null = null;

function mergeAuthHeaders(initHeaders?: HeadersInit): Headers {
  const headers = new Headers(initHeaders || {});
  const token = localStorage.getItem(AUTH_TOKEN_KEY);

  headers.set("Content-Type", "application/json");

  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  return headers;
}

async function getFreshAccessToken(): Promise<string> {
  if (!refreshPromise) {
    refreshPromise = refreshRequest()
      .then((session) => session.token)
      .finally(() => {
        refreshPromise = null;
      });
  }
  return refreshPromise;
}

async function authFetch(
  input: RequestInfo | URL,
  init: RequestInit = {}
): Promise<Response> {
  const res = await fetch(input, {
    ...init,
    headers: mergeAuthHeaders(init.headers),
    credentials: "include",
  });

  if (res.status !== 401 && res.status !== 403) {
    return res;
  }

  const newToken = await getFreshAccessToken();

  const headers = mergeAuthHeaders(init.headers);
  headers.set("Authorization", `Bearer ${newToken}`);

  return fetch(input, {
    ...init,
    headers,
    credentials: "include",
  });
}

function ts(dateStr: string): number {
  return new Date(dateStr).getTime();
}

async function getErrorMessage(
  res: Response,
  fallback: string
): Promise<string> {
  const body = await res.json().catch(() => null);
  return body?.detail ?? fallback;
}

async function ensureOk(res: Response, fallback: string): Promise<void> {
  if (!res.ok) {
    throw new ApiError(res.status, await getErrorMessage(res, fallback));
  }
}

function createChatState(chat: {
  id: number;
  title: string;
  created_at: string;
  updated_at: string;
}): Chat {
  return {
    id: String(chat.id),
    title: chat.title,
    createdAt: ts(chat.created_at),
    updatedAt: ts(chat.updated_at),
    messages: [],
    historyStatus: "idle",
    historyError: null,
    messagesOffset: 0,
    hasOlderMessages: false,
    isHistoryHydrated: false,
    pendingMessageText: null,
    sendError: null,
  };
}

export interface ChatsPage {
  items: Chat[];
  limit: number;
  offset: number;
  hasMore: boolean;
}

export interface MessagesPage {
  messages: Message[];
  limit: number;
  offset: number;
  hasMore: boolean;
}

export async function createChat(
  content: string,
  signal?: AbortSignal
): Promise<Chat> {
  const res = await authFetch(`${API_BASE}/chats/`, {
    method: "POST",
    body: JSON.stringify({ content }),
    signal,
  });

  await ensureOk(res, "Не удалось создать чат");

  const data = await res.json();

  return {
    ...createChatState(data),
    historyStatus: "ready",
    isHistoryHydrated: true,
  };
}

export async function fetchChat(
  chatId: string,
  signal?: AbortSignal
): Promise<Chat> {
  const res = await authFetch(
    `${API_BASE}/chats/${encodeURIComponent(chatId)}`,
    { signal }
  );

  await ensureOk(res, "Не удалось загрузить чат");

  const data = await res.json();
  return createChatState(data);
}

export async function fetchChats(
  limit = 100,
  offset = 0,
  signal?: AbortSignal
): Promise<ChatsPage> {
  const qs = new URLSearchParams({ limit: String(limit), offset: String(offset) });
  const res = await authFetch(`${API_BASE}/chats/?${qs}`, { signal });

  await ensureOk(res, "Не удалось загрузить список чатов");

  const data = await res.json();
  const items = (data.items || []).map(
    (c: {
      id: number;
      user_id: number;
      title: string;
      created_at: string;
      updated_at: string;
    }) => createChatState(c)
  );

  return {
    items,
    limit: Number(data.limit ?? limit),
    offset: Number(data.offset ?? offset),
    hasMore: items.length >= Number(data.limit ?? limit),
  };
}

export async function fetchMessages(
  chatId: string,
  limit = 100,
  offset = 0,
  signal?: AbortSignal
): Promise<MessagesPage> {
  const qs = new URLSearchParams({ limit: String(limit), offset: String(offset) });
  const res = await authFetch(
    `${API_BASE}/chats/${encodeURIComponent(chatId)}/messages?${qs}`,
    { signal }
  );

  await ensureOk(res, "Не удалось загрузить сообщения");

  const data = await res.json();
  const messages = (data.messages || []).map(
    (m: { id: number; role: string; content: string; created_at: string }) => ({
      id: String(m.id),
      role: m.role as "user" | "assistant" | "system",
      content: m.content,
      timestamp: ts(m.created_at),
    })
  );

  return {
    messages,
    limit,
    offset,
    hasMore: messages.length >= limit,
  };
}

export async function sendMessageToChat(
  chatId: string,
  content: string,
  signal?: AbortSignal
): Promise<{ userMsg: Message; assistantMsg: Message; contextCompressed: boolean }> {
  const res = await authFetch(`${API_BASE}/chats/${encodeURIComponent(chatId)}/messages`, {
    method: "POST",
    body: JSON.stringify({ content }),
    signal,
  });

  await ensureOk(res, "Не удалось отправить сообщение");

  const data = await res.json();

  const userMsg: Message = {
    id: String(data.user_message.id),
    role: "user",
    content: data.user_message.content,
    timestamp: ts(data.user_message.created_at),
  };

  const assistantMsg: Message = {
    id: String(data.assistant_message.id),
    role: "assistant",
    content: data.assistant_message.content,
    timestamp: ts(data.assistant_message.created_at),
  };

  return {
    userMsg,
    assistantMsg,
    contextCompressed: data.context_compressed ?? false,
  };
}

export async function renameChat(
  chatId: string,
  title: string,
  signal?: AbortSignal
): Promise<Chat> {
  const res = await authFetch(`${API_BASE}/chats/${encodeURIComponent(chatId)}`, {
    method: "PATCH",
    body: JSON.stringify({ title }),
    signal,
  });

  await ensureOk(res, "Не удалось переименовать чат");

  const data = await res.json();
  return createChatState(data);
}

export async function deleteChat(
  chatId: string,
  signal?: AbortSignal
): Promise<void> {
  const res = await authFetch(`${API_BASE}/chats/${encodeURIComponent(chatId)}`, {
    method: "DELETE",
    signal,
  });

  await ensureOk(res, "Не удалось удалить чат");
}
