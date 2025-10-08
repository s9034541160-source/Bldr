# Bldr Empire v2 - Подробное описание проекта

**Дата создания:** 05.10.2025  
**Версия:** 2.0.0  
**Статус:** Production Ready

## 🎯 Обзор проекта

**Bldr Empire v2** — это комплексная многоагентная система для управления строительными проектами, объединяющая обработку нормативной документации, сметное дело, проектное управление и автоматизацию строительных процессов.

### Основные цели:
- Автоматизация извлечения и структурирования строительных знаний
- Повышение эффективности и снижение ошибок в строительных проектах
- Интеграция нормативной документации (СП, ГОСТ, СНиП, ГЭСН)
- Управление проектами производства работ (ППР, технологические карты)
- Сметное дело и финансовое планирование
- Рабочая документация (чертежи, спецификации)

## 🏗️ Архитектура системы

### 1. Основные компоненты

#### **Ядро системы (Core Architecture)**
```
SuperBuilder
├── ModelManager (управление моделями ИИ)
├── RAGSystem (специализированная RAG-система)
├── ToolsSystem (система инструментов)
└── Coordinator (центральный интеллект системы)
```

#### **Многоуровневая обработка документов**
1. **Уровень 1**: Извлечение и классификация
2. **Уровень 2**: Симбиотическая обработка (Regex + RuBERT)
3. **Уровень 3**: Генерация рабочих последовательностей
4. **Уровень 4**: Векторное представление

### 2. Технологический стек

#### **Backend**
- **FastAPI** - основной веб-фреймворк
- **Python 3.10+** - основной язык программирования
- **Celery + Redis** - асинхронные задачи и очереди
- **Neo4j** - графовая база данных для связей
- **Qdrant** - векторная база данных для эмбеддингов
- **WebSocket** - реальное время коммуникации

#### **Frontend**
- **React 18 + TypeScript** - пользовательский интерфейс
- **Vite** - сборщик и dev-сервер
- **Ant Design** - UI компоненты
- **Zustand** - управление состоянием
- **React Query** - кэширование данных

#### **AI/ML Stack**
- **LangChain** - фреймворк для LLM приложений
- **Sentence Transformers** - эмбеддинги
- **PyTorch** - машинное обучение
- **Transformers** - предобученные модели
- **spaCy** - обработка естественного языка

#### **Инфраструктура**
- **Docker + Docker Compose** - контейнеризация
- **Prometheus** - мониторинг
- **Sentry** - отслеживание ошибок
- **NGINX** - обратный прокси

## 📁 Структура проекта

### Корневая структура
```
C:\Bldr\
├── main.py                          # Точка входа FastAPI приложения
├── requirements.txt                  # Python зависимости
├── docker-compose.yml               # Docker конфигурация
├── pyproject.toml                    # Конфигурация проекта
├── core/                           # Основной backend модуль
├── backend/                        # API модули
├── web/bldr_dashboard/             # Frontend приложение
├── tools/                          # Специализированные инструменты
├── integrations/                   # Внешние интеграции
├── data/                          # Данные и кэш
├── logs/                          # Логи системы
└── docs/                          # Документация
```

### Детальная структура модулей

#### **Core модуль** (`core/`)
```
core/
├── agents/                        # Многоагентная система
│   ├── coordinator_agent.py       # Координатор
│   ├── specialist_agents.py       # Специализированные агенты
│   └── agent_manager.py           # Менеджер агентов
├── config.py                      # Конфигурация системы
├── unified_tools_system.py       # Унифицированная система инструментов
├── model_manager.py               # Управление LLM моделями
├── websocket_manager.py          # WebSocket менеджер
├── celery_app.py                 # Celery конфигурация
├── memory/                       # Система памяти
├── meta_tools/                   # Мета-инструменты
├── security/                     # Безопасность
└── tracing/                      # Трассировка выполнения
```

