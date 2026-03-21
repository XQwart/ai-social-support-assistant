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
      Это ИИ-продукт. Он может ошибаться, пожалуйста, проверяйте предоставленные источники.
    </p>
  );
}
