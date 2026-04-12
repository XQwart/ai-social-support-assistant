import { useId, useState } from "react";

import { cn } from "@/utils/cn";

const AVATAR_SRC = `${import.meta.env.BASE_URL.replace(/\/$/, "")}/ai-assistant-avatar.png`;

interface AssistantAvatarProps {
  className?: string;
  variant?: "default" | "error";
}

function FallbackGlyph({
  className,
  variant,
  gradDefaultId,
  gradRoseId,
}: {
  className?: string;
  variant: "default" | "error";
  gradDefaultId: string;
  gradRoseId: string;
}) {
  const gradId = variant === "error" ? gradRoseId : gradDefaultId;
  return (
    <svg
      className={cn("h-[22px] w-[22px]", className)}
      viewBox="0 0 32 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden
    >
      <defs>
        <linearGradient
          id={gradDefaultId}
          x1="4"
          y1="28"
          x2="28"
          y2="4"
          gradientUnits="userSpaceOnUse"
        >
          <stop stopColor="#10b981" />
          <stop offset="0.55" stopColor="#14b8a6" />
          <stop offset="1" stopColor="#06b6d4" />
        </linearGradient>
        <linearGradient
          id={gradRoseId}
          x1="4"
          y1="28"
          x2="28"
          y2="4"
          gradientUnits="userSpaceOnUse"
        >
          <stop stopColor="#fb7185" />
          <stop offset="1" stopColor="#f43f5e" />
        </linearGradient>
      </defs>
      <circle cx="16" cy="16" r="14" stroke={`url(#${gradId})`} strokeWidth="2" />
      <path
        d="M10 17c1.2-3.2 3.8-5.5 6.8-5.5 2.2 0 4.1 1.1 5.4 2.8M12 22.5c1.4 1.2 3.2 1.9 5.2 1.9 1.4 0 2.7-.3 3.8-.9"
        stroke={`url(#${gradId})`}
        strokeWidth="2"
        strokeLinecap="round"
      />
      <circle cx="12" cy="13" r="1.35" fill={`url(#${gradId})`} />
      <circle cx="20" cy="13" r="1.35" fill={`url(#${gradId})`} />
    </svg>
  );
}

export function AssistantAvatar({
  className,
  variant = "default",
}: AssistantAvatarProps) {
  const [imageFailed, setImageFailed] = useState(false);
  const uid = useId().replace(/:/g, "");
  const gradDefaultId = `assistant-fg-${uid}`;
  const gradRoseId = `assistant-fr-${uid}`;

  return (
    <div
      className={cn(
        "select-none mt-0.5 flex h-12 w-12 shrink-0 items-center justify-center overflow-hidden rounded-full border shadow-[0_8px_24px_rgba(15,23,42,0.08)] md:h-14 md:w-14",
        variant === "error"
          ? "border-rose-200 bg-rose-50"
          : "border-slate-200/90 bg-white",
        className
      )}
    >
      {!imageFailed ? (
        <img
          src={AVATAR_SRC}
          alt=""
          draggable={false}
          className="h-full w-full origin-center object-cover object-center scale-[1.42]"
          onDragStart={(e) => e.preventDefault()}
          onError={() => setImageFailed(true)}
        />
      ) : (
        <FallbackGlyph
          variant={variant}
          gradDefaultId={gradDefaultId}
          gradRoseId={gradRoseId}
        />
      )}
    </div>
  );
}