#### **Backend API** (`backend/`)
```
backend/
├── api/                          # REST API эндпоинты
│   ├── tools_api.py              # API инструментов
│   ├── meta_tools_api.py         # API мета-инструментов
│   ├── models_api.py             # API моделей
│   └── websocket_server.py       # WebSocket сервер
├── core/                         # Backend core
└── data/                        # Backend данные
```

#### **Frontend** (`web/bldr_dashboard/`)
```
web/bldr_dashboard/
├── src/
│   ├── components/               # React компоненты
│   │   ├── AIShell.tsx          # AI интерфейс
│   │   ├── RAGModule.tsx        # RAG модуль
│   │   ├── Projects.tsx         # Управление проектами
│   │   └── Tools/               # Инструменты
│   ├── services/                # API сервисы
│   ├── contexts/                # React контексты
│   ├── hooks/                   # Custom hooks
│   └── store/                   # Zustand store
├── package.json                 # Node.js зависимости
└── vite.config.ts              # Vite конфигурация
```

#### **Tools система** (`tools/`)
```
tools/
├── ai/                          # AI инструменты
├── analysis/                    # Аналитические инструменты
├── bim/                         # BIM инструменты
├── custom/                      # Пользовательские инструменты
├── document_generation/         # Генерация документов
├── document_processing/         # Обработка документов
├── financial/                   # Финансовые инструменты
├── project_management/          # Управление проектами
└── visual/                     # Визуализация
```

## 🤖 Многоагентная система

### Роли и специализации

#### **1. Coordinator (Координатор)**
- **Модель**: Qwen3-Coder-30B
- **Роль**: Главный координатор системы
- **Функции**:
  - Анализ запросов и планирование
  - Делегирование задач специалистам
  - Синтез финальных ответов
  - Координация между ролями

#### **2. Chief Engineer (Главный инженер)**
- **Модель**: Qwen2.5-VL-7B
- **Роль**: Технические решения и анализ
- **Функции**:
  - Анализ соответствия СП, СНиП, ГОСТ
  - Интерпретация чертежей и схем
  - Предложение технических решений
  - Выявление нарушений

#### **3. Structural Engineer (Инженер-конструктор)**
- **Модель**: Mistral-Nemo-Instruct-2407
- **Роль**: Конструктивные расчеты
- **Функции**:
  - Расчеты конструкций (бетон/сталь/дерево)
  - Геотехнический анализ
  - FEM моделирование
  - Соответствие СП/СНиП

#### **4. Project Manager (Менеджер проекта)**
- **Модель**: DeepSeek-R1-0528-Qwen3-8B
- **Роль**: Управление проектами
- **Функции**:
  - Составление графиков работ
  - Управление ресурсами и сроками
  - Координация подрядчиков
  - Соответствие ФЗ-44/223

#### **5. Safety Engineer (Инженер по ОТ)**
- **Модель**: Qwen2.5-VL-7B
- **Роль**: Безопасность на стройплощадке
- **Функции**:
  - Анализ рисков и нарушений
  - Генерация инструктажей
  - Проверка соответствия СП 48 и СанПиН

#### **6. QC Engineer (Инженер по качеству)**
- **Модель**: Mistral-Nemo-Instruct-2407
- **Роль**: Контроль качества
- **Функции**:
  - Проверки соответствия работ проекту
  - Генерация актов и отчетов
  - Выявление дефектов

#### **7. Analyst (Аналитик)**
- **Модель**: Qwen2.5-VL-7B
- **Роль**: Финансовый анализ
- **Функции**:
  - Расчет стоимости по ГЭСН/ФЕР
  - Анализ финансовой эффективности
  - Подготовка данных для тендеров

#### **8. Tech Coder (Технический программист)**
- **Модель**: Qwen3-Coder-30B
- **Роль**: BIM и автоматизация
- **Функции**:
  - BIM скрипты и кодогенерация
  - Автоматизация процессов
  - Обработка данных

