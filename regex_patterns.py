"""
Regex patterns for SuperBuilder RAG pipeline stages.
Contains patterns for seed extraction, metadata extraction, and document type detection.
"""

import re
from typing import List, Dict, Any, Optional

# Document type detection patterns
DOCUMENT_TYPE_PATTERNS = {
    'norms': {
        'keywords': [
            r'СП\s+\d+\.\d+',           # СП 45.13330
            r'ГОСТ\s+\d+\.\d+',         # ГОСТ 21.101
            r'СНиП\s+\d+\.\d+',         # СНиП 3.03.01
            r'п\.\s*\d+\.\d+',          # п. 5.10
            r'ФЗ-\d+',                  # ФЗ-44
            r'cl\.\d+\.\d+',            # cl.5.2
        ],
        'subtype_patterns': {
            'sp': r'СП\s+\d+\.\d+',
            'gost': r'ГОСТ\s+\d+\.\d+',
            'snip': r'СНиП\s+\d+\.\d+',
            'fz': r'ФЗ-\d+',
        }
    },
    'ppr': {
        'keywords': [
            r'проект\s+производства\s+работ',
            r'ППР',
            r'технологическая\s+карта',
            r'этап\s+работ',
            r'рабочая\s+последовательность',
        ],
        'subtype_patterns': {
            'ppr': r'ППР|проект\s+производства\s+работ',
            'tech_card': r'технологическая\s+карта',
        }
    },
    'smeta': {
        'keywords': [
            r'смета',
            r'расчет',
            r'ГЭСН\s+\d+-\d+-\d+',
            r'ФЕР\s+\d+-\d+-\d+',
            r'расценка',
            r'стоимость',
        ],
        'subtype_patterns': {
            'estimate': r'смета|расчет',
            'gesn': r'ГЭСН\s+\d+-\d+-\d+',
            'fer': r'ФЕР\s+\d+-\d+-\d+',
        }
    },
    'rd': {
        'keywords': [
            r'рабочая\s+документация',
            r'чертеж',
            r'спецификация',
            r'схема',
            r'план',
        ],
        'subtype_patterns': {
            'drawing': r'чертеж|план',
            'spec': r'спецификация',
        }
    },
    'educational': {
        'keywords': [
            r'учебник',
            r'пособие',
            r'пример',
            r'задача',
            r'методичка',
        ],
        'subtype_patterns': {
            'textbook': r'учебник',
            'manual': r'пособие|методичка',
        }
    },
    # New categories for full Russian NTD coverage
    'finance': {
        'keywords': [
            r'налог',
            r'бюджет',
            r'расчет',
            r'ФНС',
            r'прибыль',
            r'зарплата',
            r'расходы',
            r'НДФЛ',
            r'НДС',
            r'минимальная зарплата',
            r'оклад',
        ],
        'subtype_patterns': {
            'tax': r'НДФЛ|НДС',
            'salary': r'минимальная зарплата|оклад',
        }
    },
    'safety': {
        'keywords': [
            r'охрана труда',
            r'промышленная безопасность',
            r'СанПиН',
            r'ГОСТ 12',
            r'авария',
            r'риски',
            r'инструктаж',
            r'СИЗ',
            r'пожарная безопасность',
        ],
        'subtype_patterns': {
            'labor_safety': r'инструктаж|СИЗ',
            'industrial': r'пожарная безопасность',
        }
    },
    'ecology': {
        'keywords': [
            r'экология',
            r'ОВОС',
            r'воздействие',
            r'экологическая экспертиза',
            r'отходы',
            r'ФЗ-7',
            r'воздействие на окружающую среду',
            r'управление отходами',
        ],
        'subtype_patterns': {
            'impact': r'воздействие на окружающую среду',
            'waste': r'управление отходами',
        }
    },
    'accounting': {
        'keywords': [
            r'бухгалтерский учет',
            r'баланс',
            r'отчетность',
            r'амортизация',
            r'ФНС',
            r'бухгалтерская отчетность',
            r'налоговая база',
        ],
        'subtype_patterns': {
            'reporting': r'бухгалтерская отчетность',
            'tax': r'налоговая база',
        }
    },
    'hr': {
        'keywords': [
            r'кадры',
            r'трудовой договор',
            r'зарплата',
            r'Минимальный размер оплаты труда',
            r'отпуск',
            r'ФЗ-273',
            r'трудовые отношения',
            r'расчет зарплаты',
            r'МРОТ',
        ],
        'subtype_patterns': {
            'hr': r'трудовые отношения',
            'salary': r'расчет зарплаты|МРОТ',
        }
    },
    'logistics': {
        'keywords': [
            r'логистика',
            r'доставка материалов',
            r'транспортировка',
            r'складирование',
        ],
        'subtype_patterns': {
            'transport': r'транспортировка',
            'storage': r'складирование',
        }
    },
    'procurement': {
        'keywords': [
            r'закупки',
            r'тендеры ФЗ-44',
            r'конкурс',
            r'аукцион',
            r'электронные закупки',
        ],
        'subtype_patterns': {
            'tenders': r'тендеры|конкурс',
            'auctions': r'аукцион',
        }
    },
    'insurance': {
        'keywords': [
            r'страхование',
            r'гарантии',
            r'ОСАГО',
            r'КАСКО',
            r'страховой полис',
        ],
        'subtype_patterns': {
            'osago': r'ОСАГО',
            'kasko': r'КАСКО',
        }
    }
}

