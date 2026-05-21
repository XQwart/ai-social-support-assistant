import { AUTH_TOKEN_KEY, refreshRequest } from "@/api/authApi";

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

export async function authFetch(
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
