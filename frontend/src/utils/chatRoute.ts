const CHAT_PATH_PREFIX = "/c/";
const CHAT_ID_PATTERN = /^\d+$/;

export function parseChatIdFromLocation(): string | null {
  if (typeof window === "undefined") {
    return null;
  }

  const path = window.location.pathname;

  if (!path.startsWith(CHAT_PATH_PREFIX)) {
    return null;
  }

  const rest = path.slice(CHAT_PATH_PREFIX.length);
  const [rawId] = rest.split("/", 1);

  if (!rawId) {
    return null;
  }

  let decoded: string;
  try {
    decoded = decodeURIComponent(rawId);
  } catch {
    return null;
  }

  return CHAT_ID_PATTERN.test(decoded) ? decoded : null;
}

export function buildChatRoute(chatId: string | null): string {
  if (!chatId || !CHAT_ID_PATTERN.test(chatId)) {
    return "/";
  }

  return `${CHAT_PATH_PREFIX}${encodeURIComponent(chatId)}`;
}

function buildUrl(chatId: string | null): string {
  if (typeof window === "undefined") {
    return buildChatRoute(chatId);
  }

  const target = buildChatRoute(chatId);
  return `${target}${window.location.search}${window.location.hash}`;
}

function isSameRoute(chatId: string | null): boolean {
  if (typeof window === "undefined") {
    return false;
  }

  return window.location.pathname === buildChatRoute(chatId);
}

export function pushChatRoute(chatId: string | null): void {
  if (typeof window === "undefined" || isSameRoute(chatId)) {
    return;
  }

  window.history.pushState(window.history.state, "", buildUrl(chatId));
}

export function replaceChatRoute(chatId: string | null): void {
  if (typeof window === "undefined" || isSameRoute(chatId)) {
    return;
  }

  window.history.replaceState(window.history.state, "", buildUrl(chatId));
}