# Seed work extraction patterns by document type
SEED_WORK_PATTERNS = {
    'norms': {
        'work_activities': r'(?:работы?|выполнение|осуществление|производство)\s+([а-яёА-ЯЁ][а-яёА-ЯЁ\s]{10,50})',
        'procedures': r'(?:процедура|порядок|методика)\s+([а-яёА-ЯЁ][а-яёА-ЯЁ\s]{10,50})',
        'requirements': r'(?:требования?|необходимо|следует)\s+([а-яёА-ЯЁ][а-яёА-ЯЁ\s]{10,50})',
        'operations': r'(?:операция|действие|мероприятие)\s+([а-яёА-ЯЁ][а-яёА-ЯЁ\s]{10,50})',
    },
    'ppr': {
        'construction_works': r'(?:работы?\s+по|\s+строительство|\s+монтаж|\s+укладка)\s+([а-яёА-ЯЁ][а-яёА-ЯЁ\s]{10,50})',
        'installation': r'(?:установка|монтаж|сборка)\s+([а-яёА-ЯЁ][а-яёА-ЯЁ\s]{10,50})',
        'preparation': r'(?:подготовка|очистка|обработка)\s+([а-яёА-ЯЁ][а-яёА-ЯЁ\s]{10,50})',
        'finishing': r'(?:отделка|покрытие|окраска)\s+([а-яёА-ЯЁ][а-яёА-ЯЁ\s]{10,50})',
    },
    'smeta': {
        'work_items': r'(?:наименование\s+работ|вид\s+работ)\s*[:\-]\s*([а-яёА-ЯЁ][а-яёА-ЯЁ\s]{10,70})',
        'materials': r'(?:материалы?|сырье|ресурсы?)\s*[:\-]\s*([а-яёА-ЯЁ][а-яёА-ЯЁ\s]{10,50})',
        'services': r'(?:услуги?|работы?\s+по)\s*([а-яёА-ЯЁ][а-яёА-ЯЁ\s]{10,50})',
    },
    'rd': {
        'sheets': r'(?:Лист|Чертеж)\s+([A-Z0-9\-]+)',
        'elements': r'(?:Элемент|Конструкция)\s+(\d+(?:\.\d+)*)',
        'spec_items': r'(?:Позиция|Обозначение)\s+([A-Z0-9\-]+)',
    },
    'educational': {
        'examples': r'(?:Пример|Example)\s+(\d+(?:\.\d+)*)',
        'exercises': r'(?:Задача|Упражнение)\s+(\d+(?:\.\d+)*)',
        'chapters': r'(?:Глава|Chapter)\s+(\d+(?:\.\d+)*)',
    },
    # New categories for full Russian NTD coverage
    'finance': {
        'budget_items': r'(?:Статья|Позиция)\s+бюджета\s+(.+?)\s*-\s*(\d+(?:\.\d+)?)',
        'tax_items': r'(?:Налог|Сбор)\s+(.+?)\s*-\s*(\d+(?:\.\d+)?)',
        'salary_items': r'(?:Оклад|Зарплата)\s+(.+?)\s*-\s*(\d+(?:\.\d+)?)',
    },
    'safety': {
        'safety_rules': r'(?:Правило|Требование)\s+безопасности\s+(\d+(?:\.\d+)*)',
        'safety_measures': r'(?:Мера|Средство)\s+безопасности\s+(.+?)\s*-\s*(\d+(?:\.\d+)?)',
        'safety_protocols': r'(?:Протокол|Процедура)\s+безопасности\s+(.+?)',
    },
    'ecology': {
        'environmental_standards': r'(?:Стандарт|Норматив)\s+экологии\s+(\d+(?:\.\d+)*)',
        'impact_assessments': r'(?:Оценка|Анализ)\s+воздействия\s+(.+?)',
        'waste_management': r'(?:Управление|Обработка)\s+отходами\s+(.+?)',
    },
    'accounting': {
        'accounting_entries': r'(?:Проводка|Запись)\s+учета\s+(.+?)\s*-\s*(\d+(?:\.\d+)?)',
        'balance_items': r'(?:Актив|Пассив)\s+(.+?)\s*-\s*(\d+(?:\.\d+)?)',
        'reporting_items': r'(?:Отчет|Документ)\s+учета\s+(.+?)',
    },
    'hr': {
        'hr_policies': r'(?:Политика|Правило)\s+кадров\s+(.+?)',
        'employment_terms': r'(?:Условие|Требование)\s+трудового\s+договора\s+(.+?)',
        'benefits': r'(?:Льгота|Преимущество)\s+(.+?)\s*-\s*(\d+(?:\.\d+)?)',
    },
    'logistics': {
        'logistics_routes': r'(?:Маршрут|Путь)\s+доставки\s+(.+?)',
        'transport_schedules': r'(?:Расписание|График)\s+транспорта\s+(.+?)',
        'storage_procedures': r'(?:Процедура|Правило)\s+хранения\s+(.+?)',
    },
    'procurement': {
        'procurement_items': r'(?:Предмет|Объект)\s+закупки\s+(.+?)',
        'tender_requirements': r'(?:Требование|Условие)\s+тендера\s+(.+?)',
        'contract_terms': r'(?:Условие|Пункт)\s+контракта\s+(.+?)',
    },
    'insurance': {
        'insurance_policies': r'(?:Полис|Страховка)\s+(.+?)\s*-\s*(\d+(?:\.\d+)?)',
        'coverage_items': r'(?:Покрытие|Страховая\s+сумма)\s+(.+?)\s*-\s*(\d+(?:\.\d+)?)',
        'claim_procedures': r'(?:Процедура|Порядок)\с+страхового\s+возмещения\s+(.+?)',
    }
}

