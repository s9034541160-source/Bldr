# -*- coding: utf-8 -*-
"""
Thread-safe dialog manager maintaining per-user dialog state with timeout.
"""
from __future__ import annotations
import time
from typing import Dict, Optional, List, Any
from threading import RLock

from .dialog_state import DialogState, DialogStatus


class DialogManager:
    def __init__(self, timeout_seconds: int = 300) -> None:
        self._dialogs_by_key: Dict[str, DialogState] = {}
        self._user_last_waiting: Dict[str, str] = {}
        self._lock = RLock()
        self.timeout_seconds = timeout_seconds

    def get_dialog(self, dialog_key: Optional[str]) -> Optional[DialogState]:
        if not dialog_key:
            return None
        with self._lock:
            ds = self._dialogs_by_key.get(dialog_key)
            if not ds:
                return None
            if ds.status == DialogStatus.WAITING_FOR_USER_INPUT and (time.time() - ds.last_interaction_time > self.timeout_seconds):
                # Auto-expire waiting dialogs
                self._dialogs_by_key.pop(dialog_key, None)
                # Clear user last waiting if matches
                if self._user_last_waiting.get(ds.user_id) == dialog_key:
                    self._user_last_waiting.pop(ds.user_id, None)
                return None
            return ds

    def get_last_waiting_for_user(self, user_id: Optional[str]) -> Optional[DialogState]:
        if not user_id:
            return None
        with self._lock:
            key = self._user_last_waiting.get(user_id)
            if not key:
                return None
            ds = self._dialogs_by_key.get(key)
            if ds and ds.status == DialogStatus.WAITING_FOR_USER_INPUT:
                # Check timeout
                if time.time() - ds.last_interaction_time > self.timeout_seconds:
                    self._dialogs_by_key.pop(key, None)
                    self._user_last_waiting.pop(user_id, None)
                    return None
                return ds
            return None

    def create_waiting_dialog(
        self,
        user_id: str,
        dialog_key: str,
        original_query: str,
        plan: Optional[Dict[str, Any]],
        pending_question: str,
        tool_results_so_far: Optional[List[Dict[str, Any]]] = None,
    ) -> DialogState:
        with self._lock:
            ds = DialogState(
                user_id=user_id,
                dialog_key=dialog_key,
                status=DialogStatus.WAITING_FOR_USER_INPUT,
                original_query=original_query,
                current_plan=plan,
                pending_question=pending_question,
            )
            if tool_results_so_far:
                ds.tool_results_so_far = list(tool_results_so_far)
            self._dialogs_by_key[dialog_key] = ds
            # Track last waiting for this user (latest wins)
            self._user_last_waiting[user_id] = dialog_key
            return ds

    def resume_dialog_by_key(self, dialog_key: str, user_input: str) -> Optional[DialogState]:
        with self._lock:
            ds = self._dialogs_by_key.get(dialog_key)
            if not ds or ds.status != DialogStatus.WAITING_FOR_USER_INPUT:
                return None
            ds.status = DialogStatus.PROCESSING
            ds.last_interaction_time = time.time()
            ds.tool_results_so_far.append({
                "tool": "user_input",
                "status": "success",
                "result": {"clarification": user_input}
            })
            return ds

    def resume_last_waiting_for_user(self, user_id: str, user_input: str) -> Optional[DialogState]:
        with self._lock:
            key = self._user_last_waiting.get(user_id)
            if not key:
                return None
            ds = self._dialogs_by_key.get(key)
            if not ds or ds.status != DialogStatus.WAITING_FOR_USER_INPUT:
                return None
            ds.status = DialogStatus.PROCESSING
            ds.last_interaction_time = time.time()
            ds.tool_results_so_far.append({
                "tool": "user_input",
                "status": "success",
                "result": {"clarification": user_input}
            })
            return ds

    def clear_dialog(self, dialog_key: Optional[str]) -> None:
        if not dialog_key:
            return
        with self._lock:
            ds = self._dialogs_by_key.pop(dialog_key, None)
            if ds and self._user_last_waiting.get(ds.user_id) == dialog_key:
                self._user_last_waiting.pop(ds.user_id, None)

    def is_waiting(self, dialog_key: Optional[str]) -> bool:
        if not dialog_key:
            return False
        with self._lock:
            ds = self._dialogs_by_key.get(dialog_key)
            return bool(ds and ds.status == DialogStatus.WAITING_FOR_USER_INPUT)


# Global singleton for easy access
dialog_manager = DialogManager()
