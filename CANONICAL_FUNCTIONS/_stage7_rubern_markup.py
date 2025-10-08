# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: _stage7_rubern_markup
# Основной источник: C:\Bldr\scripts\bldr_rag_trainer.py
# Дубликаты (для справки):
#   - C:\Bldr\scripts\optimized_bldr_rag_trainer.py
#================================================================================
    def _stage7_rubern_markup(self, content: str, doc_type: str, doc_subtype: str, seed_works: List[str], structural_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Stage 7: Generate full Rubern markup with seeds and initial structure hints
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
        
        # Add structure information
        doc_structure = {
            'sections': initial_structure['sections'],
            'tables': initial_structure['tables'],
            'figures': initial_structure['figures'],
            'works': works,
            'dependencies': deps,
            'paragraphs': re.split(r'\n\n', content)[:100]  # First 100 paragraphs
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
        except Exception as e:
            print(f'NER enrichment error: {e}')
            rubern_data['entities'] = {}
        
        log = f'Rubern markup: {len(works)} works, {len(deps)} dependencies, {len(entities)} entity types'
        print(f'✅ [Stage 7/14] Generate Rubern markup: {log}')
        
        return rubern_data