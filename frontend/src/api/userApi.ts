import { getApiBase } from "@/api/base";
import { ApiError } from "@/api/errors";
import { authFetch } from "@/api/http";

const API_BASE = getApiBase();

export interface UserMemory {
  regionCurrent: string | null;
  persistentMemory: string | null;
}

async function getErrorMessage(
  res: Response,
  fallback: string
): Promise<string> {
  const body = await res.json().catch(() => null);
  return body?.detail ?? fallback;
}

export async function fetchUserMemory(signal?: AbortSignal): Promise<UserMemory> {
  const res = await authFetch(`${API_BASE}/user/memory`, { signal });

  if (!res.ok) {
    throw new ApiError(res.status, await getErrorMessage(res, "Не удалось загрузить память"));
  }

  const data = await res.json();

  return {
    regionCurrent: data.region_current ?? null,
    persistentMemory: data.persistent_memory ?? null,
  };
}

export async function resetUserMemory(signal?: AbortSignal): Promise<void> {
  const res = await authFetch(`${API_BASE}/user/memory`, {
    method: "DELETE",
    signal,
  });

  if (!res.ok) {
    throw new ApiError(res.status, await getErrorMessage(res, "Не удалось очистить память"));
  }
}
