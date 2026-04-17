from __future__ import annotations

import logging
import re

from bs4 import BeautifulSoup, Tag

from worker.core.constants import (
    MIN_TEXT_LENGTH,
    NOISE_CLASS_RE,
    NOISE_ROLES,
    NOISE_TAGS,
    DROP_LINE_PATTERNS,
    IRRELEVANT_PARENT_MARKERS,
    MAIN_CONTENT_SELECTORS,
    STOP_SECTION_PATTERNS,
)

logger = logging.getLogger(__name__)


class HtmlTextExtractor:
    def extract_text(self, html: str, url: str) -> str | None:
        try:
            soup = BeautifulSoup(html, "lxml")
            body = soup.find("body")

            if not body:
                logger.warning("Не найден <body> на %s", url)
                return None

            self._remove_noise(body)

            main_block = self._find_main_content(body)
            text = self._extract_structured_text(main_block or body)
            text = self._clean_text(text)
            text = self._postprocess_lines(text)

            if len(text) < MIN_TEXT_LENGTH:
                logger.warning(
                    "Мало текста на %s (%d символов, порог %d)",
                    url,
                    len(text),
                    MIN_TEXT_LENGTH,
                )
                return None

            return text

        except Exception:
            logger.exception("Ошибка парсинга HTML с %s", url)
            return None

    def _find_main_content(self, body: Tag) -> Tag | None:
        for selector in MAIN_CONTENT_SELECTORS:
            found = body.select_one(selector)
            if found and self._tag_text_len(found) >= MIN_TEXT_LENGTH:
                return found

        candidates: list[tuple[int, Tag]] = []

        for tag in body.find_all(["main", "article", "section", "div"]):
            text_len = self._tag_text_len(tag)
            if text_len < MIN_TEXT_LENGTH:
                continue

            score = text_len

            attrs = getattr(tag, "attrs", {}) or {}
            classes = " ".join(attrs.get("class", []))
            tag_id = attrs.get("id", "") or ""
            marker = f"{classes} {tag_id}".lower()

            if any(
                key in marker
                for key in (
                    "content",
                    "article",
                    "post",
                    "main",
                    "page",
                    "text",
                    "news",
                    "detail",
                )
            ):
                score += 3000

            link_count = len(tag.find_all("a"))
            p_count = len(tag.find_all(["p", "li"]))

            if p_count > 0:
                score += p_count * 50

            if link_count > 0:
                score -= link_count * 10

            candidates.append((score, tag))

        if not candidates:
            return None

        candidates.sort(key=lambda item: item[0], reverse=True)
        return candidates[0][1]

    @staticmethod
    def _tag_text_len(tag: Tag) -> int:
        return len(tag.get_text(" ", strip=True))

    def _extract_structured_text(self, root: Tag) -> str:
        blocks: list[str] = []

        for child in root.find_all(
            [
                "h1",
                "h2",
                "h3",
                "h4",
                "p",
                "ul",
                "ol",
                "table",
                "blockquote",
            ]
        ):
            if self._is_nested_in_irrelevant_block(child):
                continue

            if child.name in {"ul", "ol"}:
                items = self._extract_list(child)
                if items:
                    blocks.append(items)
                continue

            if child.name == "table":
                table_text = self._extract_table(child)
                if table_text:
                    blocks.append(table_text)
                continue

            text = child.get_text(" ", strip=True)
            text = self._normalize_inline_text(text)

            if text:
                blocks.append(text)

        if not blocks:
            return root.get_text(separator="\n", strip=True)

        return "\n\n".join(self._deduplicate_blocks(blocks))

    @staticmethod
    def _is_nested_in_irrelevant_block(tag: Tag) -> bool:
        parent = tag.parent

        while parent is not None:
            if not isinstance(parent, Tag):
                break

            attrs = getattr(parent, "attrs", {}) or {}
            classes = " ".join(attrs.get("class", []))
            tag_id = attrs.get("id", "") or ""
            marker = f"{classes} {tag_id}".lower()

            if any(key in marker for key in IRRELEVANT_PARENT_MARKERS):
                return True

            parent = parent.parent

        return False

    def _extract_list(self, list_tag: Tag) -> str:
        items: list[str] = []

        for li in list_tag.find_all("li", recursive=False):
            text = li.get_text(" ", strip=True)
            text = self._normalize_inline_text(text)

            if text:
                items.append(f"- {text}")

        return "\n".join(items).strip()

    def _extract_table(self, table: Tag) -> str:
        rows: list[str] = []

        for tr in table.find_all("tr"):
            cells = tr.find_all(["th", "td"])
            values: list[str] = []

            for cell in cells:
                text = cell.get_text(" ", strip=True)
                text = self._normalize_inline_text(text)

                if text:
                    values.append(text)

            if values:
                rows.append(" | ".join(values))

        return "\n".join(rows).strip()

    @staticmethod
    def _deduplicate_blocks(blocks: list[str]) -> list[str]:
        result: list[str] = []
        previous = ""

        for block in blocks:
            normalized = re.sub(r"\s+", " ", block).strip()
            if not normalized:
                continue

            if normalized == previous:
                continue

            result.append(block)
            previous = normalized

        return result

    @staticmethod
    def _normalize_inline_text(text: str) -> str:
        text = text.replace("\xa0", " ")
        text = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", text)
        text = re.sub(r"\s+([,.;:!?])", r"\1", text)
        text = re.sub(r"[^\S\n]+", " ", text)
        return text.strip()

    @staticmethod
    def _remove_noise(body: Tag) -> None:
        for tag_name in NOISE_TAGS:
            for tag in body.find_all(tag_name):
                tag.decompose()

        for role in NOISE_ROLES:
            for tag in body.find_all(attrs={"role": role}):
                tag.decompose()

        for tag in body.find_all(True):
            attrs = getattr(tag, "attrs", None) or {}
            classes = " ".join(attrs.get("class", []))
            tag_id = attrs.get("id", "") or ""

            if NOISE_CLASS_RE.search(f"{classes} {tag_id}"):
                tag.decompose()
                continue

            if str(attrs.get("aria-hidden", "")).lower() == "true":
                tag.decompose()
                continue

            if "hidden" in attrs:
                tag.decompose()
                continue

    def _postprocess_lines(self, text: str) -> str:
        lines = [line.strip() for line in text.splitlines()]
        cleaned: list[str] = []
        seen_recent: list[str] = []

        for line in lines:
            if not line:
                if cleaned and cleaned[-1] != "":
                    cleaned.append("")
                continue

            line = self._normalize_inline_text(line)

            if len(line) <= 1:
                continue

            if "�" in line:
                line = line.replace("�", "")

            if any(pattern.match(line) for pattern in STOP_SECTION_PATTERNS):
                break

            if any(pattern.match(line) for pattern in DROP_LINE_PATTERNS):
                continue

            if re.fullmatch(r"[•\-–—]+", line):
                continue

            if re.fullmatch(r"[\d\s()+\-]{6,}", line):
                continue

            normalized = re.sub(r"\s+", " ", line).strip().lower()

            if normalized in seen_recent[-5:]:
                continue

            cleaned.append(line)
            seen_recent.append(normalized)

        text = "\n".join(cleaned)
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"[^\S\n]+", " ", text)

        return text.strip()

    @staticmethod
    def _clean_text(text: str) -> str:
        text = text.replace("\xa0", " ")
        text = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", text)
        text = re.sub(r"\r", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"[^\S\n]+", " ", text)
        return text.strip()
