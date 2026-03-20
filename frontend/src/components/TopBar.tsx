interface TopBarProps {
  onToggleSidebar: () => void;
  onSettingsClick: () => void;
  onProfileClick: () => void;
  userInitial?: string;
}

export default function TopBar({
  onToggleSidebar,
  onSettingsClick,
  onProfileClick,
  userInitial = "П",
}: TopBarProps) {
  return (
    <div className="pointer-events-none absolute left-0 right-0 top-0 z-30 px-3 py-3 md:px-4 md:py-4">
      <div className="flex items-center justify-between">
        <button
          type="button"
          onClick={onToggleSidebar}
          className="pointer-events-auto inline-flex h-11 w-11 items-center justify-center rounded-2xl border border-white/70 bg-white/58 text-slate-600 shadow-[0_8px_24px_rgba(15,23,42,0.05)] backdrop-blur-2xl transition-all hover:-translate-y-0.5 hover:bg-white/78 cursor-pointer"
          aria-label="Открыть меню"
        >
          <svg
            width="19"
            height="19"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.1"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M3 6H21" />
            <path d="M3 12H16" />
            <path d="M3 18H18" />
          </svg>
        </button>

        <div className="pointer-events-auto ml-auto flex items-center gap-2">
          <button
            type="button"
            onClick={onSettingsClick}
            className="inline-flex h-11 w-11 items-center justify-center rounded-2xl border border-white/70 bg-white/58 text-slate-600 shadow-[0_8px_24px_rgba(15,23,42,0.05)] backdrop-blur-2xl transition-all hover:-translate-y-0.5 hover:bg-white/78 cursor-pointer"
            aria-label="Настройки"
          >
            <svg
              width="19"
              height="19"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.9"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <circle cx="12" cy="12" r="3" />
              <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06A1.65 1.65 0 0 0 15 19.4a1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06A2 2 0 1 1 4.29 16.96l.06-.06A1.65 1.65 0 0 0 4.6 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06A2 2 0 1 1 7.04 4.3l.06.06A1.65 1.65 0 0 0 9 4.6a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09A1.65 1.65 0 0 0 15 4.6a1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1Z" />
            </svg>
          </button>

          <button
            type="button"
            onClick={onProfileClick}
            className="inline-flex h-11 w-11 items-center justify-center rounded-full bg-[linear-gradient(135deg,#34d399_0%,#14b8a6_100%)] text-sm font-bold text-white shadow-[0_10px_28px_rgba(16,185,129,0.28)] transition-transform hover:scale-[1.03] active:scale-[0.98] cursor-pointer"
            aria-label="Профиль"
          >
            {userInitial}
          </button>
        </div>
      </div>
    </div>
  );
}
