import { cn } from "@/utils/cn";

interface AppDisclaimerProps {
  className?: string;
}

export default function AppDisclaimer({ className }: AppDisclaimerProps) {
  return (
    <p
      className={cn(
        "mx-auto max-w-3xl text-center text-[11px] leading-5 text-slate-500 md:text-xs",
        className
      )}
    >
      Ответы генерируются ИИ и могут быть неточными. Пожалуйста, всегда проверяйте важную информацию по официальным источникам.
    </p>
  );
}
