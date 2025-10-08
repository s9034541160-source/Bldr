# Диаграмма E2E процесса системы BLDR

## 🔄 Полный End-to-End флоу системы

### 1️⃣ Telegram Bot E2E процесс

```
[Пользователь в Telegram] 
          ↓ (сообщение/команда)
[Telegram Bot Handler] 
          ↓ (parse message)
[telegram_bot.py::handle_text/query_command]
          ↓ (HTTP POST /query)
[FastAPI::bldr_api.py::query_endpoint]
          ↓ (asyncio.to_thread)
[BldrRAGTrainer::query()]
          ↓ (vector search + metadata)
[FAISS Index + Qdrant/Memory]
          ↓ (results with scores)
[Enhanced Results Processing]
          ↓ (JSON response)
[Telegram Bot] 
          ↓ (format + send message)
[Пользователь получает ответ]
```

### 2️⃣ AI Shell Frontend E2E процесс

```
[React Frontend - AI Shell]
          ↓ (user input + role selection)
[AIShell.tsx::sendToAI()]
          ↓ (coordinator role?)
[Branch A: Coordinator]     [Branch B: Direct AI]
          ↓                           ↓
[apiService.submitQuery()]   [apiService.callAI()]
          ↓                           ↓ 
[POST /submit_query]         [POST /ai]
          ↓                           ↓
[CoordinatorAgent]           [run_ai_with_updates()]
          ↓                           ↓
[LangChain + Plan Gen]       [LM Studio API call]
          ↓                           ↓
[Tools Execution]            [WebSocket updates]
          ↓                           ↓
[Aggregated Response]        [Task completion]
          ↓                           ↓
[WebSocket notification] ←─────────────┘
          ↓
[Frontend updates chat history]
          ↓
[Пользователь видит ответ]
```

### 3️⃣ Координатор и инструменты

```
[User Query] 
    ↓
[CoordinatorAgent::generate_plan()]
    ↓ (LangChain ReAct agent)
[LM Studio API]
    ↓ (JSON plan)
[Plan Analysis]
    ↓ (extract tools/roles)
[SpecialistAgentsManager::execute_plan()]
    ↓ (for each task in plan)
[Tool Execution Loop]
    ├─ search_rag_database
    ├─ calculate_estimate  
    ├─ generate_ppr
    ├─ find_normatives
    ├─ create_gantt_chart
    ├─ analyze_tender
    └─ ... (other tools)
    ↓ (collect results)
[Results Aggregation]
    ↓ (format response)
[Final Response to User]
```

### 4️⃣ WebSocket Real-time Updates

```
[FastAPI Background Task]
    ↓ (periodic updates)
[WebSocketManager::send_stage_update()]
    ↓ (JSON message)
[Active WebSocket Connections]
    ├─ Frontend (AI Shell)
    ├─ Dashboard (File Manager)  
    └─ Mobile/Other clients
    ↓ (real-time messages)
[Client receives update]
    ↓ (parse JSON)
[UI updates accordingly]
```

## 🧠 Координатор - центральный интеллект

### Логика принятия решений:

```python
def analyze_request(user_input: str) -> Dict[str, Any]:
    """
    1. Parse request using SBERT (semantic understanding)
    2. Determine complexity (low/medium/high)
    3. Select appropriate roles and tools
    4. Generate JSON execution plan
    5. Validate plan structure
    """
    
def execute_plan(plan: Dict[str, Any]) -> Dict[str, Any]:
    """
    1. For each task in plan:
       - Route to appropriate specialist agent
       - Execute with selected tools
       - Collect partial results
    2. Aggregate all results
    3. Generate natural language response
    4. Return to user via original channel
    """
```

### Типы запросов и маршрутизация:

