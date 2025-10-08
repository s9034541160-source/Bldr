#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EXECUTION TRACER FOR Bldr Empire
===============================

Система трассировки выполнения на основе паттернов
из agents-towards-production.
"""

import uuid
import time
import traceback
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json

from core.structured_logging import get_logger

logger = get_logger("execution_tracer")

class TraceStatus(str, Enum):
    """Статусы трассировки"""
    STARTED = "started"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"

class TraceType(str, Enum):
    """Типы трассировки"""
    TOOL_EXECUTION = "tool_execution"
    AGENT_CALL = "agent_call"
    RAG_QUERY = "rag_query"
    LLM_CALL = "llm_call"
    COORDINATOR_PLAN = "coordinator_plan"
    USER_INTERACTION = "user_interaction"

@dataclass
class TraceSpan:
    """Спан трассировки"""
    span_id: str
    parent_id: Optional[str]
    trace_id: str
    operation_name: str
    trace_type: TraceType
    status: TraceStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    traceback: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)
    
    def finish(self, status: TraceStatus = TraceStatus.COMPLETED, error: Exception = None):
        """Завершение спана"""
        self.end_time = datetime.now()
        self.duration_ms = (self.end_time - self.start_time).total_seconds() * 1000
        self.status = status
        
        if error:
            self.error = str(error)
            self.traceback = traceback.format_exc()
            self.status = TraceStatus.FAILED
    
    def to_dict(self) -> Dict[str, Any]:
        """Конвертация в словарь"""
        return {
            "span_id": self.span_id,
            "parent_id": self.parent_id,
            "trace_id": self.trace_id,
            "operation_name": self.operation_name,
            "trace_type": self.trace_type.value,
            "status": self.status.value,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": self.duration_ms,
            "metadata": self.metadata,
            "error": self.error,
            "traceback": self.traceback,
            "tags": self.tags
        }

class ExecutionTracer:
    """
    🚀 СИСТЕМА ТРАССИРОВКИ ВЫПОЛНЕНИЯ
    
    Отслеживает выполнение операций для отладки и мониторинга
    """
    
    def __init__(self):
        self.active_spans: Dict[str, TraceSpan] = {}
        self.completed_spans: List[TraceSpan] = []
        self.logger = get_logger("execution_tracer")
    
    def start_span(self, operation_name: str, trace_type: TraceType, 
                   parent_span_id: Optional[str] = None,
                   metadata: Dict[str, Any] = None,
                   tags: Dict[str, str] = None) -> str:
        """
        🎯 НАЧАЛО НОВОГО СПАНА
        
        Args:
            operation_name: Название операции
            trace_type: Тип трассировки
            parent_span_id: ID родительского спана
            metadata: Метаданные
            tags: Теги
        
        Returns:
            ID созданного спана
        """
        span_id = str(uuid.uuid4())
        trace_id = parent_span_id or str(uuid.uuid4())
        
        span = TraceSpan(
            span_id=span_id,
            parent_id=parent_span_id,
            trace_id=trace_id,
            operation_name=operation_name,
            trace_type=trace_type,
            status=TraceStatus.STARTED,
            start_time=datetime.now(),
            metadata=metadata or {},
            tags=tags or {}
        )
        
        self.active_spans[span_id] = span
        
        self.logger.log_agent_activity(
            agent_name="execution_tracer",
            action="span_started",
            query=operation_name,
            result_status="started",
            context={
                "span_id": span_id,
                "trace_id": trace_id,
                "operation_name": operation_name,
                "trace_type": trace_type.value
            }
        )
        
        return span_id
    
    def finish_span(self, span_id: str, status: TraceStatus = TraceStatus.COMPLETED, 
                   error: Exception = None, metadata: Dict[str, Any] = None):
        """
        🎯 ЗАВЕРШЕНИЕ СПАНА
        
        Args:
            span_id: ID спана
            status: Статус завершения
            error: Ошибка (если есть)
            metadata: Дополнительные метаданные
        """
        if span_id not in self.active_spans:
            self.logger.log_error(
                Exception(f"Span {span_id} not found"),
                {"span_id": span_id}
            )
            return
        
        span = self.active_spans[span_id]
        
        # Добавляем метаданные
        if metadata:
            span.metadata.update(metadata)
        
        # Завершаем спан
        span.finish(status, error)
        
        # Перемещаем в завершенные
        del self.active_spans[span_id]
        self.completed_spans.append(span)
        
        self.logger.log_agent_activity(
            agent_name="execution_tracer",
            action="span_finished",
            query=span.operation_name,
            result_status=status.value,
            context={
                "span_id": span_id,
                "trace_id": span.trace_id,
                "duration_ms": span.duration_ms,
                "status": status.value
            }
        )
    
    def add_span_metadata(self, span_id: str, metadata: Dict[str, Any]):
        """Добавление метаданных к спану"""
        if span_id in self.active_spans:
            self.active_spans[span_id].metadata.update(metadata)
    
    def add_span_tags(self, span_id: str, tags: Dict[str, str]):
        """Добавление тегов к спану"""
        if span_id in self.active_spans:
            self.active_spans[span_id].tags.update(tags)
    
    def get_trace(self, trace_id: str) -> List[TraceSpan]:
        """Получение всех спанов трассировки"""
        return [span for span in self.completed_spans if span.trace_id == trace_id]
    
    def get_active_spans(self) -> List[TraceSpan]:
        """Получение активных спанов"""
        return list(self.active_spans.values())
    
    def get_trace_summary(self, trace_id: str) -> Dict[str, Any]:
        """Получение сводки по трассировке"""
        spans = self.get_trace(trace_id)
        
        if not spans:
            return {"error": "Trace not found"}
        
        total_duration = sum(span.duration_ms or 0 for span in spans)
        failed_spans = [span for span in spans if span.status == TraceStatus.FAILED]
        
        return {
            "trace_id": trace_id,
            "total_spans": len(spans),
            "total_duration_ms": total_duration,
            "failed_spans": len(failed_spans),
            "success_rate": (len(spans) - len(failed_spans)) / len(spans) if spans else 0,
            "spans": [span.to_dict() for span in spans]
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Получение метрик производительности"""
        if not self.completed_spans:
            return {"message": "No completed spans"}
        
        # Группируем по типам операций
        by_type = {}
        for span in self.completed_spans:
            trace_type = span.trace_type.value
            if trace_type not in by_type:
                by_type[trace_type] = []
            by_type[trace_type].append(span)
        
        metrics = {}
        for trace_type, spans in by_type.items():
            durations = [span.duration_ms for span in spans if span.duration_ms]
            failed_count = len([span for span in spans if span.status == TraceStatus.FAILED])
            
            metrics[trace_type] = {
                "total_operations": len(spans),
                "failed_operations": failed_count,
                "success_rate": (len(spans) - failed_count) / len(spans) if spans else 0,
                "avg_duration_ms": sum(durations) / len(durations) if durations else 0,
                "min_duration_ms": min(durations) if durations else 0,
                "max_duration_ms": max(durations) if durations else 0
            }
        
        return metrics

# Глобальный трейсер
_global_tracer: Optional[ExecutionTracer] = None

def get_tracer() -> ExecutionTracer:
    """Получение глобального трейсера"""
    global _global_tracer
    if _global_tracer is None:
        _global_tracer = ExecutionTracer()
    return _global_tracer

# Декоратор для автоматической трассировки
def trace_execution(operation_name: str, trace_type: TraceType):
    """Декоратор для автоматической трассировки выполнения"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            tracer = get_tracer()
            span_id = tracer.start_span(
                operation_name=operation_name,
                trace_type=trace_type,
                metadata={"function": func.__name__}
            )
            
            try:
                result = func(*args, **kwargs)
                tracer.finish_span(span_id, TraceStatus.COMPLETED)
                return result
            except Exception as e:
                tracer.finish_span(span_id, TraceStatus.FAILED, e)
                raise
        
        return wrapper
    return decorator
