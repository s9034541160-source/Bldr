# Bldr Empire v2 — Архитектурная карта проекта

Версия: 2025-09-20

Цель документа: дать целостную картину проекта (модули, маршруты, сущности, цепочки взаимодействий, зависимости и основные сценарии) как для быстрой навигации, так и для планирования улучшений.

—

Содержание:
- 1. Обзор и стек
- 2. Структура каталогов (ключевое)
- 3. Компоненты и ответственность
- 4. Карта API (все маршруты)
- 5. Сущности и модели (Pydantic)
- 6. Потоки данных и цепочки взаимодействий
- 7. Асинхронность, очереди и фоновые задачи
- 8. Хранилища и интеграции
- 9. Конфигурация и переменные окружения
- 10. Наблюдаемость и безопасность
- 11. Известные оговорки и технический долг
- 12. Как запускать (локально / Docker)
- 13. Список идей для улучшений

—

1) Обзор и стек
- Назначение: многоагентная система для строительных проектов: нормы/регламенты (NTD), сметы/тендеры, генерация писем и документов, визуальный анализ, проектное управление.
- Архитектура: монорепозиторий, бэкенд на FastAPI + Celery, фронтенд React+TS (Vite), WebSocket для стриминга статусов, интеграции с Neo4j и Qdrant, локальные/внешние LLM (LM Studio), интеграция с Telegram ботом.
- Языки/инструменты: Python 3.10+, TypeScript/React 18, FastAPI, Celery/Redis, Neo4j, Qdrant, Prometheus, Sentry (опционально), LangChain, sentence-transformers, spaCy.

—

2) Структура каталогов (ключевое)
Корень (C:\\Bldr):
- core/ — основной бэкенд (FastAPI приложение, агенты, инструменты, тренеры, Celery и пр.)
- backend/ — модуль API «инструментов» (интегрирован как роутеры в core)
- web/bldr_dashboard/ — фронтенд (Vite + React + TS)
- system_launcher/ — GUI-лаунчер компонентов системы
- scripts/ — вспомогательные скрипты (тренинг и т.п.)
- tests и многочисленные test_*.py — e2e и интеграционные проверки
- Dockerfile, docker-compose.yml — контейнеризация
- README.md и сопроводительная документация

Примеры ключевых файлов:
- core/bldr_api.py — главное FastAPI-приложение (роутинг, CORS, аутентификация, WebSocket, интеграция API модулей)
- core/projects_api.py — CRUD проектов, файлы и результаты, шаблоны писем (через Neo4j)
- core/agents/coordinator_agent.py — координатор и сценарии многоагентного исполнения
- core/agents/specialist_agents.py — роль-агенты (через RolesAgentsManager)
- core/websocket_manager.py — менеджер WS-соединений
- core/celery_app.py, core/celery_norms.py — Celery приложение и задачи обновления NTD
- backend/api/tools_api.py — эндпоинты анализа файлов (сметы, изображения, документы, тендеры)
- backend/api/meta_tools_api.py — мета-инструменты, DAG и Celery-оркестрация
- web/bldr_dashboard/vite.config.ts — прокси на бэкенд (порт 3001 → 8000)

—