## 🧠 RAG система (Retrieval-Augmented Generation)

### Enterprise RAG Trainer

**14-этапный симбиотический пайплайн:**

#### **Этап 0**: Smart File Scanning + NTD Preprocessing
- Умное сканирование файлов
- Предобработка нормативной документации

#### **Этап 1-3**: Валидация и извлечение
- **Этап 1**: Initial Validation (проверка файла, размера, доступности)
- **Этап 2**: Duplicate Checking (MD5/SHA256, Qdrant, processed_files.json)
- **Этап 3**: Text Extraction (PDF PyPDF2+OCR, DOCX, Excel)

#### **Этап 4-8**: Анализ и обработка
- **Этап 4**: Document Type Detection (симбиотический: regex + SBERT)
- **Этап 5**: Structural Analysis (полная рекурсивная структура)
- **Этап 6**: Regex to SBERT (seed works extraction)
- **Этап 7**: SBERT Markup (полная структура + граф)
- **Этап 8**: Metadata Extraction (только из структуры)

#### **Этап 9-14**: Контроль качества и сохранение
- **Этап 9**: Quality Control
- **Этап 10**: Type-specific Processing
- **Этап 11**: Work Sequence Extraction
- **Этап 12**: Save Work Sequences (Neo4j)
- **Этап 13**: Smart Chunking (1 пункт = 1 чанк)
- **Этап 14**: Save to Qdrant

### Типы документов
1. **norms** - Нормативная документация (СП, ГОСТ, СНиП)
2. **technical** - Техническая документация
3. **financial** - Финансовая документация (ГЭСН, ФЕР)
4. **project** - Проектная документация
5. **bim** - BIM модели и данные
6. **educational** - Учебные материалы

## 🛠️ Система инструментов

### Унифицированная система инструментов (47+ инструментов)

#### **Категории инструментов:**

1. **Поиск и анализ**
   - `search_rag_database` - Поиск в базе знаний
   - `semantic_parse` - Семантический парсинг
   - `vl_analyze_photo` - Анализ изображений

2. **Документооборот**
   - `gen_docx` - Генерация документов
   - `gen_excel` - Генерация Excel файлов
   - `gen_pdf` - Генерация PDF

3. **Финансовые расчеты**
   - `calc_estimate` - Расчет смет
   - `auto_budget` - Автоматическое бюджетирование
   - `monte_carlo_sim` - Монте-Карло симуляция

4. **Проектное управление**
   - `gen_gantt` - Диаграммы Ганта
   - `gen_project_plan` - Планы проектов
   - `create_gpp` - Создание ГПП

5. **BIM и визуализация**
   - `bim_code_gen` - Генерация BIM кода
   - `analyze_bentley_model` - Анализ Bentley моделей
   - `create_pie_chart` - Создание диаграмм

6. **Безопасность и качество**
   - `gen_safety_report` - Отчеты по безопасности
   - `gen_qc_report` - Отчеты по качеству
   - `gen_checklist` - Чек-листы

### Мета-инструменты
- **DAG Orchestrator** - Оркестрация сложных процессов
- **Celery Integration** - Асинхронное выполнение
- **Workflow Management** - Управление рабочими процессами

## 🎨 Frontend архитектура

### React Dashboard
- **Технологии**: React 18, TypeScript, Vite, Ant Design
- **Состояние**: Zustand для глобального состояния
- **API**: React Query для кэширования
- **WebSocket**: Socket.io для реального времени

### Основные компоненты

#### **1. AIShell** - AI интерфейс
- Чат с многоагентной системой
- Загрузка файлов и изображений
- История диалогов

#### **2. RAGModule** - RAG управление
- **Train Tab**: Управление обучением RAG
- **Query Tab**: Семантический поиск
- **Dashboard Tab**: Визуализация метрик

#### **3. Projects** - Управление проектами
- CRUD операции с проектами
- Файлы и результаты
- Шаблоны писем

