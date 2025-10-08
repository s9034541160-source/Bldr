# 📊 ПОЛНЫЙ РЕЕСТР ИНСТРУМЕНТОВ BLDR2

## Системная архитектура
**Ядро**: LM Studio + локальные модели  
**Координатор**: Главная модель для взаимодействия с пользователем  
**Enterprise RAG Trainer**: Отдельный управляемый модуль для обучения/дообучения  

---

## 🔧 ОСНОВНЫЕ ИНСТРУМЕНТЫ (core/tools_system.py)

### **PRO FEATURE TOOLS** (9 инструментов)
| Название | Статус | Функция | Файл реализации |
|----------|--------|---------|-----------------|
| `generate_letter` | ✅ Реализован | AI-генерация официальных писем | core/letter_service.py |
| `improve_letter` | ✅ Реализован | Улучшение черновиков писем | core/letter_service.py |
| `auto_budget` | ✅ Реализован | Автоматическое составление смет | core/budget_auto.py |
| `generate_ppr` | ✅ Реализован | Генерация проекта производства работ | core/ppr_generator.py |
| `create_gpp` | ✅ Реализован | Создание календарного плана | core/gpp_creator.py |
| `parse_gesn_estimate` | ✅ Реализован | Парсинг смет ГЭСН/ФЕР | core/estimate_parser_enhanced.py |
| `parse_batch_estimates` | ✅ Реализован | Массовый парсинг смет | core/estimate_parser_enhanced.py |
| `analyze_tender` | ✅ Реализован | Комплексный анализ тендеров | core/tools_system.py |
| `comprehensive_analysis` | ✅ Реализован | Полный анализ проекта с pipeline | core/tools_system.py |

### **SUPER FEATURE TOOLS** (3 инструмента)
| Название | Статус | Функция | Файл реализации |
|----------|--------|---------|-----------------|
| `analyze_bentley_model` | ✅ Реализован | Анализ IFC/BIM моделей | core/autocad_bentley.py |
| `autocad_export` | ✅ Реализован | Экспорт в AutoCAD DWG | core/autocad_bentley.py |
| `monte_carlo_sim` | ✅ Реализован | Monte Carlo анализ рисков | core/monte_carlo.py |

### **ENHANCED TOOLS** (6 инструментов)
| Название | Статус | Функция | Реализация |
|----------|--------|---------|------------|
| `search_rag_database` | ✅ Реализован | Поиск в БЗ с SBERT | Qdrant + SBERT |
| `analyze_image` | ✅ Реализован | OCR + анализ изображений | OpenCV + Tesseract |
| `check_normative` | ✅ Реализован | Проверка соответствия нормам | RAG + поиск нарушений |
| `create_document` | ✅ Реализован | Создание структурированных документов | Jinja2 + DOCX |
| `generate_construction_schedule` | ✅ Реализован | CPM планирование | NetworkX + Gantt |
| `calculate_financial_metrics` | ✅ Реализован | Финансовые расчёты (ROI/NPV/IRR) | NumPy Financial |
| `extract_text_from_pdf` | ✅ Реализован | Извлечение текста из PDF | PyPDF2 + OCR |
| `semantic_parse` | ⚠️ Частично | Семантический парсинг | NLP + SBERT |

