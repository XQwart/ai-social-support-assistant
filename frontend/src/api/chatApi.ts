import type { Chat, Message } from "@/types";
import { UnauthorizedError } from "@/api/errors";

const API_BASE = import.meta.env.VITE_API_URL || "";
const AUTH_TOKEN_KEY = "ai-social-support.auth.token";

function getAuthHeaders(): Record<string, string> {
  const token = localStorage.getItem(AUTH_TOKEN_KEY);
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  return headers;
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

// ==================== ЧАТЫ ====================

export async function createChat(
  content: string,
  signal?: AbortSignal
): Promise<Chat> {
  const res = await fetch(`${API_BASE}/chats/`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify({ content }),
    signal,
    credentials: "include",
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
  const res = await fetch(`${API_BASE}/chats/?limit=${limit}&offset=${offset}`, {
    headers: getAuthHeaders(),
    signal,
    credentials: "include",
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
  const res = await fetch(`${API_BASE}/chats/${chatId}/messages`, {
    headers: getAuthHeaders(),
    signal,
    credentials: "include",
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
): Promise<{ userMsg: Message; assistantMsg: Message }> {
  // 1. Send user message
  const userRes = await fetch(`${API_BASE}/chats/${chatId}/messages`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify({ content, role: "user" }),
    signal,
    credentials: "include",
  });

  await ensureOk(userRes, "Не удалось отправить сообщение");

  const userData = await userRes.json();
  const userMsg: Message = {
    id: String(userData.id),
    role: "user",
    content: userData.content,
    timestamp: ts(userData.created_at),
  };

  // 2. Generate assistant response
  const assistantText = generateResponse(content);

  // 3. Save assistant message to backend
  const asstRes = await fetch(`${API_BASE}/chats/${chatId}/messages`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify({ content: assistantText, role: "assistant" }),
    signal,
    credentials: "include",
  });

  await ensureOk(asstRes, "Не удалось сохранить ответ ассистента");

  const aData = await asstRes.json();
  const assistantMsg: Message = {
    id: String(aData.id),
    role: "assistant",
    content: aData.content,
    timestamp: ts(aData.created_at),
  };

  return { userMsg, assistantMsg };
}

export async function deleteChat(
  chatId: string,
  signal?: AbortSignal
): Promise<void> {
  const res = await fetch(`${API_BASE}/chats/${chatId}`, {
    method: "DELETE",
    headers: getAuthHeaders(),
    signal,
    credentials: "include",
  });

  await ensureOk(res, "Не удалось удалить чат");
}

// ==================== ЗАГЛУШКА ИИ ====================

function generateResponse(message: string): string {
  const t = message.toLowerCase();

  if (t.includes("льгот"))
    return "Чтобы проверить, какие льготы вам доступны, обычно учитываются ваш статус, состав семьи, доход, инвалидность, возраст и регион проживания. Подготовьте паспорт, СНИЛС и документы, подтверждающие право на меру поддержки.";

  if (t.includes("жкх") || t.includes("субсид"))
    return "Субсидия на оплату ЖКХ предоставляется, если расходы семьи на коммунальные услуги превышают установленную долю от совокупного дохода. Обычно заявление подают через МФЦ, соцзащиту или портал Госуслуг.";

  if (t.includes("ребён") || t.includes("ребен") || t.includes("рождении"))
    return "При рождении ребёнка могут быть доступны единовременное пособие, ежемесячные выплаты, материнский капитал и региональные меры поддержки. Точный список зависит от дохода семьи и региона.";

  if (t.includes("малоимущ"))
    return "Для признания семьи малоимущей обычно сравнивают среднедушевой доход с региональным прожиточным минимумом. Понадобятся документы о составе семьи, доходах, паспорта и заявление.";

  if (t.includes("инвалид"))
    return "Для оформления инвалидности потребуется направление на медико-социальную экспертизу, медицинские документы и заключения врачей. После установления группы можно оформить пенсию и дополнительные льготы.";

  if (t.includes("безработ"))
    return "Для назначения пособия по безработице нужно встать на учёт через центр занятости или Госуслуги. Обычно требуются паспорт, документы об образовании и сведения о трудовой деятельности.";

  return "Я могу помочь с вопросами по льготам, пособиям, субсидиям, статусу малоимущей семьи, инвалидности и другим мерам социальной поддержки. Опишите вашу ситуацию подробнее.";
}