#### **4. Tools** - Инструменты
- Унифицированная панель инструментов
- Категоризация по типам
- Выполнение и мониторинг

#### **5. Analytics** - Аналитика
- Метрики системы
- Производительность
- Использование ресурсов

## 🔧 Конфигурация и развертывание

### Переменные окружения

#### **Основные настройки**
```env
# База данных
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
QDRANT_URL=http://localhost:6333

# LLM настройки
LLM_BASE_URL=http://localhost:1234/v1
LLM_MODEL=qwen/qwen3-coder-30b

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Безопасность
JWT_SECRET_KEY=your-secret-key
SKIP_AUTH=false
```

#### **LLM конфигурации**
- `workhorse_llm_config.env` - Рабочий ансамбль
- `russian_llm_config.env` - Российские модели
- `optimized_llm_config.env` - Оптимизированная конфигурация

### Docker развертывание

#### **docker-compose.yml**
```yaml
services:
  redis:          # Redis для Celery
  neo4j:          # Графовая БД
  qdrant:         # Векторная БД
  backend:        # FastAPI приложение
  frontend:       # React приложение
```

### Локальное развертывание

#### **Backend**
```bash
# Установка зависимостей
pip install -r requirements.txt

# Запуск сервера
python main.py
```

#### **Frontend**
```bash
cd web/bldr_dashboard
npm install
npm run dev
```

#### **Celery Worker**
```bash
celery -A core.celery_app worker --loglevel=info
```

## 📊 Мониторинг и логирование

### Структурированное логирование
- **Уровни**: DEBUG, INFO, WARNING, ERROR
- **Форматы**: JSON для машинной обработки
- **Ротация**: Автоматическая ротация логов
- **Трассировка**: Полная трассировка выполнения

### Метрики
- **Prometheus** - сбор метрик
- **Grafana** - визуализация
- **Sentry** - отслеживание ошибок

### Health Checks
- `/health` - Статус системы
- `/status` - Детальный статус
- `/debug` - Отладочная информация

## 🔐 Безопасность

### Аутентификация и авторизация
- **JWT токены** - для API доступа
- **OAuth2** - для веб-интерфейса
- **Роли и права** - гранулярный контроль доступа

### Безопасность данных
- **Шифрование** - чувствительных данных
- **Валидация** - всех входных данных
- **Санитизация** - пользовательского ввода

### Сетевая безопасность
- **CORS** - настройка для фронтенда
- **Rate Limiting** - защита от DDoS
- **HTTPS** - в продакшене

## 🚀 Производительность

### Оптимизации
- **Кэширование** - Redis для быстрого доступа
- **Асинхронность** - Celery для фоновых задач
- **Пулы соединений** - для БД
- **CDN** - для статических файлов

### Масштабирование
- **Горизонтальное** - множественные инстансы
- **Вертикальное** - увеличение ресурсов
- **Балансировка** - нагрузки

## 📈 Развитие и планы

### Текущие возможности
- ✅ Многоагентная система
- ✅ RAG обучение и поиск
- ✅ 47+ специализированных инструментов
- ✅ WebSocket реального времени
- ✅ Docker контейнеризация
- ✅ Мониторинг и логирование

### Планы развития
- 🔄 Интеграция с внешними API
- 🔄 Расширение BIM функциональности
- 🔄 Мобильное приложение
- 🔄 Машинное обучение для оптимизации
- 🔄 Интеграция с IoT устройствами

## 📚 Документация

### Техническая документация
- `docs/ARCHITECTURE.md` - Архитектура системы
- `docs/API.md` - API документация
- `RAG_API_DOCUMENTATION.md` - RAG API
- `TOOL_RESULT_STANDARDS.md` - Стандарты инструментов

### Руководства пользователя
- `README_minstroy_parser.md` - Парсер Минстроя
- `README_VLM.md` - Vision Language Models
- `CURSOR-INTEGRATION-GUIDE.md` - Интеграция с Cursor

