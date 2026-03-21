import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { v4 as uuidv4 } from "uuid";
import { deleteChat as deleteChatApi, sendMessage } from "@/api/chatApi";
import AppDisclaimer from "@/components/AppDisclaimer";
import ChatInput from "@/components/ChatInput";
import ChatView from "@/components/ChatView";
import HomePage from "@/components/HomePage";
import Sidebar from "@/components/Sidebar";
import TopBar from "@/components/TopBar";
import type { Chat, Message, MessageRole } from "@/types";

const STORAGE_KEY = "ai-social-support.chats.v1";

function isValidRole(value: unknown): value is MessageRole {
  return value === "user" || value === "assistant" || value === "system";
}

function normalizeChats(data: unknown): Chat[] {
  if (!Array.isArray(data)) {
    return [];
  }

  const now = Date.now();

  const chats: Chat[] = data
    .map((item) => {
      if (!item || typeof item !== "object") {
        return null;
      }

      const rawChat = item as Partial<Chat> & { messages?: unknown[] };

      if (typeof rawChat.id !== "string" || !Array.isArray(rawChat.messages)) {
        return null;
      }

      const createdAt =
        typeof rawChat.createdAt === "number" ? rawChat.createdAt : now;
      const updatedAt =
        typeof rawChat.updatedAt === "number" ? rawChat.updatedAt : createdAt;

      const messages: Message[] = rawChat.messages
        .map((message) => {
          if (!message || typeof message !== "object") {
            return null;
          }

          const rawMessage = message as Partial<Message>;

          if (
            typeof rawMessage.id !== "string" ||
            typeof rawMessage.content !== "string"
          ) {
            return null;
          }

          return {
            id: rawMessage.id,
            role: isValidRole(rawMessage.role) ? rawMessage.role : "assistant",
            content: rawMessage.content,
            timestamp:
              typeof rawMessage.timestamp === "number"
                ? rawMessage.timestamp
                : now,
            error: rawMessage.error === true,
          } satisfies Message;
        })
        .filter((message): message is Message => message !== null);

      return {
        id: rawChat.id,
        title:
          typeof rawChat.title === "string" && rawChat.title.trim()
            ? rawChat.title
            : "Новый диалог",
        createdAt,
        updatedAt,
        messages,
      } satisfies Chat;
    })
    .filter((chat): chat is Chat => chat !== null);

  return sortChats(chats);
}

function readStoredChats(): Chat[] {
  if (typeof window === "undefined") {
    return [];
  }

  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return [];
    }

    return normalizeChats(JSON.parse(raw));
  } catch {
    return [];
  }
}

function sortChats(chats: Chat[]): Chat[] {
  return [...chats].sort((a, b) => b.updatedAt - a.updatedAt);
}

function buildChatTitle(text: string): string {
  const normalized = text.replace(/\s+/g, " ").trim();
  if (!normalized) {
    return "Новый диалог";
  }

  return normalized.length > 54 ? `${normalized.slice(0, 54)}…` : normalized;
}

function isAbortError(error: unknown): boolean {
  return error instanceof DOMException && error.name === "AbortError";
}

function addLoadingChat(list: string[], chatId: string): string[] {
  return list.includes(chatId) ? list : [...list, chatId];
}

function removeLoadingChat(list: string[], chatId: string): string[] {
  return list.filter((id) => id !== chatId);
}

