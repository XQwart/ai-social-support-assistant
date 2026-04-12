import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  createChat,
  deleteChat as deleteChatApi,
  fetchChats,
  fetchMessages,
  sendMessageToChat,
} from "@/api/chatApi";
import {
  clearStoredAuthSession,
  exchangeSberCodeRequest,
  logoutRequest,
  refreshRequest,
  storeAuthSession,
  subscribeToAuthSession,
  type ExchangeSberCodeResponse,
  type UserInfo,
} from "@/api/authApi";
import { ApiError, UnauthorizedError } from "@/api/errors";
import { preloadSberAuthParams } from "@/components/AuthModal";
import AppDisclaimer from "@/components/AppDisclaimer";
import AuthModal from "@/components/AuthModal";
import ChatInput from "@/components/ChatInput";
import ChatView from "@/components/ChatView";
import HomePage from "@/components/HomePage";
import SettingsModal from "@/components/SettingsModal";
import Sidebar from "@/components/Sidebar";
import TopBar from "@/components/TopBar";
import type { Chat, Message } from "@/types";

const AUTH_TOKEN_KEY = "ai-social-support.auth.token";
const AUTH_USER_KEY = "ai-social-support.auth.user";
const THEME_KEY = "ai-social-support.theme";
const CHAT_PAGE_LIMIT = 100;
const MESSAGE_PAGE_LIMIT = 100;
const RECENT_MESSAGE_WINDOW_MS = 15000;
const CHAT_LIST_CONTROLLER_KEY = "chats:list";
const NEW_CHAT_CONTROLLER_KEY = "send:new";

type PendingSberCallback = {
  code: string | null;
  error: string;
};

let pendingSberCallback: PendingSberCallback | null = null;
let pendingSberExchange:
  | {
      code: string;
      promise: Promise<ExchangeSberCodeResponse>;
    }
  | null = null;

const EMPTY_USER_INFO: UserInfo = { firstName: "", secondName: "", placeOfWork: "" };
type ThemeMode = "light" | "dark";

function readStoredTheme(): ThemeMode | null {
  if (typeof window === "undefined") {
    return null;
  }

  const stored = window.localStorage.getItem(THEME_KEY);
  return stored === "light" || stored === "dark" ? stored : null;
}

function readSystemTheme(): ThemeMode {
  if (
    typeof window !== "undefined" &&
    window.matchMedia &&
    window.matchMedia("(prefers-color-scheme: dark)").matches
  ) {
    return "dark";
  }

  return "light";
}

function readTheme(): ThemeMode {
  if (typeof window === "undefined") {
    return "light";
  }

  return readStoredTheme() ?? readSystemTheme();
}

function getHistoryControllerKey(chatId: string): string {
  return `history:${chatId}`;
}

function getSendControllerKey(chatId: string): string {
  return `send:${chatId}`;
}

function getDeleteControllerKey(chatId: string): string {
  return `delete:${chatId}`;
}

function readAuthState(): { token: string | null; userInfo: UserInfo } {
  if (typeof window === "undefined") {
    return { token: null, userInfo: EMPTY_USER_INFO };
  }

  const token = window.localStorage.getItem(AUTH_TOKEN_KEY);
  const raw = window.localStorage.getItem(AUTH_USER_KEY);

  let userInfo: UserInfo = EMPTY_USER_INFO;

  if (raw) {
    try {
      userInfo = JSON.parse(raw) as UserInfo;
    } catch {}
  }

  return { token: token ?? null, userInfo };
}

function clearSberCallbackParams() {
  if (typeof window === "undefined") return;

  const url = new URL(window.location.href);
  ["code", "state", "error", "error_description", "description"].forEach(
    (key) => url.searchParams.delete(key)
  );

  const nextUrl = `${url.pathname}${url.search}${url.hash}`;
  window.history.replaceState(window.history.state, "", nextUrl);
}

function resolveSberCallbackError(searchParams: URLSearchParams): string {
  const errorCode = searchParams.get("error");
  if (!errorCode) return "";

  const description =
    searchParams.get("description") ?? searchParams.get("error_description");

  if (description) {
    return description;
  }

  switch (errorCode) {
    case "access_denied":
      return "Вход через Sber ID был отменен.";
    case "invalid_state":
      return "Сессия входа устарела. Попробуйте еще раз.";
    case "invalid_request":
      return "Сбер ID не вернул код авторизации.";
    default:
      return "Не удалось завершить вход через Sber ID. Попробуйте еще раз.";
  }
}

function readPendingSberCallback(): PendingSberCallback | null {
  if (typeof window === "undefined") {
    return pendingSberCallback;
  }

  const url = new URL(window.location.href);
  const code = url.searchParams.get("code");
  const error = resolveSberCallbackError(url.searchParams);

  if (!code && !error) {
    return pendingSberCallback;
  }

  pendingSberCallback = { code, error };
  clearSberCallbackParams();

  return pendingSberCallback;
}

function getOrCreateSberExchange(code: string): Promise<ExchangeSberCodeResponse> {
  if (pendingSberExchange?.code === code) {
    return pendingSberExchange.promise;
  }

  const promise = exchangeSberCodeRequest(code);
  pendingSberExchange = { code, promise };

  return promise;
}

