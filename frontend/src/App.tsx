import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  createChat,
  deleteChat as deleteChatApi,
  fetchChats,
  fetchMessages,
  sendMessageToChat,
} from "@/api/chatApi";
import AppDisclaimer from "@/components/AppDisclaimer";
import AuthModal from "@/components/AuthModal";
import ChatInput from "@/components/ChatInput";
import ChatView from "@/components/ChatView";
import HomePage from "@/components/HomePage";
import SettingsModal from "@/components/SettingsModal";
import Sidebar from "@/components/Sidebar";
import TopBar from "@/components/TopBar";
import type { Chat, Message } from "@/types";
import { UnauthorizedError } from "@/api/errors";

const AUTH_TOKEN_KEY = "ai-social-support.auth.token";
const AUTH_USER_KEY = "ai-social-support.auth.user";

function decodeJwtPayload(token: string): { exp?: number } | null {
  try {
    const base64Url = token.split(".")[1];
    if (!base64Url) return null;

    const base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/");
    const padded = base64.padEnd(
      base64.length + ((4 - (base64.length % 4)) % 4),
      "="
    );

    return JSON.parse(window.atob(padded)) as { exp?: number };
  } catch {
    return null;
  }
}

function isTokenExpired(token: string): boolean {
  const payload = decodeJwtPayload(token);
  if (!payload?.exp) return true;
  return payload.exp * 1000 <= Date.now();
}

function readAuthState(): { token: string | null; userName: string | null } {
  if (typeof window === "undefined") return { token: null, userName: null };

  const token = window.localStorage.getItem(AUTH_TOKEN_KEY);
  const userName = window.localStorage.getItem(AUTH_USER_KEY);

  if (!token || isTokenExpired(token)) {
    window.localStorage.removeItem(AUTH_TOKEN_KEY);
    window.localStorage.removeItem(AUTH_USER_KEY);
    return { token: null, userName: null };
  }

  return {
    token,
    userName,
  };
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

  const controllersRef = useRef<Map<string, AbortController>>(new Map());

  const isAuthenticated = !!authToken;
  const userFullName = userName || "Пользователь";
  const userInitial = userFullName.trim().charAt(0).toUpperCase() || "П";

  const activeChat = useMemo(
    () => chats.find((c) => c.id === activeChatId) ?? null,
    [chats, activeChatId]
  );

  const showHome = !activeChat || activeChat.messages.length === 0;

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
    setIsAuthModalOpen(true);
  }, []);

  const handleLogout = useCallback(() => {
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
  }, []);

  // ===== Загрузить список чатов с бэка =====
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

  // ===== Загрузить сообщения при выборе чата =====
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

  // ===== Cleanup =====
  useEffect(() => {
    return () => {
      controllersRef.current.forEach((c) => c.abort());
      controllersRef.current.clear();
    };
  }, []);

  const handleAuthSuccess = useCallback((token: string, name: string) => {
    if (typeof window !== "undefined") {
      window.localStorage.setItem(AUTH_TOKEN_KEY, token);
      window.localStorage.setItem(AUTH_USER_KEY, name);
    }

    setAuthToken(token);
    setUserName(name);
    setIsAuthModalOpen(false);
  }, []);

  const handleOpenAuth = useCallback(() => setIsAuthModalOpen(true), []);

  // ===== Отправка сообщения =====
  const handleSend = useCallback(
    async (rawText: string) => {
      const text = rawText.trim();
      if (!text) return;

      if (!authToken) {
        setIsAuthModalOpen(true);
        return;
      }

      setAnimatedMessageId(null);

      const controller = new AbortController();
      let targetChatId = activeChatId;

      try {
        // Если нет активного чата — создаём на бэке
        if (!targetChatId) {
          const newChat = await createChat(text, controller.signal);
          targetChatId = newChat.id;
          setChats((prev) =>
            [newChat, ...prev].sort((a, b) => b.updatedAt - a.updatedAt)
          );
          setActiveChatId(targetChatId);
        }

        controllersRef.current.set(targetChatId, controller);
        setLoadingChatIds((prev) =>
          prev.includes(targetChatId!) ? prev : [...prev, targetChatId!]
        );

        const { userMsg, assistantMsg } = await sendMessageToChat(
          targetChatId,
          text,
          controller.signal
        );

        const finalChatId = targetChatId;
        setChats((prev) =>
          prev
            .map((c) => {
              if (c.id !== finalChatId) return c;
              return {
                ...c,
                updatedAt: assistantMsg.timestamp,
                messages: mergeUniqueMessages(c.messages, [userMsg, assistantMsg]),
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
    [activeChatId, authToken, handleSessionExpired]
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
    <div className="relative min-h-screen overflow-hidden bg-[var(--app-bg)] text-slate-900">
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

      <div className="relative z-10 flex min-h-screen flex-col">
        {showHome ? (
          <HomePage
            onSend={handleSend}
            isLoading={false}
            isAuthenticated={isAuthenticated}
            onAuthRequired={handleOpenAuth}
          />
        ) : (
          <>
            {activeChat && (
              <ChatView
                chat={activeChat}
                isLoading={isCurrentChatLoading}
                animatedMessageId={animatedMessageId}
              />
            )}
            <div className="sticky bottom-0 z-20 border-t border-white/35 bg-[linear-gradient(180deg,rgba(239,248,243,0.2),rgba(239,248,243,0.88))] backdrop-blur-2xl">
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
          </>
        )}
      </div>

      <AuthModal
        isOpen={isAuthModalOpen}
        onClose={() => setIsAuthModalOpen(false)}
        onAuthSuccess={handleAuthSuccess}
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
