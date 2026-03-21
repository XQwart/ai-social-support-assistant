import { useEffect, useState } from "react";

interface TypingAnimationProps {
  text: string;
  speed?: number;
  onComplete?: () => void;
}

export default function TypingAnimation({
  text,
  speed = 14,
  onComplete,
}: TypingAnimationProps) {
  const [displayed, setDisplayed] = useState("");
  const [done, setDone] = useState(false);

  useEffect(() => {
    const prefersReducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)"
    ).matches;

    if (prefersReducedMotion) {
      setDisplayed(text);
      setDone(true);
      onComplete?.();
      return;
    }

    let currentIndex = 0;
    let timeoutId: number | null = null;
    let cancelled = false;

    setDisplayed("");
    setDone(false);

    const step = () => {
      if (cancelled) {
        return;
      }

      currentIndex += 1;
      setDisplayed(text.slice(0, currentIndex));

      if (currentIndex < text.length) {
        timeoutId = window.setTimeout(step, speed);
      } else {
        setDone(true);
        onComplete?.();
      }
    };

    timeoutId = window.setTimeout(step, speed);

    return () => {
      cancelled = true;
      if (timeoutId !== null) {
        window.clearTimeout(timeoutId);
      }
    };
  }, [text, speed, onComplete]);

  return (
    <span>
      {displayed}
      {!done && <span className="typing-cursor" aria-hidden="true" />}
    </span>
  );
}
