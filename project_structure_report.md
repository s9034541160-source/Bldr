### Структура проекта и архитектура системы

- **Основные компоненты системы**:
  - **Бэкенд (FastAPI)**: `main.py` поднимает REST API сервиса "SuperBuilder Tools API" с CORS, WebSocket `/ws`, аутентификацией JWT, health/status эндпоинтами и корневой HTML-страницей документации.
  - **RAG-система**: используется через инструменты `search_rag_database` и модульные тренеры (`enterprise_rag_trainer_full.py`), интеграция с Neo4j, PDF/OCR, pandas и др. (опциональные зависимости определяются в `core/tools_system.py`).
  - **Multi‑Agent Coordinator**: `core/coordinator.py` — роль координатора, которая анализирует запрос, формирует JSON‑план, вызывает инструменты через `ToolsSystem`, координирует роли (analyst, chief_engineer, project_manager и др.) и синтезирует итоговый ответ.
  - **Система инструментов (Tools System)**: `core/tools_system.py` — реестр 40+ инструментов (генерация писем, авто‑смета, анализ BIM/PDF/изображений, визулизации, фин.метрики, RAG‑поиск и др.) с валидацией параметров, ретраями и стандартизацией результатов.
  - **GUI/Launcher**: `bldr_system_launcher.py` — лаунчер GUI на Tkinter для управления сервисами. Дополнительно присутствуют GUI‑скрипты в архиве (`ARCHIVE_AUTO_CLEANUP_20250922_155822/bldr_gui.py`) и действующий `bldr_gui_manager.py`.
  - **Фронтенд**: каталог `web/` (и/или `frontend/src/`) — клиентские компоненты на TypeScript/TSX/JSX.
  - **Telegram‑бот**: интеграция упоминается на уровне инструментов/отправки файлов из координатора; явный бот‑скрипт не в текущем списке ключевых файлов, но передача документов/уведомлений предусмотрена API инструментов.

- **Технологический стек**:
  - **Ядро**: Python 3, FastAPI, Uvicorn.
  - **Хранилище знаний/граф**: Neo4j (через `neo4j` драйвер; переменные окружения `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`).
  - **Векторное/поисковое хранилище**: Qdrant (упоминается в проектной документации/требованиях; RAG‑поиск реализован в инструментах).
  - **Фоновые задачи**: Celery (проверка статуса в `main.py` `/status`).
  - **Auth**: JWT, `python-jose`/`jwt`, HTTPBearer, bcrypt/sha256 fallback.
  - **Обработка документов**: PyPDF2, Tesseract OCR, OpenCV, PIL, pandas (по возможности, с graceful degrade).
  - **Веб‑сокеты**: Starlette WebSocket, менеджер соединений в `core.websocket_manager` (если доступен).

- **Точки входа**:
  - `main.py` — запуск FastAPI API (CLI: `--host`, `--port`, `--debug`), либо через `CANONICAL_FUNCTIONS.run_server`.
  - `bldr_system_launcher.py` — GUI лаунчер системы (Tkinter) для старта/мониторинга сервисов.
  - `bldr_gui_manager.py` — отдельный GUI‑менеджер (альтернативный интерфейс управления).

- **Архитектура (Multi‑Agent System)**:
  - **Coordinator** (`core/coordinator.py`):
    - Анализирует запрос (в т.ч. с применением SBERT‑парсинга при наличии), формирует строгий JSON‑план: инструменты, аргументы, роли, данные, шаги.
    - Делегирует выполнение в **Tools System** и координирует роли (coordinator, analyst, chief_engineer, project_manager, construction_worker) через **Model Manager**.
    - Синтезирует финальный ответ на основе результатов инструментов и ответов ролей, очищает ответ от тех.деталей.
  - **Tools System** (`core/tools_system.py`):
    - Реестр инструментов с типами, категориями и обязательными параметрами; унифицированное выполнение с ретраями, валидацией, стандартизацией и метаданными.
    - Инструменты включают: `search_rag_database`, `auto_budget`, `parse_gesn_estimate`, `generate_ppr`, `create_gpp`, `analyze_bentley_model`, `autocad_export`, `monte_carlo_sim`, визуализации и др.
  - **Model Manager** (`core/model_manager.py`, используется в координаторе):
    - Предоставляет клиентов моделей для ролей ("coordinator", "analyst", и т.д.) и промпты возможностей.
  - **RAG слой**: поиск по базе знаний, семантический парсинг, интеграция с Neo4j/Qdrant; опциональная тренировка через `enterprise_rag_trainer_full.py`.

- **Web/API слой**:
  - FastAPI приложение с CORS, статикой, авторизацией (`/token`, `/auth/*`), WebSocket `/ws` (валидация JWT через query‑token или `SKIP_AUTH=true`), корневой HTML, `health`/`status`/`debug`‑эндпоинты.

- **Переменные окружения (.env)**:
  - Используются через `dotenv.load_dotenv()` (в `main.py`). Ключевые: `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `SKIP_AUTH`, `DEV_MODE`, `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`, `INIT_TRAINER_ON_START`, `BASE_DIR`.
  - Файл `.env` отсутствует в текущем рабочем снимке, значения берутся из окружения или дефолтов.

- **Текущий статус проекта**:
  - Активный **рефакторинг** ядра и инструментов, унификация и консолидация функциональности (см. `core/tools_system.py`).
  - Идет **удаление дубликатов** и авто‑очистка (наличие `ARCHIVE_AUTO_CLEANUP_*`, `ARCHIVE_DEAD_CODE_*`, отчетов `DUPLICATE_*`).
  - Структура стабилизируется: основной бэкенд — `main.py`; много исторических GUI файлов перенесено в архив; запуск и управление — через `bldr_system_launcher.py`/`bldr_gui_manager.py`.

- **Связанные каталоги**:
  - `backend/`, `core/`, `CANONICAL_FUNCTIONS/`, `web/` (TS/TSX), `data/` (хранилища), `integrations/`, `plugins/`, `templates/`, `docs/`.