# Material extraction patterns
MATERIAL_PATTERNS = {
    'concrete': r'(?:бетон| concrete)(?:\s+класса?\s+[BC]\d+|\s+марки?\с+М\d+)?',
    'steel': r'(?:сталь|steel)(?:\s+класса?\s+A\d+|\s+марки?\s+\d+)?',
    'rebar': r'(?:арматура|rebar)(?:\s+класса?\s+A\d+|\s+диаметр\s+\d+)?',
    'brick': r'(?:кирпич|brick)(?:\s+марки?\с+М\d+)?',
    'wood': r'(?:дерево| древесина|wood)(?:\s+породы?\s+\w+)?',
    'cement': r'(?:цемент|cement)(?:\s+марки?\с+М\d+)?',
    'sand': r'(?:песок|sand)(?:\s+крупности?\s+\d+)?',
    'gravel': r'(?:щебень|gravel)(?:\s+фракции?\s+\d+)?',
}

# Finance extraction patterns
FINANCE_PATTERNS = {
    'cost': r'(?:стоимость|cost|цена)\s*[=:]\s*(\d+(?:\.\d+)?\s*(?:тыс\.|млн|млрд)?\s*(?:руб\.|рублей|RUB))',
    'budget': r'(?:бюджет|budget)\s*[=:]\s*(\d+(?:\.\d+)?\s*(?:тыс\.|млн|млрд)?\s*(?:руб\.|рублей|RUB))',
    'estimate': r'(?:смета|estimate)\s*[=:]\s*(\d+(?:\.\d+)?\s*(?:тыс\.|млн|млрд)?\s*(?:руб\.|рублей|RUB))',
    'roi': r'(?:ROI|доходность)\s*[=:]\s*(\d+(?:\.\.\d+)?\s*%)',
    'profit': r'(?:прибыль|profit)\s*[=:]\s*(\d+(?:\.\d+)?\s*(?:тыс\.|млн|млрд)?\s*(?:руб\.|рублей|RUB))',
}

