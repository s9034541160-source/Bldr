# Function/Class Signature Index

Generated: 2025-09-20
Root: C:\Bldr
Directories covered (initial): core, backend/api, system_launcher (selected), integrations (selected), plugins (selected), scripts (selected)
Note: A generator script is provided: scripts/generate_function_index.py to refresh/expand this index.

## core/bldr_api.py

### Classes
- class LimitUploadSizeMiddleware

### Functions (top-level)
- async def lifespan(app: FastAPI)
- async def general_exception_handler(request: Request, exc: Exception)
- async def validation_exception_handler(request, exc)
- async def http_exception_handler(request: Request, exc: HTTPException)
- async def auth_debug()
- async def validate_token(current_user: dict = Depends(verify_api_token))
- async def health()
- async def websocket_endpoint(websocket: WebSocket, token: Optional[str] = None)
- async def submit_query_endpoint(request_data: SubmitQueryRequest, background_tasks: BackgroundTasks, credentials: dict = Depends(verify_api_token))
- async def list_processes(process_type: Optional[str] = None, status: Optional[str] = None, credentials: dict = Depends(verify_api_token))
- async def get_process_status(process_id: str, credentials: dict = Depends(verify_api_token))
- async def cancel_process(process_id: str, credentials: dict = Depends(verify_api_token))
- async def get_process_types(credentials: dict = Depends(verify_api_token))
- async def get_process_statuses(credentials: dict = Depends(verify_api_token))
- async def training_status_endpoint(credentials: dict = Depends(verify_api_token))
- async def ai_shell_endpoint(request: Request, request_data: AICall, credentials: dict = Depends(verify_api_token))
- async def get_ai_task_status_endpoint(task_id: str, credentials: dict = Depends(verify_api_token))
- async def list_ai_tasks_endpoint(credentials: dict = Depends(verify_api_token))
- async def metrics_endpoint(request: Request)
- async def metrics_json_endpoint(request: Request)
- async def db_query(request: Request, cypher: str, credentials: dict = Depends(require_role("admin")))
- async def bot_cmd(request: Request, cmd: str = Form(...), credentials: dict = Depends(verify_api_token))
- async def files_scan(request: Request, path: str = Form(...), credentials: dict = Depends(verify_api_token))
- async def upload_file(request: Request, file: UploadFile = File(...), credentials: dict = Depends(verify_api_token))
- async def upload_for_rag_training(request: Request, file: UploadFile = File(...), credentials: dict = Depends(verify_api_token))
- async def upload_for_estimate_analysis(request: Request, file: UploadFile = File(...), credentials: dict = Depends(verify_api_token))
- async def upload_from_telegram_or_shell(request: Request, file: UploadFile = File(...), credentials: dict = Depends(verify_api_token))
- async def list_tools_endpoint(request: Request, category: Optional[str] = None, credentials: dict = Depends(verify_api_token))
- async def list_tools_alias(request: Request, category: Optional[str] = None, credentials: dict = Depends(verify_api_token))
- async def get_tool_info_endpoint(request: Request, tool_name: str, credentials: dict = Depends(verify_api_token))
- async def get_categories_endpoint(request: Request, credentials: dict = Depends(verify_api_token))
- async def get_tools_stats_endpoint(request: Request, tool_name: Optional[str] = None, credentials: dict = Depends(verify_api_token))
- async def execute_tool_chain_endpoint(request: Request, chain: List[Dict[str, Any]], credentials: dict = Depends(verify_api_token))
- async def execute_tool(request: Request, tool_name: str, tool_kwargs: Dict[str, Any], credentials: dict = Depends(verify_api_token))
- async def generate_letter_endpoint(request: Request, tool_args: Dict[str, Any], credentials: dict = Depends(verify_api_token))
- async def improve_letter_endpoint(request: Request, tool_args: Dict[str, Any], credentials: dict = Depends(verify_api_token))
- async def auto_budget_endpoint(request: Request, tool_args: Dict[str, Any], credentials: dict = Depends(verify_api_token))
- async def generate_ppr_endpoint(request: Request, tool_args: Dict[str, Any], credentials: dict = Depends(verify_api_token))
- async def create_gpp_endpoint(request: Request, tool_args: Dict[str, Any], credentials: dict = Depends(verify_api_token))
- async def parse_gesn_estimate_endpoint(request: Request, tool_args: Dict[str, Any], credentials: dict = Depends(verify_api_token))
- async def analyze_tender_endpoint(request: Request, tool_args: Dict[str, Any], credentials: dict = Depends(verify_api_token))
- async def run_training_with_updates(custom_dir: Optional[str] = None, fast_mode: bool = False)
- async def train_endpoint(request: Request, background_tasks: BackgroundTasks, train_data: TrainRequest, credentials: dict = Depends(verify_api_token))
- async def status_aggregator(credentials: dict = Depends(verify_api_token))