export default function App() {
  const [chats, setChats] = useState<Chat[]>(() => readStoredChats());
  const [activeChatId, setActiveChatId] = useState<string | null>(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [loadingChatIds, setLoadingChatIds] = useState<string[]>([]);
  const [animatedMessageId, setAnimatedMessageId] = useState<string | null>(
    null
  );

  const controllersRef = useRef<Map<string, AbortController>>(new Map());

  const userFullName = "Петров Павел Игоревич";
  const userInitial = userFullName.trim().charAt(0).toUpperCase() || "П";

  const activeChat = useMemo(
    () => chats.find((chat) => chat.id === activeChatId) ?? null,
    [chats, activeChatId]
  );

  const showHome = !activeChat || activeChat.messages.length === 0;

  const isCurrentChatLoading = useMemo(() => {
    if (!activeChatId) {
      return false;
    }
    return loadingChatIds.includes(activeChatId);
  }, [activeChatId, loadingChatIds]);

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }

    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(chats));
  }, [chats]);

  useEffect(() => {
    return () => {
      controllersRef.current.forEach((controller) => controller.abort());
      controllersRef.current.clear();
    };
  }, []);

  const handleSend = useCallback(
    async (rawText: string) => {
      const text = rawText.trim();
      if (!text) {
        return;
      }

      const now = Date.now();
      const targetChatId = activeChatId ?? uuidv4();

      const userMessage: Message = {
        id: uuidv4(),
        role: "user",
        content: text,
        timestamp: now,
      };

      setAnimatedMessageId(null);
      setActiveChatId(targetChatId);

      setChats((prevChats) => {
        const existingChat = prevChats.find((chat) => chat.id === targetChatId);

        if (existingChat) {
          const nextChats = prevChats.map((chat) => {
            if (chat.id !== targetChatId) {
              return chat;
            }

            return {
              ...chat,
              title:
                chat.messages.length === 0 ? buildChatTitle(text) : chat.title,
              updatedAt: now,
              messages: [...chat.messages, userMessage],
            };
          });

          return sortChats(nextChats);
        }

        const newChat: Chat = {
          id: targetChatId,
          title: buildChatTitle(text),
          createdAt: now,
          updatedAt: now,
          messages: [userMessage],
        };

        return sortChats([newChat, ...prevChats]);
      });

      setLoadingChatIds((prev) => addLoadingChat(prev, targetChatId));

      const previousController = controllersRef.current.get(targetChatId);
      if (previousController) {
        previousController.abort();
      }

      const controller = new AbortController();
      controllersRef.current.set(targetChatId, controller);

      try {
        const assistantMessage = await sendMessage(
          targetChatId,
          text,
          controller.signal
        );

        setChats((prevChats) => {
          const nextChats = prevChats.map((chat) => {
            if (chat.id !== targetChatId) {
              return chat;
            }

            return {
              ...chat,
              updatedAt: assistantMessage.timestamp,
              messages: [...chat.messages, assistantMessage],
            };
          });

          return sortChats(nextChats);
        });

        setAnimatedMessageId(assistantMessage.id);
      } catch (error) {
        if (!isAbortError(error)) {
          const fallbackMessage: Message = {
            id: uuidv4(),
            role: "assistant",
            content:
              "Не удалось получить ответ. Проверьте соединение и попробуйте ещё раз.",
            timestamp: Date.now(),
            error: true,
          };

          setChats((prevChats) => {
            const nextChats = prevChats.map((chat) => {
              if (chat.id !== targetChatId) {
                return chat;
              }

              return {
                ...chat,
                updatedAt: fallbackMessage.timestamp,
                messages: [...chat.messages, fallbackMessage],
              };
            });

            return sortChats(nextChats);
          });

          setAnimatedMessageId(fallbackMessage.id);
        }
      } finally {
        if (controllersRef.current.get(targetChatId) === controller) {
          controllersRef.current.delete(targetChatId);
        }

        setLoadingChatIds((prev) => removeLoadingChat(prev, targetChatId));
      }
    },
    [activeChatId]
  );

  const handleSelectChat = useCallback((chatId: string) => {
    setActiveChatId(chatId);
    setAnimatedMessageId(null);
  }, []);

  const handleNewChat = useCallback(() => {
    setActiveChatId(null);
    setAnimatedMessageId(null);
  }, []);

  const handleDeleteChat = useCallback(async (chatId: string) => {
    const shouldDelete = window.confirm("Удалить этот чат?");
    if (!shouldDelete) {
      return;
    }

    const controller = controllersRef.current.get(chatId);
    if (controller) {
      controller.abort();
      controllersRef.current.delete(chatId);
    }

    setChats((prevChats) => prevChats.filter((chat) => chat.id !== chatId));
    setLoadingChatIds((prev) => removeLoadingChat(prev, chatId));
    setActiveChatId((prevId) => (prevId === chatId ? null : prevId));

    try {
      await deleteChatApi(chatId);
    } catch {
      // Заглушка под будущие уведомления
    }
  }, []);

  const handleToggleSidebar = useCallback(() => {
    setIsSidebarOpen((prev) => !prev);
  }, []);

  const handleCloseSidebar = useCallback(() => {
    setIsSidebarOpen(false);
  }, []);

  const handleSettingsClick = useCallback(() => {
    // Оставлено под будущую реализацию
  }, []);

  const handleProfileClick = useCallback(() => {
    // Оставлено под будущую реализацию
  }, []);

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
      />

      <TopBar
        onToggleSidebar={handleToggleSidebar}
        onSettingsClick={handleSettingsClick}
        onProfileClick={handleProfileClick}
        userInitial={userInitial}
      />

      <div className="relative z-10 flex min-h-screen flex-col">
        {showHome ? (
          <HomePage onSend={handleSend} isLoading={false} />
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
              />
              <AppDisclaimer className="px-4 pb-4" />
            </div>
          </>
        )}
      </div>
    </div>
  );
}
