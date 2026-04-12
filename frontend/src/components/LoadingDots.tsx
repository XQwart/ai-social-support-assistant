import { useEffect, useRef, useState } from "react";

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

const usedStatusIndicesByChat = new Map<string, Set<number>>();

function getChatStatusStore(chatId: string): Set<number> {
  const existing = usedStatusIndicesByChat.get(chatId);
  if (existing) {
    return existing;
  }

  const next = new Set<number>();
  usedStatusIndicesByChat.set(chatId, next);
  return next;
}

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

interface LoadingDotsProps {
  chatId: string;
}

export default function LoadingDots({ chatId }: LoadingDotsProps) {
  const usedInChatRef = useRef<Set<number>>(getChatStatusStore(chatId));
  const previousChatIdRef = useRef(chatId);

  const [statusIndex, setStatusIndex] = useState(() => {
    usedInChatRef.current = getChatStatusStore(chatId);
    return pickNextStatusIndex(-1, usedInChatRef.current);
  });
  const [isTransitioning, setIsTransitioning] = useState(false);

  useEffect(() => {
    if (previousChatIdRef.current === chatId) {
      return;
    }

    previousChatIdRef.current = chatId;
    usedInChatRef.current = getChatStatusStore(chatId);
    setStatusIndex((prev) => pickNextStatusIndex(prev, usedInChatRef.current));
    setIsTransitioning(false);
  }, [chatId]);

  useEffect(() => {
    let transitionTimeoutId: number | null = null;

    const interval = setInterval(() => {
      setIsTransitioning(true);

      transitionTimeoutId = window.setTimeout(() => {
        setStatusIndex((prev) => pickNextStatusIndex(prev, usedInChatRef.current));
        setIsTransitioning(false);
      }, TRANSITION_DURATION_MS);
    }, STATUS_INTERVAL_MS);

    return () => {
      clearInterval(interval);
      if (transitionTimeoutId !== null) {
        window.clearTimeout(transitionTimeoutId);
      }
    };
  }, []);

  return (
    <div className="fade-in-up flex w-full justify-start">
      <div className="flex max-w-[88%] items-start md:max-w-[78%]">
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
