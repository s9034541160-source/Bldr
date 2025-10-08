# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: _stage7_rubern_markup_enhanced
# Основной источник: C:\Bldr\scripts\bldr_rag_trainer.py
# Дубликаты (для справки):
#   - C:\Bldr\scripts\optimized_bldr_rag_trainer.py
#================================================================================
    def _stage7_rubern_markup_enhanced(self, content: str, doc_type: str, doc_subtype: str, seed_works: List[str], structural_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhanced Stage 7: Generate full Rubern markup with NetworkX graph and Mermaid export
        """
        # Create initial structure hints from structural analysis
        initial_structure = {
            'sections': structural_data.get('sections', []),
            'tables': structural_data.get('tables', []),
            'figures': structural_data.get('figures', [])
        }
        
        # Simulate Rubern markup generation with seeds and structure hints
        # In a real implementation, this would call a Rubern processor
        
        # Create Rubern-like markup with seed works
        rubern_markup = ""
        for i, work in enumerate(seed_works[:20]):  # Limit to 20 for demo
            rubern_markup += f"\\работа{{{work}}}\n"
        
        # Add some dependencies based on structure
        dependencies = []
        sections = initial_structure.get('sections', [])
        if len(sections) > 1:
            for i in range(1, min(len(sections), 5)):
                dependencies.append(f"\\зависимость{{{sections[i-1]} -> {sections[i]}}}")
        
        # Extract works from markup
        works = re.findall(r'\\работа\{([^}]+)\}', rubern_markup)
        deps = re.findall(r'\\зависимость\{([^}]+)\}', rubern_markup)
        
        # Create NetworkX graph for dependencies
        G = nx.DiGraph()
        
        # Add nodes (works)
        for i, work in enumerate(works):
            node_id = f"TASK_{i+1:03d}"
            G.add_node(node_id, name=work, duration=1.0, type='work')
        
        # Add edges (dependencies)
        task_mapping = {work: f"TASK_{i+1:03d}" for i, work in enumerate(works)}
        for dep in deps:
            # Parse dependency string like "A -> B"
            parts = dep.split(" -> ")
            if len(parts) == 2:
                source_work, target_work = parts
                source_id = task_mapping.get(source_work.strip())
                target_id = task_mapping.get(target_work.strip())
                if source_id and target_id:
                    G.add_edge(source_id, target_id)
        
        # Convert NetworkX graph to Mermaid
        mermaid_diagram = self._convert_networkx_to_mermaid(G)
        
        # Export Mermaid diagram to file
        mermaid_file = self.reports_dir / "rubern_stage7_mermaid.md"
        self._export_mermaid_to_file(mermaid_diagram, str(mermaid_file))
        
        # Add structure information
        doc_structure = {
            'sections': initial_structure['sections'],
            'tables': initial_structure['tables'],
            'figures': initial_structure['figures'],
            'works': works,
            'dependencies': deps,
            'paragraphs': re.split(r'\n\n', content)[:100],  # First 100 paragraphs
            'networkx_graph': G,  # Store the NetworkX graph
            'mermaid_diagram': mermaid_diagram,  # Store the Mermaid diagram
            'mermaid_file': str(mermaid_file)  # Store the Mermaid file path
        }
        
        # Add tables structure if available
        if initial_structure['tables']:
            doc_structure['tables'] = []
            for table_num in initial_structure['tables'][:10]:  # Limit to 10 tables
                # Simulate table content extraction
                table_content = re.search(rf'(?:Таблица|Table)\s+{re.escape(table_num)}.*?(?=(?:Таблица|Table)|$)', content, re.DOTALL)
                if table_content:
                    # Extract table rows
                    rows = re.findall(r'^(.+)$', table_content.group(), re.MULTILINE)[:20]  # Limit to 20 rows
                    doc_structure['tables'].append({
                        'number': table_num,
                        'rows': rows
                    })
        
        rubern_data = {
            'works': works,
            'dependencies': deps,
            'doc_structure': doc_structure,
            'rubern_markup': rubern_markup
        }
        
        # Spacy NER enrichment
        entities = {}
        try:
            doc = self.nlp(content[:5000])
            entities = {ent.label_: [ent.text for ent in doc.ents if ent.label_ == ent.label_] for ent in doc.ents}
            rubern_data['entities'] = entities
            
            # Add entity nodes to the graph
            for label, entity_list in entities.items():
                for i, entity in enumerate(entity_list[:5]):  # Limit to 5 entities per type
                    node_id = f"{label}_{i+1:03d}"
                    node_type = 'material' if label in ['MONEY', 'PERCENT'] else 'finance' if label == 'MONEY' else 'default'
                    G.add_node(node_id, name=entity, type=node_type)
        except Exception as e:
            print(f'NER enrichment error: {e}')
            rubern_data['entities'] = {}
        
        log = f'Rubern markup: {len(works)} works, {len(deps)} dependencies, {len(entities)} entity types, Mermaid exported to {mermaid_file.name}'
        print(f'✅ [Stage 7/14] Generate Rubern markup: {log}')
        
        return rubern_data

        # Add tables structure if available
        if initial_structure['tables']:
            doc_structure['tables'] = []
            for table_num in initial_structure['tables'][:10]:  # Limit to 10 tables
                # Simulate table content extraction
                table_content = re.search(rf'(?:Таблица|Table)\s+{re.escape(table_num)}.*?(?=(?:Таблица|Table)|$)', content, re.DOTALL)
                if table_content:
                    # Extract table rows
                    rows = re.findall(r'^(.+)$', table_content.group(), re.MULTILINE)[:20]  # Limit to 20 rows
                    doc_structure['tables'].append({
                        'number': table_num,
                        'rows': rows
                    })
        
        rubern_data = {
            'works': works,
            'dependencies': deps,
            'doc_structure': doc_structure,
            'rubern_markup': rubern_markup
        }
        
        # Spacy NER enrichment
        try:
            doc = self.nlp(content[:5000])
            entities = {ent.label_: [ent.text for ent in doc.ents if ent.label_ == ent.label_] for ent in doc.ents}
            rubern_data['entities'] = entities
        except Exception as e:
            print(f'NER enrichment error: {e}')
            rubern_data['entities'] = {}
        
        log = f'Rubern markup: {len(works)} works, {len(deps)} dependencies, {len(entities)} entity types'
        print(f'✅ [Stage 7/14] Generate Rubern markup: {log}')
        
        return rubern_data