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
  onRenameChat: (id: string, newTitle: string) => Promise<boolean>;
  onDeleteChat: (id: string) => void;
  userFullName: string;
  isAuthenticated: boolean;
  onLoginClick: () => void;
  isLoadingChats: boolean;
  isLoadingMoreChats: boolean;
  hasMoreChats: boolean;
  chatLoadError: string | null;
  onLoadMoreChats: () => void;
  onRetryLoadChats: () => void;
  theme: "light" | "dark";
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

  if (diffDays === 0) return "Сегодня";
  if (diffDays === 1) return "Вчера";
  if (diffDays < 7) return `${diffDays} дн. назад`;

  return date.toLocaleDateString("ru-RU", { day: "numeric", month: "long" });
}

interface ChatItemProps {
  chat: Chat;
  isActive: boolean;
  isDark: boolean;
  onSelect: () => void;
  onRename: (newTitle: string) => Promise<boolean>;
  onDelete: () => void;
}

function ChatItem({ chat, isActive, isDark, onSelect, onRename, onDelete }: ChatItemProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [draftTitle, setDraftTitle] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);
  const committingRef = useRef(false);

  function startEdit() {
    setDraftTitle(chat.title);
    setIsEditing(true);
  }

  useEffect(() => {
    if (isEditing) {
      requestAnimationFrame(() => {
        inputRef.current?.focus();
        inputRef.current?.select();
      });
    }
  }, [isEditing]);

  async function commit() {
    if (committingRef.current) return;
    committingRef.current = true;
    const trimmed = draftTitle.trim();
    if (trimmed && trimmed !== chat.title) {
      await onRename(trimmed);
    }
    setIsEditing(false);
    committingRef.current = false;
  }

  function cancel() {
    committingRef.current = true;
    setIsEditing(false);
    setDraftTitle("");
    setTimeout(() => { committingRef.current = false; }, 0);
  }

  function handleKeyDown(event: React.KeyboardEvent<HTMLInputElement>) {
    if (event.key === "Enter") { event.preventDefault(); void commit(); }
    else if (event.key === "Escape") { event.preventDefault(); cancel(); }
  }

  function handleBlur() {
    if (!committingRef.current) void commit();
  }

  return (
    <div className="group relative">
      {/* Main card — pointer-events-none while editing so clicks pass through to the input */}
      <button
        type="button"
        onClick={() => { if (!isEditing) onSelect(); }}
        className={cn(
          "w-full cursor-pointer rounded-2xl px-3 pb-2.5 pt-2.5 text-left transition-all duration-150",
          isEditing && "pointer-events-none",
          isActive
            ? isDark
              ? "border border-white/10 bg-white/10 shadow-[0_10px_25px_rgba(0,0,0,0.18)]"
              : "border border-white/75 bg-white/72 shadow-[0_10px_25px_rgba(15,23,42,0.05)]"
            : isDark
              ? "border border-transparent bg-transparent hover:bg-white/6"
              : "border border-transparent bg-transparent hover:bg-white/45"
        )}
      >
        {/* Title row: leaves room for 2 × action buttons (each 28px) + gap + right offset */}
        {isEditing ? (
          <input
            ref={inputRef}
            type="text"
            value={draftTitle}
            maxLength={255}
            onChange={(e) => setDraftTitle(e.target.value)}
            onKeyDown={handleKeyDown}
            onBlur={handleBlur}
            onClick={(e) => e.stopPropagation()}
            style={{ pointerEvents: "all" }}
            className={cn(
              "block w-full rounded-xl px-2.5 py-1.5",
              "text-[13px] font-medium leading-snug outline-none",
              "transition-shadow duration-150",
              isDark
                ? [
                    "bg-white/14 text-slate-50",
                    "shadow-[inset_0_0_0_1.5px_rgba(52,211,153,0.55)]",
                    "focus:shadow-[inset_0_0_0_1.5px_rgba(52,211,153,0.85),0_0_0_3px_rgba(52,211,153,0.12)]",
                  ].join(" ")
                : [
                    "bg-white text-slate-900",
                    "shadow-[inset_0_0_0_1.5px_rgba(16,185,129,0.45),inset_0_1px_2px_rgba(15,23,42,0.06)]",
                    "focus:shadow-[inset_0_0_0_1.5px_rgba(16,185,129,0.75),0_0_0_3px_rgba(16,185,129,0.12)]",
                  ].join(" ")
            )}
          />
        ) : (
          <div
            className={cn(
              "truncate text-[13px] font-medium leading-snug",
              /* right padding = 2×28px buttons + 4px gap + 8px right-offset = 68px → pr-[72px] */
              "pr-[72px]",
              isActive
                ? isDark ? "text-slate-50" : "text-slate-900"
                : isDark ? "text-slate-200" : "text-slate-700"
            )}
          >
            {chat.title}
          </div>
        )}

        <div
          className={cn(
            "mt-0.5 text-[11px] leading-none",
            isDark ? "text-slate-500" : "text-slate-400"
          )}
        >
          {new Date(chat.updatedAt).toLocaleTimeString("ru-RU", {
            hour: "2-digit",
            minute: "2-digit",
          })}
        </div>
      </button>

      {/* ── Action buttons (appear on row hover) ── */}
      {!isEditing && (
        <div
          className={cn(
            "absolute right-2 top-1/2 -translate-y-1/2",
            "hidden items-center gap-1 group-hover:flex"
          )}
        >
          {/* Rename */}
          <button
            type="button"
            onClick={(e) => { e.stopPropagation(); startEdit(); }}
            aria-label="Переименовать чат"
            className={cn(
              "flex h-[28px] w-[28px] shrink-0 cursor-pointer items-center justify-center rounded-lg",
              "transition-all duration-150",
              "hover:-translate-y-0.5 hover:scale-110 active:translate-y-0 active:scale-95",
              isDark
                ? "bg-sky-500/20 text-sky-300 ring-1 ring-sky-400/25 hover:bg-sky-500/35 hover:text-sky-200 hover:ring-sky-400/50"
                : "bg-sky-100 text-sky-500 ring-1 ring-sky-300/60 hover:bg-sky-200 hover:text-sky-600 hover:ring-sky-400/80"
            )}
          >
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
              <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
              <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
            </svg>
          </button>

          {/* Delete */}
          <button
            type="button"
            onClick={(e) => { e.stopPropagation(); onDelete(); }}
            aria-label="Удалить чат"
            className={cn(
              "flex h-[28px] w-[28px] shrink-0 cursor-pointer items-center justify-center rounded-lg",
              "transition-all duration-150",
              "hover:-translate-y-0.5 hover:scale-110 active:translate-y-0 active:scale-95",
              isDark
                ? "bg-rose-500/20 text-rose-300 ring-1 ring-rose-400/25 hover:bg-rose-500/35 hover:text-rose-200 hover:ring-rose-400/50"
                : "bg-rose-100 text-rose-500 ring-1 ring-rose-300/60 hover:bg-rose-200 hover:text-rose-600 hover:ring-rose-400/80"
            )}
          >
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
              <path d="M3 6h18" />
              <path d="M8 6V4h8v2" />
              <path d="M6 6l1 14h10l1-14" />
              <path d="M10 11v5" />
              <path d="M14 11v5" />
            </svg>
          </button>
        </div>
      )}

      {/* Editing hint */}
      {isEditing && (
        <div
          className={cn(
            "absolute bottom-2 right-3 flex items-center gap-1",
            isDark ? "text-slate-500" : "text-slate-400"
          )}
        >
          <kbd className={cn(
            "rounded px-1 py-px font-mono text-[9px] leading-tight",
            isDark ? "bg-white/10 text-slate-400" : "bg-black/6 text-slate-500"
          )}>↵</kbd>
          <span className="text-[10px]">сохранить</span>
          <span className={isDark ? "text-slate-600" : "text-slate-300"}>·</span>
          <kbd className={cn(
            "rounded px-1 py-px font-mono text-[9px] leading-tight",
            isDark ? "bg-white/10 text-slate-400" : "bg-black/6 text-slate-500"
          )}>Esc</kbd>
          <span className="text-[10px]">отмена</span>
        </div>
      )}
    </div>
  );
}