### Helpers
- authenticate_user(username: str, password: str) -> Optional[Dict]
- create_access_token(data: dict, expires_delta: Optional[timedelta] = None)
- get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security))
- verify_api_token(credentials: HTTPAuthorizationCredentials = Depends(security))
- require_role(required_role: str)
- format_ifc_error(error: Exception) -> str
- format_file_error(error: Exception, filename: Optional[str] = None) -> str

## core/projects_api.py

### Classes
- class ProjectManager
  - detect_file_type(self, filename: str, content: bytes = b'') -> str
  - create_project(self, project_data: ProjectCreate) -> dict
  - get_projects(self) -> List[dict]
  - get_project(self, project_id: str) -> dict
  - update_project(self, project_id: str, project_data: ProjectUpdate) -> dict
  - delete_project(self, project_id: str) -> dict
  - add_files_to_project(self, project_id: str, files: List[UploadFile]) -> dict
  - get_project_files(self, project_id: str) -> List[dict]
  - scan_project_files(self, project_id: str) -> dict
  - scan_directory_for_project(self, project_id: str, directory_path: str) -> dict
  - delete_project_file(self, project_id: str, file_id: str) -> dict
  - save_project_result(self, project_id: str, result_type: str, data: Dict[Any, Any]) -> Dict[Any, Any]
  - get_project_results(self, project_id: str) -> List[Dict[Any, Any]]

### Routers (/projects)
- POST / — create_project
- GET / — get_projects
- GET /{project_id} — get_project
- PUT /{project_id} — update_project
- DELETE /{project_id} — delete_project
- POST /{project_id}/files — add_files_to_project
- GET /{project_id}/files — get_project_files
- GET /{project_id}/scan — scan_project_files
- DELETE /{project_id}/files/{file_id} — delete_project_file
- POST /{project_id}/scan-directory — scan_directory_for_project
- POST /{project_id}/results — save_project_result
- GET /{project_id}/results — get_project_results
- Templates: GET/POST/PUT/DELETE /templates

## backend/api/tools_api.py

### Helpers
- async def get_coordinator()
- def get_redis() -> redis.Redis
- def _job_key(job_id: str) -> str
- def create_job(tool_type: str, params: Dict[str, Any]) -> str
- def update_job(job_id: str, status: str = None, progress: int = None, message: str = None, result: Any = None, error: str = None)
- convert_params_to_master_format(tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]
- async def execute_estimate_analysis(...)
- async def execute_image_analysis(...)
- async def execute_document_analysis(...)
- async def execute_tender_analysis(...)

### Endpoints (/api/tools)
- GET /list — list_tools
- POST /analyze/estimate — analyze_estimate
- POST /analyze/images — analyze_images
- POST /analyze/documents — analyze_documents
- POST /analyze/tender — analyze_tender
- GET /jobs/{job_id}/status — get_job_status
- GET /jobs/active — get_active_jobs
- POST /jobs/{job_id}/cancel — cancel_job
- GET /jobs/{job_id}/download — download_job_result
- DELETE /jobs/cleanup — cleanup_completed_jobs
- GET /info — get_tools_info
- GET /health — health_check

