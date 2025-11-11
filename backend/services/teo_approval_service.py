"""
Сервис согласования предварительного ТЭО.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from backend.config.settings import settings
from backend.models.project import Project
from backend.models.project_request import ProjectRequest
from backend.services.notifications.telegram import manager_notification_service
from backend.services.integrations.onec_service import onec_service

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ApprovalStep:
    """
    Описание шага согласования.
    """

    order: int
    role: str
    name: Optional[str]
    chat_id: Optional[str]
    email: Optional[str]
    status: str = "pending"
    decided_at: Optional[str] = None
    comment: Optional[str] = None
    notified_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class TEOApprovalService:
    """
    Управляет жизненным циклом согласования предварительного ТЭО.
    """

    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------ #
    # Публичные методы
    # ------------------------------------------------------------------ #

    def start_approval(
        self,
        project: Project,
        *,
        request: Optional[ProjectRequest],
        analysis: Optional[Dict[str, Any]],
        documents: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Инициализирует маршрут согласования и уведомляет первую линию.
        """
        route = self._build_route()
        if not route:
            logger.info("TEO approval route is empty; marking approval as not required for project %s", project.code)
            project.teo_approval_status = "not_required"
            project.teo_approval_route = None
            project.teo_approval_history = []
            project.teo_approved_at = None
            self._persist_project(project)
            return

        logger.info("Starting TEO approval for project %s with %d steps", project.code, len(route))
        for step in route:
            step.status = "pending"
            step.decided_at = None
            step.comment = None
            step.notified_at = None

        project.teo_approval_status = "pending"
        project.teo_approval_route = [step.to_dict() for step in route]
        project.teo_approval_history = []
        project.teo_approved_at = None
        self._persist_project(project)

        self._notify_next_step(project, analysis or {}, documents or {})
        self._sync_with_onec(project, analysis or {}, request)

    def record_decision(
        self,
        project: Project,
        *,
        role: str,
        decision: str,
        actor: Optional[str] = None,
        comment: Optional[str] = None,
        documents: Optional[Dict[str, str]] = None,
        analysis: Optional[Dict[str, Any]] = None,
        request: Optional[ProjectRequest] = None,
    ) -> None:
        """
        Фиксирует решение по конкретному этапу маршрута и продвигает согласование.
        """
        decision = decision.lower()
        if decision not in {"approved", "rejected"}:
            raise ValueError("Decision must be either 'approved' or 'rejected'.")

        route = self._route_from_project(project)
        history = list(project.teo_approval_history or [])

        step = next((item for item in route if item["role"] == role and item["status"] == "pending"), None)
        if not step:
            raise ValueError(f"Pending approval step for role '{role}' not found.")

        step["status"] = decision
        step["decided_at"] = datetime.utcnow().isoformat()
        step["comment"] = comment
        history.append(
            {
                "role": role,
                "decision": decision,
                "actor": actor or step.get("name"),
                "comment": comment,
                "decided_at": step["decided_at"],
            }
        )

        project.teo_approval_route = route
        project.teo_approval_history = history

        if decision == "rejected":
            project.teo_approval_status = "rejected"
            project.teo_approved_at = None
            logger.info("TEO for project %s rejected on step %s", project.code, role)
        else:
            remaining = [item for item in route if item["status"] == "pending"]
            if remaining:
                logger.info(
                    "TEO approval for project %s approved on step %s. %d steps remaining.",
                    project.code,
                    role,
                    len(remaining),
                )
                self._persist_project(project)
                self._notify_next_step(project, analysis or {}, documents or {})
                return
            project.teo_approval_status = "approved"
            project.teo_approved_at = datetime.utcnow()
            logger.info("TEO for project %s fully approved.", project.code)

        self._persist_project(project)
        self._sync_with_onec(project, analysis or {}, request)

    # ------------------------------------------------------------------ #
    # Внутренние утилиты
    # ------------------------------------------------------------------ #

    def _notify_next_step(
        self,
        project: Project,
        analysis: Dict[str, Any],
        documents: Dict[str, str],
    ) -> None:
        """
        Находит ближайший неотработанный шаг и отправляет уведомление.
        """
        route = self._route_from_project(project)
        if not route:
            return
        pending_steps = sorted(
            (item for item in route if item.get("status") == "pending"),
            key=lambda item: item.get("order", 0),
        )
        if not pending_steps:
            return
        current = pending_steps[0]
        chat_id = current.get("chat_id") or self._fallback_chat_id()
        summary = self._build_summary(project, analysis)
        manager_notification_service.notify_teo_approval(
            chat_id=chat_id or "",
            project_code=project.code,
            project_name=project.name,
            role=current.get("role", "Участник"),
            approver_name=current.get("name"),
            summary=summary,
            documents=documents,
        )
        current["notified_at"] = datetime.utcnow().isoformat()
        project.teo_approval_route = route
        self._persist_project(project)

    def _build_summary(self, project: Project, analysis: Dict[str, Any]) -> str:
        """
        Формирует краткое резюме для уведомления.
        """
        cost = analysis.get("cost") or {}
        timeline = analysis.get("timeline") or {}

        total_cost = cost.get("grand_total") or cost.get("total_cost")
        try:
            cost_line = f"{float(total_cost):,.2f} руб." if total_cost is not None else "n/a"
        except (TypeError, ValueError):
            cost_line = "n/a"

        duration = timeline.get("estimated_duration_days")
        try:
            duration_line = f"{int(duration)} дней" if duration is not None else "n/a"
        except (TypeError, ValueError):
            duration_line = "n/a"

        lines = [
            f"Смета: {cost_line}",
            f"Срок: {duration_line}.",
        ]
        if project.preliminary_teo_path:
            lines.append(f"Документ: {project.preliminary_teo_path}")
        return "\n".join(lines)

    def _build_route(self) -> List[ApprovalStep]:
        """
        Собирает маршрут из настроек.
        """
        raw_route = settings.TEO_APPROVAL_ROUTE
        steps: List[Dict[str, Any]] = []
        if raw_route:
            try:
                parsed = json.loads(raw_route)
                if isinstance(parsed, list):
                    steps = [item for item in parsed if isinstance(item, dict)]
            except json.JSONDecodeError as exc:
                logger.warning("Failed to parse TEO approval route JSON: %s", exc)
        if not steps and settings.TEO_APPROVAL_CHAT_IDS:
            steps = [
                {"role": f"Утверждение #{idx + 1}", "chat_id": chat_id.strip() or None, "name": None, "email": None}
                for idx, chat_id in enumerate(settings.TEO_APPROVAL_CHAT_IDS)
                if chat_id.strip()
            ]
        return [
            ApprovalStep(
                order=index + 1,
                role=step.get("role") or f"Шаг {index + 1}",
                name=step.get("name"),
                chat_id=step.get("chat_id"),
                email=step.get("email"),
            )
            for index, step in enumerate(steps)
        ]

    def _persist_project(self, project: Project) -> None:
        """
        Сохраняет изменения модели проекта.
        """
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)

    def _route_from_project(self, project: Project) -> List[Dict[str, Any]]:
        data = project.teo_approval_route or []
        if isinstance(data, list):
            return data
        if isinstance(data, str):
            try:
                parsed = json.loads(data)
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                logger.debug("Failed to decode stored approval route JSON for project %s", project.code)
        return []

    def _fallback_chat_id(self) -> Optional[str]:
        """
        Возвращает запасной чат для уведомлений (берём первый из списка).
        """
        return settings.TEO_APPROVAL_CHAT_IDS[0] if settings.TEO_APPROVAL_CHAT_IDS else None

    def _sync_with_onec(
        self,
        project: Project,
        analysis: Dict[str, Any],
        request: Optional[ProjectRequest],
    ) -> None:
        """
        Отправляет обновлённый статус согласования в 1С, если интеграция настроена.
        """
        if not onec_service.is_configured():
            return
        try:
            payload = onec_service.build_payload(project=project, request=request, analysis=analysis)
            payload.setdefault("approval", {})
            payload["approval"].update(
                {
                    "status": project.teo_approval_status,
                    "approved_at": project.teo_approved_at.isoformat() if project.teo_approved_at else None,
                    "route": project.teo_approval_route,
                    "history": project.teo_approval_history,
                }
            )
            onec_service.send_payload(payload)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to sync TEO approval status with 1C for project %s: %s", project.code, exc)


__all__ = ["TEOApprovalService", "ApprovalStep"]


