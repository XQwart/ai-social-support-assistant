import { UnauthorizedError } from "@/api/errors";

const API_BASE = import.meta.env.VITE_API_URL || "";
const AUTH_TOKEN_KEY = "ai-social-support.auth.token";

export interface AuthResponse {
  message: string;
  token: string;
}

export async function loginRequest(): Promise<AuthResponse> {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
  });

  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(body?.detail ?? "Ошибка авторизации");
  }

  return res.json();
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