## backend/api/meta_tools_api.py

### Endpoints (/api/meta-tools)
- GET / — get_meta_tools_info
- GET /list — list_meta_tools
- GET /search — search_meta_tools
- GET /{tool_name} — get_meta_tool_info
- POST /execute — execute_meta_tool_sync
- POST /execute/async — execute_meta_tool_async
- GET /tasks/active — get_active_tasks
- GET /tasks/{task_id}/status — get_task_status
- POST /tasks/{task_id}/cancel — cancel_task
- POST /tasks/cleanup — cleanup_completed_tasks
- GET /statistics — get_system_statistics
- POST /workflows — create_workflow
- POST /workflows/{workflow_id}/execute — execute_workflow
- GET /workflows/{workflow_id}/status — get_workflow_status
- GET /health — health_check

## core/celery_app.py
- celery_app = Celery(...)

## core/celery_norms.py

### Classes
- class NormsUpdateTask
  - update_norms(self, categories: Optional[List[str]] = None, force: bool = False) -> Dict[str, Any]
  - _process_new_documents(self)
  - _extract_doc_info(self, doc_path: Path, category: str) -> Dict[str, Any]
  - _extract_doc_id(self, filename: str) -> Optional[str]
  - _extract_version(self, filename: str) -> str
  - _extract_date(self, filename: str) -> str
  - _archive_old_version(self, doc_id: str, old_date: str, doc_path: Path)
  - _log_to_neo4j(self, data: Dict[str, Any])

### Tasks
- @celery_app.task name='core.celery_norms.update_norms_task' def update_norms_task(...)

## core/agents/coordinator_agent.py

### Classes
- class CoordinatorAgent
  - __init__(...)
  - _direct_response(self, query: str) -> str
  - _execute_meta_tool(self, params: str) -> str
  - _list_meta_tools(self, params: str = "") -> str
  - _search_meta_tools(self, params: str) -> str
  - _transcribe_audio(self, params: str)
  - _simple_norm_check(self, text: str) -> str
  - _analyze_and_plan(self, query: str) -> str
  - _generate_fallback_plan(self, query: str) -> str
  - get_available_tools_list(self) -> str
  - _create_agent(self) -> AgentExecutor
  - generate_plan(self, query: str) -> Dict[str, Any]
  - _convert_plan_to_natural_language(self, plan: Dict[str, Any], query: str) -> str
  - _generate_fallback_natural_language_response(self, plan: Dict[str, Any], query: str) -> str
  - process_query(self, query: str) -> str
  - generate_response(self, query: str) -> Dict[str, Any]
  - set_request_context(self, context)
  - clear_request_context(self)
  - deliver_file(self, file_path: str, description: str = "") -> str
  - _deliver_file_to_telegram(self, file_path: str, description: str = "") -> str
  - _deliver_file_to_ai_shell(self, file_path: str, description: str = "") -> str

## core/agents/specialist_agents.py

### Classes
- class SpecialistAgent
  - __init__(self, role: str, lm_studio_url: str = ..., tools_system=None)
  - execute_task(self, task_input: str, tool_results: List[Dict[str, Any]]) -> Dict[str, Any]

- class SpecialistAgentsManager
  - __init__(...)
  - get_agent(self, role: str) -> SpecialistAgent
  - execute_plan(self, plan: Dict[str, Any], tools_system: Any) -> List[Dict[str, Any]]

## core/websocket_manager.py

### Classes
- class ConnectionManager
  - __init__(self)
  - async def connect(self, websocket: WebSocket)
  - def disconnect(self, websocket: WebSocket)
  - async def send_personal_message(self, message: str, websocket: WebSocket)
  - async def broadcast(self, message: str)

