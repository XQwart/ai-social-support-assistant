import { useEffect, useRef, useState } from "react";

export interface DropDownOption {
  value: string;
  label: string;
}

interface DropDownProps {
  value: string;
  onChange: (value: string) => void;
  options: DropDownOption[];
  isDark: boolean;
  disabled?: boolean;
  className?: string;
}

export default function DropDown({
  value,
  onChange,
  options,
  isDark,
  disabled = false,
  className = "",
}: DropDownProps) {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isOpen) return;
    const handlePointerDown = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") setIsOpen(false);
    };
    document.addEventListener("mousedown", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("mousedown", handlePointerDown);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen]);

  const selectedLabel = options.find((o) => o.value === value)?.label ?? value;

  const borderColor = isDark ? "rgba(79,104,98,0.8)" : "rgba(203,213,225,0.9)";
  const surfaceColor = isDark ? "rgba(255,255,255,0.05)" : "rgba(248,250,252,0.92)";
  const textColor = isDark ? "#d4e3df" : "#475569";
  const menuBg = isDark
    ? "linear-gradient(180deg, rgba(13,42,37,0.99) 0%, rgba(10,32,28,0.99) 100%)"
    : "linear-gradient(180deg, rgba(255,255,255,0.99) 0%, rgba(244,248,246,0.99) 100%)";
  const menuBorder = isDark ? "rgba(70,98,92,0.75)" : "rgba(226,232,240,0.95)";

  return (
    <div ref={containerRef} className={`relative ${className}`}>
      <button
        type="button"
        disabled={disabled}
        onClick={() => setIsOpen((prev) => !prev)}
        className="flex h-12 w-full cursor-pointer items-center justify-between gap-3 rounded-[18px] border px-4 text-[14px] font-semibold transition-all hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50 sm:min-w-[140px]"
        style={{ borderColor, backgroundColor: surfaceColor, color: textColor }}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
      >
        <span className="truncate">{selectedLabel}</span>
        <svg
          width="14"
          height="14"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          style={{
            flexShrink: 0,
            transform: isOpen ? "rotate(180deg)" : "rotate(0deg)",
            transition: "transform 180ms ease",
          }}
        >
          <path d="m6 9 6 6 6-6" />
        </svg>
      </button>

      {isOpen && (
        <div
          className="absolute right-0 top-[calc(100%+6px)] z-50 min-w-full overflow-hidden rounded-[16px] py-1.5 shadow-[0_16px_40px_rgba(15,23,42,0.18)]"
          style={{ background: menuBg, border: `1px solid ${menuBorder}` }}
          role="listbox"
        >
          {options.map((option) => {
            const isSelected = option.value === value;
            return (
              <button
                key={option.value}
                type="button"
                role="option"
                aria-selected={isSelected}
                onClick={() => {
                  onChange(option.value);
                  setIsOpen(false);
                }}
                className="flex w-full cursor-pointer items-center gap-2.5 px-4 py-2.5 text-[14px] font-medium transition-colors"
                style={{
                  background: isSelected
                    ? isDark
                      ? "rgba(52,211,153,0.12)"
                      : "rgba(52,211,153,0.09)"
                    : "transparent",
                  color: isSelected
                    ? isDark ? "#34d399" : "#059669"
                    : isDark ? "#d4e3df" : "#475569",
                }}
                onMouseEnter={(e) => {
                  if (!isSelected) {
                    (e.currentTarget as HTMLButtonElement).style.background = isDark
                      ? "rgba(255,255,255,0.06)"
                      : "rgba(0,0,0,0.04)";
                  }
                }}
                onMouseLeave={(e) => {
                  if (!isSelected) {
                    (e.currentTarget as HTMLButtonElement).style.background = "transparent";
                  }
                }}
              >
                {isSelected && (
                  <svg
                    width="14"
                    height="14"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    style={{ flexShrink: 0 }}
                  >
                    <path d="M20 6 9 17l-5-5" />
                  </svg>
                )}
                <span style={{ paddingLeft: isSelected ? 0 : "22px" }}>{option.label}</span>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
