"""
API эндпоинты для запуска конвейера предварительного ТЭО.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.models import get_db
from backend.models.project import Project
from backend.schemas.teo import (
    CostEntrySchema,
    CostSummarySchema,
    FinancialRiskSchema,
    FinancialSummarySchema,
    LaborEntrySchema,
    LaborSummarySchema,
    MatchedNormSchema,
    TEOApprovalDecisionSchema,
    TEOApprovalStatusSchema,
    TEORequestSchema,
    TEOResponseSchema,
    TravelSummarySchema,
    WorkVolumeSchema,
)
from backend.services.teo_pipeline import MatchedNorm, PipelineResult, PreliminaryTEOPipeline
from backend.services.teo_approval_service import TEOApprovalService

router = APIRouter(prefix="/teo", tags=["teo"])


def _serialize_decimal(value: Decimal) -> float:
    return float(value)


def _serialize_matched_norm(match: MatchedNorm) -> Dict[str, Any]:
    return {
        "volume": {
            "name": match.volume.name,
            "quantity": _serialize_decimal(match.volume.quantity),
            "unit": match.volume.unit,
            "source_line": match.volume.source_line,
            "code": match.volume.code,
            "category": match.volume.category,
        },
        "norm_code": match.norm_code,
        "reasoning": match.reasoning,
        "candidate_scores": match.candidate_scores,
    }


def _serialize_pipeline_result(result: PipelineResult) -> TEOResponseSchema:
    volumes = [
        WorkVolumeSchema(
            name=entry.name,
            quantity=entry.quantity,
            unit=entry.unit,
            source_line=entry.source_line,
            code=entry.code,
            category=entry.category,
        )
        for entry in result.volumes
    ]

    matches = [_serialize_matched_norm(match) for match in result.matches]

    cost_entries = [
        CostEntrySchema(
            name=entry.name,
            quantity=entry.quantity,
            unit=entry.unit,
            cost=entry.cost,
            material_price={
                "price_per_unit": entry.material_price.price_per_unit,
            }
            if entry.material_price
            else None,
            warnings=entry.warnings,
        )
        for entry in result.cost.entries
    ]

    cost_summary = CostSummarySchema(
        total_cost=result.cost.summary.total_cost,
        by_category=result.cost.summary.by_category,
        missing_prices=result.cost.summary.missing_prices,
    )

    labor_summary = None
    if result.labor:
        labor_summary = LaborSummarySchema(
            total_labor_hours=result.labor.total_labor_hours,
            total_worker_equivalent=result.labor.total_worker_equivalent,
            worker_days=result.labor.worker_days,
            schedules=result.labor.schedules,
            entries=[
                LaborEntrySchema(
                    volume_name=entry.volume_name,
                    norm_code=entry.norm_code,
                    labor_hours=entry.labor_hours,
                    worker_equivalent=entry.worker_equivalent,
                    resources=entry.resources,
                )
                for entry in result.labor.entries
            ],
        )

    travel_summary = None
    if result.travel:
        travel_summary = TravelSummarySchema(**result.travel)

    financial_summary = None
    if result.financial:
        risk = result.financial.get("risk") or {}
        financial_summary = FinancialSummarySchema(
            npv=result.financial.get("npv", 0.0),
            irr_percent=result.financial.get("irr_percent"),
            payback_months=result.financial.get("payback_months"),
            assumptions={
                key: float(value)
                for key, value in (result.financial.get("assumptions") or {}).items()
            },
            risk=FinancialRiskSchema(
                score=risk.get("score", 0.0),
                level=risk.get("level", "n/a"),
                factors=risk.get("factors", []),
            ),
        )

    return TEOResponseSchema(
        warnings=result.warnings,
        volumes=volumes,
        matches=matches,
        cost_entries=cost_entries,
        cost_summary=cost_summary,
        labor_summary=labor_summary,
        travel_summary=travel_summary,
        financial_summary=financial_summary,
    )


@router.post("/calculate", response_model=TEOResponseSchema)
def calculate_teo(payload: TEORequestSchema, db: Session = Depends(get_db)) -> TEOResponseSchema:
    """
    Запускает конвейер предварительного ТЭО для указанного документа.
    """
    pipeline = PreliminaryTEOPipeline(session=db)
    try:
        result = pipeline.process_file(payload.file_path, top_k=payload.top_k)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Ошибка обработки ТЭО: {exc}") from exc

    return _serialize_pipeline_result(result)


def _build_documents(project: Project) -> Dict[str, str]:
    """
    Возвращает ссылки на файлы предварительного ТЭО в MinIO.
    """
    documents: Dict[str, str] = {}
    if project.preliminary_teo_path:
        documents["docx"] = project.preliminary_teo_path
        base = project.preliminary_teo_path.rsplit(".", 1)[0]
        documents["pdf"] = f"{base}.pdf"
        documents["xlsx"] = f"{base}.xlsx"
    return documents


def _build_analysis_stub(project: Project) -> Dict[str, Any]:
    """
    Формирует минимальный набор аналитики для уведомлений о согласовании.
    """
    payload: Dict[str, Any] = {"cost": {}, "timeline": {}}
    if project.preliminary_budget is not None:
        try:
            payload["cost"]["grand_total"] = float(project.preliminary_budget)
        except (TypeError, ValueError):
            pass
    if project.planned_duration_days is not None:
        payload["timeline"]["estimated_duration_days"] = project.planned_duration_days
    return payload


@router.post(
    "/projects/{project_id}/approval/decision",
    response_model=TEOApprovalStatusSchema,
    summary="Фиксация решения по согласованию ТЭО",
)
def record_teo_approval_decision(
    project_id: int,
    payload: TEOApprovalDecisionSchema,
    db: Session = Depends(get_db),
) -> TEOApprovalStatusSchema:
    project: Optional[Project] = db.query(Project).filter(Project.id == project_id).one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Проект не найден.")

    approval_service = TEOApprovalService(db)
    approval_service.record_decision(
        project,
        role=payload.role,
        decision=payload.decision,
        actor=payload.actor,
        comment=payload.comment,
        documents=_build_documents(project),
        analysis=_build_analysis_stub(project),
    )

    return TEOApprovalStatusSchema(
        status=project.teo_approval_status,
        route=project.teo_approval_route or [],
        history=project.teo_approval_history or [],
    )


