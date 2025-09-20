"""
Document Analyzer Plugin
Analyzes documents to extract insights from chunks
"""

from typing import Dict, List, Any

def analyze_document(chunks: List[Dict[str, Any]], doc_type: str = "norms") -> Dict[str, Any]:
    """
    Analyze document chunks to extract insights
    
    Args:
        chunks: List of document chunks with metadata
        doc_type: Type of document (norms, ppr, smeta, rd, educational)
        
    Returns:
        Dictionary containing analysis results and insights
    """
    insights = {
        "total_chunks": len(chunks),
        "doc_type": doc_type,
        "entities_found": {},
        "key_phrases": [],
        "violations": [],
        "recommendations": [],
        "summary": ""
    }
    
    # Extract entities and key information based on document type
    if doc_type == "norms":
        insights = _analyze_norms_document(chunks, insights)
    elif doc_type == "ppr":
        insights = _analyze_ppr_document(chunks, insights)
    elif doc_type == "smeta":
        insights = _analyze_smeta_document(chunks, insights)
    elif doc_type == "rd":
        insights = _analyze_rd_document(chunks, insights)
    elif doc_type == "educational":
        insights = _analyze_educational_document(chunks, insights)
    else:
        insights = _analyze_generic_document(chunks, insights)
    
    # Generate summary
    insights["summary"] = _generate_summary(insights)
    
    return insights

