#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TRACING API FOR Bldr Empire
===========================

API endpoints для мониторинга трассировки выполнения
на основе паттернов из agents-towards-production.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from core.tracing.execution_tracer import get_tracer, TraceStatus, TraceType
from core.structured_logging import get_logger

router = APIRouter(prefix="/tracing", tags=["tracing"])
logger = get_logger("tracing_api")

class TraceSummary(BaseModel):
    """Сводка по трассировке"""
    trace_id: str
    total_spans: int
    total_duration_ms: float
    failed_spans: int
    success_rate: float
    spans: List[Dict[str, Any]]

class PerformanceMetrics(BaseModel):
    """Метрики производительности"""
    trace_type: str
    total_operations: int
    failed_operations: int
    success_rate: float
    avg_duration_ms: float
    min_duration_ms: float
    max_duration_ms: float

@router.get("/traces/{trace_id}")
async def get_trace(trace_id: str):
    """
    🚀 ПОЛУЧЕНИЕ ТРАССИРОВКИ ПО ID
    
    Возвращает полную информацию о трассировке
    """
    try:
        tracer = get_tracer()
        trace_summary = tracer.get_trace_summary(trace_id)
        
        if "error" in trace_summary:
            raise HTTPException(status_code=404, detail=trace_summary["error"])
        
        logger.log_agent_activity(
            agent_name="tracing_api",
            action="trace_retrieved",
            query=trace_id,
            result_status="success",
            context={"trace_id": trace_id, "spans_count": trace_summary["total_spans"]}
        )
        
        return {
            "status": "success",
            "trace": trace_summary
        }
        
    except Exception as e:
        logger.log_error(e, {"trace_id": trace_id})
        raise HTTPException(status_code=500, detail=f"Failed to get trace: {str(e)}")

@router.get("/traces")
async def list_traces(limit: int = Query(default=50, ge=1, le=1000)):
    """
    🚀 ПОЛУЧЕНИЕ СПИСКА ТРАССИРОВОК
    
    Возвращает список последних трассировок
    """
    try:
        tracer = get_tracer()
        completed_spans = tracer.completed_spans
        
        # Группируем по trace_id
        traces = {}
        for span in completed_spans[-limit*10:]:  # Берем больше спанов для группировки
            if span.trace_id not in traces:
                traces[span.trace_id] = []
            traces[span.trace_id].append(span)
        
        # Создаем сводки
        trace_list = []
        for trace_id, spans in list(traces.items())[-limit:]:
            total_duration = sum(span.duration_ms or 0 for span in spans)
            failed_count = len([span for span in spans if span.status == TraceStatus.FAILED])
            
            trace_list.append({
                "trace_id": trace_id,
                "total_spans": len(spans),
                "total_duration_ms": total_duration,
                "failed_spans": failed_count,
                "success_rate": (len(spans) - failed_count) / len(spans) if spans else 0,
                "first_span_time": min(span.start_time for span in spans).isoformat(),
                "last_span_time": max(span.end_time for span in spans if span.end_time).isoformat()
            })
        
        logger.log_agent_activity(
            agent_name="tracing_api",
            action="traces_listed",
            query="",
            result_status="success",
            context={"traces_count": len(trace_list), "limit": limit}
        )
        
        return {
            "status": "success",
            "traces": trace_list,
            "total_count": len(trace_list)
        }
        
    except Exception as e:
        logger.log_error(e, {})
        raise HTTPException(status_code=500, detail=f"Failed to list traces: {str(e)}")

@router.get("/active-spans")
async def get_active_spans():
    """
    🚀 ПОЛУЧЕНИЕ АКТИВНЫХ СПАНОВ
    
    Возвращает список текущих активных спанов
    """
    try:
        tracer = get_tracer()
        active_spans = tracer.get_active_spans()
        
        spans_data = [span.to_dict() for span in active_spans]
        
        logger.log_agent_activity(
            agent_name="tracing_api",
            action="active_spans_retrieved",
            query="",
            result_status="success",
            context={"active_spans_count": len(spans_data)}
        )
        
        return {
            "status": "success",
            "active_spans": spans_data,
            "count": len(spans_data)
        }
        
    except Exception as e:
        logger.log_error(e, {})
        raise HTTPException(status_code=500, detail=f"Failed to get active spans: {str(e)}")

