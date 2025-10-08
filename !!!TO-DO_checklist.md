# 📋 ULTRA-ДЕТАЛИЗИРОВАННЫЙ ЧЕК-ЛИСТ  

**Цель:** за 6 месяцев превратить MVP в **production-ready «строй-комбайн»** — загрузил PDF → получил ZIP (смета ГЭСН, проверенные РД, ГПР, ресурсы, маржа) + ЭДО + кадры + финансы.  

**Ориентир:** 80 % задач делаются **в Cursor** по принципу «fast-prototype → test → refactor → doc → push».  

**Включены 5 critical-fixes** по итогам аудита.

---

## ✅ Daily Cursor-Workflow (фиксированный)

```text
1. Открываем Cursor → берём issue из GitHub-Projects
2. Генерируем skeleton: «Создай fastapi-инструмент...» → accept → run
3. Подкидываем реальные PDF/Excel → тест → исправляем
4. Пишем unit-тест (Cursor → «generate pytest»)
5. Генерируем docstring → mkdocs → push → PR
6. Telegram-бот сразу вызывает новый инструмент через `/test`
```

- [ ] Ежедневно следуем workflow

---

## 🔧 5 Critical-Fixes (встроены в план)

| № | Fix | Где внедрен | Done-чек |
|---|-----|-------------|----------|
| 1 | **Pre-commit хуки** (`black, flake8, mypy`) | Фаза 0.0 | - [ ] |
| 2 | **Маржа % вместо NPV** | Фаза 1.2.1 | - [ ] |
| 3 | **Recursive ГОСТ-чанкинг** (3 уровня) | Фаза 0.1.1 | - [ ] |
| 4 | **JSON-манифест state-machine** для TG | Фаза 0.2.2 | - [ ] |
| 5 | **Excel-экспорт вместо 1С/банк-API** (до v1.1) | Фаза 4.0 | - [ ] |

---

## 0. ФАЗА 0: СИНХРОНИЗАЦИЯ И СТАБИЛИЗАЦИЯ  

**Срок:** 2-3 недели  
**Done:** `docker-compose up --build` → все `healthy`, бот без бредов, RAG точный.

### 0.0 Pre-commit & CI-base (critical-fix #1)

```bash
# Cursor: создай .pre-commit-config.yaml
- repo: https://github.com/psf/black
  rev: 24.4.2
  hooks: [{id: black}]
- repo: https://github.com/pycqa/flake8
  rev: 7.0.0
  hooks: [{id: flake8}]
- repo: https://github.com/pre-commit/mirrors-mypy
  rev: v1.10.0
  hooks: [{id: mypy}]
```

- [ ] `pre-commit install` пройден  
- [ ] GitHub Action `lint.yml` зелёный  

### 0.1 RAG-тренер → 100 % (critical-fix #3)

| Подзадача | Cursor-запрос / файл | Done-чек |
|-----------|----------------------|----------|
| 0.1.1 Recursive ГОСТ-чанкинг | «Refactor `enterprise_rag_trainer_full.py` to split by regex `^(\d+\.\d+\.\d+)` (3 levels) → store path `6→6.2→6.2.3` in meta» | - [ ] |
| 0.1.2 Qdrant оптимизация | «Add batch=64, int8 quantization via `optimum-intel`» | - [ ] |
| 0.1.3 Redis-кэш | «Key=md5(query), TTL=1h, fallback to RAG» | - [ ] |
| 0.1.4 Тест на 10 real PDF | «pytest: top-1 answer must contain paragraph number» 9/10 | - [ ] |
| 0.1.5 Fallback «нет данных» | «If relevance < 0.78 → return ‘Нет информации в НТД’» | - [ ] |

### 0.2 Telegram-бот → продакшен (critical-fix #4)

| Подзадача | Cursor-запрос / файл | Done-чек |
|-----------|----------------------|----------|
| 0.2.1 ConversationHandler | «Refactor to `python-telegram-bot` ConversationHandler for 3-step: /смета → region → file → result» | - [ ] |
| 0.2.2 JSON-манифест state-machine | «Create `manifests/tender.json` with steps: file, choice-region… bot reads dynamically» | - [ ] |
| 0.2.3 Webhook | «FastAPI route `/tg-webhook` + `setWebhook` HTTPS» | - [ ] |
| 0.2.4 Быстрые команды | «BotCommandScope: /смета, /проверить_рд, /график» | - [ ] |
| 0.2.5 Rate-limit | «User-id whitelist, 20 msg/min, ban after 5 spam» | - [ ] |