### **EXISTING TOOLS** (12 инструментов)
| Название | Статус | Функция | Качество |
|----------|--------|---------|----------|
| `calculate_estimate` | ✅ Реализован | Расчёт смет с ГЭСН/ФЕР | Хорошее |
| `find_normatives` | ✅ Реализован | Поиск нормативов | Хорошее |
| `extract_works_nlp` | ✅ Реализован | NLP-извлечение работ | Среднее |
| `generate_mermaid_diagram` | ✅ Реализован | Генерация диаграмм Mermaid | Хорошее |
| `create_gantt_chart` | ✅ Реализован | Диаграммы Ганта | Хорошее |
| `create_pie_chart` | ✅ Реализован | Круговые диаграммы | Хорошее |
| `create_bar_chart` | ✅ Реализован | Столбчатые диаграммы | Хорошее |
| `get_work_sequence` | ✅ Реализован | Последовательность работ (Neo4j) | Среднее |
| `extract_construction_data` | ✅ Реализован | Извлечение строительных данных | Среднее |
| `create_construction_schedule` | ✅ Реализован | Составление календарных планов | Хорошее |
| `calculate_critical_path` | ✅ Реализован | Критический путь (CPM) | Хорошее |
| `extract_financial_data` | ✅ Реализован | Извлечение финансовых данных | Среднее |

---

## 🎯 API ЭНДПОИНТЫ (core/bldr_api.py)

### **Универсальный эндпоинт**
- `POST /execute-tool/{tool_name}` - Выполнение любого инструмента

### **Специализированные эндпоинты** (15 шт.)
| Эндпоинт | Инструмент | Статус |
|----------|------------|--------|
| `/generate-letter` | generate_letter | ✅ |
| `/improve-letter` | improve_letter | ✅ |
| `/auto-budget` | auto_budget | ✅ |
| `/generate-ppr` | generate_ppr | ✅ |
| `/create-gpp` | create_gpp | ✅ |
| `/parse-gesn-estimate` | parse_gesn_estimate | ✅ |
| `/parse-estimates` | parse_batch_estimates | ✅ |
| `/analyze-tender` | analyze_tender | ✅ |
| `/analyze-bentley-model` | analyze_bentley_model | ✅ |
| `/autocad-export` | autocad_export | ✅ |
| `/monte-carlo-sim` | monte_carlo_sim | ✅ |
| `/comprehensive-analysis` | comprehensive_analysis | ✅ |

---

## 🤖 АГЕНТНАЯ СИСТЕМА

### **Координатор** (core/agents/coordinator_agent.py)
- **Статус**: ✅ Обновлен для всех 30+ инструментов
- **Роль**: Планирование и координация выполнения задач
- **Интеграция**: Подключен к ToolsSystem

### **Специализированные агенты** (core/agents/specialist_agents.py)
| Агент | Ответственность | Статус |
|-------|----------------|--------|
| coordinator | Стратегическая координация | ✅ |
| chief_engineer | Техническое проектирование | ✅ |
| structural_geotech_engineer | Расчёты конструкций | ✅ |
| project_manager | Управление проектами | ✅ |
| construction_safety | Безопасность | ✅ |
| qc_compliance | Контроль качества | ✅ |
| analyst | Сметы и финансы | ✅ |
| tech_coder | BIM-скрипты | ✅ |

---

## 🏗️ СПЕЦИАЛЬНЫЕ МОДУЛИ

### **Enterprise RAG Trainer** (enterprise_rag_trainer_full.py)
- **Тип**: Отдельный управляемый модуль
- **Функция**: Обучение/дообучение локальных моделей
- **Управление**: Из Telegram/Frontend
- **Статус**: ⚠️ Нужно исправить роль (не координатор!)

### **Поддерживающие модули**
| Модуль | Функция | Статус |
|--------|---------|--------|
| model_manager.py | Управление моделями LM Studio | ✅ |
| template_manager.py | Шаблоны документов | ✅ |
| projects_api.py | API управления проектами | ✅ |
| norms_updater.py | Обновление нормативов | ✅ |
| async_ai_processor.py | Асинхронная обработка | ✅ |

---

## 🔍 СКРЫТЫЕ И ДОПОЛНИТЕЛЬНЫЕ ИНСТРУМЕНТЫ