@router.get("/performance")
async def get_performance_metrics():
    """
    🚀 ПОЛУЧЕНИЕ МЕТРИК ПРОИЗВОДИТЕЛЬНОСТИ
    
    Возвращает метрики производительности по типам операций
    """
    try:
        tracer = get_tracer()
        metrics = tracer.get_performance_metrics()
        
        if "message" in metrics:
            return {
                "status": "success",
                "message": metrics["message"],
                "metrics": {}
            }
        
        logger.log_agent_activity(
            agent_name="tracing_api",
            action="performance_metrics_retrieved",
            query="",
            result_status="success",
            context={"metrics_types": list(metrics.keys())}
        )
        
        return {
            "status": "success",
            "metrics": metrics
        }
        
    except Exception as e:
        logger.log_error(e, {})
        raise HTTPException(status_code=500, detail=f"Failed to get performance metrics: {str(e)}")

@router.get("/health")
async def tracing_health_check():
    """
    🚀 ПРОВЕРКА ЗДОРОВЬЯ СИСТЕМЫ ТРАССИРОВКИ
    
    Проверяет состояние системы трассировки
    """
    try:
        tracer = get_tracer()
        
        # Проверяем доступность компонентов
        active_spans = len(tracer.get_active_spans())
        completed_spans = len(tracer.completed_spans)
        
        return {
            "status": "healthy",
            "components": {
                "tracer": "available",
                "active_spans": active_spans,
                "completed_spans": completed_spans
            },
            "timestamp": "2025-09-28T16:00:00Z"
        }
        
    except Exception as e:
        logger.log_error(e, {})
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": "2025-09-28T16:00:00Z"
        }

@router.delete("/traces/{trace_id}")
async def delete_trace(trace_id: str):
    """
    🚀 УДАЛЕНИЕ ТРАССИРОВКИ
    
    Удаляет трассировку из истории (для очистки памяти)
    """
    try:
        tracer = get_tracer()
        
        # Удаляем спаны с указанным trace_id
        original_count = len(tracer.completed_spans)
        tracer.completed_spans = [
            span for span in tracer.completed_spans 
            if span.trace_id != trace_id
        ]
        deleted_count = original_count - len(tracer.completed_spans)
        
        logger.log_agent_activity(
            agent_name="tracing_api",
            action="trace_deleted",
            query=trace_id,
            result_status="success",
            context={"deleted_spans": deleted_count}
        )
        
        return {
            "status": "success",
            "message": f"Deleted {deleted_count} spans from trace {trace_id}"
        }
        
    except Exception as e:
        logger.log_error(e, {"trace_id": trace_id})
        raise HTTPException(status_code=500, detail=f"Failed to delete trace: {str(e)}")

@router.post("/traces/clear")
async def clear_all_traces():
    """
    🚀 ОЧИСТКА ВСЕХ ТРАССИРОВОК
    
    Очищает всю историю трассировок
    """
    try:
        tracer = get_tracer()
        
        completed_count = len(tracer.completed_spans)
        active_count = len(tracer.get_active_spans())
        
        tracer.completed_spans.clear()
        
        logger.log_agent_activity(
            agent_name="tracing_api",
            action="traces_cleared",
            query="",
            result_status="success",
            context={"completed_spans_cleared": completed_count, "active_spans": active_count}
        )
        
        return {
            "status": "success",
            "message": f"Cleared {completed_count} completed spans",
            "active_spans_remaining": active_count
        }
        
    except Exception as e:
        logger.log_error(e, {})
        raise HTTPException(status_code=500, detail=f"Failed to clear traces: {str(e)}")
