"""
Google Forms integration service.

Позволяет получать ответы Google Forms через Google Sheets API
и преобразовывать их в IncomingRequest.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from functools import cached_property
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from backend.config.settings import settings
from backend.services.intake.google_forms import GoogleFormsIntakeParser
from backend.services.intake.models import IncomingRequest

logger = logging.getLogger(__name__)


SCOPES: Tuple[str, ...] = (
    "https://www.googleapis.com/auth/spreadsheets.readonly",
)


def _load_credentials(raw: str) -> Credentials:
    """
    Загрузить учетные данные сервис-аккаунта.

    Поддерживаются как путь до файла, так и JSON-строка.
    """
    if not raw:
        raise ValueError("GOOGLE_SERVICE_ACCOUNT_JSON is not configured")

    expanded = os.path.expanduser(raw)
    if os.path.isfile(expanded):
        logger.debug("Loading Google credentials from file %s", expanded)
        return Credentials.from_service_account_file(expanded, scopes=SCOPES)

    try:
        info = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(
            "GOOGLE_SERVICE_ACCOUNT_JSON must be a path or JSON document"
        ) from exc

    logger.debug("Loading Google credentials from JSON payload")
    return Credentials.from_service_account_info(info, scopes=SCOPES)


@dataclass(slots=True)
class GoogleFormsService:
    """
    Клиент Google Sheets, предоставляющий данные Google Forms.
    """

    spreadsheet_id: str
    range_name: str
    parser: GoogleFormsIntakeParser = field(default_factory=GoogleFormsIntakeParser)
    credentials_raw: Optional[str] = None

    @classmethod
    def from_settings(cls, parser: Optional[GoogleFormsIntakeParser] = None) -> "GoogleFormsService":
        if not settings.GOOGLE_SERVICE_ACCOUNT_JSON or not settings.GOOGLE_FORMS_SPREADSHEET_ID:
            raise ValueError("Google Forms settings are missing")

        return cls(
            spreadsheet_id=settings.GOOGLE_FORMS_SPREADSHEET_ID,
            range_name=settings.GOOGLE_FORMS_RANGE,
            parser=parser or GoogleFormsIntakeParser(),
            credentials_raw=settings.GOOGLE_SERVICE_ACCOUNT_JSON,
        )

    @cached_property
    def _credentials(self) -> Credentials:
        raw = self.credentials_raw or settings.GOOGLE_SERVICE_ACCOUNT_JSON
        return _load_credentials(raw)

    @cached_property
    def _sheets(self):
        logger.debug("Initialising Google Sheets client")
        return build("sheets", "v4", credentials=self._credentials, cache_discovery=False)

    def fetch_rows(self) -> Sequence[Sequence[str]]:
        """
        Получить все строки из указанного диапазона.
        """
        try:
            result = (
                self._sheets.spreadsheets()
                .values()
                .get(spreadsheetId=self.spreadsheet_id, range=self.range_name)
                .execute()
            )
        except HttpError as exc:
            logger.error("Google Sheets API error: %s", exc)
            raise

        values = result.get("values") or []
        logger.debug("Fetched %s rows from Google Forms sheet", len(values))
        return values

    @staticmethod
    def _map_row(header: Sequence[str], row: Sequence[str]) -> Dict[str, Any]:
        mapped: Dict[str, Any] = {}
        for idx, key in enumerate(header):
            key_normalized = key.strip()
            mapped[key_normalized] = row[idx] if idx < len(row) else None
        return mapped

    def fetch_submissions(self) -> List[Dict[str, Any]]:
        """
        Вернуть список ответов формы в виде словарей.
        """
        rows = self.fetch_rows()
        if not rows:
            return []

        header, *data_rows = rows
        submissions = [self._map_row(header, row) for row in data_rows]
        return submissions

    def fetch_requests(
        self,
        *,
        since_row: Optional[int] = None,
        additional_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[IncomingRequest]:
        """
        Получить заявки из Google Forms, начиная с указанной строки.

        Args:
            since_row: если указан, пропускает строки до указанного (нумерация с 2, т.к. 1 — заголовок)
            additional_metadata: произвольные данные, которые будут добавлены в метаданные заявки
        """
        submissions = self.fetch_submissions()
        requests: List[IncomingRequest] = []

        for offset, submission in enumerate(submissions, start=2):
            if since_row and offset <= since_row:
                continue

            request = self.parser.parse_submission(submission)
            request.external_id = submission.get("Response Id") or submission.get("response_id") or f"{self.spreadsheet_id}:{offset}"
            request.metadata.setdefault("row_index", offset)
            if additional_metadata:
                request.metadata.update(additional_metadata)
            requests.append(request)

        logger.info("Prepared %s requests from Google Forms", len(requests))
        return requests


