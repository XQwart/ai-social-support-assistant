import { useState } from "react";

import { cn } from "@/utils/cn";
import type {
  AgentActivity,
  AgentFetchPageInput,
  AgentRagInput,
  AgentWebSearchInput,
} from "@/types";

interface AgentActivityListProps {
  activities: AgentActivity[];
  isStreaming: boolean;
}

const KIND_LABEL: Record<AgentActivity["kind"], string> = {
  thinking: "Размышляет",
  rag: "Поиск в базе знаний",
  web_search: "Поиск в интернете",
  fetch_page: "Чтение страниц",
  memory: "Сохранение факта",
};

const KIND_DONE_LABEL: Record<AgentActivity["kind"], string> = {
  thinking: "Размышления",
  rag: "Поиск в базе знаний",
  web_search: "Поиск в интернете",
  fetch_page: "Чтение страниц",
  memory: "Факт сохранён",
};

function ThinkingIcon() {
  return (
    <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M9 18h6" />
      <path d="M10 22h4" />
      <path d="M12 2a7 7 0 0 0-4 12.7c.6.5 1 1.3 1 2v.3h6V17c0-.7.4-1.5 1-2A7 7 0 0 0 12 2Z" />
    </svg>
  );
}

function RagIcon() {
  return (
    <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M4 4v14a2 2 0 0 0 2 2h14" />
      <path d="M8 8h10" />
      <path d="M8 12h7" />
      <path d="M8 16h10" />
    </svg>
  );
}

function WebSearchIcon() {
  return (
    <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <circle cx="11" cy="11" r="7" />
      <path d="m20 20-3.5-3.5" />
    </svg>
  );
}

function FetchPageIcon() {
  return (
    <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M14 3v5h5" />
      <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h9l5 5v11a2 2 0 0 1-2 2Z" />
    </svg>
  );
}

function MemoryIcon() {
  return (
    <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M12 21s-7-4.5-7-10.5A4.5 4.5 0 0 1 12 6a4.5 4.5 0 0 1 7 4.5C19 16.5 12 21 12 21Z" />
    </svg>
  );
}

function ChevronIcon({ open }: { open: boolean }) {
  return (
    <svg
      viewBox="0 0 24 24"
      width="14"
      height="14"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      className={cn("transition-transform", open ? "rotate-180" : "rotate-0")}
    >
      <path d="m6 9 6 6 6-6" />
    </svg>
  );
}

function KindIcon({ kind }: { kind: AgentActivity["kind"] }) {
  switch (kind) {
    case "thinking":
      return <ThinkingIcon />;
    case "rag":
      return <RagIcon />;
    case "web_search":
      return <WebSearchIcon />;
    case "fetch_page":
      return <FetchPageIcon />;
    case "memory":
      return <MemoryIcon />;
  }
}

function formatInput(activity: AgentActivity): string | null {
  if (!activity.input) return null;

  switch (activity.kind) {
    case "rag": {
      const input = activity.input as AgentRagInput;
      const query = input.query?.trim();
      const region = input.region?.trim();
      if (!query) return region || null;
      return region ? `«${query}» — ${region}` : `«${query}»`;
    }
    case "web_search": {
      const input = activity.input as AgentWebSearchInput;
      const query = input.query?.trim();
      return query ? `«${query}»` : null;
    }
    case "fetch_page": {
      const input = activity.input as AgentFetchPageInput;
      const urls = input.urls ?? [];
      if (urls.length === 0) return null;
      if (urls.length === 1) return urls[0];
      return `${urls.length} ссылок`;
    }
    default:
      return null;
  }
}

function RunningDots() {
  return (
    <span className="agent-activity-dots" aria-hidden="true">
      <span className="loading-dot" style={{ width: 5, height: 5 }} />
      <span
        className="loading-dot"
        style={{ width: 5, height: 5, animationDelay: "140ms" }}
      />
      <span
        className="loading-dot"
        style={{ width: 5, height: 5, animationDelay: "280ms" }}
      />
    </span>
  );
}

function ThinkingBlock({ activity }: { activity: AgentActivity }) {
  const isActive = activity.status === "running";
  const [open, setOpen] = useState(isActive);
  const text = (activity.text ?? "").trim();

  if (!text && !isActive) {
    return null;
  }

  return (
    <div
      className={cn(
        "agent-activity-card",
        isActive ? "agent-activity-running" : "agent-activity-done"
      )}
    >
      <button
        type="button"
        onClick={() => setOpen((prev) => !prev)}
        className="flex w-full cursor-pointer items-center justify-between gap-2 text-left"
      >
        <span className="agent-activity-head">
          <span className="agent-activity-icon">
            <KindIcon kind="thinking" />
          </span>
          <span className="agent-activity-label">
            {isActive ? KIND_LABEL.thinking : KIND_DONE_LABEL.thinking}
          </span>
          {isActive && <RunningDots />}
        </span>
        <span className="agent-activity-chevron">
          <ChevronIcon open={open} />
        </span>
      </button>

      {open && text && (
        <div className="agent-activity-thought">{text}</div>
      )}
    </div>
  );
}

function ActionChip({ activity }: { activity: AgentActivity }) {
  const isActive = activity.status === "running";
  const label = isActive ? KIND_LABEL[activity.kind] : KIND_DONE_LABEL[activity.kind];
  const detail = formatInput(activity);

  return (
    <div
      className={cn(
        "agent-activity-card",
        isActive ? "agent-activity-running" : "agent-activity-done"
      )}
    >
      <div className="flex items-start gap-2">
        <span className="agent-activity-icon mt-0.5">
          <KindIcon kind={activity.kind} />
        </span>
        <div className="flex min-w-0 flex-1 flex-col">
          <span className="agent-activity-head">
            <span className="agent-activity-label">{label}</span>
            {isActive && <RunningDots />}
          </span>
          {detail && <span className="agent-activity-detail">{detail}</span>}
        </div>
      </div>
    </div>
  );
}

export default function AgentActivityList({
  activities,
  isStreaming,
}: AgentActivityListProps) {
  if (activities.length === 0) {
    return null;
  }

  return (
    <div className="mb-2 flex flex-col gap-1.5">
      {activities.map((activity) =>
        activity.kind === "thinking" ? (
          <ThinkingBlock key={activity.id} activity={activity} />
        ) : (
          <ActionChip key={activity.id} activity={activity} />
        )
      )}
      {isStreaming && activities.length > 0 && (
        <span className="sr-only">Помощник продолжает работу...</span>
      )}
    </div>
  );
}