function mergeUniqueMessages(current: Message[], incoming: Message[]): Message[] {
  const map = new Map<string, Message>();

  [...current, ...incoming].forEach((message) => {
    map.set(message.id, message);
  });

  return Array.from(map.values()).sort((a, b) => a.timestamp - b.timestamp);
}

function sortChats(chats: Chat[]): Chat[] {
  return [...chats].sort((a, b) => b.updatedAt - a.updatedAt);
}

function mergeIncomingChats(current: Chat[], incoming: Chat[]): Chat[] {
  const map = new Map<string, Chat>();

  current.forEach((chat) => {
    map.set(chat.id, chat);
  });

  incoming.forEach((chat) => {
    const existing = map.get(chat.id);

    if (!existing) {
      map.set(chat.id, chat);
      return;
    }

    map.set(chat.id, {
      ...chat,
      messages: existing.messages,
      historyStatus: existing.historyStatus,
      historyError: existing.historyError,
      messagesOffset: existing.messagesOffset,
      hasOlderMessages: existing.hasOlderMessages,
      isHistoryHydrated: existing.isHistoryHydrated,
      pendingMessageText: existing.pendingMessageText,
      sendError: existing.sendError,
    });
  });

  return sortChats(Array.from(map.values()));
}

function wasMessagePersisted(messages: Message[], text: string, sentAt: number): boolean {
  return messages.some(
    (message) =>
      message.role === "user" &&
      message.content === text &&
      message.timestamp >= sentAt - RECENT_MESSAGE_WINDOW_MS
  );
}

