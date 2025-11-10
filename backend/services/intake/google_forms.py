"""
Parser for Google Forms submissions.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, Optional

from backend.services.intake.models import IncomingRequest, RequestChannel

logger = logging.getLogger(__name__)


@dataclass(slots=True, kw_only=True)
class GoogleFormsIntakeParser:
    """Maps Google Forms submission payload into IncomingRequest."""

    field_map: Mapping[str, str] = field(default_factory=dict)

    def parse_submission(self, submission: Mapping[str, Any]) -> IncomingRequest:
        """
        Преобразовать словарь с ответами формы в IncomingRequest.

        Args:
            submission: словарь с ответами (ключи — заголовки вопросов)
        """
        def resolve(key: str) -> Optional[str]:
            source_key = self.field_map.get(key, key)
            value = submission.get(source_key)
            if value is None:
                return None
            return str(value)

        metadata = {key: value for key, value in submission.items() if value is not None}
        logger.debug("Parsed Google Forms submission keys: %s", list(submission.keys()))

        return IncomingRequest(
            channel=RequestChannel.GOOGLE_FORMS,
            subject=resolve("project_name") or resolve("subject"),
            body=resolve("project_description"),
            customer_name=resolve("customer_name"),
            contact_email=resolve("contact_email"),
            contact_phone=resolve("contact_phone"),
            project_location=resolve("project_location"),
            metadata={"form_id": resolve("form_id"), "raw_headers": list(submission.keys())},
            raw_payload=dict(submission),
        )


__all__ = ["GoogleFormsIntakeParser"]

