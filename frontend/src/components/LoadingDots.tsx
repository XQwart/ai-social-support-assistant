export default function LoadingDots() {
  return (
    <div className="fade-in-up flex w-full justify-start">
      <div className="flex max-w-[88%] items-start gap-3 md:max-w-[78%]">
        <div className="mt-1 flex h-9 w-9 shrink-0 items-center justify-center rounded-2xl border border-white/70 bg-white/70 text-xs font-semibold text-emerald-600 shadow-[0_6px_18px_rgba(15,23,42,0.05)] backdrop-blur-xl">
          ИИ
        </div>

        <div className="rounded-[24px] rounded-bl-[8px] border border-white/80 bg-white/74 px-4 py-3.5 text-slate-800 shadow-[0_10px_30px_rgba(15,23,42,0.05)] backdrop-blur-2xl">
          <div className="mb-1 text-[11px] font-semibold uppercase tracking-[0.12em] text-emerald-600/90">
            Помощник
          </div>

          <div className="flex items-center gap-1.5 py-1">
            <span className="loading-dot" />
            <span className="loading-dot" style={{ animationDelay: "140ms" }} />
            <span className="loading-dot" style={{ animationDelay: "280ms" }} />
          </div>
        </div>
      </div>
    </div>
  );
}
