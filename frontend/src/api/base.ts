function normalizeLoopbackHostname(hostname: string): string {
  if (hostname === "localhost" || hostname === "127.0.0.1") {
    return hostname;
  }

  return hostname;
}

export function getApiBase(): string {
  const raw = import.meta.env.VITE_API_URL || "";

  if (!raw || typeof window === "undefined") {
    return raw;
  }

  try {
    const apiUrl = new URL(raw);
    const currentUrl = new URL(window.location.href);
    const apiHostname = normalizeLoopbackHostname(apiUrl.hostname);
    const currentHostname = normalizeLoopbackHostname(currentUrl.hostname);

    const isLoopbackPair =
      (apiHostname === "127.0.0.1" && currentHostname === "localhost") ||
      (apiHostname === "localhost" && currentHostname === "127.0.0.1");

    if (!isLoopbackPair) {
      return raw;
    }

    apiUrl.hostname = currentHostname;
    return apiUrl.toString().replace(/\/$/, "");
  } catch {
    return raw;
  }
}