from typing import Optional

def extract_works_candidates(text: str, doc_type: str, sections: Optional[List[str]] = None) -> List[str]:
    """
    Stage 6: Extract seed works candidates by document type and sections.
    
    Args:
        text: Document text
        doc_type: Document type (norms, ppr, smeta, rd, educational, finance, safety, ecology, accounting, hr, logistics, procurement, insurance)
        sections: List of sections from structural analysis (optional)
        
    Returns:
        List of seed work candidates
    """
    candidates = []
    
    # Get patterns for document type
    patterns = SEED_WORK_PATTERNS.get(doc_type, SEED_WORK_PATTERNS['norms'])
    
    # Extract candidates using all patterns for the document type
    for pattern_name, pattern in patterns.items():
        matches = re.findall(pattern, text, re.IGNORECASE)
        # Flatten tuple matches if needed
        if matches and isinstance(matches[0], tuple):
            # For patterns that capture multiple groups, join them
            flattened_matches = [' '.join(match) if isinstance(match, tuple) else match for match in matches]
            candidates.extend(flattened_matches)
        else:
            candidates.extend(matches)
    
    # If sections are provided, focus extraction on those sections
    if sections:
        section_candidates = []
        for section in sections:
            # Find text within each section
            section_pattern = rf'Раздел\s+{re.escape(section)}.*?(?=(?:Раздел\s+\d+|$))'
            section_text = re.search(section_pattern, text, re.DOTALL | re.IGNORECASE)
            if section_text:
                section_content = section_text.group()
                for pattern_name, pattern in patterns.items():
                    matches = re.findall(pattern, section_content, re.IGNORECASE)
                    # Flatten tuple matches if needed
                    if matches and isinstance(matches[0], tuple):
                        # For patterns that capture multiple groups, join them
                        flattened_matches = [' '.join(match) if isinstance(match, tuple) else match for match in matches]
                        section_candidates.extend(flattened_matches)
                    else:
                        section_candidates.extend(matches)
        # If we found section-specific candidates, use them; otherwise use general ones
        if section_candidates:
            candidates = section_candidates
    
    # Remove duplicates and limit to reasonable number
    unique_candidates = list(set(candidates))[:50]  # Limit to 50 candidates
    return unique_candidates

