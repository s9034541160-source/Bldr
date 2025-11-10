"""Сервис для извлечения текста и структурирования документов."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import fitz  # PyMuPDF
import docx

try:  # OCR опционален
    import pytesseract
    from PIL import Image
except ImportError:  # pragma: no cover - OCR может быть отключен
    pytesseract = None
    Image = None

logger = logging.getLogger(__name__)


SECTION_PATTERN = re.compile(r"^(?:[A-ZА-Я]{1,3}\.?\d*|\d+[\.\d]*)\s+.+", re.MULTILINE)
SUBSECTION_PATTERN = re.compile(r"^(?:\d+[\.\d]+)\s+.+", re.MULTILINE)
PARAGRAPH_PATTERN = re.compile(r"^(?:\d+[\.\d]+)\s+.+", re.MULTILINE)
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp"}


@dataclass
class DocumentChunk:
    """Фрагмент документа с иерархическими данными."""

    text: str
    level: str
    title: str
    hierarchy: List[str]
    metadata: Dict[str, str]


class DocumentParser:
    """Утилиты для извлечения текста и построения чанков."""

    def __init__(self, enable_ocr: bool = True, ocr_lang: str = "rus+eng") -> None:
        self.enable_ocr = enable_ocr and pytesseract is not None and Image is not None
        self.ocr_lang = ocr_lang
        if enable_ocr and not self.enable_ocr:
            logger.warning(
                "OCR requested but pytesseract/Pillow is not available. Image text extraction disabled."
            )

    # -------------------------
    # Извлечение первичного текста
    # -------------------------
    def extract_text(self, file_path: str) -> str:
        path = Path(file_path)
        ext = path.suffix.lower()
        if ext == ".pdf":
            return self._extract_text_from_pdf(path)
        if ext == ".docx":
            return self._extract_text_from_docx(path)
        if ext in IMAGE_EXTENSIONS:
            return self._extract_text_from_image(path)
        raise ValueError(f"Unsupported file extension: {ext}")

    def _extract_text_from_pdf(self, path: Path) -> str:
        logger.debug("Extracting text from PDF: %s", path)
        text_parts: List[str] = []
        with fitz.open(path) as document:
            for page in document:
                text_parts.append(page.get_text("text"))
        return "\n".join(text_parts).strip()

    def _extract_text_from_docx(self, path: Path) -> str:
        logger.debug("Extracting text from DOCX: %s", path)
        document = docx.Document(path)
        paragraphs = [paragraph.text for paragraph in document.paragraphs if paragraph.text]
        return "\n".join(paragraphs).strip()

    def _extract_text_from_image(self, path: Path) -> str:
        if not self.enable_ocr:
            raise RuntimeError("OCR is not enabled or pytesseract is not installed")
        logger.debug("Extracting text via OCR: %s", path)
        image = Image.open(path)
        text = pytesseract.image_to_string(image, lang=self.ocr_lang)
        return text.strip()

    # -------------------------
    # Структурирование текста
    # -------------------------
    def chunk_text(self, text: str) -> List[DocumentChunk]:
        """Создает иерархические чанки текста (ГОСТ стиль)."""
        if not text:
            return []

        lines = [line.rstrip() for line in text.splitlines() if line.strip()]
        chunks: List[DocumentChunk] = []
        hierarchy: List[str] = []
        buffer: List[str] = []
        current_title = "Введение"
        current_level = "section"

        def flush_buffer() -> None:
            nonlocal buffer, current_title, current_level, hierarchy
            if not buffer:
                return
            chunk_text = "\n".join(buffer).strip()
            if not chunk_text:
                buffer = []
                return
            chunks.append(
                DocumentChunk(
                    text=chunk_text,
                    level=current_level,
                    title=current_title,
                    hierarchy=list(hierarchy),
                    metadata={"title": current_title, "level": current_level},
                )
            )
            buffer = []

        for line in lines:
            normalized_line = line.strip()
            if SECTION_PATTERN.match(normalized_line):
                flush_buffer()
                current_level = "section"
                current_title = normalized_line
                hierarchy = [normalized_line]
                continue

            if SUBSECTION_PATTERN.match(normalized_line) and len(normalized_line.split(".")) >= 2:
                flush_buffer()
                current_level = "subsection"
                current_title = normalized_line
                hierarchy = hierarchy[:1] + [normalized_line]
                continue

            if PARAGRAPH_PATTERN.match(normalized_line) and len(normalized_line.split(".")) > 2:
                flush_buffer()
                current_level = "paragraph"
                current_title = normalized_line
                hierarchy = hierarchy[:2] + [normalized_line]
                continue

            buffer.append(normalized_line)

        flush_buffer()
        return chunks

    # -------------------------
    # Комплексные операции
    # -------------------------
    def extract_chunks_from_file(self, file_path: str) -> List[DocumentChunk]:
        text = self.extract_text(file_path)
        chunks = self.chunk_text(text)
        if not chunks and text:
            chunks = [
                DocumentChunk(
                    text=text,
                    level="document",
                    title="Полный документ",
                    hierarchy=[],
                    metadata={"title": "Полный документ", "level": "document"},
                )
            ]
        return chunks

    def extract_plain_text(self, file_path: str) -> str:
        return self.extract_text(file_path)


# Глобальный экземпляр
_document_parser = DocumentParser()

def get_document_parser() -> DocumentParser:
    return _document_parser
