"""
Построение CPM-графа и расчёт критического пути.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional

import networkx as nx

from backend.services.calendar_plan.dependency_builder import DependencyGraph
from backend.services.calendar_plan.work_catalog_builder import WorkCatalog, WorkTask

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class CPMNode:
    task_id: str
    task: WorkTask
    early_start: float
    early_finish: float
    late_start: float
    late_finish: float
    slack: float
    critical: bool


@dataclass(slots=True)
class CPMResult:
    graph: nx.DiGraph
    nodes: Dict[str, CPMNode]
    critical_path: List[str]
    project_duration: float


class CPMBuilder:
    """
    Рассчитывает параметры CPM (текущий проект — в днях).
    """

    def build(self, catalog: WorkCatalog, dependencies: DependencyGraph) -> CPMResult:
        graph = nx.DiGraph()

        durations: Dict[str, float] = {}

        for scheduled_task in dependencies.tasks:
            duration = self._duration_in_days(scheduled_task.task.duration_days)
            durations[scheduled_task.task_id] = duration
            graph.add_node(scheduled_task.task_id, task=scheduled_task.task, duration=duration)

        for edge in dependencies.edges:
            if edge.predecessor_id not in graph or edge.successor_id not in graph:
                logger.debug("Edge skipped: %s -> %s", edge.predecessor_id, edge.successor_id)
                continue
            graph.add_edge(edge.predecessor_id, edge.successor_id, relation=edge.relation)

        if not nx.is_directed_acyclic_graph(graph):
            raise ValueError("Граф зависимостей содержит цикл; CPM невозможен.")

        earliest_start, earliest_finish = self._forward_pass(graph, durations)
        latest_start, latest_finish, project_duration = self._backward_pass(graph, durations, earliest_finish)
        nodes: Dict[str, CPMNode] = {}
        critical_path: List[str] = []

        for node in graph.nodes:
            es = earliest_start[node]
            ef = earliest_finish[node]
            ls = latest_start[node]
            lf = latest_finish[node]
            slack = max(0.0, ls - es)
            critical = abs(slack) < 1e-6
            nodes[node] = CPMNode(
                task_id=node,
                task=graph.nodes[node]["task"],
                early_start=es,
                early_finish=ef,
                late_start=ls,
                late_finish=lf,
                slack=slack,
                critical=critical,
            )
            graph.nodes[node]["cpm"] = nodes[node]
            if critical:
                critical_path.append(node)

        return CPMResult(
            graph=graph,
            nodes=nodes,
            critical_path=critical_path,
            project_duration=project_duration,
        )

    @staticmethod
    def _duration_in_days(value: Optional[float]) -> float:
        if value is None:
            return 1.0
        try:
            return max(0.1, float(value))
        except (TypeError, ValueError):
            return 1.0

    @staticmethod
    def _forward_pass(graph: nx.DiGraph, durations: Dict[str, float]) -> tuple[Dict[str, float], Dict[str, float]]:
        es: Dict[str, float] = {}
        ef: Dict[str, float] = {}
        for node in nx.topological_sort(graph):
            incoming = list(graph.predecessors(node))
            start = max((ef[pred] for pred in incoming), default=0.0)
            es[node] = start
            ef[node] = start + durations[node]
        return es, ef

    @staticmethod
    def _backward_pass(
        graph: nx.DiGraph,
        durations: Dict[str, float],
        earliest_finish: Dict[str, float],
    ) -> tuple[Dict[str, float], Dict[str, float], float]:
        latest_finish: Dict[str, float] = {}
        latest_start: Dict[str, float] = {}
        project_duration = max(earliest_finish.values(), default=0.0)
        for node in reversed(list(nx.topological_sort(graph))):
            outgoing = list(graph.successors(node))
            finish = min((latest_start[succ] for succ in outgoing), default=project_duration)
            latest_finish[node] = finish
            latest_start[node] = finish - durations[node]
        return latest_start, latest_finish, project_duration


__all__ = ["CPMBuilder", "CPMResult", "CPMNode"]