## 🤝 Поддержка и сообщество

### Контакты
- **Issues**: GitHub Issues для багов и предложений
- **Documentation**: Подробная документация в `/docs`
- **Logs**: Детальные логи в `/logs`

### Участие в разработке
- **Code Style**: Black + isort
- **Testing**: pytest для тестов
- **Linting**: pylint для проверки кода
- **Type Hints**: Полная типизация

## 🔄 Диаграммы взаимодействия компонентов

### Общая архитектурная схема
```
┌─────────────────────────────────────────────────────────────────┐
│                    Bldr Empire v2 System                       │
│                     Многоагентная архитектура                  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │   Core System   │
│   (React)       │◄──►│   (FastAPI)     │◄──►│   (Agents)      │
│                 │    │                 │    │                 │
│ • AIShell       │    │ • REST API      │    │ • Coordinator   │
│ • RAGModule     │    │ • WebSocket     │    │ • Specialists   │
│ • Projects      │    │ • Auth          │    │ • Tools System  │
│ • Analytics     │    │ • File Upload   │    │ • RAG System     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   WebSocket     │    │   Celery        │    │   Databases     │
│   Manager       │    │   (Background)   │    │                 │
│                 │    │                 │    │ • Neo4j (Graph) │
│ • Real-time     │    │ • RAG Training  │    │ • Qdrant (Vec) │
│ • Notifications │    │ • File Process  │    │ • Redis (Cache) │
│ • Status Updates│    │ • AI Inference  │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Взаимодействие агентов
```
┌─────────────────────────────────────────────────────────────────┐
│                    Agent Coordination Flow                       │
└─────────────────────────────────────────────────────────────────┘

User Request
     │
     ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Coordinator │───►│ Tool System │───►│ Specialists │
│   Agent     │    │             │    │             │
│             │    │ • 47+ Tools │    │ • Chief Eng │
│ • Analysis  │    │ • Validation│    │ • Analyst   │
│ • Planning  │    │ • Execution │    │ • Manager   │
│ • Delegation│    │ • Results   │    │ • Safety    │
└─────────────┘    └─────────────┘    └─────────────┘
     │                       │                       │
     │                       │                       │
     ▼                       ▼                       ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ RAG System  │    │ File System │    │ Databases   │
│             │    │             │    │             │
│ • Search    │    │ • Upload    │    │ • Neo4j    │
│ • Training  │    │ • Process   │    │ • Qdrant    │
│ • Vectorize │    │ • Store     │    │ • Redis    │
└─────────────┘    └─────────────┘    └─────────────┘
```

## 📊 Схемы потоков данных и процессов

### RAG Training Pipeline
```
┌─────────────────────────────────────────────────────────────────┐
│                    RAG Training Pipeline                        │
│                    14-этапный процесс                           │
└─────────────────────────────────────────────────────────────────┘

Input Files
     │
     ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Stage 0-3   │───►│ Stage 4-8   │───►│ Stage 9-14 │
│             │    │             │    │             │
│ • Scanning  │    │ • Analysis │    │ • Quality   │
│ • Validation│    │ • Structure │    │ • Chunking  │
│ • Extraction│    │ • Metadata  │    │ • Vectorize │
└─────────────┘    └─────────────┘    └─────────────┘
     │                       │                       │
     │                       │                       │
     ▼                       ▼                       ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ File System │    │ LLM Models  │    │ Databases   │
│             │    │             │    │             │
│ • PDF/DOCX  │    │ • RuBERT    │    │ • Neo4j     │
│ • Images    │    │ • SBERT     │    │ • Qdrant    │
│ • Archives  │    │ • RuT5      │    │ • Redis     │
└─────────────┘    └─────────────┘    └─────────────┘
```

### User Request Processing Flow
```
┌─────────────────────────────────────────────────────────────────┐
│                    User Request Processing                       │
└─────────────────────────────────────────────────────────────────┘

