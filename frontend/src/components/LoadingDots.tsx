import { useEffect, useState } from "react";

const FUN_STATUSES = [
  "Ищем ответ в базе знаний...",
  "Бежим к юристу...",
  "Проверяем документы...",
  "Стоим в очереди в МФЦ...",
  "Листаем законодательство...",
  "Консультируемся со специалистом...",
  "Разбираемся в льготах...",
  "Изучаем нормативные акты...",
  "Проверяем актуальность данных...",
  "Подбираем меры поддержки...",
  "Сверяемся с Госуслугами...",
  "Считаем размер выплат...",
  "Уточняем требования...",
  "Готовим ответ...",
];

export default function LoadingDots() {
  const [statusIndex, setStatusIndex] = useState(() =>
    Math.floor(Math.random() * FUN_STATUSES.length)
  );
  const [isTransitioning, setIsTransitioning] = useState(false);

  useEffect(() => {
    const interval = setInterval(() => {
      setIsTransitioning(true);

      setTimeout(() => {
        setStatusIndex((prev) => {
          let next = Math.floor(Math.random() * FUN_STATUSES.length);
          // Не повторяем тот же статус
          while (next === prev && FUN_STATUSES.length > 1) {
            next = Math.floor(Math.random() * FUN_STATUSES.length);
          }
          return next;
        });
        setIsTransitioning(false);
      }, 300);
    }, 2500);

    return () => clearInterval(interval);
  }, []);

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

          <div
            className="min-w-[180px] text-[14px] text-slate-500 transition-opacity duration-300"
            style={{ opacity: isTransitioning ? 0 : 1 }}
          >
            {FUN_STATUSES[statusIndex]}
          </div>

          <div className="mt-1.5 flex items-center gap-1.5 py-0.5">
            <span className="loading-dot" />
            <span className="loading-dot" style={{ animationDelay: "140ms" }} />
            <span className="loading-dot" style={{ animationDelay: "280ms" }} />
          </div>
        </div>
      </div>
    </div>
  );
}