export default function App() {
  const initialAuthStateRef = useRef(readAuthState());
  const initialThemeRef = useRef(readTheme());
  const controllersRef = useRef<Map<string, AbortController>>(new Map());
  const requestEpochRef = useRef(0);
  const chatListOffsetRef = useRef(0);

  const [chats, setChats] = useState<Chat[]>([]);
  const [activeChatId, setActiveChatId] = useState<string | null>(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [loadingChatIds, setLoadingChatIds] = useState<string[]>([]);
  const [animatedMessageId, setAnimatedMessageId] = useState<string | null>(null);
  const [pendingDeleteChatId, setPendingDeleteChatId] = useState<string | null>(null);
  const [authToken, setAuthToken] = useState<string | null>(
    () => initialAuthStateRef.current.token
  );
  const [userInfo, setUserInfo] = useState<UserInfo>(
    () => initialAuthStateRef.current.userInfo
  );
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [isSettingsModalOpen, setIsSettingsModalOpen] = useState(false);
  const [sberAuthError, setSberAuthError] = useState("");
  const [isFinalizingSberAuth, setIsFinalizingSberAuth] = useState(false);
  const [isBootstrappingSession, setIsBootstrappingSession] = useState(
    !initialAuthStateRef.current.token
  );
  const [chatListStatus, setChatListStatus] = useState<
    "idle" | "loading" | "ready" | "error"
  >("idle");
  const [chatListError, setChatListError] = useState<string | null>(null);
  const [hasMoreChats, setHasMoreChats] = useState(false);
  const [isLoadingMoreChats, setIsLoadingMoreChats] = useState(false);
  const [isCreatingChat, setIsCreatingChat] = useState(false);
  const [theme, setTheme] = useState<ThemeMode>(() => initialThemeRef.current);

  const isAuthenticated = !!authToken;
  const isDarkTheme = theme === "dark";
  const userFullName =
    [userInfo.firstName, userInfo.secondName].filter(Boolean).join(" ") ||
    "Пользователь";
  const userInitial = userFullName.trim().charAt(0).toUpperCase() || "П";

  const activeChat = useMemo(
    () => chats.find((chat) => chat.id === activeChatId) ?? null,
    [chats, activeChatId]
  );
  const pendingDeleteChat = useMemo(
    () => chats.find((chat) => chat.id === pendingDeleteChatId) ?? null,
    [chats, pendingDeleteChatId]
  );

  const showHome = !activeChat;

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    document.documentElement.style.colorScheme = theme;
    window.localStorage.setItem(THEME_KEY, theme);
  }, [theme]);

  useEffect(() => {
    if (typeof window === "undefined") return;

    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
    const handleChange = () => {
      if (!readStoredTheme()) {
        setTheme(mediaQuery.matches ? "dark" : "light");
      }
    };

    handleChange();
    mediaQuery.addEventListener("change", handleChange);
    return () => mediaQuery.removeEventListener("change", handleChange);
  }, []);

  const isCurrentChatLoading = useMemo(() => {
    if (!activeChatId) {
      return false;
    }

    return loadingChatIds.includes(activeChatId);
  }, [activeChatId, loadingChatIds]);

  const updateChatListOffset = useCallback((nextOffset: number) => {
    chatListOffsetRef.current = nextOffset;
  }, []);

  const isRequestCurrent = useCallback((requestEpoch: number) => {
    return requestEpochRef.current === requestEpoch;
  }, []);

  const registerController = useCallback(
    (key: string, controller: AbortController) => {
      controllersRef.current.get(key)?.abort();
      controllersRef.current.set(key, controller);
    },
    []
  );

  const releaseController = useCallback(
    (key: string, controller?: AbortController) => {
      const current = controllersRef.current.get(key);

      if (!current) {
        return;
      }

      if (!controller || current === controller) {
        controllersRef.current.delete(key);
      }
    },
    []
  );

  const abortAllControllers = useCallback(() => {
    controllersRef.current.forEach((controller) => controller.abort());
    controllersRef.current.clear();
  }, []);

  const resetSessionState = useCallback(
    (openAuthModal: boolean) => {
      requestEpochRef.current += 1;
      abortAllControllers();
      clearStoredAuthSession();
      updateChatListOffset(0);
      setAuthToken(null);
      setUserInfo(EMPTY_USER_INFO);
      setChats([]);
      setActiveChatId(null);
      setLoadingChatIds([]);
      setAnimatedMessageId(null);
      setIsSidebarOpen(false);
      setIsSettingsModalOpen(false);
      setSberAuthError("");
      setIsFinalizingSberAuth(false);
      setIsBootstrappingSession(false);
      setChatListStatus("idle");
      setChatListError(null);
      setHasMoreChats(false);
      setIsLoadingMoreChats(false);
      setIsCreatingChat(false);
      setIsAuthModalOpen(openAuthModal);
    },
    [abortAllControllers, updateChatListOffset]
  );

  const handleSessionExpired = useCallback(() => {
    resetSessionState(true);
  }, [resetSessionState]);

  const removeChatFromState = useCallback(
    (chatId: string) => {
      const historyKey = getHistoryControllerKey(chatId);
      const sendKey = getSendControllerKey(chatId);
      const deleteKey = getDeleteControllerKey(chatId);

      controllersRef.current.get(historyKey)?.abort();
      controllersRef.current.get(sendKey)?.abort();
      controllersRef.current.get(deleteKey)?.abort();
      releaseController(historyKey);
      releaseController(sendKey);
      releaseController(deleteKey);

      setChats((prev) => prev.filter((chat) => chat.id !== chatId));
      setLoadingChatIds((prev) => prev.filter((id) => id !== chatId));
      setActiveChatId((prev) => (prev === chatId ? null : prev));
      setAnimatedMessageId(null);
      updateChatListOffset(Math.max(chatListOffsetRef.current - 1, 0));
    },
    [releaseController, updateChatListOffset]
  );

  const hydrateChatHistory = useCallback(
    async (
      chatId: string,
      options?: { retryText?: string; sentAt?: number }
    ) => {
      if (!isAuthenticated) {
        return;
      }

      const requestEpoch = requestEpochRef.current;
      const controller = new AbortController();
      const controllerKey = getHistoryControllerKey(chatId);

      registerController(controllerKey, controller);
      setChats((prev) =>
        prev.map((chat) =>
          chat.id === chatId
            ? {
                ...chat,
                historyStatus: "loading",
                historyError: null,
                hasOlderMessages: true,
                isHistoryHydrated: false,
              }
            : chat
        )
      );

      let offset = 0;
      let messages: Message[] = [];

      try {
        while (true) {
          const page = await fetchMessages(
            chatId,
            MESSAGE_PAGE_LIMIT,
            offset,
            controller.signal
          );

          if (controller.signal.aborted || !isRequestCurrent(requestEpoch)) {
            return;
          }

          messages = mergeUniqueMessages(messages, page.messages);
          offset += page.messages.length;

          setChats((prev) =>
            prev.map((chat) =>
              chat.id === chatId
                ? {
                    ...chat,
                    historyStatus: page.hasMore ? "loading" : "ready",
                    historyError: null,
                    messagesOffset: offset,
                    hasOlderMessages: page.hasMore,
                    isHistoryHydrated: !page.hasMore,
                  }
                : chat
            )
          );

          if (!page.hasMore) {
            break;
          }
        }

        const shouldExposeRetry = options?.retryText
          ? !wasMessagePersisted(messages, options.retryText, options.sentAt ?? Date.now())
          : false;
        const lastMessage = messages[messages.length - 1];

        setChats((prev) =>
          sortChats(
            prev.map((chat) =>
              chat.id === chatId
                ? {
                    ...chat,
                    messages,
                    updatedAt: lastMessage?.timestamp ?? chat.updatedAt,
                    historyStatus: "ready",
                    historyError: null,
                    messagesOffset: messages.length,
                    hasOlderMessages: false,
                    isHistoryHydrated: true,
                    pendingMessageText: shouldExposeRetry
                      ? options?.retryText ?? null
                      : null,
                    sendError: shouldExposeRetry
                      ? "Не удалось отправить сообщение. Повторите попытку."
                      : null,
                  }
                : chat
            )
          )
        );
      } catch (error) {
        if (controller.signal.aborted || !isRequestCurrent(requestEpoch)) {
          return;
        }

        if (error instanceof UnauthorizedError) {
          handleSessionExpired();
          return;
        }

        if (
          error instanceof ApiError &&
          (error.status === 403 || error.status === 404)
        ) {
          removeChatFromState(chatId);
          return;
        }

        setChats((prev) =>
          prev.map((chat) =>
            chat.id === chatId
              ? {
                  ...chat,
                  historyStatus: "error",
                  historyError:
                    error instanceof Error
                      ? error.message
                      : "Не удалось загрузить историю",
                  hasOlderMessages: offset > 0,
                  isHistoryHydrated: false,
                  pendingMessageText:
                    options?.retryText ?? chat.pendingMessageText,
                  sendError: options?.retryText
                    ? "Не удалось отправить сообщение. Повторите попытку."
                    : chat.sendError,
                }
              : chat
          )
        );
      } finally {
        releaseController(controllerKey, controller);
      }
    },
    [
      handleSessionExpired,
      isAuthenticated,
      isRequestCurrent,
      registerController,
      releaseController,
      removeChatFromState,
    ]
  );

  const loadChatsPage = useCallback(
    async (mode: "reset" | "more") => {
      if (!isAuthenticated) {
        return;
      }

      const requestEpoch = requestEpochRef.current;
      const controller = new AbortController();
      const isReset = mode === "reset";
      const offset = isReset ? 0 : chatListOffsetRef.current;

      registerController(CHAT_LIST_CONTROLLER_KEY, controller);

      if (isReset) {
        updateChatListOffset(0);
        setChatListStatus("loading");
        setChatListError(null);
        setHasMoreChats(false);
      } else {
        setIsLoadingMoreChats(true);
        setChatListError(null);
      }

      try {
        const page = await fetchChats(CHAT_PAGE_LIMIT, offset, controller.signal);

        if (controller.signal.aborted || !isRequestCurrent(requestEpoch)) {
          return;
        }

        setChats((prev) => mergeIncomingChats(prev, page.items));
        updateChatListOffset(
          Math.max(chatListOffsetRef.current, offset + page.items.length)
        );
        setChatListStatus("ready");
        setChatListError(null);
        setHasMoreChats(page.hasMore);
      } catch (error) {
        if (controller.signal.aborted || !isRequestCurrent(requestEpoch)) {
          return;
        }

        if (error instanceof UnauthorizedError) {
          handleSessionExpired();
          return;
        }

        if (error instanceof ApiError && error.status === 403) {
          handleSessionExpired();
          return;
        }

        setChatListError(
          error instanceof Error
            ? error.message
            : "Не удалось загрузить список чатов"
        );

        if (isReset) {
          setChatListStatus("error");
        }
      } finally {
        releaseController(CHAT_LIST_CONTROLLER_KEY, controller);

        if (!isReset && isRequestCurrent(requestEpoch)) {
          setIsLoadingMoreChats(false);
        }
      }
    },
    [
      handleSessionExpired,
      isAuthenticated,
      isRequestCurrent,
      registerController,
      releaseController,
      updateChatListOffset,
    ]
  );

  const handleLogout = useCallback(async () => {
    try {
      await logoutRequest();
    } catch (error) {
      if (!(error instanceof UnauthorizedError)) {
        console.error("Logout request failed", error);
      }
    }

    resetSessionState(false);
  }, [resetSessionState]);

  useEffect(() => {
    return subscribeToAuthSession((session) => {
      setAuthToken(session.token);
      setUserInfo(session.user);
      setSberAuthError("");
      setIsAuthModalOpen(false);
    });
  }, []);

  useEffect(() => {
    const requestEpoch = requestEpochRef.current;
    const persistedAuthState = readAuthState();
    if (!persistedAuthState.token) {
      setIsBootstrappingSession(false);
      return;
    }

    let cancelled = false;

    refreshRequest()
      .catch((error: unknown) => {
        if (cancelled || !isRequestCurrent(requestEpoch)) {
          return;
        }

        if (error instanceof UnauthorizedError) {
          clearStoredAuthSession();
          setAuthToken(null);
          setUserInfo(EMPTY_USER_INFO);
        }
      })
      .finally(() => {
        if (cancelled || !isRequestCurrent(requestEpoch)) {
          return;
        }

        setIsBootstrappingSession(false);
      });

    return () => {
      cancelled = true;
    };
  }, [isRequestCurrent]);

  useEffect(() => {
    if (!isAuthenticated) {
      setChats([]);
      setActiveChatId(null);
      setLoadingChatIds([]);
      setAnimatedMessageId(null);
      updateChatListOffset(0);
      setChatListStatus("idle");
      setChatListError(null);
      setHasMoreChats(false);
      setIsLoadingMoreChats(false);
      setIsCreatingChat(false);
      return;
    }

    setChats([]);
    setActiveChatId(null);
    setLoadingChatIds([]);
    setAnimatedMessageId(null);
    updateChatListOffset(0);
    void loadChatsPage("reset");
  }, [isAuthenticated, loadChatsPage, updateChatListOffset]);

  useEffect(() => {
    if (!activeChatId || !activeChat || !isAuthenticated) {
      return;
    }

    if (
      activeChat.isHistoryHydrated ||
      activeChat.historyStatus === "loading" ||
      activeChat.historyStatus === "error" ||
      loadingChatIds.includes(activeChatId)
    ) {
      return;
    }

    void hydrateChatHistory(activeChatId);
  }, [
    activeChat,
    activeChatId,
    hydrateChatHistory,
    isAuthenticated,
    loadingChatIds,
  ]);

  useEffect(() => {
    return () => {
      abortAllControllers();
    };
  }, [abortAllControllers]);

  useEffect(() => {
    preloadSberAuthParams();
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }

    const callbackData = readPendingSberCallback();

    if (!callbackData) {
      return;
    }

    if (callbackData.error) {
      pendingSberCallback = null;
      setSberAuthError(callbackData.error);
      setIsFinalizingSberAuth(false);
      setIsAuthModalOpen(true);
      return;
    }

    if (!callbackData.code) {
      pendingSberCallback = null;
      return;
    }

    const requestEpoch = requestEpochRef.current;
    let cancelled = false;

    setSberAuthError("");
    setIsFinalizingSberAuth(true);
    setIsAuthModalOpen(true);

    getOrCreateSberExchange(callbackData.code)
      .then(({ token, user }) => {
        if (cancelled || !isRequestCurrent(requestEpoch)) {
          return;
        }

        storeAuthSession({ token, user });
        pendingSberCallback = null;
      })
      .catch((error: unknown) => {
        if (cancelled || !isRequestCurrent(requestEpoch)) {
          return;
        }

        clearStoredAuthSession();
        setAuthToken(null);
        setUserInfo(EMPTY_USER_INFO);
        setSberAuthError(
          error instanceof Error
            ? error.message
            : "Не удалось завершить вход через Sber ID"
        );
        setIsAuthModalOpen(true);
        pendingSberCallback = null;
      })
      .finally(() => {
        if (cancelled || !isRequestCurrent(requestEpoch)) {
          return;
        }

        setIsFinalizingSberAuth(false);

        if (pendingSberExchange?.code === callbackData.code) {
          pendingSberExchange = null;
        }
      });

    return () => {
      cancelled = true;
    };
  }, [isRequestCurrent]);

  const handleOpenAuth = useCallback(() => {
    setSberAuthError("");
    setIsFinalizingSberAuth(false);
    setIsAuthModalOpen(true);
  }, []);

  const handleCloseAuth = useCallback(() => {
    setSberAuthError("");
    setIsFinalizingSberAuth(false);
    setIsAuthModalOpen(false);
  }, []);

  const handleMockLogin = useCallback((token: string, user: UserInfo) => {
    storeAuthSession({ token, user });
    setSberAuthError("");
    setIsAuthModalOpen(false);
  }, []);

  const handleSend = useCallback(
    async (rawText: string): Promise<boolean> => {
      const text = rawText.trim();

      if (!text) {
        return false;
      }

      if (!authToken) {
        handleOpenAuth();
        return false;
      }

      let targetChatId = activeChatId;
      let controllerKey = targetChatId
        ? getSendControllerKey(targetChatId)
        : NEW_CHAT_CONTROLLER_KEY;
      const requestEpoch = requestEpochRef.current;

      if (controllersRef.current.has(controllerKey)) {
        return false;
      }

      const controller = new AbortController();
      const requestStartedAt = Date.now();
      const optimisticUserMsg: Message = {
        id: `optimistic-${requestStartedAt}`,
        role: "user",
        content: text,
        timestamp: requestStartedAt,
      };

      let shouldReloadHistoryAfterSend = false;

      registerController(controllerKey, controller);
      setAnimatedMessageId(null);

      try {
        if (!targetChatId) {
          setIsCreatingChat(true);

          const newChat = await createChat(text, controller.signal);

          if (controller.signal.aborted || !isRequestCurrent(requestEpoch)) {
            return false;
          }

          targetChatId = newChat.id;
          releaseController(NEW_CHAT_CONTROLLER_KEY, controller);
          controllerKey = getSendControllerKey(targetChatId);
          controllersRef.current.set(controllerKey, controller);

          const nextChat: Chat = {
            ...newChat,
            messages: [optimisticUserMsg],
            messagesOffset: 1,
            pendingMessageText: null,
            sendError: null,
          };

          setChats((prev) => sortChats([nextChat, ...prev]));
          updateChatListOffset(chatListOffsetRef.current + 1);
          setChatListStatus("ready");
          setChatListError(null);
          setLoadingChatIds((prev) =>
            prev.includes(targetChatId!) ? prev : [...prev, targetChatId!]
          );
          setActiveChatId(targetChatId);
        } else {
          const currentChat = chats.find((chat) => chat.id === targetChatId) ?? null;
          const historyKey = getHistoryControllerKey(targetChatId);

          shouldReloadHistoryAfterSend = !!currentChat && !currentChat.isHistoryHydrated;
          controllersRef.current.get(historyKey)?.abort();
          releaseController(historyKey);

          setLoadingChatIds((prev) =>
            prev.includes(targetChatId!) ? prev : [...prev, targetChatId!]
          );
          setChats((prev) =>
            prev.map((chat) =>
              chat.id === targetChatId
                ? {
                    ...chat,
                    historyStatus: shouldReloadHistoryAfterSend
                      ? "idle"
                      : chat.historyStatus,
                    historyError: shouldReloadHistoryAfterSend
                      ? null
                      : chat.historyError,
                    pendingMessageText: null,
                    sendError: null,
                    messages: [...chat.messages, optimisticUserMsg],
                  }
                : chat
            )
          );
        }

        const { userMsg, assistantMsg, contextCompressed } = await sendMessageToChat(
          targetChatId,
          text,
          controller.signal
        );

        if (controller.signal.aborted || !isRequestCurrent(requestEpoch)) {
          return false;
        }

        const newMessages: Message[] = [userMsg];

        if (contextCompressed) {
          newMessages.push({
            id: `system-compress-${Date.now()}`,
            role: "system",
            content:
              "Контекст предыдущих сообщений был сжат для оптимизации. Я помню основные темы нашего разговора.",
            timestamp: assistantMsg.timestamp - 1,
          });
        }

        newMessages.push(assistantMsg);

        setChats((prev) =>
          sortChats(
            prev.map((chat) => {
              if (chat.id !== targetChatId) {
                return chat;
              }

              const withoutOptimistic = chat.messages.filter(
                (message) => message.id !== optimisticUserMsg.id
              );
              const mergedMessages = mergeUniqueMessages(withoutOptimistic, newMessages);

              return {
                ...chat,
                updatedAt: assistantMsg.timestamp,
                messages: mergedMessages,
                messagesOffset: Math.max(chat.messagesOffset, mergedMessages.length),
                historyStatus: shouldReloadHistoryAfterSend
                  ? "idle"
                  : chat.historyStatus,
                historyError: shouldReloadHistoryAfterSend
                  ? null
                  : chat.historyError,
                hasOlderMessages: shouldReloadHistoryAfterSend
                  ? true
                  : chat.hasOlderMessages,
                isHistoryHydrated: shouldReloadHistoryAfterSend
                  ? false
                  : chat.isHistoryHydrated,
                pendingMessageText: null,
                sendError: null,
              };
            })
          )
        );
        setAnimatedMessageId(assistantMsg.id);

        return true;
      } catch (error) {
        if (error instanceof UnauthorizedError) {
          if (!isRequestCurrent(requestEpoch)) {
            return false;
          }

          handleSessionExpired();
          return false;
        }

        if (
          targetChatId &&
          error instanceof ApiError &&
          (error.status === 403 || error.status === 404)
        ) {
          removeChatFromState(targetChatId);
          return false;
        }

        if (error instanceof DOMException && error.name === "AbortError") {
          return false;
        }

        if (targetChatId && isRequestCurrent(requestEpoch)) {
          setChats((prev) =>
            prev.map((chat) =>
              chat.id === targetChatId
                ? {
                    ...chat,
                    messages: chat.messages.filter(
                      (message) => message.id !== optimisticUserMsg.id
                    ),
                  }
                : chat
            )
          );
          await hydrateChatHistory(targetChatId, {
            retryText: text,
            sentAt: requestStartedAt,
          });
        }

        return false;
      } finally {
        if (targetChatId) {
          releaseController(getSendControllerKey(targetChatId), controller);
          if (isRequestCurrent(requestEpoch)) {
            setLoadingChatIds((prev) => prev.filter((id) => id !== targetChatId));
          }
        } else {
          releaseController(NEW_CHAT_CONTROLLER_KEY, controller);
        }

        if (isRequestCurrent(requestEpoch)) {
          setIsCreatingChat(false);
        }
      }
    },
    [
      activeChatId,
      authToken,
      chats,
      handleOpenAuth,
      handleSessionExpired,
      hydrateChatHistory,
      registerController,
      releaseController,
      removeChatFromState,
      updateChatListOffset,
    ]
  );

  const handleSelectChat = useCallback((chatId: string) => {
    setActiveChatId(chatId);
    setAnimatedMessageId(null);
  }, []);

  const handleNewChat = useCallback(() => {
    setActiveChatId(null);
    setAnimatedMessageId(null);
  }, []);

  const handleDeleteChat = useCallback((chatId: string) => {
    setPendingDeleteChatId(chatId);
  }, []);

  const performDeleteChat = useCallback(
    async (chatId: string) => {
      const snapshot = chats.find((chat) => chat.id === chatId);

      if (!snapshot) {
        return;
      }

      const wasActive = activeChatId === chatId;
      const requestEpoch = requestEpochRef.current;
      const historyKey = getHistoryControllerKey(chatId);
      const sendKey = getSendControllerKey(chatId);
      const deleteKey = getDeleteControllerKey(chatId);
      const controller = new AbortController();

      controllersRef.current.get(historyKey)?.abort();
      controllersRef.current.get(sendKey)?.abort();
      releaseController(historyKey);
      releaseController(sendKey);
      registerController(deleteKey, controller);

      setChats((prev) => prev.filter((chat) => chat.id !== chatId));
      setLoadingChatIds((prev) => prev.filter((id) => id !== chatId));
      setActiveChatId((prev) => (prev === chatId ? null : prev));
      setAnimatedMessageId(null);
      updateChatListOffset(Math.max(chatListOffsetRef.current - 1, 0));

      try {
        await deleteChatApi(chatId, controller.signal);
      } catch (error) {
        if (controller.signal.aborted || !isRequestCurrent(requestEpoch)) {
          return;
        }

        if (error instanceof UnauthorizedError) {
          handleSessionExpired();
          return;
        }

        if (
          error instanceof ApiError &&
          (error.status === 403 || error.status === 404)
        ) {
          return;
        }

        setChats((prev) => sortChats([...prev, snapshot]));
        updateChatListOffset(chatListOffsetRef.current + 1);
        setChatListError(
          error instanceof Error ? error.message : "Не удалось удалить чат"
        );

        if (wasActive) {
          setActiveChatId(chatId);
        }
      } finally {
        releaseController(deleteKey, controller);
      }
    },
    [
      activeChatId,
      chats,
      handleSessionExpired,
      releaseController,
      updateChatListOffset,
    ]
  );

  const handleLoadMoreChats = useCallback(() => {
    if (!hasMoreChats || isLoadingMoreChats) {
      return;
    }

    void loadChatsPage("more");
  }, [hasMoreChats, isLoadingMoreChats, loadChatsPage]);

  const handleRetryChats = useCallback(() => {
    void loadChatsPage(chats.length > 0 ? "more" : "reset");
  }, [chats.length, loadChatsPage]);

  const handleRetryHistory = useCallback(() => {
    if (!activeChatId) {
      return;
    }

    void hydrateChatHistory(activeChatId);
  }, [activeChatId, hydrateChatHistory]);

  const handleRetryPendingMessage = useCallback(() => {
    const text = activeChat?.pendingMessageText?.trim();

    if (!text) {
      return;
    }

    void handleSend(text);
  }, [activeChat?.pendingMessageText, handleSend]);

  const handleToggleSidebar = useCallback(
    () => setIsSidebarOpen((prev) => !prev),
    []
  );
  const handleCloseSidebar = useCallback(() => setIsSidebarOpen(false), []);

  if (isBootstrappingSession) {
    return (
      <div
        className="relative flex h-[100dvh] min-h-screen flex-col overflow-hidden bg-[var(--app-bg)] text-[var(--text-main)]"
        data-theme={theme}
      >
        <div className="app-background" aria-hidden="true">
          <div className="app-bg-spot app-bg-spot-one" />
          <div className="app-bg-spot app-bg-spot-two" />
          <div className="app-bg-spot app-bg-spot-three" />
        </div>

        <div className="relative z-10 flex flex-1 items-center justify-center px-6">
          <div
            className="w-full max-w-md rounded-[32px] px-8 py-10 text-center backdrop-blur-3xl"
            style={{
              border: isDarkTheme ? "1px solid rgba(255,255,255,0.08)" : "1px solid rgba(255,255,255,0.7)",
              background: isDarkTheme
                ? "rgba(10,24,20,0.84)"
                : "rgba(255,255,255,0.78)",
              boxShadow: isDarkTheme
                ? "0 28px 80px rgba(0,0,0,0.34)"
                : "0 28px 80px rgba(15,23,42,0.12)",
            }}
          >
            <div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-[linear-gradient(135deg,#12b981,#0ea5a4)] text-white shadow-[0_18px_40px_rgba(16,185,129,0.26)]">
              <span className="inline-flex items-center gap-1.5">
                <span className="loading-dot" />
                <span className="loading-dot" style={{ animationDelay: "140ms" }} />
                <span className="loading-dot" style={{ animationDelay: "280ms" }} />
              </span>
            </div>

            <h1 className="text-2xl font-black tracking-[-0.03em] text-[var(--text-main)]">
              Восстанавливаем сессию
            </h1>
            <p className="mt-3 text-sm leading-6 text-slate-500">
              Проверяем сохраненный вход и подготавливаем ваши чаты.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      className="relative flex h-[100dvh] min-h-screen flex-col overflow-hidden bg-[var(--app-bg)] text-[var(--text-main)]"
      data-theme={theme}
    >
      <div className="app-background" aria-hidden="true">
        <div className="app-bg-spot app-bg-spot-one" />
        <div className="app-bg-spot app-bg-spot-two" />
        <div className="app-bg-spot app-bg-spot-three" />
      </div>

      <Sidebar
        isOpen={isSidebarOpen}
        onClose={handleCloseSidebar}
        chats={chats}
        activeChatId={activeChatId}
        onSelectChat={handleSelectChat}
        onNewChat={handleNewChat}
        onDeleteChat={handleDeleteChat}
        userFullName={userFullName}
        isAuthenticated={isAuthenticated}
        onLoginClick={handleOpenAuth}
        isLoadingChats={chatListStatus === "loading" && chats.length === 0}
        isLoadingMoreChats={isLoadingMoreChats}
        hasMoreChats={hasMoreChats}
        chatLoadError={chatListError}
        onLoadMoreChats={handleLoadMoreChats}
        onRetryLoadChats={handleRetryChats}
        theme={theme}
      />

      <TopBar
        onToggleSidebar={handleToggleSidebar}
        onSettingsClick={() => setIsSettingsModalOpen(true)}
        onProfileClick={() => setIsSettingsModalOpen(true)}
        onLoginClick={handleOpenAuth}
        isAuthenticated={isAuthenticated}
        userInitial={userInitial}
      />

      <div className="relative z-10 flex min-h-0 flex-1 flex-col overflow-hidden">
        {showHome ? (
          <HomePage
            onSend={handleSend}
            isLoading={isCreatingChat}
            isAuthenticated={isAuthenticated}
            onAuthRequired={handleOpenAuth}
            theme={theme}
          />
        ) : (
          <div className="flex min-h-0 flex-1 flex-col overflow-hidden">
            <div className="min-h-0 flex-1">
              {activeChat && (
                <ChatView
                  chat={activeChat}
                  isLoading={isCurrentChatLoading}
                  animatedMessageId={animatedMessageId}
                  onRetryHistory={handleRetryHistory}
                  onRetryPendingMessage={handleRetryPendingMessage}
                />
              )}
            </div>

            <div
              className="sticky bottom-0 z-20 shrink-0 border-t shadow-[0_-18px_48px_rgba(15,23,42,0.08)] backdrop-blur-2xl"
              style={{
                borderColor: isDarkTheme ? "rgba(255,255,255,0.08)" : "rgba(255,255,255,0.35)",
                background: isDarkTheme
                  ? "linear-gradient(180deg, rgba(7,19,17,0.12), rgba(7,19,17,0.92))"
                  : "linear-gradient(180deg, rgba(239,248,243,0.22), rgba(239,248,243,0.92))",
                boxShadow: isDarkTheme
                  ? "0 -18px 48px rgba(0,0,0,0.22)"
                  : "0 -18px 48px rgba(15,23,42,0.08)",
              }}
            >
              <ChatInput
                onSend={handleSend}
                isLoading={isCurrentChatLoading}
                placeholder="Опишите ситуацию или задайте вопрос"
                mode="dock"
                isAuthenticated={isAuthenticated}
                onAuthRequired={handleOpenAuth}
                theme={theme}
              />

              <AppDisclaimer className="px-4 pb-4" />
            </div>
          </div>
        )}
      </div>

      {pendingDeleteChat && (
        <div className="fixed inset-0 z-[70] flex items-center justify-center px-4">
          <div
            className="absolute inset-0 bg-black/55 backdrop-blur-[4px]"
            onClick={() => setPendingDeleteChatId(null)}
          />

          <div
            className="relative z-10 w-full max-w-[360px] rounded-[24px] border p-5 shadow-[0_30px_80px_rgba(0,0,0,0.36)]"
            style={{
              borderColor: theme === "dark" ? "#233230" : "rgba(226,232,240,0.8)",
              background: theme === "dark"
                ? "linear-gradient(180deg, rgba(13,36,31,0.98) 0%, rgba(9,28,24,0.98) 100%)"
                : "linear-gradient(180deg, rgba(255,255,255,0.98) 0%, rgba(248,250,252,0.98) 100%)",
            }}
          >
            <div className="mb-5 flex items-start gap-3">
              <div
                className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl"
                style={{
                  background: theme === "dark" ? "rgba(251, 113, 133, 0.15)" : "rgba(254, 202, 202, 0.55)",
                }}
              >
                <svg
                  width="22"
                  height="22"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke={theme === "dark" ? "#fb7185" : "#ef4444"}
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="M3 6h18" />
                  <path d="M8 6V4h8v2" />
                  <path d="M6 6l1 14h10l1-14" />
                  <path d="M10 11v5" />
                  <path d="M14 11v5" />
                </svg>
              </div>

              <div className="min-w-0 pt-1">
                <div className={theme === "dark" ? "text-[22px] font-bold text-slate-50" : "text-[22px] font-bold text-slate-900"}>
                  Удалить чат?
                </div>
                <div className={theme === "dark" ? "mt-3 text-[16px] leading-7 text-slate-400" : "mt-3 text-[16px] leading-7 text-slate-600"}>
                  Этот чат и вся история сообщений будут удалены без возможности восстановления.
                </div>
              </div>
            </div>

            <div className="flex gap-3">
              <button
                type="button"
                onClick={() => setPendingDeleteChatId(null)}
                className="flex h-14 flex-1 cursor-pointer items-center justify-center rounded-2xl border text-[16px] font-semibold transition-all hover:-translate-y-0.5"
                style={{
                  borderColor: theme === "dark" ? "#233230" : "rgba(226,232,240,0.8)",
                  background: theme === "dark" ? "rgba(255,255,255,0.05)" : "rgba(255,255,255,0.78)",
                  color: theme === "dark" ? "#d1d5db" : "#475569",
                }}
              >
                Отмена
              </button>

              <button
                type="button"
                onClick={() => {
                  const chatId = pendingDeleteChatId;
                  setPendingDeleteChatId(null);
                  if (chatId) {
                    void performDeleteChat(chatId);
                  }
                }}
                className="flex h-14 flex-1 cursor-pointer items-center justify-center rounded-2xl text-[16px] font-semibold text-white transition-all hover:-translate-y-0.5"
                style={{ background: "#ff275a" }}
              >
                Удалить
              </button>
            </div>
          </div>
        </div>
      )}

      <AuthModal
        isOpen={isAuthModalOpen}
        onClose={handleCloseAuth}
        externalError={sberAuthError}
        isFinalizing={isFinalizingSberAuth}
        onMockLogin={handleMockLogin}
      />

      <SettingsModal
        isOpen={isSettingsModalOpen}
        onClose={() => setIsSettingsModalOpen(false)}
        userName={userFullName}
        onLogout={handleLogout}
        theme={theme}
        onThemeChange={setTheme}
      />
    </div>
  );
}
