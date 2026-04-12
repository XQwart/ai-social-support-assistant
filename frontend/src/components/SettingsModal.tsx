import { useState, type ReactNode } from "react";

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

  const tabs: { key: SettingsTab; label: string; icon: ReactNode }[] = [
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
      label: "Данные и конфиденциальность",
      icon: (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M12 3l7 4v5c0 5-3.5 8.5-7 10-3.5-1.5-7-5-7-10V7l7-4Z" />
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

  const panelBackground = isDark
    ? "linear-gradient(180deg, rgba(13,42,37,0.98) 0%, rgba(10,32,28,0.98) 100%)"
    : "linear-gradient(180deg, rgba(255,255,255,0.98) 0%, rgba(244,248,246,0.98) 100%)";

  const panelBorder = isDark ? "1px solid rgba(70, 98, 92, 0.75)" : "1px solid rgba(226,232,240,0.95)";
  const secondarySurface = isDark ? "rgba(255,255,255,0.05)" : "rgba(248,250,252,0.92)";
  const secondaryBorder = isDark ? "rgba(79, 104, 98, 0.8)" : "rgba(203,213,225,0.9)";
  const dividerColor = isDark ? "rgba(73, 97, 91, 0.7)" : "rgba(226,232,240,0.95)";
  const renderRow = (
    title: string,
    description: string | null,
    control: ReactNode,
    stacked = false
  ) => (
    <div
      className={`flex gap-4 py-5 ${stacked ? "flex-col items-start" : "flex-col items-start sm:flex-row sm:items-center sm:justify-between"}`}
      style={{ borderTop: `1px solid ${dividerColor}` }}
    >
      <div className="min-w-0 flex-1">
        <div className="text-[15px] font-medium text-slate-700">{title}</div>
        {description ? (
          <div className="mt-1 max-w-[320px] text-[13px] leading-6 text-slate-400">{description}</div>
        ) : null}
      </div>
      <div className="w-full sm:w-auto">{control}</div>
    </div>
  );

  return (
    <div className="fixed inset-0 z-[60] flex items-end justify-center md:items-center">
      <div
        className="absolute inset-0 bg-black/38 backdrop-blur-[3px]"
        onClick={onClose}
      />

      <div
        className="relative z-10 flex w-full max-w-[720px] flex-col overflow-hidden rounded-t-[28px] shadow-[0_24px_60px_rgba(15,23,42,0.18)] fade-in-up md:mx-4 md:h-[560px] md:flex-row md:rounded-[24px]"
        style={{
          background: panelBackground,
          backdropFilter: isDark ? "blur(30px) saturate(130%)" : "blur(30px) saturate(165%)",
          WebkitBackdropFilter: isDark ? "blur(30px) saturate(130%)" : "blur(30px) saturate(165%)",
          border: panelBorder,
          maxHeight: "92vh",
        }}
      >
        <div
          className="flex shrink-0 flex-col px-4 pb-0 pt-3 md:w-[248px] md:border-r md:p-4 lg:w-[220px]"
          style={{
            borderRightColor: dividerColor,
            background: isDark ? "rgba(255,255,255,0.025)" : "rgba(255,255,255,0.32)",
          }}
        >
          <div className="mx-auto mb-4 h-1.5 w-[52px] rounded-full bg-white/20 md:hidden" />

          <div className="mb-4 flex items-center justify-between md:mb-6 md:block">
            <div className="text-[19px] font-semibold text-slate-800 md:mb-6">Настройки</div>
            <button
              onClick={onClose}
              className="flex h-10 w-10 cursor-pointer items-center justify-center rounded-full text-slate-400 transition-colors hover:bg-white/8 hover:text-slate-200 md:h-8 md:w-8 md:rounded-xl md:hover:bg-slate-100/60 md:hover:text-slate-600"
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
          </div>

          <nav className="-mx-1 mb-1 flex gap-2 overflow-x-auto px-1 pb-2 md:mx-0 md:flex-col md:gap-1 md:overflow-visible md:px-0 md:pb-0">
            {tabs.map((tab) => {
              const isActive = activeTab === tab.key;
              return (
                <button
                  key={tab.key}
                  type="button"
                  onClick={() => setActiveTab(tab.key)}
                  className={`flex min-w-fit shrink-0 cursor-pointer items-center gap-2.5 rounded-[18px] px-4 py-3 text-left text-[13px] font-medium transition-all md:w-full md:min-w-0 md:shrink md:rounded-xl md:px-3 md:py-2.5 ${
                    isActive
                      ? isDark
                        ? "text-white md:text-emerald-700"
                        : "text-slate-700 md:text-emerald-700"
                      : isDark
                        ? "text-white/55 md:text-slate-600"
                        : "text-slate-500 md:text-slate-600"
                  }`}
                  style={{
                    background: isActive
                      ? isDark
                        ? "rgba(255,255,255,0.08)"
                        : "rgba(15, 118, 110, 0.12)"
                      : "transparent",
                  }}
                >
                  <span
                    className={
                      isActive
                        ? isDark
                          ? "text-white md:text-emerald-600"
                          : "text-emerald-700 md:text-emerald-600"
                        : isDark
                          ? "text-white/50 md:text-slate-400"
                          : "text-slate-400"
                    }
                  >
                    {tab.icon}
                  </span>
                  <span className="max-w-[160px] truncate whitespace-nowrap md:max-w-none md:whitespace-normal md:break-words md:leading-5">
                    {tab.label}
                  </span>
                </button>
              );
            })}
          </nav>

          <div className="hidden md:mt-auto md:block md:pt-4">
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

        <div className="flex-1 overflow-y-auto px-5 pb-6 pt-2 md:px-6 md:py-6">
          {activeTab === "general" && (
            <>
              <h3 className="mb-4 hidden text-lg font-bold text-slate-800 md:block">Общие</h3>

              {renderRow(
                "Внешний вид",
                null,
                <select
                  value={theme}
                  onChange={(event) => onThemeChange(event.target.value as "light" | "dark")}
                  className="h-12 w-full cursor-pointer rounded-[18px] border px-4 text-[15px] font-semibold outline-none sm:w-auto sm:min-w-[118px]"
                  style={{
                    borderColor: secondaryBorder,
                    backgroundColor: secondarySurface,
                    color: isDark ? "#d4e3df" : "#475569",
                  }}
                >
                  <option value="light">Светлая</option>
                  <option value="dark">Тёмная</option>
                </select>
              )}

              {renderRow(
                "Модель ИИ",
                "Настройка будет доступна после подключения бэкенда",
                <select
                  className="min-h-12 w-full cursor-pointer rounded-[18px] border px-4 py-2 text-[15px] font-semibold outline-none sm:w-auto sm:min-w-[160px]"
                  style={{
                    borderColor: secondaryBorder,
                    backgroundColor: secondarySurface,
                    color: isDark ? "#d4e3df" : "#475569",
                  }}
                >
                  <option>По умолчанию</option>
                </select>
              )}

              {renderRow(
                "Сквозное контекстное меню",
                "Использовать единый контекст между чатами",
                <button
                  type="button"
                  onClick={() => setNotifications(!notifications)}
                  className={`relative h-7 w-12 flex-shrink-0 cursor-pointer rounded-full transition-colors ${
                    notifications ? "bg-emerald-500" : "bg-slate-300/70"
                  }`}
                >
                  <span
                    className={`absolute top-0.5 left-0.5 h-6 w-6 rounded-full bg-white shadow-md transition-transform ${
                      notifications ? "translate-x-5" : "translate-x-0"
                    }`}
                  />
                </button>,
                true
              )}
            </>
          )}

          {activeTab === "privacy" && (
            <>
              <h3 className="mb-4 hidden text-lg font-bold text-slate-800 md:block">Данные и конфиденциальность</h3>

              <div className="space-y-3 pt-1 md:pt-0">
                {[
                  ["Аккаунт", userName],
                  ["Политика конфиденциальности", "Ссылка будет добавлена позже"],
                  ["Удалить данные", "Удалить историю чатов и данные аккаунта"],
                ].map(([title, description]) => (
                  <div
                    key={title}
                    className="rounded-[22px] border p-4"
                    style={{
                      borderColor: secondaryBorder,
                      background: secondarySurface,
                    }}
                  >
                    <div className="text-[15px] font-medium text-slate-700">{title}</div>
                    <div className="mt-1 text-[13px] leading-6 text-slate-400">{description}</div>
                  </div>
                ))}
              </div>
            </>
          )}

          {activeTab === "about" && (
            <>
              <h3 className="mb-4 hidden text-lg font-bold text-slate-800 md:block">О приложении</h3>

              <div className="space-y-3 pt-1 md:pt-0">
                {[
                  ["ИИ-помощник по социальной поддержке", "Версия 0.1.0"],
                  ["Разработчики", "Команда проекта"],
                ].map(([title, description]) => (
                  <div
                    key={title}
                    className="rounded-[22px] border p-4"
                    style={{
                      borderColor: secondaryBorder,
                      background: secondarySurface,
                    }}
                  >
                    <div className="text-[15px] font-medium text-slate-700">{title}</div>
                    <div className="mt-1 text-[13px] leading-6 text-slate-400">{description}</div>
                  </div>
                ))}
              </div>
            </>
          )}

          <div className="pt-5 md:hidden">
            <button
              onClick={onLogout}
              className="flex h-12 w-full cursor-pointer items-center justify-center rounded-[18px] border text-[15px] font-semibold text-rose-400 transition-all"
              style={{
                borderColor: "rgba(251, 113, 133, 0.18)",
                background: isDark ? "rgba(255,255,255,0.03)" : "rgba(255,255,255,0.75)",
              }}
            >
              Выйти
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
