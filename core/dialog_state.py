# -*- coding: utf-8 -*-
"""
Dialog state definitions for per-user conversational control.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any, List
import time


class DialogStatus(Enum):
    WAITING_FOR_USER_INPUT = "waiting_for_user_input"
    PROCESSING = "processing"
    COMPLETED = "completed"


@dataclass
class DialogState:
    user_id: str
    dialog_key: str
    status: DialogStatus
    original_query: str
    current_plan: Optional[Dict[str, Any]] = None
    current_step: Optional[int] = None
    tool_results_so_far: List[Dict[str, Any]] = field(default_factory=list)
    pending_question: Optional[str] = None
    last_interaction_time: float = field(default_factory=lambda: time.time())
