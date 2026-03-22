import AppDisclaimer from "@/components/AppDisclaimer";
import ChatInput from "@/components/ChatInput";

interface HomePageProps {
  onSend: (message: string) => void;
  isLoading: boolean;
  isAuthenticated: boolean;
  onAuthRequired: () => void;
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
}: HomePageProps) {
  const handleQuestionClick = (question: string) => {
    if (!isAuthenticated) {
      onAuthRequired();
      return;
    }
    onSend(question);
  };
  return (
    <div className="relative flex flex-1 flex-col overflow-hidden px-4 pt-28">
      <div className="hero-aurora-wrap" aria-hidden="true">
        <div className="hero-aurora hero-aurora-one" />
        <div className="hero-aurora hero-aurora-two" />
        <div className="hero-aurora hero-aurora-three" />
      </div>

      <div className="relative z-10 flex flex-1 flex-col items-center justify-center pb-10">
        <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-white/70 bg-white/56 px-4 py-2 text-xs font-medium text-slate-600 shadow-[0_6px_20px_rgba(15,23,42,0.04)] backdrop-blur-xl">
          <span className="inline-block h-2 w-2 rounded-full bg-emerald-400 shadow-[0_0_10px_rgba(16,185,129,0.5)]" />
          ИИ-помощник по социальной поддержке
        </div>

        <div className="relative mb-10 text-center">
          <h1 className="mx-auto max-w-4xl text-balance text-[40px] font-black leading-[1.04] tracking-[-0.045em] text-slate-900 md:text-[64px]">
            Остались вопросы?
            <br />
            <span className="text-slate-900">Спросите у нас</span>
          </h1>

          <p className="mx-auto mt-5 max-w-2xl text-balance text-[15px] leading-7 text-slate-600 md:text-base">
            Подскажем по льготам, пособиям, субсидиям, инвалидности, выплатам
            семьям с детьми и другим мерам социальной поддержки.
          </p>
        </div>

        <ChatInput
          onSend={onSend}
          isLoading={isLoading}
          placeholder="Например: какие пособия мне доступны?"
          mode="hero"
          autoFocus
          isAuthenticated={isAuthenticated}
          onAuthRequired={onAuthRequired}
        />

        <div className="mt-14 flex max-w-3xl flex-wrap justify-center gap-2.5">
          {POPULAR_QUESTIONS.map((question) => (
            <button
              key={question}
              type="button"
              onClick={() => handleQuestionClick(question)}
              className="cursor-pointer rounded-full border border-white/78 bg-white/64 px-4 py-2.5 text-[13px] font-medium text-slate-700 shadow-[0_4px_18px_rgba(15,23,42,0.035)] backdrop-blur-xl transition-all hover:-translate-y-0.5 hover:bg-white/82 hover:text-slate-900 active:translate-y-0"
            >
              {question}
            </button>
          ))}
        </div>
      </div>

      <AppDisclaimer className="pb-5 md:pb-6" />
    </div>
  );
}