export default function Sidebar({
  isOpen,
  onClose,
  chats,
  activeChatId,
  onSelectChat,
  onNewChat,
  onRenameChat,
  onDeleteChat,
  userFullName,
  isAuthenticated,
  onLoginClick,
  isLoadingChats,
  isLoadingMoreChats,
  hasMoreChats,
  chatLoadError,
  onLoadMoreChats,
  onRetryLoadChats,
  theme,
}: SidebarProps) {
  const [search, setSearch] = useState("");
  const panelRef = useRef<HTMLDivElement>(null);
  const isDark = theme === "dark";

  useEffect(() => {
    const handlePointerDown = (event: MouseEvent) => {
      if (!isOpen) return;
      const target = event.target as Node | null;
      if (target && panelRef.current && !panelRef.current.contains(target)) {
        onClose();
      }
    };

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };

    document.addEventListener("mousedown", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown);

    const previousOverflow = document.body.style.overflow;
    if (isOpen) document.body.style.overflow = "hidden";

    return () => {
      document.removeEventListener("mousedown", handlePointerDown);
      document.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = previousOverflow;
    };
  }, [isOpen, onClose]);

  const filteredChats = useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query) return chats;
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
          "fixed inset-0 z-40 transition-opacity duration-300",
          isOpen ? "pointer-events-auto opacity-100" : "pointer-events-none opacity-0"
        )}
        style={{
          backgroundColor: isDark ? "rgba(0,0,0,0.45)" : "rgba(15,23,42,0.10)",
          backdropFilter: isDark ? "blur(3px)" : "blur(2px)",
        }}
      />

      <aside
        ref={panelRef}
        className={cn(
          "fixed left-0 top-0 z-50 flex h-full w-[320px] max-w-[88vw] flex-col transition-transform duration-[420ms] ease-[cubic-bezier(0.22,1,0.36,1)]",
          isOpen ? "translate-x-0" : "-translate-x-[105%]"
        )}
        style={{
          background: isDark
            ? "linear-gradient(180deg, rgba(11,31,27,0.96) 0%, rgba(8,24,21,0.92) 100%)"
            : "linear-gradient(180deg, rgba(255,255,255,0.7) 0%, rgba(255,255,255,0.54) 100%)",
          backdropFilter: isDark ? "blur(28px) saturate(140%)" : "blur(30px) saturate(180%)",
          WebkitBackdropFilter: isDark ? "blur(28px) saturate(140%)" : "blur(30px) saturate(180%)",
          borderRight: isDark ? "1px solid rgba(255,255,255,0.08)" : "1px solid rgba(255,255,255,0.78)",
          borderTopRightRadius: "28px",
          borderBottomRightRadius: "28px",
          boxShadow: isDark
            ? "0 24px 60px rgba(0,0,0,0.35), inset 0 1px 0 rgba(255,255,255,0.04)"
            : "0 24px 60px rgba(15,23,42,0.12), inset 0 1px 0 rgba(255,255,255,0.65)",
        }}
      >
        <div
          className="pointer-events-none absolute inset-0"
          aria-hidden="true"
          style={{
            background: isDark
              ? "linear-gradient(160deg, rgba(45,212,191,0.08) 0%, rgba(255,255,255,0.04) 38%, rgba(255,255,255,0) 60%)"
              : "linear-gradient(160deg, rgba(255,255,255,0.48) 0%, rgba(255,255,255,0.12) 38%, rgba(255,255,255,0) 60%)",
            borderTopRightRadius: "28px",
            borderBottomRightRadius: "28px",
          }}
        />

        <div className="relative z-10 flex items-center justify-between px-5 pb-3 pt-5">
          <div>
            <div className={isDark ? "text-[15px] font-semibold text-slate-50" : "text-[15px] font-semibold text-slate-800"}>
              История чатов
            </div>
            <div className={isDark ? "mt-1 text-xs text-slate-400" : "mt-1 text-xs text-slate-500"}>
              Быстрый доступ к прошлым диалогам
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className={cn(
              "inline-flex h-9 w-9 cursor-pointer items-center justify-center rounded-2xl transition-colors",
              isDark
                ? "border border-white/10 bg-white/6 text-slate-300 hover:bg-white/12"
                : "border border-white/60 bg-white/45 text-slate-500 hover:bg-white/75"
            )}
            aria-label="Закрыть меню"
          >
            <svg
              width="16" height="16" viewBox="0 0 24 24"
              fill="none" stroke="currentColor" strokeWidth="2.2"
              strokeLinecap="round" strokeLinejoin="round"
            >
              <path d="M18 6L6 18" />
              <path d="M6 6L18 18" />
            </svg>
          </button>
        </div>

        {isAuthenticated ? (
          <>
            <div className="relative z-10 px-4 pb-3">
              <div
                className="flex items-center gap-2 rounded-2xl px-3 py-2.5"
                style={{
                  border: isDark ? "1px solid rgba(255,255,255,0.10)" : "1px solid rgba(255,255,255,0.65)",
                  background: isDark ? "rgba(255,255,255,0.06)" : "rgba(255,255,255,0.50)",
                  boxShadow: isDark
                    ? "inset 0 1px 1px rgba(255,255,255,0.04)"
                    : "inset 0 1px 1px rgba(255,255,255,0.45)",
                }}
              >
                <svg
                  width="15" height="15" viewBox="0 0 24 24"
                  fill="none" stroke="#94a3b8" strokeWidth="2.2"
                  strokeLinecap="round" strokeLinejoin="round"
                >
                  <circle cx="11" cy="11" r="7" />
                  <path d="M20 20L17 17" />
                </svg>
                <input
                  type="text"
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  placeholder="Поиск по чатам"
                  className={cn(
                    "w-full bg-transparent text-[14px] outline-none",
                    isDark ? "text-slate-100 placeholder:text-slate-500" : "text-slate-700 placeholder:text-slate-400"
                  )}
                />
              </div>
            </div>

            <div className="relative z-10 px-4 pb-4">
              <button
                type="button"
                onClick={() => { onNewChat(); onClose(); }}
                className={cn(
                  "flex w-full cursor-pointer items-center justify-center gap-2 rounded-2xl px-3 py-2.5 text-[13px] font-semibold transition-all hover:-translate-y-0.5",
                  isDark
                    ? "border border-emerald-400/20 bg-emerald-500/10 text-emerald-300 hover:bg-emerald-500/14"
                    : "border border-emerald-200/80 bg-emerald-500/12 text-emerald-700 hover:bg-emerald-500/16"
                )}
              >
                <svg
                  width="15" height="15" viewBox="0 0 24 24"
                  fill="none" stroke="currentColor" strokeWidth="2.3"
                  strokeLinecap="round" strokeLinejoin="round"
                >
                  <path d="M12 5V19" />
                  <path d="M5 12H19" />
                </svg>
                Новый чат
              </button>
            </div>

            <div className="relative z-10 custom-scrollbar flex-1 overflow-y-auto px-3 pb-4">
              {chatLoadError && (
                <div
                  className="mb-4 rounded-2xl px-4 py-3 text-sm shadow-[0_10px_24px_rgba(15,23,42,0.04)]"
                  style={{
                    border: isDark ? "1px solid rgba(251,191,36,0.20)" : "1px solid rgba(251,191,36,0.80)",
                    background: isDark ? "rgba(245,158,11,0.10)" : "rgba(255,251,235,0.90)",
                    color: isDark ? "#fde68a" : "#334155",
                  }}
                >
                  <div>{chatLoadError}</div>
                  <button
                    type="button"
                    onClick={onRetryLoadChats}
                    className="mt-3 inline-flex cursor-pointer items-center justify-center rounded-full bg-amber-500 px-3 py-1.5 text-xs font-semibold text-white transition-all hover:-translate-y-0.5 hover:bg-amber-600 active:translate-y-0"
                  >
                    Повторить
                  </button>
                </div>
              )}

              {isLoadingChats && chats.length === 0 && (
                <div className={isDark ? "px-2 pt-10 text-center text-sm text-slate-500" : "px-2 pt-10 text-center text-sm text-slate-400"}>
                  Загружаем чаты...
                </div>
              )}

              {Object.entries(groupedChats).map(([groupLabel, groupChats]) => (
                <div key={groupLabel} className="mb-4">
                  <div className="mb-2 px-2 text-[10px] font-bold uppercase tracking-[0.18em] text-slate-400">
                    {groupLabel}
                  </div>
                  <div className="space-y-1">
                    {groupChats.map((chat) => (
                      <ChatItem
                        key={chat.id}
                        chat={chat}
                        isActive={chat.id === activeChatId}
                        isDark={isDark}
                        onSelect={() => { onSelectChat(chat.id); onClose(); }}
                        onRename={(newTitle) => onRenameChat(chat.id, newTitle)}
                        onDelete={() => onDeleteChat(chat.id)}
                      />
                    ))}
                  </div>
                </div>
              ))}

              {!isLoadingChats && filteredChats.length === 0 && (
                <div className={isDark ? "px-2 pt-10 text-center text-sm text-slate-500" : "px-2 pt-10 text-center text-sm text-slate-400"}>
                  {search ? "Ничего не найдено" : "Пока нет сохранённых чатов"}
                </div>
              )}

              {(hasMoreChats || isLoadingMoreChats) && (
                <div className="pt-2">
                  <button
                    type="button"
                    disabled={isLoadingMoreChats}
                    onClick={onLoadMoreChats}
                    className={cn(
                      "flex w-full cursor-pointer items-center justify-center rounded-2xl px-3 py-2.5 text-[13px] font-semibold shadow-[0_10px_24px_rgba(15,23,42,0.04)] transition-all hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:translate-y-0",
                      isDark
                        ? "border border-white/10 bg-white/8 text-slate-200 hover:bg-white/12 disabled:hover:bg-white/8"
                        : "border border-white/70 bg-white/68 text-slate-700 hover:bg-white/82 disabled:hover:bg-white/68"
                    )}
                  >
                    {isLoadingMoreChats ? "Загружаем..." : "Показать ещё"}
                  </button>
                </div>
              )}
            </div>

            <div className={cn("relative z-10 border-t px-4 py-4", isDark ? "border-white/10" : "border-white/55")}>
              <div
                className="flex items-center gap-3 rounded-2xl p-3 shadow-[0_10px_25px_rgba(15,23,42,0.04)] backdrop-blur-xl"
                style={{
                  border: isDark ? "1px solid rgba(255,255,255,0.10)" : "1px solid rgba(255,255,255,0.70)",
                  background: isDark ? "rgba(255,255,255,0.06)" : "rgba(255,255,255,0.58)",
                }}
              >
                <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-[linear-gradient(135deg,#34d399_0%,#14b8a6_100%)] text-sm font-bold text-white shadow-[0_10px_24px_rgba(16,185,129,0.24)]">
                  {userInitial}
                </div>
                <div className="min-w-0">
                  <div className={isDark ? "truncate text-sm font-semibold text-slate-50" : "truncate text-sm font-semibold text-slate-800"}>
                    {userFullName}
                  </div>
                  <div className={isDark ? "truncate text-xs text-slate-400" : "truncate text-xs text-slate-500"}>
                    Пользователь системы
                  </div>
                </div>
              </div>
            </div>
          </>
        ) : (
          <div className="relative z-10 flex flex-1 flex-col items-center justify-center px-6">
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

            <div className="relative z-10 flex flex-col items-center text-center">
              <div
                className="mb-3 flex h-14 w-14 items-center justify-center rounded-2xl"
                style={{
                  border: isDark ? "1px solid rgba(255,255,255,0.10)" : "1px solid rgba(255,255,255,0.60)",
                  background: isDark ? "rgba(255,255,255,0.06)" : "rgba(255,255,255,0.50)",
                }}
              >
                <svg
                  width="24" height="24" viewBox="0 0 24 24"
                  fill="none" stroke="#94a3b8" strokeWidth="1.8"
                  strokeLinecap="round" strokeLinejoin="round"
                >
                  <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                  <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                </svg>
              </div>

              <p className={isDark ? "mb-1 text-[15px] font-semibold text-slate-100" : "mb-1 text-[15px] font-semibold text-slate-700"}>
                Войдите в аккаунт
              </p>
              <p className={isDark ? "mb-5 text-[13px] leading-5 text-slate-500" : "mb-5 text-[13px] leading-5 text-slate-400"}>
                чтобы увидеть историю чатов
              </p>

              <button
                type="button"
                onClick={() => { onLoginClick(); onClose(); }}
                className="flex cursor-pointer items-center justify-center gap-2 rounded-full bg-emerald-500 px-8 py-3 text-[14px] font-semibold text-white shadow-[0_10px_28px_rgba(16,185,129,0.28)] transition-all hover:-translate-y-0.5 hover:bg-emerald-600"
              >
                <svg
                  width="16" height="16" viewBox="0 0 24 24"
                  fill="none" stroke="currentColor" strokeWidth="2.2"
                  strokeLinecap="round" strokeLinejoin="round"
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