def extract_materials_from_rubern_tables(structure: Dict[str, Any]) -> List[str]:
    """
    Stage 8: Extract materials ONLY from Rubern tables structure.
    
    Args:
        structure: Rubern document structure
        
    Returns:
        List of extracted materials
    """
    materials = []
    
    # Look for materials in table structures
    if 'tables' in structure:
        for table in structure['tables']:
            # Convert table content to string for pattern matching
            table_content = str(table)
            for material_name, pattern in MATERIAL_PATTERNS.items():
                matches = re.findall(pattern, table_content, re.IGNORECASE)
                materials.extend([f"{material_name}: {match}" for match in matches])
    
    # Also look in structured data that might contain material info
    if 'materials' in structure:
        materials.extend(structure['materials'])
    
    return list(set(materials))  # Remove duplicates

def extract_finances_from_rubern_paragraphs(structure: Dict[str, Any]) -> List[str]:
    """
    Stage 8: Extract finances ONLY from Rubern paragraphs structure.
    
    Args:
        structure: Rubern document structure
        
    Returns:
        List of extracted financial information
    """
    finances = []
    
    # Look for finances in paragraph structures
    if 'paragraphs' in structure:
        for paragraph in structure['paragraphs']:
            # Convert paragraph content to string for pattern matching
            paragraph_content = str(paragraph)
            for finance_name, pattern in FINANCE_PATTERNS.items():
                matches = re.findall(pattern, paragraph_content, re.IGNORECASE)
                finances.extend([f"{finance_name}: {match}" for match in matches])
    
    # Also look in structured data that might contain finance info
    if 'finances' in structure:
        finances.extend(structure['finances'])
    
    return list(set(finances))  # Remove duplicates

def light_rubern_scan(content: str) -> Dict[str, Any]:
    """
    Stage 4: Light Rubern scan for signatures (regex only, no full markup).
    
    Args:
        content: Document content
        
    Returns:
        Dictionary with detected Rubern signatures
    """
    signatures = {
        'works': [],
        'dependencies': [],
        'norms': [],
        'examples': [],
        'sections': []
    }
    
    # Look for common Rubern-like patterns
    works = re.findall(r'\\(?:работа|work)\{([^}]+)\}', content)
    dependencies = re.findall(r'\\(?:зависимость|dependency)\{([^}]+)\}', content)
    norms = re.findall(r'\\(?:норма|norm)\{([^}]+)\}', content)
    examples = re.findall(r'\\(?:пример|example)\{([^}]+)\}', content)
    sections = re.findall(r'\\(?:раздел|section)\{([^}]+)\}', content)
    
    signatures['works'] = works[:10]  # Limit to 10
    signatures['dependencies'] = dependencies[:10]
    signatures['norms'] = norms[:10]
    signatures['examples'] = examples[:10]
    signatures['sections'] = sections[:10]
    
    return signatures

