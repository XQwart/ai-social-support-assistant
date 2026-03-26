import { getApiBase } from "@/api/base";
import { UnauthorizedError } from "@/api/errors";

const API_BASE = getApiBase();
const AUTH_TOKEN_KEY = "ai-social-support.auth.token";

interface ExchangeSberCodeResponseDto {
  message: string;
  token: string;
  user_name?: string;
}

export interface ExchangeSberCodeResponse {
  message: string;
  token: string;
  userName: string;
}

export async function exchangeSberCodeRequest(
  tokenCode: string
): Promise<ExchangeSberCodeResponse> {
  const res = await fetch(
    `${API_BASE}/auth/exchange?token_code=${encodeURIComponent(tokenCode)}`,
    {
      method: "GET",
      credentials: "include",
    }
  );

  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(body?.detail ?? "Не удалось завершить вход через Sber ID");
  }

  const data = (await res.json()) as ExchangeSberCodeResponseDto;

  return {
    message: data.message,
    token: data.token,
    userName: data.user_name?.trim() || "Пользователь",
  };
}

export async function refreshRequest(): Promise<string> {
  const res = await fetch(`${API_BASE}/auth/refresh`, {
    method: "POST",
    credentials: "include",
  });

  if (res.status === 401) {
    throw new UnauthorizedError();
  }

  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(body?.detail ?? "Refresh failed");
  }

  const data = await res.json();
  localStorage.setItem(AUTH_TOKEN_KEY, data.token);
  return data.token;
}

export async function logoutRequest(): Promise<void> {
  const res = await fetch(`${API_BASE}/auth/logout`, {
    method: "POST",
    credentials: "include",
  });

  if (res.status === 401) {
    throw new UnauthorizedError();
  }

  if (!res.ok) {
    throw new Error("Logout failed");
  }
}
