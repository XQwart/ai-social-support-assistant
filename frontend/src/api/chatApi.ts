import { getApiBase } from "@/api/base";
import type { Chat, Message } from "@/types";
import { UnauthorizedError } from "@/api/errors";
import { refreshRequest } from "@/api/authApi";

const API_BASE = getApiBase();
const AUTH_TOKEN_KEY = "ai-social-support.auth.token";

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
    refreshPromise = refreshRequest().finally(() => {
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

  if (res.status !== 401) {
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
  if (res.status === 401) {
    throw new UnauthorizedError();
  }

  if (!res.ok) {
    throw new Error(await getErrorMessage(res, fallback));
  }
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
    id: String(data.id),
    title: data.title,
    createdAt: ts(data.created_at),
    updatedAt: ts(data.updated_at),
    messages: [],
  };
}

export async function fetchChats(
  limit = 100,
  offset = 0,
  signal?: AbortSignal
): Promise<Chat[]> {
  const res = await authFetch(`${API_BASE}/chats/?limit=${limit}&offset=${offset}`, {
    signal,
  });

  await ensureOk(res, "Не удалось загрузить список чатов");

  const data = await res.json();

  return (data.items || []).map(
    (c: {
      id: number;
      user_id: number;
      title: string;
      created_at: string;
      updated_at: string;
    }) => ({
      id: String(c.id),
      title: c.title,
      createdAt: ts(c.created_at),
      updatedAt: ts(c.updated_at),
      messages: [],
    })
  );
}

export async function fetchMessages(
  chatId: string,
  signal?: AbortSignal
): Promise<Message[]> {
  const res = await authFetch(`${API_BASE}/chats/${chatId}/messages`, {
    signal,
  });

  await ensureOk(res, "Не удалось загрузить сообщения");

  const data = await res.json();

  return (data.messages || []).map(
    (m: { id: number; role: string; content: string; created_at: string }) => ({
      id: String(m.id),
      role: m.role as "user" | "assistant" | "system",
      content: m.content,
      timestamp: ts(m.created_at),
    })
  );
}

export async function sendMessageToChat(
  chatId: string,
  content: string,
  signal?: AbortSignal
): Promise<{ userMsg: Message; assistantMsg: Message; contextCompressed: boolean }> {
  const res = await authFetch(`${API_BASE}/chats/${chatId}/messages`, {
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

export async function deleteChat(
  chatId: string,
  signal?: AbortSignal
): Promise<void> {
  const res = await authFetch(`${API_BASE}/chats/${chatId}`, {
    method: "DELETE",
    signal,
  });

  await ensureOk(res, "Не удалось удалить чат");
}
