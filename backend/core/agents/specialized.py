"""Специализированные агенты для ключевых доменов BLDR."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from backend.core.agent import BaseAgent
from backend.core.model_manager import model_manager

logger = logging.getLogger(__name__)


class DomainAgent(BaseAgent):
    """Агент, умеющий работать с доменно-специализированными моделями."""

    domain: str = "general"
    default_summary_key: str = "summary"

    def __init__(
        self,
        agent_id: str,
        name: str,
        description: str,
        domain: Optional[str] = None,
    ):
        super().__init__(agent_id=agent_id, name=name, description=description)
        if domain:
            self.domain = domain
        self.active_model_id: Optional[str] = None

    def ensure_domain_model(self) -> Optional[str]:
        """Гарантирует наличие подходящей модели для домена."""
        if self.domain == "general":
            return model_manager.current_model

        if self.active_model_id and self.active_model_id in model_manager.list_registered_models():
            return self.active_model_id

        loaded_model_id = model_manager.load_model_by_domain(self.domain)
        if loaded_model_id:
            self.active_model_id = loaded_model_id
            logger.info("Agent %s loaded domain model %s", self.agent_id, loaded_model_id)
        else:
            logger.warning(
                "Agent %s could not find domain model for domain '%s'",
                self.agent_id,
                self.domain,
            )
        return loaded_model_id

    def execute(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        self.ensure_domain_model()
        enriched_context = self.enrich_context(task, context)
        result = super().execute(task, enriched_context)
        result["domain"] = self.domain
        return result

    def enrich_context(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Добавляет доменные подсказки в контекст (может быть переопределено)."""
        if self.domain and self.domain != "general":
            context = dict(context)
            context.setdefault("domain", self.domain)
        return context


class ProjectAgent(DomainAgent):
    """Агент для управления проектами."""

    domain = "general"

    def __init__(self):
        super().__init__(
            agent_id="project_agent",
            name="Project Agent",
            description="Агент для анализа и управления проектными данными",
        )

    def enrich_context(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        context = super().enrich_context(task, context)
        context.setdefault("summary_type", "project_status")
        return context


class DocumentAgent(DomainAgent):
    """Агент для работы с документами и комплаенсом."""

    domain = "legal"

    def __init__(self):
        super().__init__(
            agent_id="document_agent",
            name="Document Agent",
            description="Агент для анализа и классификации документации",
            domain="legal",
        )

    def enrich_context(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        context = super().enrich_context(task, context)
        context.setdefault("required_outputs", ["classification", "compliance_flags"])
        return context


class EstimateAgent(DomainAgent):
    """Агент для сметных расчетов и финансовых оценок."""

    domain = "finance"

    def __init__(self):
        super().__init__(
            agent_id="estimate_agent",
            name="Estimate Agent",
            description="Агент для расчета смет и финансовых показателей",
            domain="finance",
        )

    def enrich_context(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        context = super().enrich_context(task, context)
        context.setdefault("requires_breakdown", True)
        context.setdefault("currency", "RUB")
        return context


class ProcessAgent(DomainAgent):
    """Агент для управления бизнес-процессами."""

    domain = "general"

    def __init__(self):
        super().__init__(
            agent_id="process_agent",
            name="Process Agent",
            description="Агент для мониторинга и оптимизации процессов",
        )

    def enrich_context(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        context = super().enrich_context(task, context)
        context.setdefault("needs_sop", True)
        context.setdefault("kpi_focus", ["sla", "bottlenecks"])
        return context


def bootstrap_default_agents() -> Dict[str, DomainAgent]:
    """Создает и возвращает набор агентов по умолчанию."""
    agents = {
        "project_agent": ProjectAgent(),
        "document_agent": DocumentAgent(),
        "estimate_agent": EstimateAgent(),
        "process_agent": ProcessAgent(),
    }
    return agents
