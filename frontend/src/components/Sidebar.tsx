import { useEffect, useMemo, useRef, useState } from "react";
import type { Chat } from "@/types";
import { cn } from "@/utils/cn";

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
  chats: Chat[];
  activeChatId: string | null;
  onSelectChat: (id: string) => void;
  onNewChat: () => void;
  onDeleteChat: (id: string) => void;
  userFullName: string;
  isAuthenticated: boolean;
  onLoginClick: () => void;
}

function getDateLabel(timestamp: number): string {
  const date = new Date(timestamp);
  const today = new Date();

  const startOfToday = new Date(
    today.getFullYear(),
    today.getMonth(),
    today.getDate()
  ).getTime();

  const startOfDate = new Date(
    date.getFullYear(),
    date.getMonth(),
    date.getDate()
  ).getTime();

  const diffDays = Math.floor((startOfToday - startOfDate) / 86400000);

  if (diffDays === 0) {
    return "Сегодня";
  }

  if (diffDays === 1) {
    return "Вчера";
  }

  if (diffDays < 7) {
    return `${diffDays} дн. назад`;
  }

  return date.toLocaleDateString("ru-RU", {
    day: "numeric",
    month: "long",
  });
}

export default function Sidebar({
  isOpen,
  onClose,
  chats,
  activeChatId,
  onSelectChat,
  onNewChat,
  onDeleteChat,
  userFullName,
  isAuthenticated,
  onLoginClick,
}: SidebarProps) {
  const [search, setSearch] = useState("");
  const panelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handlePointerDown = (event: MouseEvent) => {
      if (!isOpen) {
        return;
      }

      const target = event.target as Node | null;
      if (target && panelRef.current && !panelRef.current.contains(target)) {
        onClose();
      }
    };

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onClose();
      }
    };

    document.addEventListener("mousedown", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown);

    const previousOverflow = document.body.style.overflow;
    if (isOpen) {
      document.body.style.overflow = "hidden";
    }

    return () => {
      document.removeEventListener("mousedown", handlePointerDown);
      document.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = previousOverflow;
    };
  }, [isOpen, onClose]);

  const filteredChats = useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query) {
      return chats;
    }

    return chats.filter((chat) => chat.title.toLowerCase().includes(query));
  }, [chats, search]);

  const groupedChats = useMemo(() => {
    return filteredChats.reduce<Record<string, Chat[]>>((acc, chat) => {
      const label = getDateLabel(chat.updatedAt);
      (acc[label] ??= []).push(chat);
      return acc;
    }, {});
  }, [filteredChats]);

  const userInitial = userFullName.trim().charAt(0).toUpperCase() || "П";

  return (
    <>
      <div
        className={cn(
          "fixed inset-0 z-40 bg-slate-900/10 backdrop-blur-[2px] transition-opacity duration-300",
          isOpen
            ? "pointer-events-auto opacity-100"
            : "pointer-events-none opacity-0"
        )}
      />

      <aside
        ref={panelRef}
        className={cn(
          "fixed left-0 top-0 z-50 flex h-full w-[320px] max-w-[88vw] flex-col transition-transform duration-[420ms] ease-[cubic-bezier(0.22,1,0.36,1)]",
          isOpen ? "translate-x-0" : "-translate-x-[105%]"
        )}
        style={{
          background:
            "linear-gradient(180deg, rgba(255,255,255,0.7) 0%, rgba(255,255,255,0.54) 100%)",
          backdropFilter: "blur(30px) saturate(180%)",
          WebkitBackdropFilter: "blur(30px) saturate(180%)",
          borderRight: "1px solid rgba(255,255,255,0.78)",
          borderTopRightRadius: "28px",
          borderBottomRightRadius: "28px",
          boxShadow:
            "0 24px 60px rgba(15,23,42,0.12), inset 0 1px 0 rgba(255,255,255,0.65)",
        }}
      >
        <div
          className="pointer-events-none absolute inset-0"
          aria-hidden="true"
          style={{
            background:
              "linear-gradient(160deg, rgba(255,255,255,0.48) 0%, rgba(255,255,255,0.12) 38%, rgba(255,255,255,0) 60%)",
            borderTopRightRadius: "28px",
            borderBottomRightRadius: "28px",
          }}
        />

        <div className="relative z-10 flex items-center justify-between px-5 pb-3 pt-5">
          <div>
            <div className="text-[15px] font-semibold text-slate-800">
              История чатов
            </div>
            <div className="mt-1 text-xs text-slate-500">
              Быстрый доступ к прошлым диалогам
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="inline-flex h-9 w-9 cursor-pointer items-center justify-center rounded-2xl border border-white/60 bg-white/45 text-slate-500 transition-colors hover:bg-white/75"
            aria-label="Закрыть меню"
          >
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M18 6L6 18" />
              <path d="M6 6L18 18" />
            </svg>
          </button>
        </div>

        {/* Content area — authenticated vs not */}
        {isAuthenticated ? (
          <>
            {/* Search */}
            <div className="relative z-10 px-4 pb-3">
              <div className="flex items-center gap-2 rounded-2xl border border-white/65 bg-white/50 px-3 py-2.5 shadow-[inset_0_1px_1px_rgba(255,255,255,0.45)]">
                <svg
                  width="15"
                  height="15"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="#94a3b8"
                  strokeWidth="2.2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <circle cx="11" cy="11" r="7" />
                  <path d="M20 20L17 17" />
                </svg>
                <input
                  type="text"
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  placeholder="Поиск по чатам"
                  className="w-full bg-transparent text-[14px] text-slate-700 outline-none placeholder:text-slate-400"
                />
              </div>
            </div>

            {/* New chat */}
            <div className="relative z-10 px-4 pb-4">
              <button
                type="button"
                onClick={() => {
                  onNewChat();
                  onClose();
                }}
                className="flex w-full cursor-pointer items-center justify-center gap-2 rounded-2xl border border-emerald-200/80 bg-emerald-500/12 px-3 py-2.5 text-[13px] font-semibold text-emerald-700 transition-all hover:-translate-y-0.5 hover:bg-emerald-500/16"
              >
                <svg
                  width="15"
                  height="15"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2.3"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="M12 5V19" />
                  <path d="M5 12H19" />
                </svg>
                Новый чат
              </button>
            </div>

            {/* Chat list */}
            <div className="relative z-10 custom-scrollbar flex-1 overflow-y-auto px-3 pb-4">
              {Object.entries(groupedChats).map(([groupLabel, groupChats]) => (
                <div key={groupLabel} className="mb-4">
                  <div className="mb-2 px-2 text-[10px] font-bold uppercase tracking-[0.18em] text-slate-400">
                    {groupLabel}
                  </div>
                  <div className="space-y-1">
                    {groupChats.map((chat) => {
                      const isActive = chat.id === activeChatId;
                      return (
                        <div key={chat.id} className="group relative">
                          <button
                            type="button"
                            onClick={() => {
                              onSelectChat(chat.id);
                              onClose();
                            }}
                            className={cn(
                              "w-full cursor-pointer rounded-2xl px-3 py-3 text-left transition-all",
                              isActive
                                ? "border border-white/75 bg-white/72 shadow-[0_10px_25px_rgba(15,23,42,0.05)]"
                                : "border border-transparent bg-transparent hover:bg-white/45"
                            )}
                          >
                            <div
                              className={cn(
                                "truncate pr-8 text-[13px] font-medium",
                                isActive ? "text-slate-900" : "text-slate-700"
                              )}
                            >
                              {chat.title}
                            </div>
                            <div className="mt-1 text-[11px] text-slate-400">
                              {new Date(chat.updatedAt).toLocaleTimeString(
                                "ru-RU",
                                {
                                  hour: "2-digit",
                                  minute: "2-digit",
                                }
                              )}
                            </div>
                          </button>

                          <button
                            type="button"
                            onClick={(event) => {
                              event.stopPropagation();
                              onDeleteChat(chat.id);
                            }}
                            className="absolute right-2 top-1/2 hidden h-8 w-8 -translate-y-1/2 cursor-pointer items-center justify-center rounded-xl border border-white/60 bg-white/70 text-slate-400 transition-colors hover:text-rose-500 group-hover:flex"
                            aria-label="Удалить чат"
                          >
                            <svg
                              width="13"
                              height="13"
                              viewBox="0 0 24 24"
                              fill="none"
                              stroke="currentColor"
                              strokeWidth="2.4"
                              strokeLinecap="round"
                              strokeLinejoin="round"
                            >
                              <path d="M18 6L6 18" />
                              <path d="M6 6L18 18" />
                            </svg>
                          </button>
                        </div>
                      );
                    })}
                  </div>
                </div>
              ))}

              {filteredChats.length === 0 && (
                <div className="px-2 pt-10 text-center text-sm text-slate-400">
                  {search ? "Ничего не найдено" : "Пока нет сохранённых чатов"}
                </div>
              )}
            </div>

            {/* User card at bottom */}
            <div className="relative z-10 border-t border-white/55 px-4 py-4">
              <div className="flex items-center gap-3 rounded-2xl border border-white/70 bg-white/58 p-3 shadow-[0_10px_25px_rgba(15,23,42,0.04)] backdrop-blur-xl">
                <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-[linear-gradient(135deg,#34d399_0%,#14b8a6_100%)] text-sm font-bold text-white shadow-[0_10px_24px_rgba(16,185,129,0.24)]">
                  {userInitial}
                </div>
                <div className="min-w-0">
                  <div className="truncate text-sm font-semibold text-slate-800">
                    {userFullName}
                  </div>
                  <div className="truncate text-xs text-slate-500">
                    Пользователь системы
                  </div>
                </div>
              </div>
            </div>
          </>
        ) : (
          /* ===== NOT AUTHENTICATED — blurred overlay ===== */
          <div className="relative z-10 flex flex-1 flex-col items-center justify-center px-6">
            {/* Blurred fake chat list behind */}
            <div className="pointer-events-none absolute inset-0 overflow-hidden px-3 pt-2 opacity-40">
              <div className="space-y-3">
                {[1, 2, 3, 4, 5, 6].map((i) => (
                  <div
                    key={i}
                    className="rounded-2xl bg-white/50 p-3"
                    style={{ filter: "blur(6px)" }}
                  >
                    <div className="h-3 w-3/4 rounded bg-slate-300/50" />
                    <div className="mt-2 h-2 w-1/3 rounded bg-slate-200/50" />
                  </div>
                ))}
              </div>
            </div>

            {/* Message + login button */}
            <div className="relative z-10 flex flex-col items-center text-center">
              <div className="mb-3 flex h-14 w-14 items-center justify-center rounded-2xl border border-white/60 bg-white/50">
                <svg
                  width="24"
                  height="24"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="#94a3b8"
                  strokeWidth="1.8"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                  <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                </svg>
              </div>

              <p className="mb-1 text-[15px] font-semibold text-slate-700">
                Войдите в аккаунт
              </p>
              <p className="mb-5 text-[13px] leading-5 text-slate-400">
                чтобы увидеть историю чатов
              </p>

              <button
                type="button"
                onClick={() => {
                  onLoginClick();
                  onClose();
                }}
                className="flex cursor-pointer items-center justify-center gap-2 rounded-full bg-emerald-500 px-8 py-3 text-[14px] font-semibold text-white shadow-[0_10px_28px_rgba(16,185,129,0.28)] transition-all hover:-translate-y-0.5 hover:bg-emerald-600"
              >
                <svg
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2.2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="M15 3H19a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4" />
                  <polyline points="10 17 15 12 10 7" />
                  <line x1="15" y1="12" x2="3" y2="12" />
                </svg>
                Войти
              </button>
            </div>
          </div>
        )}
      </aside>
    </>
  );
}