def _analyze_norms_document(chunks: List[Dict[str, Any]], insights: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze norms documents for violations and key information"""
    entities = {}
    violations = []
    key_phrases = []
    
    for chunk in chunks:
        meta = chunk.get("meta", {})
        chunk_text = chunk.get("chunk", "")
        
        # Extract entities
        chunk_entities = meta.get("entities", {})
        for entity_type, entity_list in chunk_entities.items():
            if entity_type not in entities:
                entities[entity_type] = []
            entities[entity_type].extend(entity_list)
        
        # Find violations
        if "нарушени" in chunk_text.lower() or "viola" in chunk_text.lower():
            violations.append({
                "chunk_id": hash(chunk_text) % 10000,
                "text": chunk_text[:200] + "..." if len(chunk_text) > 200 else chunk_text,
                "confidence": 0.99
            })
        
        # Extract key phrases related to norms
        norm_phrases = ["СП ", "ГОСТ", "СНиП", "пункт", "требован", "обязатель"]
        for phrase in norm_phrases:
            if phrase.lower() in chunk_text.lower():
                key_phrases.append(phrase)
    
    insights["entities_found"] = entities
    insights["violations"] = violations[:10]  # Limit to 10 violations
    insights["key_phrases"] = list(set(key_phrases))[:20]  # Limit to 20 unique phrases
    
    # Add recommendations for norms documents
    if violations:
        insights["recommendations"].append("Обратите внимание на выявленные нарушения требований нормативных документов")
    
    insights["recommendations"].append("Проверьте соответствие проектных решений актуальным нормативам")
    
    return insights

def _analyze_ppr_document(chunks: List[Dict[str, Any]], insights: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze PPR documents for work sequences and dependencies"""
    entities = {}
    key_phrases = []
    
    for chunk in chunks:
        meta = chunk.get("meta", {})
        chunk_text = chunk.get("chunk", "")
        
        # Extract entities
        chunk_entities = meta.get("entities", {})
        for entity_type, entity_list in chunk_entities.items():
            if entity_type not in entities:
                entities[entity_type] = []
            entities[entity_type].extend(entity_list)
        
        # Extract PPR-related phrases
        ppr_phrases = ["работа", "этап", "мероприят", "технолог", "последовательн", "зависим"]
        for phrase in ppr_phrases:
            if phrase.lower() in chunk_text.lower():
                key_phrases.append(phrase)
    
    insights["entities_found"] = entities
    insights["key_phrases"] = list(set(key_phrases))[:20]
    
    # Add recommendations for PPR documents
    insights["recommendations"].append("Оптимизируйте последовательность выполнения работ")
    insights["recommendations"].append("Проверьте критические пути в сетевом графике")
    
    return insights

def _analyze_smeta_document(chunks: List[Dict[str, Any]], insights: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze estimate documents for costs and financial information"""
    entities = {}
    key_phrases = []
    finances = []
    
    for chunk in chunks:
        meta = chunk.get("meta", {})
        chunk_text = chunk.get("chunk", "")
        
        # Extract entities
        chunk_entities = meta.get("entities", {})
        for entity_type, entity_list in chunk_entities.items():
            if entity_type not in entities:
                entities[entity_type] = []
            entities[entity_type].extend(entity_list)
        
        # Extract financial information
        finance_info = meta.get("finances", [])
        finances.extend(finance_info)
        
        # Extract estimate-related phrases
        estimate_phrases = ["смета", "стоимость", "расчет", "ГЭСН", "ФЕР", "цена", "бюджет"]
        for phrase in estimate_phrases:
            if phrase.lower() in chunk_text.lower():
                key_phrases.append(phrase)
    
    insights["entities_found"] = entities
    insights["key_phrases"] = list(set(key_phrases))[:20]
    
    # Add recommendations for estimate documents
    insights["recommendations"].append("Проверьте актуальность применяемых расценок")
    insights["recommendations"].append("Проанализируйте риски изменения стоимости материалов")
    
    return insights

def _analyze_rd_document(chunks: List[Dict[str, Any]], insights: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze working documentation for technical specifications"""
    entities = {}
    key_phrases = []
    
    for chunk in chunks:
        meta = chunk.get("meta", {})
        chunk_text = chunk.get("chunk", "")
        
        # Extract entities
        chunk_entities = meta.get("entities", {})
        for entity_type, entity_list in chunk_entities.items():
            if entity_type not in entities:
                entities[entity_type] = []
            entities[entity_type].extend(entity_list)
        
        # Extract RD-related phrases
        rd_phrases = ["чертеж", "спецификац", "схема", "узел", "детал", "материал"]
        for phrase in rd_phrases:
            if phrase.lower() in chunk_text.lower():
                key_phrases.append(phrase)
    
    insights["entities_found"] = entities
    insights["key_phrases"] = list(set(key_phrases))[:20]
    
    # Add recommendations for RD documents
    insights["recommendations"].append("Проверьте соответствие спецификаций проектным решениям")
    insights["recommendations"].append("Обеспечьте согласование всех листов комплекта")
    
    return insights

def _analyze_educational_document(chunks: List[Dict[str, Any]], insights: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze educational documents for learning content"""
    entities = {}
    key_phrases = []
    
    for chunk in chunks:
        meta = chunk.get("meta", {})
        chunk_text = chunk.get("chunk", "")
        
        # Extract entities
        chunk_entities = meta.get("entities", {})
        for entity_type, entity_list in chunk_entities.items():
            if entity_type not in entities:
                entities[entity_type] = []
            entities[entity_type].extend(entity_list)
        
        # Extract educational-related phrases
        edu_phrases = ["пример", "задач", "упражнен", "тест", "контроль", "знан"]
        for phrase in edu_phrases:
            if phrase.lower() in chunk_text.lower():
                key_phrases.append(phrase)
    
    insights["entities_found"] = entities
    insights["key_phrases"] = list(set(key_phrases))[:20]
    
    # Add recommendations for educational documents
    insights["recommendations"].append("Используйте примеры для лучшего усвоения материала")
    insights["recommendations"].append("Проверьте полноту изложения учебного материала")
    
    return insights

def _analyze_generic_document(chunks: List[Dict[str, Any]], insights: Dict[str, Any]) -> Dict[str, Any]:
    """Generic document analysis"""
    entities = {}
    key_phrases = []
    
    for chunk in chunks:
        meta = chunk.get("meta", {})
        chunk_text = chunk.get("chunk", "")
        
        # Extract entities
        chunk_entities = meta.get("entities", {})
        for entity_type, entity_list in chunk_entities.items():
            if entity_type not in entities:
                entities[entity_type] = []
            entities[entity_type].extend(entity_list)
        
        # Extract common phrases
        common_phrases = ["важн", "ключев", "основн", "необходим", "рекоменд"]
        for phrase in common_phrases:
            if phrase.lower() in chunk_text.lower():
                key_phrases.append(phrase)
    
    insights["entities_found"] = entities
    insights["key_phrases"] = list(set(key_phrases))[:20]
    
    return insights

def _generate_summary(insights: Dict[str, Any]) -> str:
    """Generate a summary based on insights"""
    doc_type = insights.get("doc_type", "документ")
    total_chunks = insights.get("total_chunks", 0)
    entities_count = sum(len(entities) for entities in insights.get("entities_found", {}).values())
    violations_count = len(insights.get("violations", []))
    
    summary = f"Анализ {doc_type} документа завершен. Обработано {total_chunks} фрагментов. "
    summary += f"Найдено {entities_count} сущностей. "
    
    if violations_count > 0:
        summary += f"Выявлено {violations_count} потенциальных нарушений. "
    
    if insights.get("recommendations"):
        summary += f"Сформировано {len(insights['recommendations'])} рекомендаций. "
    
    return summary