import { getApiBase } from "@/api/base";
import { UnauthorizedError } from "@/api/errors";

const API_BASE = getApiBase();
const AUTH_TOKEN_KEY = "ai-social-support.auth.token";
const AUTH_USER_KEY = "ai-social-support.auth.user";
const AUTH_SESSION_EVENT = "ai-social-support:auth-session";

export interface UserInfo {
  firstName: string;
  secondName: string;
  placeOfWork: string;
}

export interface AuthSession {
  token: string;
  user: UserInfo;
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

function emitAuthSession(session: AuthSession) {
  if (typeof window === "undefined") {
    return;
  }

  window.dispatchEvent(
    new CustomEvent<AuthSession>(AUTH_SESSION_EVENT, {
      detail: session,
    })
  );
}

export function storeAuthSession(session: AuthSession) {
  if (typeof window !== "undefined") {
    localStorage.setItem(AUTH_TOKEN_KEY, session.token);
    localStorage.setItem(AUTH_USER_KEY, JSON.stringify(session.user));
  }

  emitAuthSession(session);
}

export function clearStoredAuthSession() {
  if (typeof window === "undefined") {
    return;
  }

  localStorage.removeItem(AUTH_TOKEN_KEY);
  localStorage.removeItem(AUTH_USER_KEY);
}

export function subscribeToAuthSession(
  listener: (session: AuthSession) => void
): () => void {
  if (typeof window === "undefined") {
    return () => undefined;
  }

  const handler = (event: Event) => {
    listener((event as CustomEvent<AuthSession>).detail);
  };

  window.addEventListener(AUTH_SESSION_EVENT, handler as EventListener);

  return () => {
    window.removeEventListener(AUTH_SESSION_EVENT, handler as EventListener);
  };
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

export async function refreshRequest(): Promise<AuthSession> {
  const res = await fetch(`${API_BASE}/auth/refresh`, {
    method: "POST",
    credentials: "include",
  });

  if (res.status === 401 || res.status === 403) {
    throw new UnauthorizedError(undefined, res.status);
  }

  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(body?.detail ?? "Refresh failed");
  }

  const data = await res.json();
  const session = {
    token: data.token,
    user: parseUserInfo(data.user),
  };

  storeAuthSession(session);

  return session;
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
