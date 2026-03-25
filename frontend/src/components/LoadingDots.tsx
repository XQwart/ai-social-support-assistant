import { useEffect, useRef, useState } from "react";

import { AssistantAvatar } from "@/components/AssistantAvatar";

const ROLE_LABEL = "Помощник";

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
  "Пьём кофе перед ответом...",
  "Гуглим за вас...",
  "Спрашиваем у бабушки на лавочке...",
  "Звоним на горячую линию...",
  "Ищем лазейку в законе...",
  "Надеваем очки для чтения мелкого шрифта...",
  "Перелопачиваем кодексы...",
  "Роемся в архивах...",
  "Общаемся с ботом Госуслуг...",
  "Заполняем форму в трёх экземплярах...",
  "Берём талончик в электронной очереди...",
  "Поднимаем судебную практику...",
  "Просим совет у знакомого депутата...",
  "Расшифровываем юридический язык...",
  "Ищем нужный пункт в 400-страничном законе...",
  "Уже почти нашли...",
  "Сканируем все поправки за последний год...",
  "Пробиваемся через бюрократию...",
];

const STATUS_INTERVAL_MS = 2500;
const TRANSITION_DURATION_MS = 300;

function pickNextStatusIndex(prevIndex: number, used: Set<number>): number {
  const n = FUN_STATUSES.length;
  let available = Array.from({ length: n }, (_, i) => i).filter(
    (i) => !used.has(i)
  );

  if (available.length === 0) {
    used.clear();
    available = Array.from({ length: n }, (_, i) => i);
  }

  const pool =
    available.length > 1
      ? available.filter((i) => i !== prevIndex)
      : available;

  const next = pool[Math.floor(Math.random() * pool.length)]!;
  used.add(next);
  return next;
}

export default function LoadingDots() {
  const usedInRequestRef = useRef<Set<number>>(new Set());

  const [statusIndex, setStatusIndex] = useState(() => {
    const n = FUN_STATUSES.length;
    const i = Math.floor(Math.random() * n);
    usedInRequestRef.current = new Set([i]);
    return i;
  });
  const [isTransitioning, setIsTransitioning] = useState(false);

  useEffect(() => {
    const interval = setInterval(() => {
      setIsTransitioning(true);

      setTimeout(() => {
        setStatusIndex((prev) =>
          pickNextStatusIndex(prev, usedInRequestRef.current)
        );
        setIsTransitioning(false);
      }, TRANSITION_DURATION_MS);
    }, STATUS_INTERVAL_MS);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="fade-in-up flex w-full justify-start">
      <div className="flex max-w-[88%] items-start gap-3 md:max-w-[78%]">
        <AssistantAvatar />

        <div className="rounded-[24px] rounded-bl-[8px] border border-white/80 bg-white/74 px-4 py-3.5 text-slate-800 shadow-[0_10px_30px_rgba(15,23,42,0.05)] backdrop-blur-2xl">
          <div className="mb-1 text-[11px] font-semibold tracking-[0.12em] text-emerald-600/90">
            {ROLE_LABEL}
          </div>

          <div
            className="loading-status-text min-w-[180px] text-[14px] font-medium leading-snug transition-opacity duration-300"
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
