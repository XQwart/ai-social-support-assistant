from __future__ import annotations
import json
import logging
from typing import TYPE_CHECKING

from fastapi.concurrency import run_in_threadpool
from openai import OpenAI, DefaultHttpxClient

from app.core.constants import FAQ_JSON, CHUCK_JSON

if TYPE_CHECKING:
    from app.core.config import Config


logger = logging.getLogger(__name__)


class AIService:
    _config: Config
    _model: str

    def __init__(self, config: Config):
        self._config = config
        self._model = config.polza_ai_model

    def _create_client(self, timeout: float = 60.0) -> OpenAI:

        http_client = DefaultHttpxClient(
            verify=False,  # Обход SSL для OpenSSL 1.1.1
            timeout=timeout,
        )

        return OpenAI(
            base_url=self._config.polza_ai_base_url,
            api_key=self._config.polza_ai_api_key,
            max_retries=2,
            http_client=http_client,
        )

    def _load_knowledge_base(self) -> tuple[list[dict], list[dict]]:
        faq_data: list[dict] = []
        chuck_data: list[dict] = []

        try:
            if FAQ_JSON.exists():
                content = FAQ_JSON.read_text(encoding="utf-8")
                if content.strip():
                    faq_data = json.loads(content)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Не удалось загрузить faq.json: %s", e)

        try:
            if CHUCK_JSON.exists():
                content = CHUCK_JSON.read_text(encoding="utf-8")
                if content.strip():
                    chuck_data = json.loads(content)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Не удалось загрузить chuck.json: %s", e)

        return faq_data, chuck_data

    def _build_system_prompt(self, faq_data: list, chuck_data: list) -> str:
        faq_section = ""
        chuck_section = ""

        if faq_data:
            faq_text = json.dumps(faq_data[:200], ensure_ascii=False)
            faq_section = f"\n\nБАЗА ЗНАНИЙ (FAQ — вопросы и ответы):\n{faq_text}"

        if chuck_data:
            chuck_text = json.dumps(chuck_data[:100], ensure_ascii=False)
            chuck_section = f"\n\nСТАТЬИ (для цитирования):\n{chuck_text}"

        return (
            "Ты — ИИ-ассистент по социальной поддержке граждан РФ. "
            "Твоя задача — точно и надёжно отвечать на вопросы о льготах, пособиях, "
            "субсидиях и мерах социальной поддержки.\n\n"
            "ПРАВИЛА:\n"
            "1. Отвечай ТОЛЬКО на основе предоставленной базы знаний (FAQ и статей ниже). "
            "Если база знаний пуста — используй свои общие знания о мерах социальной поддержки в РФ, "
            "но ОБЯЗАТЕЛЬНО предупреди пользователя, что рекомендуешь проверить информацию "
            "на официальных сайтах (gosuslugi.ru, sfr.gov.ru, сайт соцзащиты региона).\n"
            "2. Если вопрос по теме социальной поддержки и ответ есть в базе — "
            "дай ответ с цитатами и ссылкой на источник.\n"
            "3. Если вопрос по теме, но ответа в базе нет — извинись и предоставь ссылку "
            "на официальный сайт, где можно получить подробную информацию.\n"
            "4. Если вопрос НЕ по теме социальной поддержки — вежливо скажи: "
            '"Я могу помочь только с вопросами по социальной поддержке, '
            'льготам, пособиям и субсидиям. Задайте мне вопрос на эту тему!"\n'
            "5. Используй небольшие прямые цитаты из статей, указывая источник.\n"
            "6. НЕ выдумывай информацию. НЕ галлюцинируй.\n"
            "7. Отвечай на русском языке.\n"
            "8. Будь вежливым и дружелюбным.\n"
            "9. Если пользователь здоровается или пишет приветствие — "
            "поздоровайся в ответ и предложи помочь с вопросами по соцподдержке."
            f"{faq_section}"
            f"{chuck_section}"
        )

    async def generate_response(
        self,
        user_message: str,
        chat_history: list[dict[str, str]],
        compressed_context: str | None = None,
    ) -> str:
        return await run_in_threadpool(
            self._generate_response_sync,
            user_message,
            chat_history,
            compressed_context,
        )

    def _generate_response_sync(
        self,
        user_message: str,
        chat_history: list[dict[str, str]],
        compressed_context: str | None = None,
    ) -> str:
        logger.info(
            "Запрос к ИИ: user_message='%s', history_len=%d",
            user_message[:100],
            len(chat_history),
        )
        faq_data, chuck_data = self._load_knowledge_base()
        system_prompt = self._build_system_prompt(faq_data, chuck_data)

        messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]

        if compressed_context:
            messages.append(
                {
                    "role": "system",
                    "content": (
                        f"Сжатый контекст предыдущего разговора:\n{compressed_context}"
                    ),
                }
            )

        messages.extend(chat_history)
        messages.append({"role": "user", "content": user_message})

        try:
            client = self._create_client(timeout=60.0)
            completion = client.chat.completions.create(
                model=self._model,
                messages=messages,
                temperature=0.3,
                max_tokens=2048,
            )
            response_text = completion.choices[0].message.content
            if response_text:
                logger.info(
                    "ИИ успешно сгенерировал ответ (длина: %d)", len(response_text)
                )
                return response_text

            logger.warning("ИИ вернул пустой ответ")
            return (
                "Произошла ошибка при генерации ответа. Пожалуйста, попробуйте позже."
            )

        except Exception as e:
            logger.exception("Критическая ошибка при обращении к ИИ")
            return (
                "К сожалению, не удалось получить ответ от ИИ. "
                "Пожалуйста, попробуйте позже или обратитесь на портал Госуслуг: "
                "https://www.gosuslugi.ru/social-navigator"
            )

    async def compress_context(self, messages: list[dict[str, str]]) -> str:
        return await run_in_threadpool(self._compress_context_sync, messages)

    def _compress_context_sync(self, messages: list[dict[str, str]]) -> str:
        messages_text = "\n".join(
            f"{'Пользователь' if m['role'] == 'user' else 'Ассистент'}: {m['content']}"
            for m in messages
        )

        try:
            completion = self._create_client(timeout=60.0).chat.completions.create(
                model=self._model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Сожми следующий диалог в краткое резюме на 3-5 предложений. "
                            "Сохрани ключевые вопросы пользователя, основные ответы и важные факты. "
                            "Резюме должно быть на русском языке."
                        ),
                    },
                    {"role": "user", "content": messages_text},
                ],
                temperature=0.2,
                max_tokens=512,
            )
            return completion.choices[0].message.content or ""
        except Exception as e:
            logger.error("Ошибка сжатия контекста: %s", e)
            return messages_text[:1000]

    def extract_faq_from_texts(self, texts: list[dict]) -> list[dict]:
        logger.info("Начало извлечения FAQ из %d текстов", len(texts))
        combined = "\n\n---\n\n".join(
            f"Источник: {t.get('source_url', 'N/A')}\n"
            f"Регион: {t.get('region', 'N/A')}\n"
            f"Текст:\n{t.get('text', '')[:3000]}"
            for t in texts
        )

        try:
            completion = self._create_client(timeout=120.0).chat.completions.create(
                model=self._model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Проанализируй тексты о мерах социальной поддержки. "
                            "Извлеки пары «вопрос-ответ» в формате JSON-массива:\n"
                            "[\n"
                            "  {\n"
                            '    "question": "Вопрос, который может задать гражданин",\n'
                            '    "answer": "Точный ответ из текста",\n'
                            '    "source_url": "URL источника",\n'
                            '    "region": "Регион",\n'
                            '    "category": "категория"\n'
                            "  }\n"
                            "]\n"
                            "Категории: семьи_с_детьми, пенсионеры, инвалиды, "
                            "ветераны, малоимущие, жку, общие.\n"
                            "Возвращай ТОЛЬКО JSON-массив, без Markdown-обёрток."
                        ),
                    },
                    {"role": "user", "content": combined},
                ],
                temperature=0.1,
                max_tokens=4096,
            )

            raw = completion.choices[0].message.content or "[]"
            raw = raw.strip()

            if raw.startswith("```"):
                lines = raw.split("\n", 1)
                raw = lines[1] if len(lines) > 1 else raw[3:]
            if raw.endswith("```"):
                raw = raw[:-3]
            raw = raw.strip()

            result = json.loads(raw)
            logger.info("Успешно извлечено %d пар FAQ", len(result))
            return result
        except json.JSONDecodeError as e:
            logger.error(
                "Ошибка декодирования JSON при извлечении FAQ: %s. Raw content: %s",
                e,
                raw[:200],
            )
            return []
        except Exception as e:
            logger.exception("Непредвиденная ошибка при извлечении FAQ")
            return []
