import { v4 as uuidv4 } from "uuid";
import type { Chat, Message } from "@/types";

function sleep(ms: number, signal?: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    const onAbort = () => {
      clearTimeout(timeoutId);
      reject(new DOMException("Request aborted", "AbortError"));
    };

    const timeoutId = window.setTimeout(() => {
      signal?.removeEventListener("abort", onAbort);
      resolve();
    }, ms);

    if (signal) {
      if (signal.aborted) {
        onAbort();
        return;
      }

      signal.addEventListener("abort", onAbort, { once: true });
    }
  });
}

function buildDemoResponse(message: string): string {
  const text = message.toLowerCase();

  if (text.includes("льгот")) {
    return "Чтобы проверить, какие льготы вам доступны, обычно учитываются ваш статус, состав семьи, доход, инвалидность, возраст и регион проживания. Подготовьте паспорт, СНИЛС и документы, подтверждающие право на меру поддержки.";
  }

  if (text.includes("жкх") || text.includes("субсид")) {
    return "Субсидия на оплату ЖКХ предоставляется, если расходы семьи на коммунальные услуги превышают установленную долю от совокупного дохода. Обычно заявление подают через МФЦ, соцзащиту или портал Госуслуг.";
  }

  if (
    text.includes("ребён") ||
    text.includes("ребен") ||
    text.includes("рождении")
  ) {
    return "При рождении ребёнка могут быть доступны единовременное пособие, ежемесячные выплаты, материнский капитал и региональные меры поддержки. Точный список зависит от дохода семьи и региона.";
  }

  if (text.includes("малоимущ")) {
    return "Для признания семьи малоимущей обычно сравнивают среднедушевой доход с региональным прожиточным минимумом. Понадобятся документы о составе семьи, доходах, паспорта и заявление.";
  }

  if (text.includes("инвалид")) {
    return "Для оформления инвалидности потребуется направление на медико-социальную экспертизу, медицинские документы и заключения врачей. После установления группы можно оформить пенсию и дополнительные льготы.";
  }

  if (text.includes("безработ")) {
    return "Для назначения пособия по безработице нужно встать на учёт через центр занятости или Госуслуги. Обычно требуются паспорт, документы об образовании и сведения о трудовой деятельности.";
  }

  return "Я могу помочь с вопросами по льготам, пособиям, субсидиям, статусу малоимущей семьи, инвалидности и другим мерам социальной поддержки. Если хотите, опишите вашу ситуацию подробнее.";
}

/**
 * Временная заглушка под будущий backend.
 * Потом можно заменить на реальный fetch:
 *
 * const res = await fetch('/api/chat', {
 *   method: 'POST',
 *   headers: { 'Content-Type': 'application/json' },
 *   body: JSON.stringify({ chatId, message }),
 *   signal,
 * });
 * return await res.json();
 */
export async function sendMessage(
  chatId: string,
  message: string,
  signal?: AbortSignal
): Promise<Message> {
  void chatId;

  await sleep(900 + Math.random() * 1100, signal);

  return {
    id: uuidv4(),
    role: "assistant",
    content: buildDemoResponse(message),
    timestamp: Date.now(),
  };
}

/**
 * Заглушка под будущую загрузку истории.
 */
export async function fetchChatHistory(
  signal?: AbortSignal
): Promise<Chat[]> {
  await sleep(120, signal);
  return [];
}

/**
 * Заглушка под удаление чата на сервере.
 */
export async function deleteChat(
  chatId: string,
  signal?: AbortSignal
): Promise<void> {
  void chatId;
  await sleep(120, signal);
}