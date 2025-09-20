import os
import re
import json
import time
import requests
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import sqlite3
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class NormativeDocument:
    """Data class for normative document information"""
    id: int
    category: str
    code: str
    title: str
    year: int
    status: str
    pdf_url: str
    source_site: str
    description: str
    file_path: Optional[str] = None
    processed_at: Optional[float] = None

class NormativeDatabase:
    """Database for normative technical documentation"""
    
    def __init__(self, db_path: Optional[str] = None, json_path: Optional[str] = None):
        # Use BASE_DIR environment variable or default to I:/docs
        base_dir_env = os.getenv("BASE_DIR", "I:/docs")
        default_db_path = os.path.join(base_dir_env, "norms_db", "ntd_local.db")
        default_json_path = os.path.join(base_dir_env, "norms_db", "ntd_full_db.json")
        
        self.db_path = Path(db_path or default_db_path)
        self.json_path = Path(json_path or default_json_path)
        self.documents: Dict[str, NormativeDocument] = {}
        self.categories = {
            "construction": "Строительство",
            "finance": "Финансы и бюджет",
            "safety": "Техника безопасности и охрана труда",
            "environment": "Экология",
            "hr": "HR и кадры",
            "procurement": "Тендеры, конкурсы, закупки",
            "contracts": "Договора",
            "documentation": "Исполнительная документация",
            "materials": "Материальное снабжение и складирование",
            "accounting": "Бухгалтерский учет"
        }
        self._init_db()
        self._load_documents()
    
    def _init_db(self):
        """Initialize SQLite database for processed documents tracking"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute('''CREATE TABLE IF NOT EXISTS processed_docs 
                            (id INTEGER PRIMARY KEY, 
                             code TEXT UNIQUE, 
                             title TEXT, 
                             file_path TEXT, 
                             processed_at REAL,
                             status TEXT)''')
        self.conn.commit()
    
    def _load_documents(self):
        """Load documents from JSON database"""
        if self.json_path.exists():
            with open(self.json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for doc_data in data:
                    doc = NormativeDocument(**doc_data)
                    self.documents[doc.code] = doc
            logger.info(f"Loaded {len(self.documents)} normative documents from JSON")
        else:
            logger.warning(f"Normative documents JSON not found: {self.json_path}")
    
    def get_document(self, code: str) -> Optional[NormativeDocument]:
        """Get document by code"""
        return self.documents.get(code.upper())
    
    def search_documents(self, query: str, category: Optional[str] = None) -> List[NormativeDocument]:
        """Search documents by query and category"""
        results = []
        query_lower = query.lower()
        
        for doc in self.documents.values():
            if category and doc.category != category:
                continue
            
            if (query_lower in doc.code.lower() or 
                query_lower in doc.title.lower() or
                query_lower in doc.description.lower()):
                results.append(doc)
        
        return results
    
    def is_document_actual(self, code: str) -> bool:
        """Check if document is actual (not outdated)"""
        doc = self.get_document(code)
        if not doc:
            return False
        return doc.status in ["Обязательный", "Актуальный", "Рекомендательный"]
    
    def get_replacement_document(self, code: str) -> Optional[NormativeDocument]:
        """Get replacement document if current is outdated"""
        doc = self.get_document(code)
        if not doc or "устарел" not in doc.status.lower():
            return None
        
        # Search for replacement documents in official databases
        # For now, we'll just return None
        return None
    
    def mark_as_processed(self, code: str, file_path: str, status: str = "processed"):
        """Mark document as processed in database"""
        try:
            self.conn.execute(
                "INSERT OR REPLACE INTO processed_docs (code, title, file_path, processed_at, status) VALUES (?, ?, ?, ?, ?)",
                (code, self.documents[code].title, file_path, time.time(), status)
            )
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error marking document as processed: {e}")
    
    def is_processed(self, code: str) -> bool:
        """Check if document is already processed"""
        try:
            cursor = self.conn.execute("SELECT code FROM processed_docs WHERE code = ?", (code,))
            return cursor.fetchone() is not None
        except Exception as e:
            logger.error(f"Error checking if document is processed: {e}")
            return False

class NormativeChecker:
    """Checker for normative document actuality and processing"""
    
    def __init__(self, normative_db: NormativeDatabase):
        self.normative_db = normative_db
        self.sources = [
            "https://docs.cntd.ru",
            "https://www.minstroyrf.gov.ru",
            "https://meganorm.ru",
            "https://files.stroyinf.ru",
            "https://helpeng.ru",
            "https://gostbank.metaltorg.ru"
        ]
    
    def extract_document_info(self, file_path: str, content: Optional[str] = None) -> Dict:
        """Extract document information from file and content"""
        info = {"code": "", "title": ""}
        
        # Try to extract code from filename
        file_name = Path(file_path).name.lower()
        norm_patterns = [
            # English patterns (SP_, GOST_, etc.)
            r"(sp)[\s_]+[\d\.\-]+",  # SP_25.13330.2020
            r"(gost)[\s_]+[\d\.\-]+",  # GOST_52742-2007
            r"(snip)[\s_]+[\d\.\-]+",  # SNiP_2.02.01-83
            r"(gesn)[\s_]+[\d\.\-]+",  # GESN_01
            r"(mds)[\s_]+[\d\.\-]+",  # MDS_21-1.98
            r"(ppr)[\s_]*",  # PPR_
            r"(pos)[\s_]*",  # POS_
            # Russian patterns
            r"(сп|снип|гост|постановление|приказ|фз)\s*[\d\.\-]+",
            r"(сп|снип|гост|постановление|приказ|фз)[\s_]*\d+[\.\-\d]*",
            r"(гэсн|мдс)[\s_]*\d+[\.\-\d]*"
        ]
        
        for pattern in norm_patterns:
            match = re.search(pattern, file_name, re.IGNORECASE)
            if match:
                info["code"] = match.group(0).upper().replace("_", " ")
                break
        
        # If content is provided, extract more information
        if content:
            # Search for document codes in content
            content_patterns = [
                r"(?:СП|СНиП|ГОСТ|Постановление|Приказ|ФЗ)\s+\d{2,4}[.:]?\d{2,4}[.:]?\d{2,4}[-]?\d{4}",
                r"(?:СП|СНиП|ГОСТ|Постановление|Приказ|ФЗ)\s+\d{1,4}-[Фф][Зз]",
                r"(?:СП|СНиП|ГОСТ)\s+\d{2}\-\d{2}\-\d{4}",
                r"(?:СП|СНиП|ГОСТ)\s+\d{4}\-\d{4}"
            ]
            
            for pattern in content_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    info["code"] = matches[0].strip()
                    break
            
            # Search for document titles
            title_patterns = [
                r'(?:СП|СНиП|ГОСТ|Постановление|Приказ|ФЗ)\s+[\d\.\-]+\s*[«"]([^»"]+)[»"]',
                r'(?:Свод\s+правил|Строительные\s+нормы\s+и\s+правила|Государственный\s+стандарт)\s+([^»"]+)',
                r'(?:СП|СНиП|ГОСТ)\s+[\d\.\-]+\s*[-–—]\s*([^»"]+)'
            ]
            
            for pattern in title_patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    info["title"] = match.group(1).strip()
                    break
        
        return info
    
    def check_document_actual(self, file_path: str, content: Optional[str] = None) -> Dict:
        """Check if document is actual and provide recommendations"""
        result = {
            "file_path": file_path,
            "detected_code": "",
            "detected_title": "",
            "status": "unknown",
            "actual_version": None,
            "recommendations": [],
            "actions": []
        }
        
        # Extract document info
        doc_info = self.extract_document_info(file_path, content)
        result["detected_code"] = doc_info.get("code", "")
        result["detected_title"] = doc_info.get("title", "")
        
        if not doc_info.get("code"):
            result["status"] = "not_found"
            result["recommendations"].append("Не удалось определить код документа")
            return result
        
        # Check if document exists in database
        norm_doc = self.normative_db.get_document(doc_info["code"])
        if not norm_doc:
            result["status"] = "not_in_db"
            result["recommendations"].append(f"Документ {doc_info['code']} не найден в базе нормативных документов")
            return result
        
        # Check if document is actual
        if self.normative_db.is_document_actual(doc_info["code"]):
            result["status"] = "actual"
            result["actual_version"] = asdict(norm_doc)
            result["recommendations"].append(f"Документ {doc_info['code']} актуален")
        else:
            result["status"] = "outdated"
            replacement = self.normative_db.get_replacement_document(doc_info["code"])
            if replacement:
                result["actual_version"] = asdict(replacement)
                result["recommendations"].append(f"Документ {doc_info['code']} устарел, заменен на {replacement.code}")
                result["actions"].append({
                    "type": "replace",
                    "old_file": file_path,
                    "new_code": replacement.code,
                    "new_title": replacement.title
                })
            else:
                result["recommendations"].append(f"Документ {doc_info['code']} устарел, заменяющий документ не найден")
        
        return result
    
    def download_document(self, code: str, target_dir: str) -> Optional[str]:
        """Download document PDF from database URL"""
        norm_doc = self.normative_db.get_document(code)
        if not norm_doc or not norm_doc.pdf_url:
            return None
        
        try:
            # Create filename
            file_name = f"{norm_doc.code}_{norm_doc.title.replace(' ', '_')}.pdf"
            file_name = re.sub(r'[\\/*?:"<>|]', "_", file_name)  # Remove invalid characters
            file_path = Path(target_dir) / file_name
            
            # Download file
            response = requests.get(norm_doc.pdf_url, timeout=30)
            if response.status_code == 200:
                with open(file_path, "wb") as f:
                    f.write(response.content)
                return str(file_path)
            else:
                logger.error(f"Error downloading {norm_doc.pdf_url}: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error downloading document {code}: {e}")
            return None

def _determine_document_category(file_name_lower: str, content: str) -> str:
    """
    Determine the appropriate БАЗА category for a document based on filename and content
    Supports all subject areas: construction, finance, accounting, safety, HR, ecology, training
    """
    # Patterns for each category - ORDER MATTERS! More specific patterns first
    category_patterns = {
        # === СТРОИТЕЛЬСТВО (most specific first) ===
        "09. СТРОИТЕЛЬСТВО - СВОДЫ ПРАВИЛ": [
            r"\bсп[\s_]+\d",  # SP 25.13330.2020
            r"свод\s+правил",
            r"сп\s+рк"
        ],
        "07. СТРОИТЕЛЬСТВО - ГОСТы": [
            r"\bгост[\s_]+\d",  # GOST_52742-2007
            r"\bгост[\s_]+р",
            r"\bост[\s_]+\d"
        ],
        "08. СТРОИТЕЛЬСТВО - СНиПы": [
            r"\bсниип?[\s_]+\d",  # SNiP_2.02.01-83
            r"\bсн[\s_]+\d",
            r"\bвсхн"
        ],
        "05. СТРОИТЕЛЬСТВО - СМЕТЫ": [
            r"\bгэсн[\s_]*\d",  # GESN_01
            r"\bфер[\s_]*\d",
            r"\bтер[\s_]*\d",
            r"расценк",
            r"норматив\s+затрат",
            r"сметн",
            r"единичные\s+расценки"
        ],
        "02. СТРОИТЕЛЬСТВО - МДС": [
            r"\bмдс[\s_]*\d",  # MDS_21-1.98
            r"методические\s+документы",
            r"методические\s+рекомендации"
        ],
        "03. СТРОИТЕЛЬСТВО - ПОС/ППР": [
            r"\bппр[\s_]*",  # PPR_
            r"\bпос[\s_]*",
            r"проект\s+производства\s+работ",
            r"проект\s+организации\s+строительства",
            r"технологическая\s+карта",
            r"\bттк[\s_]*",
            r"\bтк[\s_]*"
        ],
        "04. СТРОИТЕЛЬСТВО - ПРОЕКТЫ": [
            r"типовой\s+проект",
            r"типовый\s+проект",
            r"альбом",
            r"серия",
            r"индивидуальный\s+проект"
        ],
        "06. СТРОИТЕЛЬСТВО - ОБРАЗЦЫ": [
            r"\bакт[\s_]*",
            r"справка",
            r"заключение",
            r"протокол",
            r"ведомость",
            r"образец",
            r"форма",
            r"бланк"
        ],
        
        # === ФИНАНСЫ ===
        "10. ФИНАНСЫ - ЗАКОНЫ": [
            r"налоговый\s+кодекс",
            r"\bнк\s+рф",
            r"финансы",
            r"бюджет",
            r"налог"
        ],
        "12. ФИНАНСЫ - СТАНДАРТЫ": [
            r"\bпбу[\s_]*\d",
            r"\bфсбу[\s_]*\d",
            r"\bрсбу[\s_]*\d",
            r"мсфо",
            r"положение\s+по\s+бухгалтерскому\s+учету"
        ],
        "14. ФИНАНСЫ - БАНКОВСКОЕ ДЕЛО": [
            r"центральный\s+банк",
            r"\bцб[\s_]*",
            r"инструкция\s+банка\s+россии",
            r"банковская",
            r"кредит"
        ],
        
        # === БУХГАЛТЕРИЯ ===
        "16. БУХУЧЕТ - ЗАКОНЫ": [
            r"федеральный\s+закон.*бухгалтерском\s+учете",
            r"бухгалтерский\s+учет",
            r"приказ.*минфин"
        ],
        "18. БУХУЧЕТ - ПЛАН СЧЕТОВ": [
            r"план\s+счетов",
            r"балансовые\s+счета",
            r"корреспонденция\s+счетов"
        ],
        
        # === ПРОМБЕЗОПАСНОСТЬ ===
        "22. ПРОМБЕЗОПАСНОСТЬ - ЗАКОНЫ": [
            r"промышленная\s+безопасность",
            r"ростехнадзор",
            r"опасные\s+производственные\s+объекты"
        ],
        "23. ПРОМБЕЗОПАСНОСТЬ - ПРАВИЛА": [
            r"\bфнп[\s_]*\d",
            r"\bпб[\s_]*\d",
            r"правила\s+безопасности",
            r"руководящий\s+документ"
        ],
        
        # === ОХРАНА ТРУДА ===
        "28. ОХРАНА ТРУДА - ЗАКОНЫ": [
            r"охрана\s+труда",
            r"трудовой\s+кодекс",
            r"\bтк\s+рф",
            r"безопасность\s+труда"
        ],
        "29. ОХРАНА ТРУДА - ПРАВИЛА": [
            r"правила.*охране\s+труда",
            r"типовые\s+инструкции",
            r"инструкция\s+по\s+охране\s+труда"
        ],
        "32. ОХРАНА ТРУДА - СИЗ": [
            r"средства\s+индивидуальной\s+защиты",
            r"\bсиз\b",
            r"нормы\s+выдачи",
            r"спецодежда"
        ],
        
        # === HR И КАДРЫ ===
        "35. HR - ТРУДОВОЕ ПРАВО": [
            r"трудовое\s+право",
            r"трудовой\s+договор",
            r"рабочее\s+время",
            r"отпуск"
        ],
        "36. HR - КАДРОВОЕ ДЕЛОПРОИЗВОДСТВО": [
            r"кадровое\s+делопроизводство",
            r"личная\s+карточка",
            r"трудовая\s+книжка",
            r"приказ\s+о\s+приеме"
        ],
        "38. HR - ОПЛАТА ТРУДА": [
            r"минимальный\s+размер\s+оплаты\s+труда",
            r"\bмрот\b",
            r"районные\s+коэффициенты",
            r"заработная\s+плата"
        ],
        
        # === ЭКОЛОГИЯ ===
        "42. ЭКОЛОГИЯ - ЗАКОНЫ": [
            r"охрана\s+окружающей\s+среды",
            r"водный\s+кодекс",
            r"лесной\s+кодекс",
            r"экология"
        ],
        "43. ЭКОЛОГИЯ - НОРМАТИВЫ": [
            r"предельно\s+допустимые\s+концентрации",
            r"\bпдк\b",
            r"\bпдв\b",
            r"\bндс\b",
            r"лимиты.*выброс"
        ],
        "47. ЭКОЛОГИЯ - ОТХОДЫ": [
            r"федеральный\s+классификатор\s+кодов\s+отходов",
            r"\bфкко\b",
            r"паспорт.*отход",
            r"обращение\s+с\s+отходами"
        ],
        
        # === ОБУЧАЮЩИЕ МАТЕРИАЛЫ ===
        "49. ЛЕКЦИИ И КУРСЫ": [
            r"лекция",
            r"курс",
            r"семинар",
            r"вебинар",
            r"презентация",
            r"обучение"
        ],
        "50. КНИГИ ОБЩИЕ": [
            r"учебник",
            r"пособие",
            r"справочник",
            r"монография",
            r"энциклопедия"
        ],
        "51. СТАНДАРТЫ КАЧЕСТВА": [
            r"\biso[\s_]*\d",
            r"гост\s+р\s+исо",
            r"система\s+менеджмента\s+качества",
            r"качество"
        ],
        
        # === ОБЩИЕ КАТЕГОРИИ (строительные fallback) ===
        "01. СТРОИТЕЛЬСТВО - НТД": [
            r"постановление",
            r"приказ",
            r"федеральный\s+закон",
            r"\bфз[\-\s]*\d+",
            r"строительные\s+нормы",
            r"государственный\s+стандарт"
        ]
    }
    
    # Check filename first (more reliable)
    for category, patterns in category_patterns.items():
        for pattern in patterns:
            if re.search(pattern, file_name_lower, re.IGNORECASE):
                return category
    
    # If no match in filename, check content (first 1000 chars for speed)
    if content:
        content_sample = content[:1000].lower()
        for category, patterns in category_patterns.items():
            for pattern in patterns:
                if re.search(pattern, content_sample, re.IGNORECASE):
                    return category
    
    # Default category
    return "99. ДРУГИЕ ДОКУМЕНТЫ"

def organize_normative_documents(base_path: str) -> Dict[str, str]:
    """Organize folder structure for comprehensive knowledge base covering all subject areas"""
    structure = {
        "БАЗА": {
            # === СТРОИТЕЛЬСТВО И АРХИТЕКТУРА ===
            "01. СТРОИТЕЛЬСТВО - НТД": ["СП", "СНиП", "ГОСТ", "Постановления", "Приказы"],
            "02. СТРОИТЕЛЬСТВО - МДС": ["МДС", "Рекомендации", "Пособия"],
            "03. СТРОИТЕЛЬСТВО - ПОС/ППР": ["ПОС", "ППР", "ТК", "ТТК"],
            "04. СТРОИТЕЛЬСТВО - ПРОЕКТЫ": ["Типовые проекты", "Альбомы", "Серии"],
            "05. СТРОИТЕЛЬСТВО - СМЕТЫ": ["ГЭСН", "ФЕР", "ТЕР", "Расценки"],
            "06. СТРОИТЕЛЬСТВО - ОБРАЗЦЫ": ["Акты", "Справки", "Заключения"],
            "07. СТРОИТЕЛЬСТВО - ГОСТы": ["ГОСТ", "ГОСТ Р", "ОСТ"],
            "08. СТРОИТЕЛЬСТВО - СНиПы": ["СНиП", "СН", "ВСХН"],
            "09. СТРОИТЕЛЬСТВО - СВОДЫ ПРАВИЛ": ["СП", "СП РК"],
            
            # === ФИНАНСЫ И ЭКОНОМИКА ===
            "10. ФИНАНСЫ - ЗАКОНЫ": ["НК РФ", "ФЗ", "Постановления", "Распоряжения"],
            "11. ФИНАНСЫ - МЕТОДИЧКИ": ["Методические указания", "Рекомендации", "Разъяснения"],
            "12. ФИНАНСЫ - СТАНДАРТЫ": ["ПБУ", "ФСБУ", "РСБУ", "МСФО"],
            "13. ФИНАНСЫ - ФОРМЫ ОТЧЕТНОСТИ": ["Баланс", "ОПУ", "Декларации", "Справки"],
            "14. ФИНАНСЫ - БАНКОВСКОЕ ДЕЛО": ["Инструкции ЦБ", "Положения", "Указания"],
            "15. ФИНАНСЫ - КНИГИ": ["Учебники", "Пособия", "Монографии"],
            
            # === БУХГАЛТЕРСКИЙ УЧЕТ ===
            "16. БУХУЧЕТ - ЗАКОНЫ": ["ФЗ О бухучете", "НК РФ", "Приказы МинФина"],
            "17. БУХУЧЕТ - ПБУ/ФСБУ": ["ПБУ", "ФСБУ", "Методические указания"],
            "18. БУХУЧЕТ - ПЛАН СЧЕТОВ": ["План счетов", "Инструкции", "Корреспонденция"],
            "19. БУХУЧЕТ - ДОКУМЕНТООБОРОТ": ["Первичные документы", "Регистры", "Формы"],
            "20. БУХУЧЕТ - ОТЧЕТНОСТЬ": ["Формы отчетности", "Пояснения", "Инструкции"],
            "21. БУХУЧЕТ - КНИГИ": ["Учебники", "Практические пособия", "Справочники"],
            
            # === ПРОМЫШЛЕННАЯ БЕЗОПАСНОСТЬ ===
            "22. ПРОМБЕЗОПАСНОСТЬ - ЗАКОНЫ": ["ФЗ", "Постановления", "Приказы Ростехнадзора"],
            "23. ПРОМБЕЗОПАСНОСТЬ - ПРАВИЛА": ["ФНП", "ПБ", "РД", "ГОСТ Р"],
            "24. ПРОМБЕЗОПАСНОСТЬ - ЭКСПЕРТИЗА": ["Требования", "Методики", "Регламенты"],
            "25. ПРОМБЕЗОПАСНОСТЬ - ЛИЦЕНЗИРОВАНИЕ": ["Положения", "Требования", "Формы"],
            "26. ПРОМБЕЗОПАСНОСТЬ - АВАРИИ": ["Расследование", "Классификация", "Учет"],
            "27. ПРОМБЕЗОПАСНОСТЬ - КНИГИ": ["Учебники", "Методические пособия", "Справочники"],
            
            # === ОХРАНА ТРУДА ===
            "28. ОХРАНА ТРУДА - ЗАКОНЫ": ["ТК РФ", "ФЗ", "Постановления Правительства"],
            "29. ОХРАНА ТРУДА - ПРАВИЛА": ["Правила по ОТ", "Инструкции", "ГОСТ Р"],
            "30. ОХРАНА ТРУДА - ОБУЧЕНИЕ": ["Программы обучения", "Билеты", "Тесты"],
            "31. ОХРАНА ТРУДА - МЕДОСМОТРЫ": ["Приказы МинЗдрава", "Списки", "Формы"],
            "32. ОХРАНА ТРУДА - СИЗ": ["ГОСТы", "Сертификаты", "Нормы выдачи"],
            "33. ОХРАНА ТРУДА - РАССЛЕДОВАНИЕ": ["Положения", "Формы актов", "Методики"],
            "34. ОХРАНА ТРУДА - КНИГИ": ["Учебники", "Пособия", "Справочники"],
            
            # === HR И ТРУДОВОЕ ПРАВО ===
            "35. HR - ТРУДОВОЕ ПРАВО": ["ТК РФ", "ФЗ", "Постановления ВС РФ"],
            "36. HR - КАДРОВОЕ ДЕЛОПРОИЗВОДСТВО": ["Приказы", "Положения", "Инструкции"],
            "37. HR - ДОКУМЕНТЫ КАДРОВЫЕ": ["Трудовые договоры", "Приказы", "Личные карточки"],
            "38. HR - ОПЛАТА ТРУДА": ["МРОТ", "Районные коэффициенты", "Надбавки"],
            "39. HR - ОТПУСКА И БОЛЬНИЧНЫЕ": ["Расчеты", "Формы", "Справки"],
            "40. HR - АТТЕСТАЦИЯ": ["Положения", "Формы", "Критерии"],
            "41. HR - КНИГИ": ["Учебники по HR", "Практические пособия", "Психология"],
            
            # === ЭКОЛОГИЯ ===
            "42. ЭКОЛОГИЯ - ЗАКОНЫ": ["ФЗ Об охране окружающей среды", "Водный кодекс", "Лесной кодекс"],
            "43. ЭКОЛОГИЯ - НОРМАТИВЫ": ["ПДК", "ПДВ", "НДС", "Лимиты"],
            "44. ЭКОЛОГИЯ - РАЗРЕШЕНИЯ": ["Лицензии", "Разрешения на выбросы", "ПНООЛР"],
            "45. ЭКОЛОГИЯ - ОТЧЕТНОСТЬ": ["2-ТП", "Статистика", "Декларации"],
            "46. ЭКОЛОГИЯ - МОНИТОРИНГ": ["ПЭК", "ПЭМ", "Измерения", "Контроль"],
            "47. ЭКОЛОГИЯ - ОТХОДЫ": ["ФККО", "Паспорта отходов", "Обращение с отходами"],
            "48. ЭКОЛОГИЯ - КНИГИ": ["Учебники", "Справочники", "Методические пособия"],
            
            # === ОБУЧАЮЩИЕ МАТЕРИАЛЫ ===
            "49. ЛЕКЦИИ И КУРСЫ": ["Видеолекции", "Презентации", "Конспекты"],
            "50. КНИГИ ОБЩИЕ": ["Техническая литература", "Справочники", "Энциклопедии"],
            "51. СТАНДАРТЫ КАЧЕСТВА": ["ISO", "ГОСТ Р ИСО", "Системы менеджмента"],
            "52. ПРОЕКТИРОВАНИЕ": ["САПР", "BIM", "Технологии проектирования"],
            
            # === ПРОЧЕЕ ===
            "99. ДРУГИЕ ДОКУМЕНТЫ": ["Разное", "Архив", "Временные файлы"]
        }
    }
    
    folder_mapping = {}
    
    # Create folder structure
    for main_folder, subfolders in structure.items():
        main_path = Path(base_path) / main_folder
        main_path.mkdir(parents=True, exist_ok=True)
        folder_mapping[main_folder] = str(main_path)
        
        for subfolder, prefixes in subfolders.items():
            sub_path = main_path / subfolder
            sub_path.mkdir(parents=True, exist_ok=True)
            folder_mapping[subfolder] = str(sub_path)
    
    logger.info(f"Created normative documents folder structure in {base_path}")
    return folder_mapping

def rename_normative_file(file_path: str, doc_info: Dict, normative_db: NormativeDatabase) -> str:
    """Rename normative file with proper naming convention"""
    try:
        if not doc_info.get("code"):
            return file_path
        
        code = doc_info["code"]
        title = doc_info.get("title", "Без названия")
        
        # Get document from database
        norm_doc = normative_db.get_document(code)
        if not norm_doc:
            # If not in database, use extracted info
            new_file_name = f"{code}_{title.replace(' ', '_')}.pdf"
        else:
            # Use database info
            new_file_name = f"{norm_doc.code}_{norm_doc.title.replace(' ', '_')}.pdf"
        
        # Remove invalid characters
        new_file_name = re.sub(r'[\\/*?:"<>|]', "_", new_file_name)
        new_file_path = Path(file_path).parent / new_file_name
        
        # Rename file if needed
        if str(new_file_path) != file_path:
            Path(file_path).rename(new_file_path)
            logger.info(f"Renamed file: {Path(file_path).name} -> {new_file_name}")
            return str(new_file_path)
        else:
            return file_path
            
    except Exception as e:
        logger.error(f"Error renaming file: {e}")
        return file_path

def ntd_preprocess(file_path: str, normative_db: NormativeDatabase, normative_checker: NormativeChecker, 
                  target_dir: Optional[str] = None, test_mode: bool = False) -> Optional[str]:
    """
    Stage 0: Pre-process normative document
    This function integrates into the 14-stage RAG pipeline as the initial stage
    for normative technical documentation files
    """
    # Use BASE_DIR environment variable or default to I:/docs
    if target_dir is None:
        base_dir_env = os.getenv("BASE_DIR", "I:/docs")
        target_dir = base_dir_env  # Используем базовую папку напрямую
    
    try:
        logger.info(f"Starting NTD preprocessing for: {file_path}")
        
        # 1. Check if file exists and is readable
        if not Path(file_path).exists():
            logger.error(f"File not found: {file_path}")
            return None
        
        if not os.access(file_path, os.R_OK):
            logger.error(f"Cannot read file: {file_path}")
            return None
        
        # 2. Extract content for analysis (basic text extraction)
        content = ""
        try:
            if file_path.lower().endswith('.pdf'):
                # In test mode, try to read as text first
                if test_mode:
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                    except:
                        # If text read fails, try PDF
                        from PyPDF2 import PdfReader
                        reader = PdfReader(file_path)
                        content = ' '.join(page.extract_text() for page in reader.pages if page.extract_text())
                else:
                    from PyPDF2 import PdfReader
                    reader = PdfReader(file_path)
                    content = ' '.join(page.extract_text() for page in reader.pages if page.extract_text())
            elif file_path.lower().endswith('.txt'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
        except Exception as e:
            logger.warning(f"Could not extract text from {file_path}: {e}")
        
        # 3. Check document actuality (skip in test mode)
        if test_mode:
            # In test mode, create mock check result based on extracted info
            doc_info = normative_checker.extract_document_info(file_path, content)
            check_result = {
                "status": "test_mode",
                "detected_code": doc_info.get("code", Path(file_path).stem),
                "detected_title": doc_info.get("title", ""),
                "file_path": file_path
            }
        else:
            check_result = normative_checker.check_document_actual(file_path, content)
            logger.info(f"Document check result: {check_result['status']}")
            
            # 4. If document is outdated, try to download actual version
            if check_result["status"] == "outdated" and check_result.get("actual_version"):
                actual_code = check_result["actual_version"]["code"]
                logger.info(f"Downloading actual version: {actual_code}")
                new_file_path = normative_checker.download_document(actual_code, target_dir)
                if new_file_path:
                    logger.info(f"Downloaded actual version: {new_file_path}")
                    file_path = new_file_path
                    # Re-check the new document
                    content = ""
                    try:
                        if file_path.lower().endswith('.pdf'):
                            from PyPDF2 import PdfReader
                            reader = PdfReader(file_path)
                            content = ' '.join(page.extract_text() for page in reader.pages if page.extract_text())
                    except Exception as e:
                        logger.warning(f"Could not extract text from downloaded file: {e}")
                    
                    check_result = normative_checker.check_document_actual(file_path, content)
                else:
                    logger.warning("Failed to download actual version")
            
            # 5. If document is not found in DB, continue processing anyway
            if check_result["status"] in ["not_found", "not_in_db"]:
                logger.info(f"Document not in NTD database, but continuing processing: {check_result['status']}")
                # Continue processing even if not in NTD database
        
        # 6. Rename file with proper naming convention
        renamed_file_path = rename_normative_file(file_path, check_result, normative_db)
        
        # 7. Move file to appropriate БАЗА category folder based on document type
        doc_info = normative_checker.extract_document_info(renamed_file_path, content)
        file_name_lower = Path(renamed_file_path).name.lower()
        
        # Determine category based on document type patterns
        category_path = _determine_document_category(file_name_lower, content)
        
        # Create full path: I:/docs/БАЗА/{category}/
        base_dir_env = os.getenv("BASE_DIR", "I:/docs")
        target_path = Path(base_dir_env) / "БАЗА" / category_path
        target_path.mkdir(parents=True, exist_ok=True)
        
        # Move file to appropriate category folder
        final_file_path = target_path / Path(renamed_file_path).name
        if str(final_file_path) != renamed_file_path:
            try:
                import shutil
                shutil.move(renamed_file_path, str(final_file_path))
                renamed_file_path = str(final_file_path)
                logger.info(f"📁 Moved file to БАЗА category: {category_path}")
            except Exception as e:
                logger.error(f"Error moving file to category folder: {e}")
                # If move fails, continue with original path
        
        # 8. Mark as processed in database
        if doc_info.get("code"):
            normative_db.mark_as_processed(doc_info["code"], renamed_file_path)
        
        logger.info(f"NTD preprocessing completed: {renamed_file_path}")
        return renamed_file_path
        
    except Exception as e:
        logger.error(f"Error in NTD preprocessing: {e}")
        return None

# Example usage function
def initialize_ntd_system(base_dir: Optional[str] = None) -> Tuple[NormativeDatabase, NormativeChecker]:
    """Initialize NTD system with database and checker"""
    # Use BASE_DIR environment variable or default to I:/docs
    if base_dir is None:
        base_dir_env = os.getenv("BASE_DIR", "I:/docs")
        base_dir = base_dir_env
    
    # Create folder structure
    organize_normative_documents(base_dir)
    
    # Initialize database
    normative_db = NormativeDatabase(
        db_path=os.path.join(base_dir, "norms_db", "ntd_local.db"),
        json_path=os.path.join(base_dir, "norms_db", "ntd_full_db.json")
    )
    
    # Initialize checker
    normative_checker = NormativeChecker(normative_db)
    
    return normative_db, normative_checker

if __name__ == "__main__":
    # Example usage
    normative_db, normative_checker = initialize_ntd_system()
    print(f"Initialized NTD system with {len(normative_db.documents)} documents")
    
    # Example search
    results = normative_db.search_documents("строительство", "construction")
    print(f"Found {len(results)} construction documents")
    
    # Example document check
    # check_result = normative_checker.check_document_actual("example_file.pdf")
    # print(f"Document check result: {check_result}")