3) Компоненты и ответственность
- FastAPI (core/bldr_api.py):
  - Инициализация приложения, CORS, глобальные обработчики ошибок
  - JWT-аутентификация (HTTPBearer), переменная SKIP_AUTH для отладки
  - Подключение роутеров: /projects (core.projects_api), /api/tools (backend.api.tools_api), /api/meta-tools (backend.api.meta_tools_api)
  - WebSocket /ws для live-обновлений
  - Эндпоинты инструментов (/tools/*) — единая точка выполнения «мастер-системы инструментов» (через adapter)
  - Тренинг RAG (/train, /api/training/status), AI-задачи (/ai/*), процесс-менеджмент (/processes/*)
- Проекты (core/projects_api.py):
  - CRUD проектов в Neo4j
  - Загрузка/сканирование файлов проекта (категоризация: сметы/РД/графики)
  - Сохранение и выдача результатов инструментов для проекта
  - Управление шаблонами официальных писем
- Инструменты (backend/api/tools_api.py):
  - Анализ смет/изображений/документов/тендеров асинхронно (фоновые задания)
  - Учёт задач, статусы, скачивание результатов, очистка
  - Нотификации через общий WebSocket менеджер core.websocket_manager
- Мета-инструменты (backend/api/meta_tools_api.py):
  - Перечень и поиск мета-инструментов
  - Синхронное и асинхронное (Celery) выполнение
  - DAG-оркестрация workflow’ов, статус и статистика
- Многоагентная система (core/agents/*):
  - CoordinatorAgent: план → исполнение ролями → свёртка ответа; интеграция Meta-Tools
  - SpecialistAgentsManager/RolesAgentsManager: исполнение задач ролями (chief_engineer, analyst, project_manager и др.)
  - История диалога (сжатая/обычная) для контекста
- Celery (core/celery_app.py, core/celery_norms.py):
  - Планировщик beat для ежедневного обновления NTD
  - Задача update_norms_task: скачивание/обновление, запись в Neo4j, WS-нотификации
- Вебсокеты (core/websocket_manager.py):
  - Подключения, персональные сообщения, широковещание → используется инструментами, тренингом и Celery-task’ами
- Фронтенд (web/bldr_dashboard):
  - React+TS + Ant Design 5, Zustand, Router, Query
  - Прокси на backend (порт 3001), страницы: Projects, Queue, Settings, ProFeatures и др.
- System Launcher (system_launcher/*):
  - GUI на Tkinter для старта/остановки компонентов, мониторинга и диагностики

—

4) Карта API (все маршруты)
4.1 Core (bldr_api.py)
- Аутентификация и состояние:
  - POST /token — получить JWT (OAuth2PasswordRequestForm)
  - GET /auth/debug — отладка параметров аутентификации
  - GET /auth/validate — проверить токен
  - GET /health — состояние: db/celery/кол-во маршрутов
  - GET /metrics — Prometheus; GET /metrics-json — JSON-метрики для UI
- WebSocket:
  - WS /ws — live-уведомления (требует валидный origin и токен; SKIP_AUTH поддерживается)
- Процессы (process_tracker + retry_system):
  - GET /processes — фильтр по типу/статусу
  - GET /processes/{process_id}
  - POST /processes/{process_id}/cancel
  - GET /processes/types, GET /processes/statuses
- AI и тренинг:
  - POST /ai — запускает async обработку (через core.async_ai_processor), возвращает task_id
  - GET /ai/status/{task_id}, GET /ai/tasks — статус/список задач
  - POST /train — запуск тренинга (fast/normal) с WS-этапами; GET /api/training/status — прогресс
- Работа с БД/ботом/файлами:
  - POST /db — выполнить Cypher против Neo4j через trainer.neo4j
  - POST /bot — передать команду в Telegram боту
  - POST /files-scan — безопасный рекурсивный скан директории и копирование в norms_db
  - POST /upload-file — общий аплоад для тренинга RAG
  - POST /upload-for-training — аплоад именно для тренинга
  - POST /upload-for-analysis — аплоад для анализа смет
  - POST /upload-from-client — аплоад из каналов (Telegram/AI Shell)
- Единая витрина инструментов (через unified/master tools):
  - GET /tools, GET /tools/list — перечень инструментов (с категориями)
  - GET /tools/{tool_name}/info — метаданные инструмента
  - GET /tools/categories — список категорий
  - GET /tools/stats — статистика исполнения
  - POST /tools/chain — выполнение цепочки инструментов
  - POST /tools/{tool_name} — универсальный вызов с kwargs
  - Частные вспомогательные:
    - POST /tools/generate_letter
    - POST /tools/improve_letter
    - POST /tools/auto_budget
    - POST /tools/generate_ppr
    - POST /tools/create_gpp
    - POST /tools/parse_gesn_estimate
    - POST /tools/analyze_tender

Примечание: в core/bldr_api.py задвоены некоторые декларации маршрутов (/train, /ai, /ai/status, /ai/tasks) — стоит унифицировать (см. раздел 11).

4.2 Проекты (core/projects_api.py, префикс /projects)
- POST /projects — создать проект
- GET /projects — список проектов
- GET /projects/{project_id} — получить проект
- PUT /projects/{project_id} — обновить проект
- DELETE /projects/{project_id} — удалить проект и связанные файлы
- POST /projects/{project_id}/files — добавить файлы в проект
- GET /projects/{project_id}/files — список файлов проекта
- GET /projects/{project_id}/scan — агрегированная статистика по типам файлов
- DELETE /projects/{project_id}/files/{file_id} — удалить файл
- POST /projects/{project_id}/scan-directory — просканировать директорию и добавить релевантные файлы
- POST /projects/{project_id}/results — сохранить результат инструмента
- GET /projects/{project_id}/results — список результатов
- Шаблоны писем:
  - GET /projects/templates[?category]
  - POST /projects/templates
  - PUT /projects/templates/{template_id}
  - DELETE /projects/templates/{template_id}

4.3 Инструменты (backend/api/tools_api.py, префикс /api/tools)
- GET /api/tools/list — перечень анализаторов
- POST /api/tools/analyze/estimate — анализ смет (UploadFile[] + params)
- POST /api/tools/analyze/images — анализ изображений/чертежей
- POST /api/tools/analyze/documents — анализ документов
- POST /api/tools/analyze/tender — комплексный анализ тендерных документов
- GET /api/tools/jobs/{job_id}/status — статус задачи
- GET /api/tools/jobs/active — активные задачи
- POST /api/tools/jobs/{job_id}/cancel — отмена
- GET /api/tools/jobs/{job_id}/download — выгрузка результата
- DELETE /api/tools/jobs/cleanup — чистка завершённых
- GET /api/tools/info — краткая информация по инструментам
- GET /api/tools/health — здоровья подсистемы инструментов

4.4 Мета-инструменты (backend/api/meta_tools_api.py, префикс /api/meta-tools)
- GET /api/meta-tools/ — общая информация о системе
- GET /api/meta-tools/list[?category][?search] — список мета-инструментов
- GET /api/meta-tools/search?query=... — поиск по мета-инструментам
- GET /api/meta-tools/{tool_name} — информация о мета-инструменте
- POST /api/meta-tools/execute — синхронный запуск (для коротких задач)
- POST /api/meta-tools/execute/async — асинхронный запуск через Celery
- GET /api/meta-tools/tasks/active — активные Celery-задачи
- GET /api/meta-tools/tasks/{task_id}/status — статус задачи
- POST /api/meta-tools/tasks/{task_id}/cancel — отмена
- POST /api/meta-tools/tasks/cleanup — очистка завершённых
- GET /api/meta-tools/statistics — сводная статистика Meta-Tools и Celery
- Workflow (DAG):
  - POST /api/meta-tools/workflows — создать workflow (DAG)
  - POST /api/meta-tools/workflows/{workflow_id}/execute — запуск
  - GET /api/meta-tools/workflows/{workflow_id}/status — статус
- GET /api/meta-tools/health — здоровье мета-инструментов

—

5) Сущности и модели (Pydantic, выборочно)
- bldr_api:
  - User, Token, TokenData — аутентификация
  - AICall — запрос к /ai (prompt, model, image/voice/document base64)
  - TrainRequest — /train (custom_dir, fast_mode)
  - FileUploadResponse — ответ аплоадов
  - SubmitQueryRequest — /submit_query (query, source, project_id, user_id)
- projects_api:
  - ProjectCreate/Update/Response — проекты
  - FileResponse — файлы проекта
  - ScanResult — агрегаты по типам
  - ResultCreate/ProjectResult — результаты инструментов для проекта
  - TemplateCreate/Update/Response — шаблоны писем
- tools_api:
  - JobStatus, ToolExecutionResponse — задачи инструментов
- meta_tools_api:
  - MetaToolExecutionRequest, WorkflowCreateRequest, TaskStatusResponse, MetaToolInfo, MetaToolsListResponse, ExecutionResponse

—

6) Потоки данных и цепочки взаимодействий
- От фронтенда к бэкенду:
  - Auth: POST /token → JWT → все защищённые вызовы (при SKIP_AUTH=true допускается анонимная работа)
  - Live: WS /ws (токен в query или в заголовке Authorization Bearer) → мониторинг прогресса тренинга/задач
  - Tools: загрузка файлов → POST /api/tools/analyze/* → создаётся job → WS уведомления → GET статус → скачивание результата
  - Проекты: CRUD + добавление/сканирование файлов + сохранение/получение результатов
  - Мета-инструменты: синхронные/асинхронные запуски, DAG workflow, просмотр статуса/статистики
  - Тренинг RAG: POST /train (fast/normal) → WS этапы 1/14…14/14 → GET /api/training/status
  - AI Shell: POST /ai → отложенная обработка → GET /ai/status/{id}
- Многоагентный сценарий (/submit_query):
  - CoordinatorAgent.generate_plan(query) → SpecialistAgentsManager.execute_plan(plan, tools_system) → CoordinatorAgent.generate_response(query)
  - tools_system — адаптер «мастер-системы» инструментов: единая точка для вызова parse_gesn_estimate, generate_letter, и др.
- Celery update_norms_task:
  - Планировщик beat → core.celery_norms.update_norms_task → NormsUpdater.update_norms_daily → запись/обновление узлов в Neo4j → WS-уведомления

—

7) Асинхронность, очереди и фоновые задачи
- Celery (Redis брокер и backend):
  - core/celery_app.py — конфиг, beat_schedule (ежедневное обновление)
  - core/celery_norms.py — задача update_norms_task: логирование в Neo4j, WS-нотификации
- Async внутри FastAPI:
  - /ai — обработчик через core.async_ai_processor с хранением статуса задач
  - /train — фоновые задачи (BackgroundTasks) + WS-этапы
  - tools_api — BackgroundTasks для обработки файлов; статусы в памяти (active_jobs/completed_jobs)

—

8) Хранилища и интеграции
- Neo4j (bolt://localhost:7687):
  - Узлы Project, File, Result, NormDoc, Task, UpdateLog
  - Используется в projects_api и celery_norms
- Qdrant (локальный путь или контейнер): в тренировочном пайплайне
- Redis: брокер и backend для Celery; кеш/состояния
- LM Studio (http://localhost:1234/v1): генерация/помощь LLM через LangChain/ChatOpenAI
- Telegram Bot (integrations/telegram_bot.py): отправка команд и файлов
- Prometheus/Sentry: опционально (инструментация/трассировка)

—

9) Конфигурация и переменные окружения (основные)
- SKIP_AUTH=true — пропуск проверки токена (для отладки)
- SKIP_NEO4J=true — пропуск проверок Neo4j в /health
- FRONTEND_URL=http://localhost:3001 — CORS/Origin
- NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD — настройки Neo4j
- CELERY_BROKER_URL, CELERY_RESULT_BACKEND — настройки Celery/Redis
- LLM_BASE_URL (по умолчанию http://localhost:1234) — LM Studio
- BASE_DIR (по умолчанию I:/docs) — база документов/выгрузок
- SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES — JWT

—

10) Наблюдаемость и безопасность
- Наблюдаемость:
  - /metrics (Prometheus) и /metrics-json для фронтенда
  - Логи задач Celery, WS-поток стадий тренинга/задач
- Безопасность:
  - JWT (HTTPBearer), CORS со списком trusted origins (docs/README уточняет порты)
  - Ограничение размера загрузок (100MB), валидация расширений
  - Проверки путей/директорий (без traversal)
  - Переменная SKIP_AUTH — только для локальной отладки (в прод. выключить)

—

11) Известные оговорки и технический долг
- Дубли маршрутов в core/bldr_api.py: @app.post("/train") и endpoints /ai/* объявлены дважды — нужно оставить один набор (ревью и удаление дублей).
- Централизация инструментов: часть функционала есть в core/tools_* и backend/api/tools_api — следить за единообразием интерфейса и ответов.
- Статусы инструментов в памяти (tools_api) — рассмотреть перевод на Redis/БД для устойчивости к рестартам.
- Разделить dev и prod-конфигурации (CORS, SKIP_AUTH, BASE_DIR, порты фронта 3001 vs 3005, и т.д.).
- Стандартизовать схемы ответов для /tools/*, /api/tools/*, /api/meta-tools/* (status, error, data).
- Описать и закрепить контракт unified/master tools adapter (core.tools_adapter) и набор доступных инструментов.

—

12) Как запускать
- Нативно (Windows, рекомендовано для разработки):
  - Python зависимости: pip install -r requirements.txt
  - Frontend: cd web/bldr_dashboard && npm install && npm run dev (порт 3001)
  - Бэкенд: uvicorn core.bldr_api:app --reload --port 8000
  - (Опционально) Redis, Neo4j Desktop, Qdrant
- Docker Compose (для прод/изоляции): docker-compose up -d
  - Контейнеры: redis, neo4j, qdrant, backend, frontend

—

13) Идеи для улучшений (backlog)
- Убрать дубли роутов в core/bldr_api.py; покрыть тестом «маршруты не конфликтуют»
- Вынести схемы ответов в отдельные модели (единый формат: status/data/error/meta)
- Перевести учёт jobs из памяти (tools_api) в Redis + TTL/cleanup
- Консистентно вывести список доступных инструментов из unified/master tools в /tools и /api/tools/list
- Добавить RBAC-уровни ролей (admin/user) на маршруты (напр., /db)
- Подчистить пути BASE_DIR и вводимые пути (одинаково работать на Win/Linux)
- Документировать полный состав инструментов и мета-инструментов (автогенерация документации из кода)
- Единый health /status endpoint со сведением всех подсистем

—

Приложение: быстрые ссылки на ключевые файлы
- core/bldr_api.py — главное приложение FastAPI
- core/projects_api.py — управление проектами/шаблонами
- backend/api/tools_api.py — анализ файлов (REST, очереди)
- backend/api/meta_tools_api.py — мета-инструменты и DAG
- core/agents/coordinator_agent.py — координатор и многоагентная логика
- core/celery_app.py, core/celery_norms.py — Celery и обновление NTD
- core/websocket_manager.py — WebSocket менеджер
- web/bldr_dashboard/vite.config.ts — прокси на бэкенд

Если требуется расширить документ до уровня «каждая функция/метод во всех модулях», укажи — пройдёмся генератором по конкретным директориям и добавим автосводки по сигнатурам/докстрингам.