User Input
     │
     ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Frontend    │───►│ Backend API │───►│ Coordinator │
│             │    │             │    │             │
│ • Chat UI   │    │ • Auth      │    │ • Analysis  │
│ • File Up   │    │ • Validation│    │ • Planning  │
│ • Commands  │    │ • Routing   │    │ • Delegation│
└─────────────┘    └─────────────┘    └─────────────┘
     │                       │                       │
     │                       │                       │
     ▼                       ▼                       ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ WebSocket   │    │ Celery      │    │ Tools       │
│             │    │             │    │             │
│ • Real-time │    │ • Background│    │ • Execution │
│ • Status    │    │ • Training  │    │ • Results   │
│ • Progress  │    │ • Processing│    │ • Synthesis │
└─────────────┘    └─────────────┘    └─────────────┘
```

## 🔌 Интерфейсы API и протоколы взаимодействия

### REST API Endpoints

#### **Authentication & Authorization**
```http
POST /token                    # Получение JWT токена
POST /auth/login              # Вход в систему
POST /auth/register           # Регистрация
GET  /auth/me                 # Информация о пользователе
```

#### **Core System API**
```http
POST /chat                    # AI чат с координатором
POST /ws                      # WebSocket соединение
GET  /health                  # Статус системы
GET  /status                  # Детальный статус
GET  /debug                   # Отладочная информация
```

#### **RAG System API**
```http
POST /train                   # Запуск обучения RAG
POST /api/analyze-file         # Анализ файла
GET  /api/search              # Поиск в базе знаний
POST /api/query               # Семантический поиск
GET  /api/status              # Статус RAG системы
```

#### **Tools API**
```http
GET  /api/tools               # Список инструментов
POST /api/tools/execute       # Выполнение инструмента
GET  /api/tools/{tool_id}     # Информация об инструменте
POST /api/tools/upload        # Загрузка файлов
```

#### **Projects API**
```http
GET    /api/projects          # Список проектов
POST   /api/projects          # Создание проекта
GET    /api/projects/{id}     # Получение проекта
PUT    /api/projects/{id}     # Обновление проекта
DELETE /api/projects/{id}     # Удаление проекта
```

#### **Meta-Tools API**
```http
GET  /api/meta-tools          # Мета-инструменты
POST /api/meta-tools/execute  # Выполнение мета-инструмента
GET  /api/workflows           # Рабочие процессы
POST /api/workflows/create    # Создание процесса
```

### WebSocket Protocol

#### **Connection**
```javascript
// Подключение к WebSocket
const ws = new WebSocket('ws://localhost:8000/ws?token=jwt_token');

// Обработка сообщений
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    // Обработка данных
};
```

#### **Message Types**
```json
{
  "type": "status_update",
  "data": {
    "task_id": "uuid",
    "status": "processing",
    "progress": 45,
    "message": "Processing file..."
  }
}

{
  "type": "tool_result",
  "data": {
    "tool_name": "search_rag_database",
    "result": {...},
    "execution_time": 1.23
  }
}

{
  "type": "error",
  "data": {
    "error": "Tool execution failed",
    "details": "..."
  }
}
```

### API Request/Response Formats

#### **Chat Request**
```json
{
  "message": "Проанализируй смету",
  "image_data": "base64_encoded_image",
  "voice_data": "base64_encoded_audio",
  "document_data": "base64_encoded_document",
  "document_name": "estimate.xlsx",
  "agent_role": "coordinator",
  "request_context": {
    "project_id": "uuid",
    "user_id": "uuid"
  }
}
```

#### **Tool Execution Request**
```json
{
  "tool_name": "search_rag_database",
  "parameters": {
    "query": "СП 48.13330.2023",
    "n_results": 5,
    "min_relevance": 0.7,
    "doc_types": ["norms"]
  },
  "priority": 5,
  "async_execution": false
}
```

## 🗄️ Диаграммы баз данных

### Neo4j Graph Database Schema
```
┌─────────────────────────────────────────────────────────────────┐
│                    Neo4j Graph Schema                           │
└─────────────────────────────────────────────────────────────────┘

┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Project   │───►│   Document  │───►│   Section   │
│             │    │             │    │             │
│ • id        │    │ • id        │    │ • id        │
│ • name      │    │ • title     │    │ • title     │
│ • status    │    │ • type      │    │ • content   │
│ • created   │    │ • path      │    │ • order     │
└─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │
       │                   │                   │
       ▼                   ▼                   ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   User      │    │   Work      │    │   Metadata  │
│             │    │  Sequence   │    │             │
│ • id        │    │             │    │ • key       │
│ • username  │    │ • id        │    │ • value     │
│ • email     │    │ • steps     │    │ • type      │
│ • role      │    │ • order     │    │ • source    │
└─────────────┘    └─────────────┘    └─────────────┘

Relationships:
- Project ─[HAS]─> Document
- Document ─[CONTAINS]─> Section
- User ─[OWNS]─> Project
- Document ─[GENERATES]─> WorkSequence
- Section ─[HAS]─> Metadata
```

### Qdrant Vector Database Schema
```
┌─────────────────────────────────────────────────────────────────┐
│                    Qdrant Vector Schema                         │
└─────────────────────────────────────────────────────────────────┘

Collection: "documents"
├── Vector: 768-dimensional embeddings (sentence-transformers)
├── Payload:
│   ├── document_id: string
│   ├── section_id: string
│   ├── content: string
│   ├── doc_type: string (norms|technical|financial|project|bim|educational)
│   ├── doc_subtype: string
│   ├── title: string
│   ├── source: string
│   ├── created_at: timestamp
│   └── metadata: object
│
Collection: "work_sequences"
├── Vector: 768-dimensional embeddings
├── Payload:
│   ├── sequence_id: string
│   ├── project_id: string
│   ├── steps: array
│   ├── dependencies: array
│   ├── estimated_time: number
│   └── requirements: object
│
Collection: "knowledge_base"
├── Vector: 768-dimensional embeddings
├── Payload:
│   ├── kb_id: string
│   ├── category: string
│   ├── subcategory: string
│   ├── content: string
│   ├── source_document: string
│   └── confidence: float
```

### Redis Cache Schema
```
┌─────────────────────────────────────────────────────────────────┐
│                    Redis Cache Schema                           │
└─────────────────────────────────────────────────────────────────┘

Keys Structure:
├── user:{user_id}:session          # Пользовательские сессии
├── project:{project_id}:data       # Данные проектов
├── tool:{tool_name}:cache          # Кэш инструментов
├── rag:training:status             # Статус обучения RAG
├── celery:task:{task_id}           # Статус Celery задач
├── websocket:{connection_id}       # WebSocket соединения
└── api:rate_limit:{ip}             # Rate limiting

Data Types:
├── String: Простые значения
├── Hash: Объекты с полями
├── List: Очереди и списки
├── Set: Уникальные значения
└── ZSet: Отсортированные множества
```

## 🤝 Механизмы координации между агентами

### Agent Communication Protocol
```
┌─────────────────────────────────────────────────────────────────┐
│                    Agent Coordination System                     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Coordinator │◄──►│ Tool System │◄──►│ Specialists │
│             │    │             │    │             │
│ • Planning  │    │ • Registry  │    │ • Chief Eng │
│ • Delegation│    │ • Execution │    │ • Analyst   │
│ • Synthesis │    │ • Validation│    │ • Manager   │
│ • Results   │    │ • Monitoring│    │ • Safety    │
└─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │
       │                   │                   │
       ▼                   ▼                   ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Message Bus │    │ Task Queue │    │ Result Pool │
