"""
Round-robin распределение менеджеров проектов.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
import json

from sqlalchemy.orm import Session

from backend.config.settings import settings
from backend.models.auth import Role
from backend.models.project import Project
from backend.services.redis_service import redis_service

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ManagerAssignment:
    manager_id: int
    rotation_index: int
    last_assigned_at: Optional[datetime] = None
    active_projects: int = 0


@dataclass(slots=True)
class ManagerLoad:
    manager_id: int
    full_name: Optional[str]
    active_projects: int


class ProjectManagerRotation:
    """Round-robin очередь менеджеров проектов."""

    REDIS_ROTATION_KEY = "project_manager_rotation:last_index"

    def __init__(self, db: Session):
        self.db = db

    def assign_next_manager(self) -> Optional[int]:
        managers = self._load_managers()
        if not managers:
            logger.warning("No managers available for rotation.")
            return settings.DEFAULT_PROJECT_MANAGER_ID

        try:
            last_index_raw = redis_service.get(self.REDIS_ROTATION_KEY)
            last_index = int(last_index_raw) if last_index_raw is not None else -1
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to read rotation state from Redis: %s", exc)
            last_index = -1

        next_index = (last_index + 1) % len(managers)
        selected = managers[next_index]

        try:
            redis_service.set(self.REDIS_ROTATION_KEY, next_index)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to persist rotation index: %s", exc)

        self._cache_manager_loads(managers)

        logger.info(
            "Assigned manager %s using rotation index %s (last assigned %s)",
            selected.manager_id,
            next_index,
            selected.last_assigned_at,
        )
        return selected.manager_id

    def list_manager_loads(self) -> List[ManagerLoad]:
        manager_role = self.db.query(Role).filter(Role.name == "manager").first()
        if not manager_role:
            return []
        loads: List[ManagerLoad] = []
        for user in manager_role.users:
            if not user.is_active:
                continue
            active_count = (
                self.db.query(Project)
                .filter(
                    Project.manager_id == user.id,
                    Project.status.notin_(["completed", "cancelled"]),
                )
                .count()
            )
            loads.append(ManagerLoad(manager_id=user.id, full_name=user.full_name, active_projects=active_count))
        loads.sort(key=lambda item: (item.active_projects, item.manager_id))
        return loads

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #

    def _load_managers(self) -> List[ManagerAssignment]:
        manager_role = self.db.query(Role).filter(Role.name == "manager").first()
        if not manager_role:
            return []

        manager_ids = [user.id for user in manager_role.users if user.is_active]
        if not manager_ids:
            return []

        last_map = {mid: self._get_last_project_date(mid) for mid in manager_ids}
        load_map = {mid: self._get_active_project_count(mid) for mid in manager_ids}

        rotation = []
        for idx, manager_id in enumerate(sorted(manager_ids)):
            rotation.append(
                ManagerAssignment(
                    manager_id=manager_id,
                    rotation_index=idx,
                    last_assigned_at=last_map.get(manager_id),
                    active_projects=load_map.get(manager_id, 0),
                )
            )
        rotation.sort(
            key=lambda item: (
                item.active_projects,
                item.last_assigned_at or datetime.min,
                item.rotation_index,
            )
        )
        return rotation

    def _get_last_project_date(self, manager_id: int) -> Optional[datetime]:
        project = (
            self.db.query(Project)
            .filter(Project.manager_id == manager_id)
            .order_by(Project.created_at.desc())
            .first()
        )
        return project.created_at if project else None

    def _get_active_project_count(self, manager_id: int) -> int:
        return (
            self.db.query(Project)
            .filter(
                Project.manager_id == manager_id,
                Project.status.notin_(["completed", "cancelled"]),
            )
            .count()
        )

    def _cache_manager_loads(self, managers: List[ManagerAssignment]) -> None:
        payload = [
            {
                "manager_id": item.manager_id,
                "active_projects": item.active_projects,
                "last_assigned_at": item.last_assigned_at.isoformat() if item.last_assigned_at else None,
            }
            for item in managers
        ]
        try:
            redis_service.set("project_manager_rotation:loads", json.dumps(payload), ex=300)
        except Exception as exc:  # noqa: BLE001
            logger.debug("Failed to cache manager loads: %s", exc)


__all__ = ["ProjectManagerRotation", "ManagerLoad"]


