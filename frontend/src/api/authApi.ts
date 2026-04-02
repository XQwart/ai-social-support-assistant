import { getApiBase } from "@/api/base";
import { UnauthorizedError } from "@/api/errors";

const API_BASE = getApiBase();
const AUTH_TOKEN_KEY = "ai-social-support.auth.token";
const AUTH_USER_KEY = "ai-social-support.auth.user";

export interface UserInfo {
  firstName: string;
  secondName: string;
  placeOfWork: string;
}

function parseUserInfo(raw: unknown): UserInfo {
  const u = raw as { first_name?: string; second_name?: string; place_of_work?: string } | null;
  return {
    firstName: u?.first_name?.trim() ?? "",
    secondName: u?.second_name?.trim() ?? "",
    placeOfWork: u?.place_of_work?.trim() ?? "",
  };
}

export interface ExchangeSberCodeResponse {
  message: string;
  token: string;
  user: UserInfo;
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

  const data = await res.json();

  return {
    message: data.message,
    token: data.token,
    user: parseUserInfo(data.user),
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
  localStorage.setItem(AUTH_USER_KEY, JSON.stringify(parseUserInfo(data.user)));
  return data.token;
}

export interface MockLoginResponse {
  message: string;
  token: string;
  user: UserInfo;
}

export async function mockLoginRequest(): Promise<MockLoginResponse> {
  const res = await fetch(`${API_BASE}/auth/mock-login`, {
    method: "POST",
    credentials: "include",
  });

  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(body?.detail ?? "Не удалось выполнить временный вход");
  }

  const data = await res.json();

  return {
    message: data.message,
    token: data.token,
    user: parseUserInfo(data.user),
  };
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
