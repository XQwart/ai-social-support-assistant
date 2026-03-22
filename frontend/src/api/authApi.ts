const API_BASE = import.meta.env.VITE_API_URL || "";

export interface AuthResponse {
  message: string;
  token: string;
}

/**
 * Авторизация через заглушку POST /auth/login
 * Бэкенд создаёт захардкоженного пользователя и возвращает JWT
 */
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