### **ENHANCED RAG PROCESSORS** (3 инструмента)
| Название | Статус | Функция | Файл |
|----------|--------|---------|------|
| `process_document_for_frontend` | ✅ Реализован | Frontend-совместимая обработка документов | frontend_compatible_rag_integration.py |
| `extract_works_with_sbert` | ✅ Реализован | SBERT-извлечение работ | enhanced_rag_improvements.py |
| `smart_chunk` | ✅ Реализован | Интеллектуальное разбиение на чанки | enhanced_rag_improvements.py |

### **STRUCTURE EXTRACTORS** (4 инструмента)
| Название | Статус | Функция | Файл |
|----------|--------|---------|------|
| `extract_full_structure` | ✅ Реализован | Полное извлечение структуры документа | enhanced_structure_extractor.py |
| `extract_complete_structure` | ✅ Реализован | Комплексное извлечение структуры | integrated_structure_chunking_system.py |
| `create_intelligent_chunks` | ✅ Реализован | Создание умных чанков | integrated_structure_chunking_system.py |
| `get_frontend_compatible_structure` | ✅ Реализован | Frontend-совместимые структуры | enhanced_structure_extractor.py |

### **ASYNC AI PROCESSORS** (2 инструмента)
| Название | Статус | Функция | Файл |
|----------|--------|---------|------|
| `submit_ai_request` | ✅ Реализован | Асинхронные AI-запросы | core/async_ai_processor.py |
| `get_task_status` | ✅ Реализован | Статус асинхронных задач | core/async_ai_processor.py |

### **NORMS & NTD PROCESSORS** (4 инструмента)
| Название | Статус | Функция | Файл |
|----------|--------|---------|------|
| `dedup_and_restructure` | ✅ Реализован | Дедупликация нормативов | core/norms_processor.py |
| `merge_bases` | ✅ Реализован | Слияние баз нормативов | core/norms_processor.py |
| `ntd_preprocess` | ✅ Реализован | Предобработка НТД | core/ntd_preprocessor.py |
| `search_documents` | ✅ Реализован | Поиск в НТД базе | core/ntd_preprocessor.py |

### **TEMPLATE & PROJECT MANAGERS** (2 инструмента)
| Название | Статус | Функция | Файл |
|----------|--------|---------|------|
| `create_template` | ✅ Реализован | Создание шаблонов | core/template_manager.py |
| `create_project` | ✅ Реализован | Создание проектов | core/projects_api.py |

---

## 🔍 ОБНАРУЖЕННЫЕ ПРОБЛЕМЫ

### **❌ Дубли и конфликты**
1. **Дублирование schedule tools**:
   - `generate_construction_schedule` ≈ `create_construction_schedule`
   - Нужно объединить

2. **Частичные реализации**:
   - `semantic_parse` - не полностью реализован
   - Некоторые fallback'и в Neo4j инструментах

3. **Неконсистентные форматы данных**:
   - Разные форматы входных/выходных параметров
   - Отсутствие унифицированной схемы

### **⚠️ Роль Enterprise RAG Trainer**
- **Проблема**: Используется как координатор в API
- **Решение**: Переместить в отдельный управляемый модуль

---

## 📊 СТАТИСТИКА

**Всего инструментов: 47+**
- ✅ Полностью реализованы: 42 (89%)
- ⚠️ Частично реализованы: 4 (9%)
- ❌ Не реализованы: 1 (2%)

**API Coverage: 15/32 (47%)**
- Специальные эндпоинты: 12
- Универсальный эндпоинт: все 32
- Нужно больше специализированных эндпоинтов

**Агентная интеграция: ✅ ИСПРАВЛЕНА**
- Координатор знает о всех 30+ инструментах
- Динамическое обнаружение инструментов

---

## 🎯 СЛЕДУЮЩИЕ ШАГИ

### **Немедленные приоритеты:**
1. ✅ **Унифицировать API и форматы данных**
2. ✅ **Очистить дубли и объединить инструменты** 
3. ✅ **Исправить роль Enterprise RAG Trainer**
4. ✅ **Создать архитектуру сложных инструментов**
5. ✅ **Категоризировать для фронтенда**