### 0.3 Ускорение инструментов

| Подзадача | Cursor-запрос / файл | Done-чек |
|-----------|----------------------|----------|
| 0.3.1 Шаблон new_tool | «CLI `new_tool.py EstimateRoad` → scaffolds manifest, main.py, test, README» | - [ ] |
| 0.3.2 BaseTool класс | «All tools inherit `execute(params: BaseModel) -> ToolResult`» | - [ ] |
| 0.3.3 Авто-документация | «GitHub Action: on push to `/tools/*` → mkdocs update» | - [ ] |
| 0.3.4 pytest-tools | «Plugin runs `tool.validate_manifest()` and `tool.execute(mock)`» | - [ ] |

---

## 1. ФАЗА 1: ЯДЕРНЫЕ ИНСТРУМЕНТЫ «МЕГА-КОМБАЙНА»  

**Срок:** 6-8 недель  
**Done:** пользователь в TG `/смета` → загружает ПДФ → получает ZIP (смета, ГПР, ресурсы, маржа) ≤ 3 минуты.

### 1.1 Инструмент «Анализ тендера» (`analyze_tender_full`)

| Шаг | Название | Cursor-запрос | Выход | Done |
|-----|----------|---------------|--------|------|
| 1 | extract_volumes | «Parse tables via `camelot-py` → {code, name, unit, qty}» | `volumes.json` | - [ ] |
| 2 | extract_specs | «Zero-shot NER → steel/concrete/pipe entities» | `specs.json` | - [ ] |
| 3 | check_rd | «Compare sections vs ГОСТ-21.101 mandatory via RAG» | `rd_issues.json` | - [ ] |
| 4 | gesn_map | «Fuzzy + SBERT embed → ГЭСН-codes» | `gesn_mapped.json` | - [ ] |
| 5 | calculate_estimate | «Call `estimate_calculator` with mapped» | `estimate.xlsx` | - [ ] |
| 6 | generate_schedule | «Feed to `scheduler_tool`» | `gantt.xlsx` | - [ ] |
| 7 | financial_summary | «Margin %, cash-flow (critical-fix #2)» | `finance.json` | - [ ] |
| 8 | compile_report | «Merge to `tender_report.docx` via `docxtpl`» | `tender_report.docx` | - [ ] |

### 1.2 Инструмент «Сметный калькулятор» (`estimate_calculator`)  

**Фичи:** вахта, районные коэффициенты, командировочные, СИЗ, накладные 18 % (critical-fix #2)

| Подзадача | Cursor-запрос | Done |
|-----------|---------------|------|
| 1.2.1 Model `ShiftWork` | «Pydantic: shift_days, pattern, travel, north_coeff» | - [ ] |
| 1.2.2 ЗП вахты | «base_salary * north_coeff * (shift_days/30) + travel*daily» | - [ ] |
| 1.2.3 СИЗ-нормативы | «Parse СИЗ-2024.xlsx → dict{prof: cost_month}» | - [ ] |
| 1.2.4 Итоговый Excel | «Template ГЭСН-2024.xlsx → openpyxl fill» | - [ ] |
| 1.2.5 Тест vs ручная смета | «deviation ≤ 2 % on 10 samples» | - [ ] |

### 1.3 Инструмент «Планировщик ГПР» (`scheduler_tool`)

| Подзадача | Cursor-запрос | Done |
|-----------|---------------|------|
| 1.3.1 CPM-граф | «NetworkX: critical_path from WBS+durations» | - [ ] |
| 1.3.2 Resource levelling | «Heuristic min-late-finish → flatten headcount» | - [ ] |
| 1.3.3 Export MS-Project | «python-msproject → .xml» | - [ ] |
| 1.3.4 Excel-Gantt | «xlsxwriter bar-chart per week» | - [ ] |
| 1.3.5 TG-бот | «/график → upload estimate.xlsx → return gantt.xlsx+PNG» | - [ ] |

---

## 2. ФАЗА 2: ОДИН КЛИК — ОДИН АРХИВ  

**Срок:** 2 недели  
**Done:** пользователь жмёт «📄» → получает `project-{date}.zip` (всё inside)

### 2.1 Orchestrator-service (Celery-chain)

```python
chain = extract_signature.s(file_id) |
        analyze_tender_full.s() |
        generate_schedule.s() |
        compile_final_report.s() |
        notify_tg.s(chat_id)
```

- [ ] Время цепочки ≤ 180 сек на 50-страниц  
- [ ] WebSocket progress-bar %  

### 2.2 TG-одна кнопка

```
[📄 Получить смету] [📊 График] [💰 Финансы]
```

- [ ] Кнопка «📄» → chain → ZIP → `project.zip`  

---

## 3. ФАЗА 3: WEB-UI + MOBILE PWA  

**Срок:** 2 недели  

### 3.1 Web-React

- [ ] Drag-and-drop PDF → progress-bar → download ZIP  
- [ ] Preview PDF.js отчёта  

### 3.2 Mobile PWA (CapacitorJS)

- [ ] Камера → OCR table → `/analyze_tender`  
- [ ] Offline-queue → sync when online  

---

## 4. ФАЗА 4: КАДРЫ + ФИНАНСЫ (critical-fix #5: Excel до v1.1)  

**Параллельно 6-12 недель**  

### 4.1 Кадровый модуль

| Подзадача | Выход | Done |
|-----------|--------|------|
| 4.1.1 Табель | Интеграция турникет REST → `timesheet.xlsx` | - [ ] |
| 4.1.2 Зарплата вахты | Экспорт в 1С-ЗУП **XML-шаблон** (не API) | - [ ] |

### 4.2 Финмодуль (margin %, not NPV)

| Подзадача | Выход | Done |
|-----------|--------|------|
| 4.2.1 Cash-flow по неделям | `cashflow.xlsx` (income/outcome/balance) | - [ ] |
| 4.2.2 Календарь платежей | `payment_calendar.xlsx` → TG notify | - [ ] |
| 4.2.3 Экспорт банк-выписки | **CSV-загрузка** (не API) → auto-match | - [ ] |

---

## 5. КОНТРОЛЬ КАЧЕСТВА (всё время)

| Тип | Как | Метрика | Done |
|-----|-----|---------|------|
| **Unit** | `pytest --cov=services --cov-report=html` | ≥ 85 % | - [ ] |
| **E2E** | Playwright: PDF→ZIP ≤ 5 мин | 100 % проходит | - [ ] |
| **Load** | Locust: 50 users | p95 < 5 с | - [ ] |
| **Security** | `bandit -r .` — 0 HIGH | 0 критических | - [ ] |
| **Mutation** | `mutmut run && mutmut html` | ≥ 60 % убито | - [ ] |

---

## 6. РЕЛИЗНАЯ МОДЕЛЬ

| Версия | Что показываем | Дата | Успех-метрика |
|--------|----------------|------|---------------|
| **v0.6** | RAG точный + TG без бредов | +2 нед | 90 % точных ответов |
| **v0.7** | Один инструмент «смета» | +4 нед | 100 % PDF проходят |
| **v0.8** | Один клик = ZIP (≤3 мин) | +6 нед | Время ≤ 180 сек |
| **v0.9** | Web-UI + мобильное фото | +8 нед | 80 % юзеров через web |
| **v1.0 MVP** | Кадры+Excel-1С+ЭДО | +12 нед | ROI ↑ 10 % vs Excel |

---

## 7. GitHub-Projects доска (автоматизировано)

| Колонка | Авто-правило |
|---------|--------------|
| **Backlog** | `label=feature` |
| **Cursor** | `assignee=@me AND label=cursor` |
| **Review** | `PR opened` |
| **Test** | `label=need-test` |
| **Done** | `PR merged` |

---

## 8. ЧТО ДЕЛАТЬ ПРЯМО СЕЙЧАС (сегодня)

- [ ] Создать ветку `feat/audit-fixes`  
- [ ] Cursor → открыть `enterprise_rag_trainer_full.py` → применить recursive чанкинг  
- [ ] Скоммитить → push → PR → перетащить issue в Review  

---

✅ **Готово к печати и галочкам!**  
**Следующий шаг:** скажи **«Берём 0.1.1 и 1.2.1»** — и я создаю PR + issue-шаблоны.