def detect_document_type_with_symbiosis(content: str, file_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Stage 4: Symbiotic document type detection (regex + light Rubern scan).
    
    Args:
        content: Document content
        file_path: File path (optional, for filename-based hints)
        
    Returns:
        Dictionary with detected type, subtype, and confidence
    """
    # Regex-based detection
    regex_scores = {}
    for doc_type, patterns in DOCUMENT_TYPE_PATTERNS.items():
        score = 0
        for keyword_pattern in patterns['keywords']:
            matches = re.findall(keyword_pattern, content, re.IGNORECASE)
            score += len(matches)
        # Normalize score by content length
        if len(content) > 0:
            regex_scores[doc_type] = min(score / len(content) * 1000, 100)
        else:
            regex_scores[doc_type] = 0
    
    # Light Rubern scan
    rubern_signatures = light_rubern_scan(content)
    rubern_score = 0
    rubern_type = 'unknown'
    
    # Score based on Rubern signatures
    total_signatures = sum(len(v) for v in rubern_signatures.values())
    if total_signatures > 0:
        if len(rubern_signatures['norms']) > 0:
            rubern_type = 'norms'
            rubern_score = min(len(rubern_signatures['norms']) * 10, 50)
        elif len(rubern_signatures['works']) > 0:
            rubern_type = 'ppr'
            rubern_score = min(len(rubern_signatures['works']) * 5, 30)
        elif len(rubern_signatures['examples']) > 0:
            rubern_type = 'educational'
            rubern_score = min(len(rubern_signatures['examples']) * 5, 30)
    
    # Combine scores
    final_type = 'unknown'
    final_subtype = 'unknown'
    final_confidence = 0.0
    
    # Get best regex score
    if regex_scores:
        best_regex_type = max(regex_scores.keys(), key=lambda x: regex_scores[x])
        best_regex_score = regex_scores[best_regex_type]
    else:
        best_regex_type = 'unknown'
        best_regex_score = 0
        
    # If Rubern agrees or is unsure, trust regex more
    if rubern_type == 'unknown' or rubern_type == best_regex_type:
        final_type = best_regex_type
        final_confidence = best_regex_score
    # If Rubern disagrees but has low confidence, trust regex
    elif rubern_score < 20:
        final_type = best_regex_type
        final_confidence = best_regex_score * 0.8  # Slight penalty
    # If Rubern has high confidence and disagrees, consider it
    else:
        # Weighted combination
        if rubern_score > best_regex_score:
            final_type = rubern_type
            final_confidence = rubern_score * 0.7 + best_regex_score * 0.3
        else:
            final_type = best_regex_type
            final_confidence = best_regex_score * 0.7 + rubern_score * 0.3
    
    # Determine subtype
    if final_type in DOCUMENT_TYPE_PATTERNS:
        subtype_patterns = DOCUMENT_TYPE_PATTERNS[final_type]['subtype_patterns']
        for subtype, pattern in subtype_patterns.items():
            if re.search(pattern, content, re.IGNORECASE):
                final_subtype = subtype
                break
    
    # Enhanced content-based detection
    content_lower = content.lower()
    
    # Additional strong indicators
    if final_confidence < 50:
        # Construction/technical documents
        if any(word in content_lower for word in ['сп ', 'гост ', 'снип ', 'фз-', 'норматив']):
            final_type = 'norms'
            final_confidence = max(final_confidence, 60)
        
        # Project documentation
        elif any(word in content_lower for word in ['проект производства', 'ппр', 'технологическая карта', 'рабочая последовательность']):
            final_type = 'ppr'
            final_confidence = max(final_confidence, 60)
            
        # Estimates
        elif any(word in content_lower for word in ['смета', 'гэсн', 'фер', 'расценка', 'позиция', 'расчет стоимости']):
            final_type = 'smeta'
            final_confidence = max(final_confidence, 60)
            
        # Procurement
        elif any(word in content_lower for word in ['закупка', 'тендер', 'фз-44', 'конкурс', 'аукцион']):
            final_type = 'procurement'
            final_confidence = max(final_confidence, 60)
            
        # Working documentation  
        elif any(word in content_lower for word in ['рабочая документация', 'чертеж', 'спецификация', 'схема']):
            final_type = 'rd'
            final_confidence = max(final_confidence, 60)
    
    # Filename hints (less priority but still useful)
    if final_confidence < 60 and file_path:
        filename = file_path.lower()
        if 'сп' in filename or 'гост' in filename or 'снип' in filename:
            final_type = 'norms'
            final_confidence = max(final_confidence, 50)
        elif 'ппр' in filename or 'технолог' in filename:
            final_type = 'ppr'
            final_confidence = max(final_confidence, 50)
        elif 'смет' in filename or 'расч' in filename:
            final_type = 'smeta'
            final_confidence = max(final_confidence, 50)
        elif 'закуп' in filename or 'тендер' in filename:
            final_type = 'procurement'
            final_confidence = max(final_confidence, 50)
        elif 'учеб' in filename or 'пособ' in filename:
            final_type = 'educational'
            final_confidence = max(final_confidence, 50)
    
    return {
        'doc_type': final_type,
        'doc_subtype': final_subtype,
        'confidence': min(final_confidence, 100),
        'regex_score': max(regex_scores.values()) if regex_scores else 0,
        'rubern_score': rubern_score,
        'rubern_signatures': rubern_signatures
    }