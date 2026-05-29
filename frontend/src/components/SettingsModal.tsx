import { useCallback, useEffect, useRef, useState, type ReactNode } from "react";
import DropDown from "@/components/DropDown";
import type { Personality } from "@/api/chatApi";
import { fetchUserMemory, resetUserMemory } from "@/api/userApi";
import { UnauthorizedError } from "@/api/errors";

export type SettingsTab = "privacy" | "personalization" | "about";

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  userName: string;
  placeOfWork: string;
  onLogout: () => void;
  theme: "light" | "dark";
  onThemeChange: (theme: "light" | "dark") => void;
  personality: Personality;
  onPersonalityChange: (personality: Personality) => void;
  onAgreementClick: () => void;
  initialTab?: SettingsTab;
}

const SBERBANK_PLACE_OF_WORK = "ПАО Сбербанк";
const APP_VERSION = "21.5.26";

const DEVELOPERS_LINES: string[] = [];

const DEVELOPERS_DESCRIPTION =
  "Данный проект разработан в рамках проектного практикума студентами УРФУ по задаче ПАО «Сбербанк»";

const THEME_OPTIONS = [
  { value: "light", label: "Светлая" },
  { value: "dark", label: "Тёмная" },
];

const PERSONALITY_OPTIONS: {
  value: Personality;
  label: string;
  description: string;
}[] = [
  {
    value: "default",
    label: "По умолчанию",
    description: "Наиболее предпочтительный тон для большинства пользователей",
  },
  {
    value: "professional",
    label: "Профессиональный",
    description:
      "Тактичный и точный. Даёт максимально чёткие и строгие формулировки прямо по правилам",
  },
  {
    value: "friendly",
    label: "Дружелюбный",
    description:
      "Тёплый и разговорчивый. Использует эмодзи и ведёт себя как друг, который хочет помочь",
  },
];

