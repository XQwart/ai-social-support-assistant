import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  createChat,
  deleteChat as deleteChatApi,
  fetchChats,
  fetchMessages,
  sendMessageToChat,
} from "@/api/chatApi";
import { preloadSberAuthParams } from "@/components/AuthModal";
import AppDisclaimer from "@/components/AppDisclaimer";
import AuthModal from "@/components/AuthModal";
import { exchangeSberCodeRequest, logoutRequest } from "@/api/authApi";
import { UnauthorizedError } from "@/api/errors";
import ChatInput from "@/components/ChatInput";
import ChatView from "@/components/ChatView";
import HomePage from "@/components/HomePage";
import SettingsModal from "@/components/SettingsModal";
import Sidebar from "@/components/Sidebar";
import TopBar from "@/components/TopBar";
import type { Chat, Message } from "@/types";
import type { ExchangeSberCodeResponse } from "@/api/authApi";

const AUTH_TOKEN_KEY = "ai-social-support.auth.token";
const AUTH_USER_KEY = "ai-social-support.auth.user";

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

function readAuthState(): { token: string | null; userName: string | null } {
  if (typeof window === "undefined") return { token: null, userName: null };

  const token = window.localStorage.getItem(AUTH_TOKEN_KEY);
  const userName = window.localStorage.getItem(AUTH_USER_KEY);

  return {
    token: token ?? null,
    userName,
  };
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
    searchParams.get("description") ??
    searchParams.get("error_description");

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

function mergeUniqueMessages(
  current: Message[],
  incoming: Message[]
): Message[] {
  const map = new Map<string, Message>();

  [...current, ...incoming].forEach((msg) => {
    map.set(msg.id, msg);
  });

  return Array.from(map.values()).sort((a, b) => a.timestamp - b.timestamp);
}

export default function App() {
  const [chats, setChats] = useState<Chat[]>([]);
  const [activeChatId, setActiveChatId] = useState<string | null>(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [loadingChatIds, setLoadingChatIds] = useState<string[]>([]);
  const [animatedMessageId, setAnimatedMessageId] = useState<string | null>(
    null
  );

  const [authToken, setAuthToken] = useState<string | null>(
    () => readAuthState().token
  );
  const [userName, setUserName] = useState<string>(
    () => readAuthState().userName || ""
  );

  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [isSettingsModalOpen, setIsSettingsModalOpen] = useState(false);
  const [sberAuthError, setSberAuthError] = useState("");
  const [isFinalizingSberAuth, setIsFinalizingSberAuth] = useState(false);

  const controllersRef = useRef<Map<string, AbortController>>(new Map());

  const isAuthenticated = !!authToken;
  const userFullName = userName || "Пользователь";
  const userInitial = userFullName.trim().charAt(0).toUpperCase() || "П";

  const activeChat = useMemo(
    () => chats.find((c) => c.id === activeChatId) ?? null,
    [chats, activeChatId]
  );

  const showHome = !activeChat;

  const isCurrentChatLoading = useMemo(() => {
    if (!activeChatId) return false;
    return loadingChatIds.includes(activeChatId);
  }, [activeChatId, loadingChatIds]);

  const handleSessionExpired = useCallback(() => {
    controllersRef.current.forEach((c) => c.abort());
    controllersRef.current.clear();

    if (typeof window !== "undefined") {
      window.localStorage.removeItem(AUTH_TOKEN_KEY);
      window.localStorage.removeItem(AUTH_USER_KEY);
    }

    setAuthToken(null);
    setUserName("");
    setChats([]);
    setActiveChatId(null);
    setLoadingChatIds([]);
    setAnimatedMessageId(null);
    setIsSidebarOpen(false);
    setIsSettingsModalOpen(false);
    setSberAuthError("");
    setIsFinalizingSberAuth(false);
    setIsAuthModalOpen(true);
  }, []);

  const handleLogout = useCallback(async () => {
    try {
      await logoutRequest();
    } catch (error) {
      if (!(error instanceof UnauthorizedError)) {
        console.error("Logout request failed", error);
      }
    }

    if (typeof window !== "undefined") {
      window.localStorage.removeItem(AUTH_TOKEN_KEY);
      window.localStorage.removeItem(AUTH_USER_KEY);
    }

    setAuthToken(null);
    setUserName("");
    setChats([]);
    setActiveChatId(null);
    setLoadingChatIds([]);
    setAnimatedMessageId(null);
    setIsSettingsModalOpen(false);
    setSberAuthError("");
    setIsFinalizingSberAuth(false);
  }, []);

  useEffect(() => {
    if (!authToken) {
      setChats([]);
      return;
    }

    const ctrl = new AbortController();

    fetchChats(100, 0, ctrl.signal)
      .then((list) => setChats(list.sort((a, b) => b.updatedAt - a.updatedAt)))
      .catch((error: unknown) => {
        if (error instanceof UnauthorizedError) {
          handleSessionExpired();
        }
      });

    return () => ctrl.abort();
  }, [authToken, handleSessionExpired]);

  useEffect(() => {
    if (!activeChatId || !authToken) return;

    const chat = chats.find((c) => c.id === activeChatId);
    if (chat && chat.messages.length > 0) return;

    // Важно: пока в этот чат идёт отправка первого сообщения,
    // не подгружаем сообщения отдельно, иначе получаем дубли
    if (loadingChatIds.includes(activeChatId)) return;

    const ctrl = new AbortController();

    fetchMessages(activeChatId, ctrl.signal)
      .then((msgs) => {
        setChats((prev) =>
          prev.map((c) =>
            c.id === activeChatId
              ? { ...c, messages: mergeUniqueMessages(c.messages, msgs) }
              : c
          )
        );
      })
      .catch((error: unknown) => {
        if (error instanceof UnauthorizedError) {
          handleSessionExpired();
        }
      });

    return () => ctrl.abort();
  }, [
    activeChatId,
    authToken,
    chats,
    loadingChatIds,
    handleSessionExpired,
  ]);

  useEffect(() => {
    return () => {
      controllersRef.current.forEach((c) => c.abort());
      controllersRef.current.clear();
    };
  }, []);

  useEffect(() => {
    preloadSberAuthParams();
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") return;

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

    let cancelled = false;

    setSberAuthError("");
    setIsFinalizingSberAuth(true);
    setIsAuthModalOpen(true);

    getOrCreateSberExchange(callbackData.code)
      .then(({ token, userName }) => {
        if (cancelled) return;

        if (typeof window !== "undefined") {
          window.localStorage.setItem(AUTH_TOKEN_KEY, token);
          window.localStorage.setItem(AUTH_USER_KEY, userName);
        }

        setAuthToken(token);
        setUserName(userName);
        setSberAuthError("");
        setIsAuthModalOpen(false);
        pendingSberCallback = null;
      })
      .catch((error: unknown) => {
        if (cancelled) return;

        if (typeof window !== "undefined") {
          window.localStorage.removeItem(AUTH_TOKEN_KEY);
          window.localStorage.removeItem(AUTH_USER_KEY);
        }

        setAuthToken(null);
        setUserName("");
        setSberAuthError(
          error instanceof Error
            ? error.message
            : "Не удалось завершить вход через Sber ID"
        );
        setIsAuthModalOpen(true);
        pendingSberCallback = null;
      })
      .finally(() => {
        if (cancelled) {
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
  }, []);

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

  const handleSend = useCallback(
    async (rawText: string) => {
      const text = rawText.trim();
      if (!text) return;

      if (!authToken) {
        handleOpenAuth();
        return;
      }

      setAnimatedMessageId(null);

      const controller = new AbortController();
      let targetChatId = activeChatId;


      const optimisticUserMsg: Message = {
        id: `optimistic-${Date.now()}`,
        role: "user",
        content: text,
        timestamp: Date.now(),
      };

      try {
        if (!targetChatId) {
          const newChat = await createChat(text, controller.signal);
          targetChatId = newChat.id;

          controllersRef.current.set(targetChatId, controller);
          setLoadingChatIds((prev) =>
            prev.includes(targetChatId!) ? prev : [...prev, targetChatId!]
          );

          setChats((prev) =>
            [{ ...newChat, messages: [optimisticUserMsg] }, ...prev].sort(
              (a, b) => b.updatedAt - a.updatedAt
            )
          );
          setActiveChatId(targetChatId);
        } else {
          controllersRef.current.set(targetChatId, controller);
          setLoadingChatIds((prev) =>
            prev.includes(targetChatId!) ? prev : [...prev, targetChatId!]
          );

          const chatId = targetChatId;
          setChats((prev) =>
            prev.map((c) =>
              c.id === chatId
                ? { ...c, messages: [...c.messages, optimisticUserMsg] }
                : c
            )
          );
        }

        const { userMsg, assistantMsg, contextCompressed } = await sendMessageToChat(
          targetChatId,
          text,
          controller.signal
        );

        const finalChatId = targetChatId;
        const newMessages: Message[] = [userMsg];

        if (contextCompressed) {
          newMessages.push({
            id: `system-compress-${Date.now()}`,
            role: "system",
            content: "Контекст предыдущих сообщений был сжат для оптимизации. Я помню основные темы нашего разговора.",
            timestamp: assistantMsg.timestamp - 1,
          });
        }

        newMessages.push(assistantMsg);

        setChats((prev) =>
          prev
            .map((c) => {
              if (c.id !== finalChatId) return c;
              const withoutOptimistic = c.messages.filter(
                (m) => m.id !== optimisticUserMsg.id
              );
              return {
                ...c,
                updatedAt: assistantMsg.timestamp,
                messages: mergeUniqueMessages(withoutOptimistic, newMessages),
              };
            })
            .sort((a, b) => b.updatedAt - a.updatedAt)
        );

        setAnimatedMessageId(assistantMsg.id);
      } catch (error) {
        if (error instanceof UnauthorizedError) {
          handleSessionExpired();
          return;
        }

        if (!(error instanceof DOMException && error.name === "AbortError")) {
          const fallback: Message = {
            id: `error-${Date.now()}`,
            role: "assistant",
            content:
              "Не удалось получить ответ. Проверьте соединение и попробуйте ещё раз.",
            timestamp: Date.now(),
            error: true,
          };

          if (targetChatId) {
            const errChatId = targetChatId;
            setChats((prev) =>
              prev.map((c) => {
                if (c.id !== errChatId) return c;
                return {
                  ...c,
                  updatedAt: fallback.timestamp,
                  messages: [...c.messages, fallback],
                };
              })
            );
            setAnimatedMessageId(fallback.id);
          }
        }
      } finally {
        if (targetChatId) {
          controllersRef.current.delete(targetChatId);
          setLoadingChatIds((prev) =>
            prev.filter((id) => id !== targetChatId)
          );
        }
      }
    },
    [activeChatId, authToken, handleOpenAuth, handleSessionExpired]
  );

  const handleSelectChat = useCallback((chatId: string) => {
    setActiveChatId(chatId);
    setAnimatedMessageId(null);
  }, []);

  const handleNewChat = useCallback(() => {
    setActiveChatId(null);
    setAnimatedMessageId(null);
  }, []);

  const handleDeleteChat = useCallback(
    async (chatId: string) => {
      const shouldDelete = window.confirm("Удалить этот чат?");
      if (!shouldDelete) return;

      const ctrl = controllersRef.current.get(chatId);
      if (ctrl) {
        ctrl.abort();
        controllersRef.current.delete(chatId);
      }

      setChats((prev) => prev.filter((c) => c.id !== chatId));
      setLoadingChatIds((prev) => prev.filter((id) => id !== chatId));
      setActiveChatId((prev) => (prev === chatId ? null : prev));

      try {
        await deleteChatApi(chatId);
      } catch (error) {
        if (error instanceof UnauthorizedError) {
          handleSessionExpired();
        }
      }
    },
    [handleSessionExpired]
  );

  const handleToggleSidebar = useCallback(
    () => setIsSidebarOpen((p) => !p),
    []
  );
  const handleCloseSidebar = useCallback(() => setIsSidebarOpen(false), []);

  return (
    <div className="relative flex h-[100dvh] min-h-screen flex-col overflow-hidden bg-[var(--app-bg)] text-slate-900">
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
            isLoading={false}
            isAuthenticated={isAuthenticated}
            onAuthRequired={handleOpenAuth}
          />
        ) : (
          <div className="flex min-h-0 flex-1 flex-col overflow-hidden">
            <div className="min-h-0 flex-1">
              {activeChat && (
                <ChatView
                  chat={activeChat}
                  isLoading={isCurrentChatLoading}
                  animatedMessageId={animatedMessageId}
                />
              )}
            </div>

            <div className="sticky bottom-0 z-20 shrink-0 border-t border-white/35 bg-[linear-gradient(180deg,rgba(239,248,243,0.22),rgba(239,248,243,0.92))] shadow-[0_-18px_48px_rgba(15,23,42,0.08)] backdrop-blur-2xl">
              <ChatInput
                onSend={handleSend}
                isLoading={isCurrentChatLoading}
                placeholder="Опишите ситуацию или задайте вопрос"
                mode="dock"
                isAuthenticated={isAuthenticated}
                onAuthRequired={handleOpenAuth}
              />

              <AppDisclaimer className="px-4 pb-4" />
            </div>
          </div>
        )}
      </div>

      <AuthModal
        isOpen={isAuthModalOpen}
        onClose={handleCloseAuth}
        externalError={sberAuthError}
        isFinalizing={isFinalizingSberAuth}
      />

      <SettingsModal
        isOpen={isSettingsModalOpen}
        onClose={() => setIsSettingsModalOpen(false)}
        userName={userFullName}
        onLogout={handleLogout}
      />
    </div>
  );
}
