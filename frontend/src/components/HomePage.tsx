import AppDisclaimer from "@/components/AppDisclaimer";
import ChatInput from "@/components/ChatInput";

interface HomePageProps {
  onSend: (message: string) => Promise<boolean>;
  isLoading: boolean;
  isAuthenticated: boolean;
  onAuthRequired: () => void;
  theme: "light" | "dark";
}

const POPULAR_QUESTIONS = [
  "Узнать, какие мне полагаются льготы",
  "Как оформить субсидию на ЖКХ?",
  "Какие выплаты положены при рождении ребёнка?",
  "Как получить статус малоимущей семьи?",
  "Как оформить пенсию по инвалидности?",
];

export default function HomePage({
  onSend,
  isLoading,
  isAuthenticated,
  onAuthRequired,
  theme,
}: HomePageProps) {
  const handleQuestionClick = (question: string) => {
    if (!isAuthenticated) {
      onAuthRequired();
      return;
    }
    if (isLoading) return;
    void onSend(question);
  };

  const isDark = theme === "dark";

  return (
    <div className="relative flex flex-1 flex-col overflow-x-hidden overflow-y-auto px-4 pb-4 pt-[70px] sm:pb-20 sm:pt-28">
      <div className="hero-aurora-wrap" aria-hidden="true">
        <div className="hero-aurora hero-aurora-one" />
        <div className="hero-aurora hero-aurora-two" />
        <div className="hero-aurora hero-aurora-three" />
      </div>

      <div className="relative z-10 flex flex-1 flex-col items-center sm:justify-center">

        <div className="flex w-full flex-1 flex-col items-center justify-center text-center sm:flex-none">
          <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-white/70 bg-white/56 px-4 py-2 text-xs font-medium text-slate-600 shadow-[0_6px_20px_rgba(15,23,42,0.04)] backdrop-blur-xl">
            <span className="inline-block h-2 w-2 rounded-full bg-emerald-400 shadow-[0_0_10px_rgba(16,185,129,0.5)]" />
            ИИ-помощник по социальной поддержке
          </div>

          <h1 className="mx-auto max-w-4xl text-balance text-[26px] font-black leading-[1.1] tracking-[-0.045em] text-slate-900 sm:text-[40px] md:text-[64px]">
            Остались вопросы?
            <br />
            <span className="text-slate-900">Спросите у нас</span>
          </h1>

          <p className="mx-auto mt-2 max-w-2xl text-balance text-[13px] leading-5 text-slate-600 sm:mt-3 sm:text-[15px] sm:leading-7 md:mt-5 md:text-base">
            Подскажем по льготам, пособиям, субсидиям, инвалидности, выплатам
            семьям с детьми и другим мерам социальной поддержки.
          </p>
        </div>

        <div className="w-full sm:mt-9">

          <div className="relative mb-3 w-full sm:hidden">
            <div className="no-scrollbar flex gap-2 overflow-x-auto px-1 pb-2 pt-0.5">
              {POPULAR_QUESTIONS.map((question) => (
                <button
                  key={question}
                  type="button"
                  disabled={isLoading}
                  onClick={() => handleQuestionClick(question)}
                  className="shrink-0 cursor-pointer rounded-full border border-white/78 bg-white/64 px-4 py-2.5 text-[12px] font-medium text-slate-700 shadow-[0_4px_18px_rgba(15,23,42,0.035)] backdrop-blur-xl transition-all active:scale-[0.97] disabled:cursor-not-allowed disabled:opacity-55"
                >
                  {question}
                </button>
              ))}
            </div>
            <div
              className="pointer-events-none absolute right-0 top-0 h-full w-12"
              style={{
                background: isDark
                  ? "linear-gradient(to left, rgba(6,17,15,0.95), transparent)"
                  : "linear-gradient(to left, rgba(237,248,240,0.95), transparent)",
              }}
            />
          </div>

          <ChatInput
            onSend={onSend}
            isLoading={isLoading}
            placeholder="Например: какие пособия мне доступны?"
            mode="hero"
            autoFocus
            isAuthenticated={isAuthenticated}
            onAuthRequired={onAuthRequired}
            theme={theme}
          />

          <div className="mx-auto mt-3 max-w-[300px] sm:hidden">
            <AppDisclaimer className="text-[10px] leading-4" />
          </div>

          <div className="mx-auto mt-8 hidden max-w-3xl flex-wrap justify-center gap-2.5 pb-2 sm:flex sm:mt-[2.75rem]">
            {POPULAR_QUESTIONS.map((question) => (
              <button
                key={question}
                type="button"
                disabled={isLoading}
                onClick={() => handleQuestionClick(question)}
                className="cursor-pointer rounded-full border border-white/78 bg-white/64 px-4 py-2.5 text-[13px] font-medium text-slate-700 shadow-[0_4px_18px_rgba(15,23,42,0.035)] backdrop-blur-xl transition-all hover:-translate-y-0.5 hover:bg-white/82 hover:text-slate-900 active:translate-y-0 disabled:cursor-not-allowed disabled:opacity-55 disabled:hover:translate-y-0 disabled:hover:bg-white/64 disabled:hover:text-slate-700"
              >
                {question}
              </button>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
}