export default function SettingsModal({
  isOpen,
  onClose,
  userName,
  placeOfWork,
  onLogout,
  theme,
  onThemeChange,
  personality,
  onPersonalityChange,
  onAgreementClick,
  initialTab = "privacy",
}: SettingsModalProps) {
  const [activeTab, setActiveTab] = useState<SettingsTab>(initialTab);
  const [memoryText, setMemoryText] = useState<string | null>(null);
  const [memoryStatus, setMemoryStatus] = useState<
    "idle" | "loading" | "ready" | "error"
  >("idle");
  const [memoryError, setMemoryError] = useState<string | null>(null);
  const [isMemoryMenuOpen, setIsMemoryMenuOpen] = useState(false);
  const [isClearingMemory, setIsClearingMemory] = useState(false);
  const memoryMenuRef = useRef<HTMLDivElement>(null);

  const isDark = theme === "dark";
  const isSberEmployee =
    placeOfWork.trim().toLowerCase() === SBERBANK_PLACE_OF_WORK.toLowerCase();

  useEffect(() => {
    if (isOpen) setActiveTab(initialTab);
  }, [isOpen, initialTab]);

  const loadMemory = useCallback(async (signal?: AbortSignal) => {
    setMemoryStatus("loading");
    setMemoryError(null);

    try {
      const memory = await fetchUserMemory(signal);

      if (signal?.aborted) return;

      setMemoryText(memory.persistentMemory);
      setMemoryStatus("ready");
    } catch (error) {
      if (signal?.aborted) return;
      if (error instanceof UnauthorizedError) return;

      setMemoryError(
        error instanceof Error ? error.message : "Не удалось загрузить память"
      );
      setMemoryStatus("error");
    }
  }, []);

  useEffect(() => {
    if (!isOpen || activeTab !== "privacy") {
      return;
    }

    const controller = new AbortController();
    void loadMemory(controller.signal);

    return () => controller.abort();
  }, [isOpen, activeTab, loadMemory]);

  useEffect(() => {
    if (!isMemoryMenuOpen) return;

    const handlePointerDown = (event: MouseEvent) => {
      if (
        memoryMenuRef.current &&
        !memoryMenuRef.current.contains(event.target as Node)
      ) {
        setIsMemoryMenuOpen(false);
      }
    };
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setIsMemoryMenuOpen(false);
    };

    document.addEventListener("mousedown", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("mousedown", handlePointerDown);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [isMemoryMenuOpen]);

  const handleClearMemory = useCallback(async () => {
    setIsMemoryMenuOpen(false);
    setIsClearingMemory(true);
    setMemoryError(null);

    try {
      await resetUserMemory();
      setMemoryText(null);
      setMemoryStatus("ready");
    } catch (error) {
      if (error instanceof UnauthorizedError) return;
      setMemoryError(
        error instanceof Error ? error.message : "Не удалось очистить память"
      );
    } finally {
      setIsClearingMemory(false);
    }
  }, []);

  if (!isOpen) return null;

  const tabs: { key: SettingsTab; label: string; mobileLabel: string; icon: ReactNode }[] = [
    {
      key: "privacy",
      label: "Данные и конфиденциальность",
      mobileLabel: "Данные",
      icon: (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M12 3l7 4v5c0 5-3.5 8.5-7 10-3.5-1.5-7-5-7-10V7l7-4Z" />
        </svg>
      ),
    },
    {
      key: "personalization",
      label: "Персонализация",
      mobileLabel: "Настройки",
      icon: (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M20.71 4.63l-1.34-1.34a1 1 0 0 0-1.41 0L9 12.25 11.75 15l8.96-8.96a1 1 0 0 0 0-1.41z" />
          <path d="M6 20h4" />
          <path d="M9 16l-3 3" />
        </svg>
      ),
    },
    {
      key: "about",
      label: "О приложении",
      mobileLabel: "О приложении",
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
  const memoryMenuBg = isDark
    ? "linear-gradient(180deg, rgba(13,42,37,0.99) 0%, rgba(10,32,28,0.99) 100%)"
    : "linear-gradient(180deg, rgba(255,255,255,0.99) 0%, rgba(244,248,246,0.99) 100%)";
  const memoryMenuBorder = isDark ? "rgba(70,98,92,0.75)" : "rgba(226,232,240,0.95)";

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
        <div className={`text-[15px] font-medium ${isDark ? "text-slate-200" : "text-slate-700"}`}>{title}</div>
        {description ? (
          <div className={`mt-1 max-w-[320px] text-[13px] leading-6 ${isDark ? "text-slate-500" : "text-slate-400"}`}>{description}</div>
        ) : null}
      </div>
      <div className="w-full sm:w-auto">{control}</div>
    </div>
  );

  const selectedPersonality =
    PERSONALITY_OPTIONS.find((option) => option.value === personality) ??
    PERSONALITY_OPTIONS[0];

  const renderMemoryBlock = () => (
    <div
      className="mt-3 min-h-[80px] overflow-y-auto rounded-[14px] border px-3 py-2.5"
      style={{
        borderColor: isDark ? "rgba(79,104,98,0.6)" : "rgba(203,213,225,0.8)",
        background: isDark ? "rgba(255,255,255,0.03)" : "rgba(248,250,252,0.9)",
        maxHeight: "160px",
      }}
    >
      {memoryStatus === "loading" ? (
        <div className={`text-[13px] leading-6 ${isDark ? "text-slate-500" : "text-slate-400"}`}>
          Загружаем память…
        </div>
      ) : memoryStatus === "error" ? (
        <div className="space-y-2">
          <div className="text-[13px] leading-6 text-rose-400">
            {memoryError ?? "Не удалось загрузить память"}
          </div>
          <button
            type="button"
            onClick={() => void loadMemory()}
            className={`text-[13px] font-semibold transition-colors ${
              isDark ? "text-emerald-300 hover:text-emerald-200" : "text-emerald-700 hover:text-emerald-600"
            }`}
          >
            Повторить
          </button>
        </div>
      ) : !memoryText ? (
        <div className={`text-[13px] leading-6 ${isDark ? "text-slate-500" : "text-slate-400"}`}>
          Пока ничего не запомнено. Расскажите ассистенту о себе — и он будет
          использовать эти факты в ответах.
        </div>
      ) : (
        <div className={`whitespace-pre-wrap break-words text-[13px] leading-6 ${isDark ? "text-slate-300" : "text-slate-600"}`}>
          {memoryText}
        </div>
      )}
    </div>
  );

  return (
    <div className="fixed inset-0 z-[60] flex items-end justify-center md:items-center">
      <div
        className="absolute inset-0 bg-black/38 backdrop-blur-[3px]"
        onClick={onClose}
      />

      <div
        className="relative z-10 flex w-full max-w-[720px] flex-col overflow-hidden rounded-t-[28px] shadow-[0_24px_60px_rgba(15,23,42,0.18)] fade-in-up md:mx-4 md:h-[520px] md:flex-row md:rounded-[24px]"
        style={{
          background: panelBackground,
          backdropFilter: isDark ? "blur(30px) saturate(130%)" : "blur(30px) saturate(165%)",
          WebkitBackdropFilter: isDark ? "blur(30px) saturate(130%)" : "blur(30px) saturate(165%)",
          border: panelBorder,
          maxHeight: "88dvh",
        }}
      >
        <div
          className="flex shrink-0 flex-col pb-0 pt-2 md:w-[220px] md:border-r md:p-4 md:pt-4"
          style={{
            borderRightColor: dividerColor,
            background: isDark ? "rgba(255,255,255,0.025)" : "rgba(255,255,255,0.32)",
          }}
        >
          <div className="mb-2 flex items-center justify-between px-4 md:hidden">
            <div className="h-1.5 w-[52px] rounded-full bg-white/20" />
            <button
              onClick={onClose}
              className={`flex h-8 w-8 cursor-pointer items-center justify-center rounded-xl border transition-all duration-200 hover:-translate-y-0.5 active:translate-y-0 ${
                isDark
                  ? "border-white/10 bg-white/6 text-slate-300 shadow-[inset_0_1px_0_rgba(255,255,255,0.04)] hover:text-slate-100"
                  : "border-white/60 bg-white/45 text-slate-500 hover:text-slate-600"
              }`}
              aria-label="Закрыть"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M18 6L6 18" />
                <path d="M6 6L18 18" />
              </svg>
            </button>
          </div>

          <div className="mb-3 hidden items-center justify-start md:flex md:mb-4 md:px-0">
            <button
              onClick={onClose}
              className={`flex h-9 w-9 cursor-pointer items-center justify-center rounded-xl border transition-all duration-200 hover:-translate-y-0.5 active:translate-y-0 ${
                isDark
                  ? "border-white/10 bg-white/6 text-slate-300 shadow-[inset_0_1px_0_rgba(255,255,255,0.04)] hover:text-slate-100"
                  : "border-white/60 bg-white/45 text-slate-500 hover:text-slate-600"
              }`}
              aria-label="Закрыть"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M18 6L6 18" />
                <path d="M6 6L18 18" />
              </svg>
            </button>
          </div>

          <nav className="flex px-3 pb-2 md:mx-0 md:flex-col md:gap-0.5 md:overflow-visible md:px-0 md:pb-0">
            {tabs.map((tab) => {
              const isActive = activeTab === tab.key;
              return (
                <button
                  key={tab.key}
                  type="button"
                  onClick={() => setActiveTab(tab.key)}
                  className={`flex flex-1 cursor-pointer flex-col items-center gap-1 rounded-[14px] px-2 py-2 text-center text-[11px] font-medium transition-all md:h-10 md:w-full md:flex-row md:gap-2.5 md:rounded-xl md:px-3 md:py-0 md:text-left md:text-[13px] ${
                    isActive
                      ? isDark
                        ? "text-emerald-300"
                        : "text-emerald-700"
                      : isDark
                        ? "text-slate-400 hover:text-slate-200"
                        : "text-slate-500 hover:text-slate-700"
                  }`}
                  style={{
                    background: isActive
                      ? isDark
                        ? "rgba(52,211,153,0.12)"
                        : "rgba(15,118,110,0.09)"
                      : "transparent",
                  }}
                >
                  <span
                    className="shrink-0"
                    style={{
                      color: isActive
                        ? isDark ? "#34d399" : "#0d9488"
                        : isDark ? "#64748b" : "#94a3b8",
                    }}
                  >
                    {tab.icon}
                  </span>
                  <span className="leading-tight md:truncate md:whitespace-nowrap">
                    <span className="md:hidden">{tab.mobileLabel}</span>
                    <span className="hidden md:inline">{tab.label}</span>
                  </span>
                </button>
              );
            })}
          </nav>

          <div
            className="mt-1 block h-px md:hidden"
            style={{ background: dividerColor }}
          />

          <div className="hidden md:mt-auto md:block md:pt-4">
            <button
              onClick={onLogout}
              className={`flex w-full cursor-pointer items-center gap-2 rounded-xl px-3 py-2.5 text-[13px] font-medium text-rose-500 transition-all ${
                isDark ? "hover:bg-rose-500/10" : "hover:bg-rose-50/60"
              }`}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                <polyline points="16 17 21 12 16 7" />
                <line x1="21" y1="12" x2="9" y2="12" />
              </svg>
              Выйти из аккаунта
            </button>
          </div>
        </div>

        <div className="min-h-0 flex-1 overflow-y-auto px-4 pb-5 pt-2 custom-scrollbar md:px-6 md:py-5">
          {activeTab === "personalization" && (
            <>
              <h3 className={`mb-4 hidden text-lg font-bold md:block ${isDark ? "text-slate-50" : "text-slate-800"}`}>Персонализация</h3>

              <div className="space-y-3 pt-1 md:pt-0">
                <div
                  className="rounded-[22px] border p-4"
                  style={{ borderColor: secondaryBorder, background: secondarySurface }}
                >
                  <div className={`text-[15px] font-medium ${isDark ? "text-slate-200" : "text-slate-700"}`}>Внешний вид</div>
                  <div className="mt-3">
                    <DropDown
                      value={theme}
                      onChange={(v) => onThemeChange(v as "light" | "dark")}
                      options={THEME_OPTIONS}
                      isDark={isDark}
                    />
                  </div>
                </div>

                <div
                  className="rounded-[22px] border p-4"
                  style={{ borderColor: secondaryBorder, background: secondarySurface }}
                >
                  <div className={`text-[15px] font-medium ${isDark ? "text-slate-200" : "text-slate-700"}`}>Характер ассистента</div>
                  <div className={`mt-1 text-[13px] leading-6 ${isDark ? "text-slate-500" : "text-slate-400"}`}>
                    {selectedPersonality.description}
                  </div>
                  <div className="mt-3">
                    <DropDown
                      value={personality}
                      onChange={(v) => onPersonalityChange(v as Personality)}
                      options={PERSONALITY_OPTIONS.map(({ value, label }) => ({
                        value,
                        label,
                      }))}
                      isDark={isDark}
                    />
                  </div>
                </div>
              </div>
            </>
          )}

          {activeTab === "privacy" && (
            <>
              <h3 className={`mb-4 hidden text-lg font-bold md:block ${isDark ? "text-slate-50" : "text-slate-800"}`}>Данные и конфиденциальность</h3>

              <div className="space-y-3 pt-1 md:pt-0">
                <div
                  className="rounded-[22px] border p-4"
                  style={{ borderColor: secondaryBorder, background: secondarySurface }}
                >
                  <div className={`text-[15px] font-medium ${isDark ? "text-slate-200" : "text-slate-700"}`}>Аккаунт</div>
                  <div className={`mt-1 text-[13px] leading-6 ${isDark ? "text-slate-500" : "text-slate-400"}`}>{userName}</div>
                </div>

                <div
                  className="flex items-start justify-between gap-4 rounded-[22px] border p-4"
                  style={{ borderColor: secondaryBorder, background: secondarySurface }}
                >
                  <div className="min-w-0">
                    <div className={`text-[15px] font-medium ${isDark ? "text-slate-200" : "text-slate-700"}`}>
                      Статус сотрудника Сбербанка
                    </div>
                    <div className={`mt-1 text-[13px] leading-6 ${isDark ? "text-slate-500" : "text-slate-400"}`}>
                      {isSberEmployee
                        ? `Место работы: ${placeOfWork}`
                        : "Пользователь не является сотрудником ПАО Сбербанк"}
                    </div>
                  </div>
                  <span
                    className={`shrink-0 rounded-full px-3 py-1 text-[12px] font-semibold ${
                      isSberEmployee
                        ? isDark
                          ? "bg-emerald-500/15 text-emerald-300"
                          : "bg-emerald-100 text-emerald-700"
                        : isDark
                          ? "bg-white/[0.06] text-slate-300"
                          : "bg-slate-200/70 text-slate-600"
                    }`}
                  >
                    {isSberEmployee ? "Сотрудник" : "Не сотрудник"}
                  </span>
                </div>

                <div
                  ref={memoryMenuRef}
                  className="relative rounded-[22px] border p-4"
                  style={{ borderColor: secondaryBorder, background: secondarySurface }}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0 flex-1">
                      <div className={`text-[15px] font-medium ${isDark ? "text-slate-200" : "text-slate-700"}`}>
                        Память о пользователе
                      </div>
                      <div className={`mt-1 text-[12px] leading-5 ${isDark ? "text-slate-500" : "text-slate-400"}`}>
                        Факты, которые ассистент сохранил для персонализации ответов
                      </div>
                    </div>

                    <button
                      type="button"
                      onClick={() => setIsMemoryMenuOpen((prev) => !prev)}
                      disabled={isClearingMemory}
                      aria-haspopup="menu"
                      aria-expanded={isMemoryMenuOpen}
                      aria-label="Действия с памятью"
                      className={`flex h-8 w-8 shrink-0 cursor-pointer items-center justify-center rounded-full transition-colors disabled:cursor-not-allowed disabled:opacity-50 ${
                        isDark
                          ? "text-slate-300 hover:bg-white/10"
                          : "text-slate-500 hover:bg-slate-200/70"
                      }`}
                    >
                      <svg
                        width="18"
                        height="18"
                        viewBox="0 0 24 24"
                        fill="currentColor"
                      >
                        <circle cx="5" cy="12" r="1.8" />
                        <circle cx="12" cy="12" r="1.8" />
                        <circle cx="19" cy="12" r="1.8" />
                      </svg>
                    </button>

                    {isMemoryMenuOpen && (
                      <div
                        role="menu"
                        className="absolute right-3 top-12 z-20 min-w-[200px] overflow-hidden rounded-[16px] py-1.5 shadow-[0_16px_40px_rgba(15,23,42,0.18)]"
                        style={{
                          background: memoryMenuBg,
                          border: `1px solid ${memoryMenuBorder}`,
                        }}
                      >
                        <button
                          type="button"
                          role="menuitem"
                          onClick={() => void handleClearMemory()}
                          disabled={isClearingMemory || !memoryText}
                          className="flex w-full cursor-pointer items-center gap-2 px-4 py-2.5 text-left text-[14px] font-medium text-rose-500 transition-colors hover:bg-rose-500/10 disabled:cursor-not-allowed disabled:opacity-50"
                        >
                          <svg
                            width="16"
                            height="16"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
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
                          {isClearingMemory ? "Очистка…" : "Очистить память"}
                        </button>
                      </div>
                    )}
                  </div>

                  {renderMemoryBlock()}
                </div>

                <button
                  type="button"
                  onClick={onAgreementClick}
                  className={`w-full rounded-[22px] border p-4 text-left transition-all hover:-translate-y-0.5 hover:shadow-[0_12px_28px_rgba(16,185,129,0.12)] ${
                    isDark ? 'hover:bg-emerald-500/8' : 'hover:bg-emerald-500/6'
                  }`}
                  style={{ 
                    borderColor: secondaryBorder, 
                    background: secondarySurface
                  }}
                >
                  <div className={`text-[15px] font-medium ${isDark ? "text-emerald-400" : "text-emerald-700"}`}>
                    Пользовательское соглашение
                  </div>
                  <div className={`mt-1 text-[13px] leading-6 ${isDark ? "text-slate-500" : "text-slate-400"}`}>
                    Прочитать условия использования сервиса
                  </div>
                </button>
              </div>
            </>
          )}

          {activeTab === "about" && (
            <>
              <h3 className={`mb-4 hidden text-lg font-bold md:block ${isDark ? "text-slate-50" : "text-slate-800"}`}>О приложении</h3>

              <div className="space-y-3 pt-1 md:pt-0">
                <div
                  className="rounded-[22px] border p-4"
                  style={{ borderColor: secondaryBorder, background: secondarySurface }}
                >
                  <div className={`text-[15px] font-medium ${isDark ? "text-slate-200" : "text-slate-700"}`}>
                    ИИ-помощник по социальной поддержке
                  </div>
                  <div className={`mt-1 text-[13px] leading-6 ${isDark ? "text-slate-500" : "text-slate-400"}`}>
                    Версия {APP_VERSION}
                  </div>
                </div>

                <div
                  className="rounded-[22px] border p-4"
                  style={{ borderColor: secondaryBorder, background: secondarySurface }}
                >
                  <div className={`text-[15px] font-medium ${isDark ? "text-slate-200" : "text-slate-700"}`}>
                    Справка
                  </div>
                  <div className={`mt-1 text-[13px] leading-6 ${isDark ? "text-slate-500" : "text-slate-400"}`}>
                    {DEVELOPERS_DESCRIPTION}
                  </div>
                  <ul className={`mt-2 space-y-1 text-[13px] leading-6 ${isDark ? "text-slate-300" : "text-slate-600"}`}>
                    {DEVELOPERS_LINES.map((line) => (
                      <li key={line}>{line}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </>
          )}

        </div>

        <div
          className="shrink-0 px-4 pb-[max(env(safe-area-inset-bottom),1rem)] pt-3 md:hidden"
          style={{ borderTop: `1px solid ${dividerColor}` }}
        >
          <button
            onClick={onLogout}
            className={`flex h-12 w-full cursor-pointer items-center justify-center rounded-[18px] border text-[15px] font-semibold text-rose-400 transition-all ${
              isDark ? "hover:bg-rose-500/10" : "hover:bg-rose-50/80"
            }`}
            style={{
              borderColor: "rgba(251, 113, 133, 0.18)",
              background: isDark ? "rgba(255,255,255,0.03)" : "rgba(255,255,255,0.75)",
            }}
          >
            Выйти из аккаунта
          </button>
        </div>
      </div>
    </div>
  );
}