| Тип запроса | Ключевые слова | Роли | Инструменты |
|------------|---------------|------|-------------|
| **Нормативы** | СП, ГОСТ, СНИП, пункт | chief_engineer | search_rag_database, find_normatives |
| **Финансы** | стоимость, смета, расчет | analyst, chief_engineer | calculate_estimate, parse_gesn_estimate |
| **Проекты** | ППР, график, работы | project_manager, construction_worker | generate_ppr, create_gantt_chart |
| **Визуализация** | диаграмма, график, chart | analyst, project_manager | create_pie_chart, generate_mermaid_diagram |
| **Документы** | письмо, официальное | chief_engineer | generate_letter |

## 🔧 Инструменты системы

### Core Tools (всегда доступны):
- `search_rag_database` - поиск в базе знаний
- `search_knowledge_base` - поиск информации
- `analyze_image` - анализ изображений

### Financial Tools:
- `calculate_estimate` - расчет смет
- `auto_budget` - автоматический бюджет  
- `parse_gesn_estimate` - парсинг ГЭСН
- `calculate_financial_metrics` - ROI, NPV, IRR

### Project Management:
- `generate_ppr` - создание ППР
- `create_gpp` - график производства работ
- `get_work_sequence` - последовательность работ
- `create_construction_schedule` - график строительства

### Visualization:
- `create_gantt_chart` - диаграммы Ганта
- `create_pie_chart` - круговые диаграммы
- `create_bar_chart` - столбчатые диаграммы
- `generate_mermaid_diagram` - блок-схемы

### Document Generation:
- `generate_letter` - официальные письма
- `create_document` - создание документов
- `extract_text_from_pdf` - извлечение текста

## 🏗️ Архитектура системы

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   User Layer    │    │   Interface      │    │   Processing    │
├─────────────────┤    ├──────────────────┤    ├─────────────────┤
│ • Telegram Bot  │───▶│ • FastAPI        │───▶│ • Coordinator   │
│ • Web Frontend  │    │ • WebSockets     │    │ • Specialists   │
│ • Mobile Apps   │    │ • REST API       │    │ • Tools System  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                ▲                        │
                                │                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Data Layer    │    │   Models         │    │   External      │
├─────────────────┤    ├──────────────────┤    ├─────────────────┤
│ • FAISS Index   │◀───│ • LM Studio      │◀───│ • Neo4j Graph   │
│ • Qdrant Vector │    │ • DeepSeek R1    │    │ • File Storage  │
│ • Document Store│    │ • Qwen 2.5 VL    │    │ • Cloud Services│
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 🚦 Проверочные точки E2E

### 1. Connectivity Tests
- ✅ FastAPI Health Check (`/health`)
- ✅ LM Studio Models (`/v1/models`)  
- ✅ WebSocket Connection (`/ws`)
- ✅ Neo4j Database (if enabled)

### 2. Core Functionality
- ✅ RAG Search (`/api/search`)
- ✅ Query Processing (`/query`)
- ✅ AI Requests (`/ai`)
- ✅ Coordinator Plans (`/submit_query`)

### 3. Integration Points
- ✅ Frontend ↔ API communication
- ✅ Telegram Bot ↔ API integration
- ✅ Coordinator ↔ Tools execution
- ✅ WebSocket real-time updates

### 4. Data Flow Validation
- ✅ User input → Coordinator analysis
- ✅ Plan generation → Tools selection
- ✅ Tools execution → Results aggregation
- ✅ Response formatting → User delivery

## 🎯 Ключевые метрики производительности

- **Response Time**: < 2s для простых запросов, < 30s для сложных
- **Accuracy**: NDCG > 0.9 для RAG поиска
- **Availability**: > 99% uptime для API
- **Concurrency**: поддержка 100+ одновременных соединений

## 🔍 Мониторинг и отладка

### Логи системы:
- **FastAPI**: HTTP requests/responses
- **Coordinator**: Plan generation and execution  
- **Tools**: Individual tool execution results
- **WebSocket**: Real-time message flow

### Метрики для отслеживания:
- Время ответа по типам запросов
- Успешность выполнения планов координатора
- Использование инструментов (частота/эффективность)
- Качество RAG поиска (NDCG, precision)

---

*Эта диаграмма показывает полный путь запроса пользователя через все компоненты системы до получения итогового ответа.*