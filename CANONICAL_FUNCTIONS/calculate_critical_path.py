# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: calculate_critical_path
# Основной источник: C:\Bldr\core\gpp_creator.py
# Дубликаты (для справки):
#   - C:\Bldr\core\ppr_generator.py
#================================================================================
def calculate_critical_path(works_seq: List[Dict[str, Any]]) -> List[str]:
    """
    Calculate critical path for the project
    
    Args:
        works_seq: Work sequences
        
    Returns:
        List of task IDs in critical path
    """
    # Create directed graph
    G = nx.DiGraph()
    
    # Add nodes
    for i, work in enumerate(works_seq):
        task_id = f"TASK_{i+1:03d}"
        duration = work.get("duration", 1.0)
        G.add_node(task_id, duration=duration, name=work.get("name", f"Работа {i+1}"))
    
    # Add edges (dependencies)
    task_mapping = {work.get("name", f"Работа {i+1}"): f"TASK_{i+1:03d}" 
                   for i, work in enumerate(works_seq)}
    
    for i, work in enumerate(works_seq):
        task_id = f"TASK_{i+1:03d}"
        dependencies = work.get("deps", [])
        
        for dep in dependencies:
            dep_task_id = task_mapping.get(dep)
            if dep_task_id and dep_task_id in G.nodes():
                G.add_edge(dep_task_id, task_id)
    
    # Calculate critical path using network analysis
    try:
        # Topological sort
        topological_order = list(nx.topological_sort(G))
        
        # Initialize earliest start and finish times
        earliest_start = {node: 0 for node in G.nodes()}
        earliest_finish = {node: 0 for node in G.nodes()}
        
        # Forward pass
        for node in topological_order:
            duration = G.nodes[node].get("duration", 0.0)
            earliest_finish[node] = earliest_start[node] + duration
            
            # Update successors
            for successor in G.successors(node):
                earliest_start[successor] = max(earliest_start[successor], earliest_finish[node])
        
        # Initialize latest start and finish times
        project_duration = max(earliest_finish.values()) if earliest_finish else 0
        latest_finish = {node: project_duration for node in G.nodes()}
        latest_start = {node: project_duration for node in G.nodes()}
        
        # Backward pass
        for node in reversed(topological_order):
            duration = G.nodes[node].get("duration", 0.0)
            latest_start[node] = latest_finish[node] - duration
            
            # Update predecessors
            for predecessor in G.predecessors(node):
                latest_finish[predecessor] = min(latest_finish[predecessor], latest_start[node])
        
        # Identify critical path (activities with zero slack)
        critical_path = []
        for node in G.nodes():
            slack = latest_start[node] - earliest_start[node]
            if abs(slack) < 1e-6:  # Essentially zero
                critical_path.append(node)
        
        return critical_path
        
    except (nx.NetworkXError, nx.NetworkXUnfeasible):
        # Fallback to simple approach if graph has issues
        return [f"TASK_{i+1:03d}" for i in range(min(5, len(works_seq)))]  # First 5 tasks