│             │    │             │    │             │
│ • Routing   │    │ • Priority  │    │ • Storage   │
│ • Filtering │    │ • Scheduling│    │ • Retrieval │
│ • Broadcasting│    │ • Retry     │    │ • Cleanup   │
└─────────────┘    └─────────────┘    └─────────────┘
```

### Coordination Flow
```
┌─────────────────────────────────────────────────────────────────┐
│                    Agent Coordination Flow                       │
└─────────────────────────────────────────────────────────────────┘

1. Request Analysis
   │
   ▼
┌─────────────┐
│ Coordinator │
│ • Intent    │
│ • Context   │
│ • Planning  │
└─────────────┘
   │
   ▼
┌─────────────┐
│ Tool System │
│ • Selection │
│ • Validation│
│ • Execution │
└─────────────┘
   │
   ▼
┌─────────────┐
│ Specialists │
│ • Delegation│
│ • Processing│
│ • Results   │
└─────────────┘
   │
   ▼
┌─────────────┐
│ Synthesis   │
│ • Aggregation│
│ • Validation│
│ • Response  │
└─────────────┘
```

### Message Types and Protocols

#### **Internal Agent Messages**
```json
{
  "message_type": "delegation",
  "from_agent": "coordinator",
  "to_agent": "chief_engineer",
  "task": {
    "tool_name": "vl_analyze_photo",
    "parameters": {
      "image_path": "site_photo.jpg",
      "query": "Safety violations"
    },
    "priority": "high",
    "timeout": 300
  },
  "context": {
    "project_id": "uuid",
    "user_id": "uuid",
    "session_id": "uuid"
  }
}
```

#### **Tool Execution Messages**
```json
{
  "message_type": "tool_execution",
  "tool_name": "search_rag_database",
  "parameters": {
    "query": "СП 48.13330.2023",
    "doc_types": ["norms"],
    "n_results": 5
  },
  "execution_id": "uuid",
  "timestamp": "2025-01-05T10:30:00Z",
  "status": "running"
}
```

#### **Result Aggregation**
```json
{
  "message_type": "result_aggregation",
  "execution_id": "uuid",
  "results": [
    {
      "agent": "chief_engineer",
      "tool": "vl_analyze_photo",
      "result": {...},
      "confidence": 0.95
    },
    {
      "agent": "analyst",
      "tool": "calc_estimate",
      "result": {...},
      "confidence": 0.88
    }
  ],
  "synthesis": {
    "final_result": {...},
    "confidence": 0.91,
    "sources": [...]
  }
}
```

### Error Handling and Recovery
```
┌─────────────────────────────────────────────────────────────────┐
│                    Error Handling Flow                          │
└─────────────────────────────────────────────────────────────────┘

Error Detection
     │
     ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Error       │───►│ Retry       │───►│ Fallback    │
│ Classification│    │ Mechanism   │    │ Strategy    │
│             │    │             │    │             │
│ • Tool      │    │ • Exponential│    │ • Alternative│
│ • Network   │    │ • Backoff    │    │ • Tool      │
│ • Agent     │    │ • Max 3x     │    │ • Agent     │
│ • System    │    │             │    │ • Response  │
└─────────────┘    └─────────────┘    └─────────────┘
```

### Performance Monitoring
```
┌─────────────────────────────────────────────────────────────────┐
│                    Performance Monitoring                       │
└─────────────────────────────────────────────────────────────────┘

┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Metrics     │───►│ Analytics   │───►│ Optimization│
│ Collection  │    │ Dashboard   │    │ Suggestions │
│             │    │             │    │             │
│ • Response  │    │ • Real-time │    │ • Load      │
│ • Time      │    │ • Historical│    │ • Balancing  │
│ • Success   │    │ • Trends    │    │ • Caching   │
│ • Error     │    │ • Alerts    │    │ • Scaling   │
└─────────────┘    └─────────────┘    └─────────────┘
```

---

**Bldr Empire v2** - это комплексное решение для автоматизации строительных процессов, объединяющее современные технологии ИИ, многоагентные системы и специализированные инструменты для максимальной эффективности в строительной отрасли.
