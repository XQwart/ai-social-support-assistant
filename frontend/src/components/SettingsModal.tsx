import { useState } from "react";

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  userName: string;
  onLogout: () => void;
  theme: "light" | "dark";
  onThemeChange: (theme: "light" | "dark") => void;
}

type SettingsTab = "general" | "privacy" | "about";

export default function SettingsModal({
  isOpen,
  onClose,
  userName,
  onLogout,
  theme,
  onThemeChange,
}: SettingsModalProps) {
  const [activeTab, setActiveTab] = useState<SettingsTab>("general");
  const [notifications, setNotifications] = useState(false);
  const isDark = theme === "dark";

  if (!isOpen) return null;

  const tabs: { key: SettingsTab; label: string; icon: React.ReactNode }[] = [
    {
      key: "general",
      label: "Общие",
      icon: (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="3" />
          <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06A1.65 1.65 0 0 0 15 19.4a1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06A2 2 0 1 1 4.29 16.96l.06-.06A1.65 1.65 0 0 0 4.6 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06A2 2 0 1 1 7.04 4.3l.06.06A1.65 1.65 0 0 0 9 4.6a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09A1.65 1.65 0 0 0 15 4.6a1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1Z" />
        </svg>
      ),
    },
    {
      key: "privacy",
      label: "Данные и конфиден...",
      icon: (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
          <path d="M7 11V7a5 5 0 0 1 10 0v4" />
        </svg>
      ),
    },
    {
      key: "about",
      label: "О приложении",
      icon: (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="10" />
          <line x1="12" y1="16" x2="12" y2="12" />
          <line x1="12" y1="8" x2="12.01" y2="8" />
        </svg>
      ),
    },
  ];

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center">
      <div
        className="absolute inset-0 bg-black/30 backdrop-blur-[2px]"
        onClick={onClose}
      />

      <div
        className="relative z-10 mx-4 flex w-full max-w-[720px] overflow-hidden rounded-[24px] shadow-[0_24px_60px_rgba(15,23,42,0.14)] fade-in-up"
        style={{
          background: isDark
            ? "linear-gradient(180deg, rgba(11,31,27,0.96) 0%, rgba(8,24,21,0.92) 100%)"
            : "linear-gradient(180deg, rgba(255,255,255,0.95) 0%, rgba(255,255,255,0.88) 100%)",
          backdropFilter: isDark ? "blur(30px) saturate(140%)" : "blur(30px) saturate(180%)",
          WebkitBackdropFilter: isDark ? "blur(30px) saturate(140%)" : "blur(30px) saturate(180%)",
          border: isDark ? "1px solid #233230" : "1px solid rgba(255,255,255,0.7)",
          height: "560px",
        }}
      >
        <div
          className="flex w-[200px] flex-shrink-0 flex-col p-4"
          style={{
            borderRight: isDark ? "1px solid #233230" : "1px solid rgba(226,232,240,0.8)",
            background: isDark ? "rgba(255,255,255,0.03)" : "rgba(255,255,255,0.3)",
          }}
        >
          <button
            onClick={onClose}
            className="mb-4 flex h-8 w-8 cursor-pointer items-center justify-center rounded-xl text-slate-400 transition-colors hover:bg-slate-100/60 hover:text-slate-600"
            aria-label="Закрыть"
          >
            <svg
              width="18"
              height="18"
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

          <nav className="flex flex-col gap-1">
            {tabs.map((t) => (
              <button
                key={t.key}
                type="button"
                onClick={() => setActiveTab(t.key)}
                className={`flex cursor-pointer items-center gap-2.5 rounded-xl px-3 py-2.5 text-left text-[13px] font-medium transition-all ${
                  activeTab === t.key
                    ? "bg-emerald-500/10 text-emerald-700"
                    : "text-slate-600 hover:bg-slate-100/60"
                }`}
              >
                <span className={activeTab === t.key ? "text-emerald-600" : "text-slate-400"}>
                  {t.icon}
                </span>
                {t.label}
              </button>
            ))}
          </nav>

          <div className="mt-auto pt-4">
            <button
              onClick={onLogout}
              className="flex w-full cursor-pointer items-center gap-2 rounded-xl px-3 py-2.5 text-[13px] font-medium text-rose-500 transition-all hover:bg-rose-50/60"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                <polyline points="16 17 21 12 16 7" />
                <line x1="21" y1="12" x2="9" y2="12" />
              </svg>
              Выйти
            </button>
          </div>
        </div>

        <div className="flex-1 p-6">
          {activeTab === "general" && (
            <>
              <h3 className="mb-6 text-lg font-bold text-slate-800">Общие</h3>

              <div className="space-y-5">
                <div className="flex items-center justify-between">
                  <span className="text-[14px] font-medium text-slate-700">
                    Внешний вид
                  </span>
                  <select
                    value={theme}
                    onChange={(event) => onThemeChange(event.target.value as "light" | "dark")}
                    className="cursor-pointer rounded-xl border bg-white/70 px-4 py-2 text-[13px] text-slate-600 outline-none"
                    style={{
                      borderColor: isDark
                        ? "#233230"
                        : "rgba(148, 163, 184, 0.55)",
                      backgroundColor: isDark ? "rgba(255,255,255,0.04)" : "rgba(255,255,255,0.70)",
                      color: isDark ? "#ecfdf5" : "#475569",
                    }}
                  >
                    <option value="light">Светлая</option>
                    <option value="dark">Тёмная</option>
                  </select>
                </div>

                <div className="h-px bg-slate-100/80" />

                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-[14px] font-medium text-slate-700">
                      Модель ИИ
                    </div>
                    <div className="mt-0.5 text-[12px] text-slate-400">
                      Настройка будет доступна после подключения бэкенда
                    </div>
                  </div>
                  <select
                    className="cursor-pointer rounded-xl border border-slate-200/80 bg-white/70 px-4 py-2 text-[13px] text-slate-600 outline-none"
                    style={{
                      borderColor: isDark ? "#233230" : "rgba(148, 163, 184, 0.55)",
                      backgroundColor: isDark ? "rgba(255,255,255,0.04)" : "rgba(255,255,255,0.70)",
                      color: isDark ? "#ecfdf5" : "#475569",
                    }}
                  >
                    <option>По умолчанию</option>
                  </select>
                </div>

                <div className="h-px bg-slate-100/80" />

                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-[14px] font-medium text-slate-700">
                      Сквозное контекстное меню
                    </div>
                    <div className="mt-0.5 text-[12px] text-slate-400">
                      Использовать единый контекст между чатами
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => setNotifications(!notifications)}
                    className={`relative h-6 w-11 flex-shrink-0 cursor-pointer rounded-full transition-colors ${
                      notifications ? "bg-emerald-500" : "bg-slate-300/70"
                    }`}
                  >
                    <span
                      className={`absolute top-0.5 left-0.5 h-5 w-5 rounded-full bg-white shadow-md transition-transform ${
                        notifications ? "translate-x-5" : "translate-x-0"
                      }`}
                    />
                  </button>
                </div>
              </div>
            </>
          )}

          {activeTab === "privacy" && (
            <>
              <h3 className="mb-6 text-lg font-bold text-slate-800">
                Данные и конфиденциальность
              </h3>

              <div className="space-y-4">
                <div
                  className="rounded-2xl border p-4"
                  style={{
                    borderColor: isDark ? "#233230" : "rgba(226,232,240,0.8)",
                    background: isDark ? "rgba(255,255,255,0.04)" : "rgba(255,255,255,0.50)",
                  }}
                >
                  <div className="text-[14px] font-medium text-slate-700">
                    Аккаунт
                  </div>
                  <div className="mt-1 text-[13px] text-slate-500">
                    {userName}
                  </div>
                </div>

                <div
                  className="rounded-2xl border p-4"
                  style={{
                    borderColor: isDark ? "#233230" : "rgba(226,232,240,0.8)",
                    background: isDark ? "rgba(255,255,255,0.04)" : "rgba(255,255,255,0.50)",
                  }}
                >
                  <div className="text-[14px] font-medium text-slate-700">
                    Политика конфиденциальности
                  </div>
                  <div className="mt-1 text-[13px] text-slate-400">
                    Ссылка будет добавлена позже
                  </div>
                </div>

                <div
                  className="rounded-2xl border p-4"
                  style={{
                    borderColor: isDark ? "#233230" : "rgba(226,232,240,0.8)",
                    background: isDark ? "rgba(255,255,255,0.04)" : "rgba(255,255,255,0.50)",
                  }}
                >
                  <div className="text-[14px] font-medium text-slate-700">
                    Удалить данные
                  </div>
                  <div className="mt-1 text-[13px] text-slate-400">
                    Удалить историю чатов и данные аккаунта
                  </div>
                </div>
              </div>
            </>
          )}

          {activeTab === "about" && (
            <>
              <h3 className="mb-6 text-lg font-bold text-slate-800">
                О приложении
              </h3>

              <div className="space-y-4">
                <div
                  className="rounded-2xl border p-4"
                  style={{
                    borderColor: isDark ? "#233230" : "rgba(226,232,240,0.8)",
                    background: isDark ? "rgba(255,255,255,0.04)" : "rgba(255,255,255,0.50)",
                  }}
                >
                  <div className="text-[14px] font-medium text-slate-700">
                    ИИ-помощник по социальной поддержке
                  </div>
                  <div className="mt-1 text-[13px] text-slate-400">
                    Версия 0.1.0
                  </div>
                </div>

                <div
                  className="rounded-2xl border p-4"
                  style={{
                    borderColor: isDark ? "#233230" : "rgba(226,232,240,0.8)",
                    background: isDark ? "rgba(255,255,255,0.04)" : "rgba(255,255,255,0.50)",
                  }}
                >
                  <div className="text-[14px] font-medium text-slate-700">
                    Разработчики
                  </div>
                  <div className="mt-1 text-[13px] text-slate-400">
                    Команда проекта
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
