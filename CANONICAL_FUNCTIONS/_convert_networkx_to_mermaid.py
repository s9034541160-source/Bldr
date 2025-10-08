# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: _convert_networkx_to_mermaid
# Основной источник: C:\Bldr\scripts\bldr_rag_trainer.py
# Дубликаты (для справки):
#   - C:\Bldr\scripts\optimized_bldr_rag_trainer.py
#================================================================================
    def _convert_networkx_to_mermaid(self, G: nx.DiGraph) -> str:
        """
        Convert NetworkX graph to Mermaid diagram string with colored nodes based on entity types
        
        Args:
            G: NetworkX directed graph with task dependencies
            
        Returns:
            Mermaid diagram string
        """
        # Start mermaid diagram
        mermaid_lines = ["graph TD"]
        
        # Add nodes with colors based on entity types
        for node in G.nodes():
            node_data = G.nodes[node]
            node_name = node_data.get('name', node)
            node_type = node_data.get('type', 'default')
            
            # Escape special characters in node names
            escaped_name = node_name.replace('"', '&quot;').replace("'", "&#39;")
            
            # Assign colors based on node type
            color_map = {
                'work': 'fill:#4CAF50,stroke:#388E3C',      # Green for works
                'material': 'fill:#2196F3,stroke:#0D47A1',  # Blue for materials
                'finance': 'fill:#FF9800,stroke:#E65100',   # Orange for finances
                'violation': 'fill:#F44336,stroke:#B71C1C', # Red for violations
                'default': 'fill:#9E9E9E,stroke:#616161'    # Gray for default
            }
            
            color_style = color_map.get(node_type, color_map['default'])
            mermaid_lines.append(f'    {node}["{escaped_name}"]:::class_{node_type}')
        
        # Add edges
        for edge in G.edges():
            source, target = edge
            mermaid_lines.append(f'    {source} --> {target}')
        
        # Add CSS classes for styling
        mermaid_lines.append("")
        mermaid_lines.append("    classDef class_work fill:#4CAF50,stroke:#388E3C,stroke-width:2px,color:#fff;")
        mermaid_lines.append("    classDef class_material fill:#2196F3,stroke:#0D47A1,stroke-width:2px,color:#fff;")
        mermaid_lines.append("    classDef class_finance fill:#FF9800,stroke:#E65100,stroke-width:2px,color:#fff;")
        mermaid_lines.append("    classDef class_violation fill:#F44336,stroke:#B71C1C,stroke-width:2px,color:#fff;")
        mermaid_lines.append("    classDef class_default fill:#9E9E9E,stroke:#616161,stroke-width:2px,color:#fff;")
        
        # Join all lines
        mermaid_str = "\n".join(mermaid_lines)
        return mermaid_str