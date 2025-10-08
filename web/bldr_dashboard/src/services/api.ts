// api.ts - Сервис для работы с API Bldr Empire
import axios from 'axios';
import { message } from 'antd';
import { useStore } from '../store';

// Базовая конфигурация axios
const api = axios.create({
  baseURL: 'http://localhost:8000/api', // HARDCODE: Force connection to backend port 8000
  timeout: 3600000, // Increased timeout to 3600 seconds (1 hour) for coordinator requests
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor
api.interceptors.request.use(
  (config) => {
    // Get user and settings from zustand store
    const storeState = useStore.getState();
    const { user, settings } = storeState;
    
    // Set baseURL from store settings
    if (settings?.host) {
      config.baseURL = settings.host.startsWith('http') ? settings.host : `http://${settings.host}`;
    }
    
    // Add authorization header if token exists
    if (user && user.token) {
      config.headers.Authorization = `Bearer ${user.token}`;
    }
    
    return config;
  },
  (error) => {
    console.error(`Запрос ошибка: ${error.message}`);
    return Promise.reject(error);
  }
);

// Add response interceptor for global error handling (with unified-schema support)
api.interceptors.response.use(
  (response) => {
    try {
      const ct = (response.headers?.['content-type'] || '').toString();
      if (ct.includes('application/json') && response.data && typeof response.data === 'object') {
        const payload = response.data as any;
        // If backend returned unified schema — optionally surface errors here
        if (typeof payload.status === 'string' && ('data' in payload || 'error' in payload)) {
          if (payload.status !== 'success') {
            // Non-blocking toast; let caller handle specifics
            if (payload.error) message.error(String(payload.error));
          }
        }
      }
    } catch (e) {
      // ignore
    }
    return response;
  },
  (error) => {
    if (error.response?.status === 401) {
      // Clear user data and redirect to login
      const { clearUser } = useStore.getState();
      clearUser();
      message.warning('Сессия истекла — перелогиньтесь');
      return Promise.reject(error);
    }
    
    if (error.response?.status === 404) {
      message.error(`Не найдено: ${error.config?.url}. Обновите backend или роут.`);
    }
    
    if (error.response?.status >= 500) {
      const msg = error.response?.data?.error || error.response?.data?.detail || `Ошибка сервера (${error.response.status})`;
      message.error(msg);
    }
    
    if (!error.response) {
      message.error('Сеть недоступна — проверьте backend (localhost:8000)');
    }
    
    return Promise.reject(error);
  }
);

// Unified/legacy response unwrapping helper
export type UnifiedEnvelope<T = any> = {
  status: 'success' | 'error' | string;
  data?: T;
  error?: any;
  meta?: any;
};

export function unwrap<T = any>(payload: any): { ok: boolean; data?: T; error?: any } {
  try {
    if (payload && typeof payload === 'object' && typeof payload.status === 'string') {
      if (payload.status === 'success') {
        return { ok: true, data: (payload as UnifiedEnvelope<T>).data as T };
      }
      return { ok: false, error: (payload as UnifiedEnvelope<T>).error ?? (payload as any).error ?? 'Unknown error' };
    }
    // Legacy payload (treat as success)
    return { ok: true, data: payload as T };
  } catch (e: any) {
    return { ok: false, error: e?.message || 'unwrap failed' };
  }
}

// Интерфейсы для типизации ответов
export interface QueryRequest {
  query: string;
  k?: number;
  category?: string;
}

export interface QueryResult {
  chunk: string;
  meta: {
    conf: number;
    entities: Record<string, string[]>;
    work_sequences?: string[];
    violations?: string[];
    category?: string;
    categories?: string[];
    [key: string]: any;
  };
  score: number;
  tezis: string;
  viol: number;
}

export interface MetricsData {
  total_chunks: number;
  avg_ndcg: number;
  coverage: number;
  conf: number;
  viol: number;
  entities?: Record<string, number>;
}

export interface TrainRequest {
  custom_dir?: string;
}

export interface HealthStatus {
  status: string;
  timestamp: string;
  components: Record<string, string>;
}

export interface CypherRequest {
  cypher: string;
}

export interface CypherResponse {
  cypher: string;
  records: Record<string, any>[];
}

export interface BotRequest {
  cmd: string;
}

export interface BotResponse {
  cmd: string;
  status: string;
  message: string;
}

export interface FileScanRequest {
  path: string;
}

export interface FileScanResponse {
  scanned: number;
  copied: number;
  path: string;
}

export interface AIRequest {
  prompt: string;
  model?: string;
}

export interface AIResponse {
  response?: string;
  model?: string;
  status?: string;
  task_id?: string;
  message?: string;
}

// Project interfaces
export interface Project {
  id: string;
  name: string;
  code: string;
  location: string;
  status: string;
  files_count: number;
  roi: number;
  updated_at: string;
}

export interface ProjectCreate {
  name: string;
  code?: string;
  location?: string;
  status?: string;
}

export interface ProjectUpdate {
  name?: string;
  code?: string;
  location?: string;
  status?: string;
}

export interface ProjectFile {
  id: string;
  name: string;
  path: string;
  size: number;
  type: string;
  uploaded_at: string;
}

export interface ProjectResult {
  id: string;
  type: string;
  data: any;
  created_at: string;
}

export interface ScanResult {
  files_count: number;
  smeta_count: number;
  rd_count: number;
  graphs_count: number;
  smeta_paths: string[];
  rd_paths: string[];
}

// Pro Features interfaces
export interface LetterData {
  template: string;
  recipient: string;
  sender: string;
  subject: string;
  compliance_details?: string[];
  violations?: string[];
}

export interface BudgetData {
  project_name: string;
  positions: Array<{
    code: string;
    name: string;
    unit: string;
    quantity: number;
    unit_cost: number;
  }>;
  regional_coefficients: Record<string, number>;
  overheads_percentage: number;
  profit_percentage: number;
}

export interface PPRData {
  project_name: string;
  project_code: string;
  location: string;
  client: string;
  works_seq: Array<{
    name: string;
    description: string;
    duration: number;
    deps: string[];
    resources: Record<string, any>;
  }>;
}

export interface TenderData {
  tender_data?: {
    id?: string;
    name?: string;
    value?: number;
  };
  project_id?: string;
  estimate_file?: File | null;
  requirements?: string[];
}

// Super Features interfaces
export interface BIMAnalysisData {
  ifc_path: string;
  analysis_type: string;
}

export interface DWGExportData {
  dwg_data: any;
  works_seq: any[];
}

export interface MonteCarloData {
  project_data: {
    base_cost: number;
    profit: number;
    vars: {
      cost: number;
      time: number;
      roi: number;
    };
  };
}

export interface BIMAnalysisResponse {
  status: string;
  elements_count: number;
  clashes: any[];
  violations: any[];
  error?: string;
}

export interface DWGExportResponse {
  status: string;
  file_path: string;
  message: string;
  error?: string;
}

export interface MonteCarloResponse {
  status: string;
  mean: number;
  std: number;
  p10: number;
  p90: number;
  hist_bins: number[];
  roi_stats: {
    mean: number;
    p10: number;
    p90: number;
  };
  error?: string;
}

export interface LetterResponse {
  status: string;
  file_path: string;
  message: string;
  letter?: string;
  tokens?: number;
  error?: string;
}

export interface BudgetResponse {
  status: string;
  budget: any;
  total_cost: number;
  error?: string;
}

export interface PPRResponse {
  status: string;
  ppr: any;
  stages_count: number;
  message?: string;
  error?: string;
}

export interface TenderResponse {
  status: string;
  analysis: any;
  message?: string;
  error?: string;
}

// Add interfaces for norms management
export interface NormDoc {
  id: string;
  name: string;
  category: string;
  type: string;
  status: string;
  issue_date: string;
  check_date: string;
  source: string;
  link: string;
  description: string;
  violations_count: number;
}

export interface NormsListResponse {
  data: NormDoc[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    pages: number;
  };
}

export interface NormsSummaryResponse {
  total: number;
  actual: number;
  outdated: number;
  pending: number;
}

export interface NormsStatusResponse {
  status: string;
  sources: Record<string, {
    category: string;
    documents: number;
    last_update: string | null;
  }>;
}

export interface UpdateNormsResponse {
  status: string;
  message: string;
  results?: any;
  error?: string;
}

export interface ResetDatabasesResponse {
  status: string;
  message: string;
  error?: string;
}

// Add interface for queue data
export interface QueueTask {
  id: string;
  type: string;
  status: string;
  progress: number;
  owner: string;
  started_at: string;
  eta: string | null;
}

export interface QueueStatus {
  status: string;
  queue_length: number;
  active_tasks: QueueTask[];
}

// Add template interfaces
export interface Template {
  id: string;
  name: string;
  category: string;
  preview: string;
  full_text: string;
}

export interface TemplateCreate {
  name: string;
  category: string;
  preview: string;
  full_text: string;
}

export interface TemplateUpdate {
  name?: string;
  category?: string;
  preview?: string;
  full_text?: string;
}

// Add advanced letter interfaces
export interface AdvancedLetterData {
  description: string;
  template_id?: string;
  project_id?: string;
  tone?: number;
  dryness?: number;
  humanity?: number;
  length?: string;
  formality?: string;
  recipient?: string;
  sender?: string;
  subject?: string;
}

export interface ImproveLetterData {
  draft: string;
  description: string;
  template_id?: string;
  project_id?: string;
  tone: number;
  dryness: number;
  humanity: number;
  length: string;
  formality: string;
}

// API методы

export interface CoordinatorSettings {
  planning_enabled: boolean;
  max_iterations: number;
  simple_plan_fast_path: boolean;
  artifact_default_enabled: boolean;
  complexity_auto_expand: boolean;
  complexity_thresholds: { tools_count: number; time_est_minutes: number };
}

export interface PromptInfo {
  role: string;
  title: string;
  source: 'active' | 'default' | string;
  updated_at?: string | null;
}

export interface PromptResponse {
  role: string;
  title: string;
  content: string;
  source: 'active' | 'default' | string;
  updated_at?: string | null;
}

export interface RulesResponse {
  content: string;
  source: 'active' | 'default' | string;
  updated_at?: string | null;
}

export interface RoleInfo { role: string; title: string; }
export interface AvailableModel { id: string; label: string; base_url: string; temperature?: number; max_tokens?: number; }

export const apiService = {
  // Запрос к RAG системе
  query: async (data: QueryRequest) => {
    try {
      const response = await api.post<{results: QueryResult[], ndcg: number}>('/query', data);
      
      // 🚨 КРИТИЧЕСКОЕ ИЗМЕНЕНИЕ: Проверяем HTTP статус
      if (response.status !== 200) {
        throw new Error(`Ошибка API (HTTP ${response.status}): ${response.data?.error_message || 'Неизвестная ошибка'}`);
      }
      
      return response.data; // Возвращаем только чистые данные при успехе
    } catch (error) {
      console.error('Ошибка выполнения запроса:', error);
      throw error;
    }
  },

  // Запуск обучения RAG
  train: async (data?: TrainRequest) => {
    try {
      // Create special axios instance with longer timeout for training (2 hours)
      const trainApi = axios.create({
        baseURL: api.defaults.baseURL,
        timeout: 7200000, // 2 hours timeout for training
        headers: api.defaults.headers,
      });
      
      // Add authorization header if exists
      const storeState = useStore.getState();
      const { user } = storeState;
      if (user && user.token) {
        trainApi.defaults.headers.Authorization = `Bearer ${user.token}`;
      }
      
      const response = await trainApi.post('/train', data || {});
      return response.data || {};
    } catch (error) {
      console.error('Ошибка запуска обучения:', error);
      throw error;
    }
  },


  // Вызов AI с определенной ролью
  callAI: async (data: AIRequest) => {
    try {
      const response = await api.post<AIResponse>('/ai', data);
      return response.data || { response: '', model: '', status: 'completed' };
    } catch (error) {
      console.error('Ошибка вызова AI:', error);
      throw error;
    }
  },

  // ===== NEW RAG API METHODS =====
  
  // Анализ одного файла
  analyzeFile: async (filePath: string, saveToDb: boolean = false) => {
    try {
      const response = await api.post('/api/analyze-file', {
        file_path: filePath,
        save_to_db: saveToDb
      });
      return response.data;
    } catch (error) {
      console.error('Ошибка анализа файла:', error);
      throw error;
    }
  },

  // Анализ проекта (несколько файлов)
  analyzeProject: async (filePaths: string[]) => {
    try {
      const response = await api.post('/api/analyze-project', {
        file_paths: filePaths
      });
      return response.data;
    } catch (error) {
      console.error('Ошибка анализа проекта:', error);
      throw error;
    }
  },

  // Дообучение на файле
  trainFile: async (filePath: string) => {
    try {
      const response = await api.post('/api/train-file', {
        file_path: filePath
      });
      return response.data;
    } catch (error) {
      console.error('Ошибка дообучения на файле:', error);
      throw error;
    }
  },

  // Получение информации о файле
  getFileInfo: async (filePath: string) => {
    try {
      const response = await api.get('/api/get-file-info', {
        params: { file_path: filePath }
      });
      return response.data;
    } catch (error) {
      console.error('Ошибка получения информации о файле:', error);
      throw error;
    }
  },

  // Получение списка файлов
  listFiles: async (directory?: string, extension: string = '.pdf') => {
    try {
      const response = await api.get('/api/list-files', {
        params: { 
          directory: directory,
          extension: extension
        }
      });
      return response.data;
    } catch (error) {
      console.error('Ошибка получения списка файлов:', error);
      throw error;
    }
  },

  // Проверка состояния системы
  getHealth: async () => {
    try {
      const response = await api.get<HealthStatus>('/health');
      return response.data || { status: 'unknown', timestamp: '', components: {} };
    } catch (error) {
      console.error('Ошибка проверки состояния:', error);
      throw error;
    }
  },

  // ===== SETTINGS: Coordinator =====
  getCoordinatorSettings: async (): Promise<CoordinatorSettings> => {
    try {
      const response = await api.get('/api/settings/coordinator');
      // Backend returns object directly
      return response.data;
    } catch (error) {
      console.error('Ошибка получения настроек координатора:', error);
      throw error;
    }
  },
  updateCoordinatorSettings: async (settings: CoordinatorSettings) => {
    try {
      const response = await api.put('/api/settings/coordinator', settings);
      return response.data;
    } catch (error) {
      console.error('Ошибка сохранения настроек координатора:', error);
      throw error;
    }
  },

  // ===== SETTINGS: Role ↔ Model Assignment =====
  listRoles: async (): Promise<RoleInfo[]> => {
    try {
      const response = await api.get('/api/settings/roles');
      return response.data?.roles || [];
    } catch (error) {
      console.error('Ошибка получения списка ролей:', error);
      throw error;
    }
  },
  listAvailableModels: async (): Promise<{ models: AvailableModel[]; default_base_url: string }> => {
    try {
      const response = await api.get('/api/settings/models/available');
      return response.data || { models: [], default_base_url: '' };
    } catch (error) {
      console.error('Ошибка получения моделей:', error);
      throw error;
    }
  },
  getRoleModels: async () => {
    try {
      const response = await api.get('/api/settings/role-models');
      return response.data || { roles: {} };
    } catch (error) {
      console.error('Ошибка получения назначений ролей:', error);
      throw error;
    }
  },
  updateRoleModels: async (mapping: Record<string, any>) => {
    try {
      const response = await api.put('/api/settings/role-models', mapping);
      return response.data;
    } catch (error) {
      console.error('Ошибка обновления назначений ролей:', error);
      throw error;
    }
  },
  resetRoleModel: async (role?: string) => {
    try {
      const params = role ? `?role=${encodeURIComponent(role)}` : '';
      const response = await api.post(`/api/settings/role-models/reset${params}`, {});
      return response.data;
    } catch (error) {
      console.error('Ошибка сброса назначений ролей:', error);
      throw error;
    }
  },
  // ===== SETTINGS: Raw JSON =====
  getFullSettingsJson: async () => {
    try {
      const response = await api.get('/api/settings/json');
      return response.data || {};
    } catch (error) {
      console.error('Ошибка получения settings.json:', error);
      throw error;
    }
  },
  downloadFullSettingsJson: async () => {
    try {
      const response = await api.get('/api/settings/json/download', { responseType: 'blob' });
      return response.data;
    } catch (error) {
      console.error('Ошибка скачивания settings.json:', error);
      throw error;
    }
  },
  openSettingsInEditor: async () => {
    try {
      const response = await api.post('/api/settings/json/open', {});
      return response.data;
    } catch (error) {
      console.error('Ошибка открытия settings.json:', error);
      throw error;
    }
  },
  clearModelCache: async (keepCoordinator: boolean = true) => {
    try {
      const response = await api.post(`/api/settings/models/clear-cache?keep_coordinator=${keepCoordinator ? 'true' : 'false'}`, {});
      return response.data;
    } catch (error) {
      console.error('Ошибка очистки кеша моделей:', error);
      throw error;
    }
  },

  // ===== SETTINGS: Prompts & Factual Rules =====
  listPrompts: async (): Promise<PromptInfo[]> => {
    try {
      const response = await api.get('/api/settings/prompts/list');
      return response.data || [];
    } catch (error) {
      console.error('Ошибка получения списка промптов:', error);
      throw error;
    }
  },
  getPrompt: async (roleKey: string): Promise<PromptResponse> => {
    try {
      const response = await api.get(`/api/settings/prompts/${roleKey}`);
      return response.data;
    } catch (error) {
      console.error('Ошибка получения промпта роли:', error);
      throw error;
    }
  },
  updatePrompt: async (roleKey: string, content: string): Promise<PromptResponse> => {
    try {
      const response = await api.put(`/api/settings/prompts/${roleKey}`, { content });
      return response.data;
    } catch (error) {
      console.error('Ошибка обновления промпта роли:', error);
      throw error;
    }
  },
  resetPrompt: async (roleKey: string): Promise<PromptResponse> => {
    try {
      const response = await api.post(`/api/settings/prompts/${roleKey}/reset`, {});
      return response.data;
    } catch (error) {
      console.error('Ошибка сброса промпта роли:', error);
      throw error;
    }
  },
  getFactualRules: async (): Promise<RulesResponse> => {
    try {
      const response = await api.get('/api/settings/factual-rules');
      return response.data;
    } catch (error) {
      console.error('Ошибка получения правил фактической точности:', error);
      throw error;
    }
  },
  updateFactualRules: async (content: string): Promise<RulesResponse> => {
    try {
      const response = await api.put('/api/settings/factual-rules', { content });
      return response.data;
    } catch (error) {
      console.error('Ошибка обновления правил фактической точности:', error);
      throw error;
    }
  },
  resetFactualRules: async (): Promise<RulesResponse> => {
    try {
      const response = await api.post('/api/settings/factual-rules/reset', {});
      return response.data;
    } catch (error) {
      console.error('Ошибка сброса правил фактической точности:', error);
      throw error;
    }
  },

  // Unified status aggregator
  getStatus: async () => {
    try {
      const response = await api.get('/status');
      // Accept both unified and legacy
      const data: any = response.data;
      if (data && typeof data === 'object' && 'status' in data && ('data' in data || 'components' in data)) {
        return data.data ? data.data : data; // prefer unified.data
      }
      return data;
    } catch (error) {
      console.error('Ошибка получения статуса системы:', error);
      throw error;
    }
  },

  // Debug auth configuration
  getAuthDebug: async () => {
    try {
      const response = await api.get('/auth/debug');
      return response.data || {};
    } catch (error) {
      // If endpoint is not available, assume auth is enabled
      return { skip_auth: false };
    }
  },

  // User management (admin)
  listUsers: async () => {
    try {
      const response = await api.get('/auth/users');
      // unified ok/err support
      const data = response.data?.data || response.data;
      return data?.users || [];
    } catch (error) {
      console.error('Ошибка получения пользователей:', error);
      throw error;
    }
  },
  createUser: async (username: string, password: string, role: string = 'user') => {
    try {
      const response = await api.post('/auth/users', { username, password, role });
      return response.data;
    } catch (error) {
      console.error('Ошибка создания пользователя:', error);
      throw error;
    }
  },

  // Выполнение Cypher запроса к Neo4j
  executeCypher: async (data: CypherRequest) => {
    try {
      const response = await api.post<CypherResponse>('/db', data);
      return response.data || { cypher: data.cypher, records: [] };
    } catch (error) {
      console.error('Ошибка выполнения Cypher запроса:', error);
      throw error;
    }
  },

  // Отправка команды боту
  sendBotCommand: async (data: BotRequest) => {
    try {
      const response = await api.post<BotResponse>('/bot', new URLSearchParams(data as any), {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      });
      return response.data || { cmd: data.cmd, status: 'error', message: 'Пустой ответ от сервера' };
    } catch (error) {
      console.error('Ошибка отправки команды боту:', error);
      throw error;
    }
  },

  // Сканирование файлов
  scanFiles: async (data: FileScanRequest) => {
    try {
      // Create FormData to send path as form data (required by backend)
      const formData = new FormData();
      formData.append('path', data.path);
      
      const response = await api.post<FileScanResponse>('/files-scan', formData);
      return response.data || { scanned: 0, copied: 0, path: data.path };
    } catch (error) {
      console.error('Ошибка сканирования файлов:', error);
      throw error;
    }
  },

  // Project Management API methods
  getProjects: async () => {
    try {
      const response = await api.get<Project[]>('/api/projects');
      return response.data || [];
    } catch (error) {
      console.error('Ошибка получения проектов:', error);
      throw error;
    }
  },

  getProject: async (id: string) => {
    try {
      const response = await api.get<Project>(`/api/projects/${id}`);
      return response.data;
    } catch (error) {
      console.error('Ошибка получения проекта:', error);
      throw error;
    }
  },

  createProject: async (data: ProjectCreate) => {
    try {
      // Backend expects POST /projects/ (with trailing slash) to avoid 307 redirect
      const response = await api.post<Project>('/api/projects/', data);
      return response.data;
    } catch (error) {
      console.error('Ошибка создания проекта:', error);
      throw error;
    }
  },

  updateProject: async (id: string, data: ProjectUpdate) => {
    try {
      const response = await api.put<Project>(`/api/projects/${id}`, data);
      return response.data;
    } catch (error) {
      console.error('Ошибка обновления проекта:', error);
      throw error;
    }
  },

  deleteProject: async (id: string) => {
    try {
      const response = await api.delete(`/api/projects/${id}`);
      return response.data;
    } catch (error) {
      console.error('Ошибка удаления проекта:', error);
      throw error;
    }
  },

  addProjectFiles: async (projectId: string, files: File[]) => {
    try {
      const formData = new FormData();
      files.forEach(file => {
        formData.append('files', file);
      });
      
      const response = await api.post(`/api/projects/${projectId}/files`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    } catch (error) {
      console.error('Ошибка добавления файлов в проект:', error);
      throw error;
    }
  },

  getProjectFiles: async (projectId: string) => {
    try {
      const response = await api.get<ProjectFile[]>(`/api/projects/${projectId}/files`);
      return response.data || [];
    } catch (error) {
      console.error('Ошибка получения файлов проекта:', error);
      throw error;
    }
  },

  getProjectResults: async (projectId: string) => {
    try {
      const response = await api.get<ProjectResult[]>(`/api/projects/${projectId}/results`);
      return response.data || [];
    } catch (error) {
      console.error('Ошибка получения результатов проекта:', error);
      throw error;
    }
  },

  // Add method to save project result
  saveProjectResult: async (projectId: string, type: string, data: any) => {
    try {
      const response = await api.post(`/api/projects/${projectId}/results`, { type, data });
      return response.data;
    } catch (error) {
      console.error('Ошибка сохранения результата проекта:', error);
      throw error;
    }
  },

  scanProjectFiles: async (projectId: string) => {
    try {
      const response = await api.get<ScanResult>(`/api/projects/${projectId}/scan`);
      return response.data;
    } catch (error) {
      console.error('Ошибка сканирования файлов проекта:', error);
      throw error;
    }
  },

  deleteProjectFile: async (projectId: string, fileId: string) => {
    try {
      const response = await api.delete(`/api/projects/${projectId}/files/${fileId}`);
      return response.data;
    } catch (error) {
      console.error('Ошибка удаления файла из проекта:', error);
      throw error;
    }
  },

  scanDirectoryForProject: async (projectId: string, directoryPath: string) => {
    try {
      const formData = new FormData();
      formData.append('directory_path', directoryPath);
      
      const response = await api.post(`/api/projects/${projectId}/scan-directory`, formData);
      return response.data;
    } catch (error) {
      console.error('Ошибка сканирования директории для проекта:', error);
      throw error;
    }
  },

  // Pro Features API methods
  generateLetter: async (data: LetterData) => {
    try {
      const response = await api.post<LetterResponse>('/tools/generate_letter', data);
      return response.data || { status: 'error', file_path: '', message: 'Пустой ответ от сервера' };
    } catch (error) {
      console.error('Ошибка генерации письма:', error);
      throw error;
    }
  },

  autoBudget: async (data: BudgetData) => {
    try {
      const response = await api.post<BudgetResponse>('/tools/auto_budget', data);
      return response.data || { status: 'error', budget: null, total_cost: 0 };
    } catch (error) {
      console.error('Ошибка расчета бюджета:', error);
      throw error;
    }
  },

  generatePPR: async (data: PPRData) => {
    try {
      const response = await api.post<PPRResponse>('/tools/generate_ppr', data);
      return response.data || { status: 'error', ppr: null, stages_count: 0 };
    } catch (error) {
      console.error('Ошибка генерации ППР:', error);
      throw error;
    }
  },

  analyzeTender: async (data: TenderData) => {
    try {
      const response = await api.post<TenderResponse>('/tools/analyze_tender', { tool_args: data });
      return response.data || { status: 'error', analysis: null };
    } catch (error) {
      console.error('Ошибка анализа тендера:', error);
      throw error;
    }
  },

  parseGesnEstimate: async (data: FormData) => {
    try {
      const response = await api.post('/tools/parse_gesn_estimate', data, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data || {};
    } catch (error) {
      console.error('Ошибка парсинга сметы:', error);
      throw error;
    }
  },

  // File upload method
  uploadFile: async (file: File) => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      // Note: We don't set Content-Type header explicitly for FormData
      // The browser will automatically set it with the correct boundary
      const response = await api.post('/upload-file', formData);
      return response.data || { status: 'error', message: 'Пустой ответ от сервера' };
    } catch (error) {
      console.error('Ошибка загрузки файла:', error);
      throw error;
    }
  },

  // Add method to download file
  downloadFile: async (filePath: string) => {
    try {
      const response = await api.get(filePath, { responseType: 'blob' });
      return response.data;
    } catch (error) {
      console.error('Ошибка скачивания файла:', error);
      throw error;
    }
  },

  // Super Features API methods
  analyzeBIM: async (data: BIMAnalysisData) => {
    try {
      const response = await api.post<BIMAnalysisResponse>('/tools/analyze_bentley_model', data);
      return response.data || { 
        status: 'error', 
        elements_count: 0, 
        clashes: [], 
        violations: [],
        error: 'Пустой ответ от сервера'
      };
    } catch (error) {
      console.error('Ошибка анализа BIM модели:', error);
      throw error;
    }
  },

  exportDWG: async (data: DWGExportData) => {
    try {
      const response = await api.post<DWGExportResponse>('/tools/autocad_export', data);
      return response.data || { 
        status: 'error', 
        file_path: '', 
        message: 'Пустой ответ от сервера' 
      };
    } catch (error) {
      console.error('Ошибка экспорта DWG:', error);
      throw error;
    }
  },

  runMonteCarlo: async (data: MonteCarloData) => {
    try {
      const response = await api.post<MonteCarloResponse>('/tools/monte_carlo_sim', data);
      return response.data || { 
        status: 'error', 
        mean: 0, 
        std: 0, 
        p10: 0, 
        p90: 0, 
        hist_bins: [], 
        roi_stats: { mean: 0, p10: 0, p90: 0 } 
      };
    } catch (error) {
      console.error('Ошибка симуляции Монте-Карло:', error);
      throw error;
    }
  },



  updateNorms: async (data: { categories?: string[]; force?: boolean }) => {
    try {
      const response = await api.post<UpdateNormsResponse>('/norms-update', data);
      return response.data || { status: 'error', message: 'Пустой ответ от сервера' };
    } catch (error) {
      console.error('Ошибка обновления норм:', error);
      throw error;
    }
  },

  exportNorms: async (params: {
    format: string;
    category?: string;
    status?: string;
    type?: string;
    search?: string;
  }) => {
    try {
      const response = await api.get('/norms-export', { 
        params,
        responseType: 'blob'
      });
      return response.data;
    } catch (error) {
      console.error('Ошибка экспорта норм:', error);
      throw error;
    }
  },

  toggleCron: async (enabled: boolean) => {
    try {
      const response = await api.post<ResetDatabasesResponse>('/toggle-cron', { enabled });
      return response.data || { status: 'error', message: 'Пустой ответ от сервера' };
    } catch (error) {
      console.error('Ошибка изменения настроек cron:', error);
      throw error;
    }
  },

  // Reset databases
  resetDatabases: async () => {
    try {
      const response = await api.post<ResetDatabasesResponse>('/reset-databases');
      return response.data || { status: 'error', message: 'Пустой ответ от сервера' };
    } catch (error) {
      console.error('Ошибка сброса баз данных:', error);
      throw error;
    }
  },


  // Template management methods
  getTemplates: async (category?: string) => {
    try {
      const params = category ? { category } : {};
      const response = await api.get<Template[]>('/api/projects/templates', { params });
      return response.data || [];
    } catch (error) {
      console.error('Ошибка получения шаблонов:', error);
      throw error;
    }
  },

  createTemplate: async (data: TemplateCreate) => {
    try {
      const response = await api.post<Template>('/api/projects/templates', data);
      return response.data || null;
    } catch (error) {
      console.error('Ошибка создания шаблона:', error);
      throw error;
    }
  },

  updateTemplate: async (templateId: string, data: TemplateUpdate) => {
    try {
      const response = await api.put<Template>(`/api/projects/templates/${templateId}`, data);
      return response.data || null;
    } catch (error) {
      console.error('Ошибка обновления шаблона:', error);
      throw error;
    }
  },

  deleteTemplate: async (templateId: string) => {
    try {
      const response = await api.delete(`/api/projects/templates/${templateId}`);
      return response.data || null;
    } catch (error) {
      console.error('Ошибка удаления шаблона:', error);
      throw error;
    }
  },

  // Add method to get token
  getToken: async (username: string = 'admin', password: string = 'admin') => {
    try {
      // Create form data for OAuth2 password flow
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);
      formData.append('grant_type', 'password');
      
      // Use the main api instance but override baseURL for token requests
      // This ensures the request goes through the proxy correctly
      const response = await api.post<{access_token: string, token_type: string}>('/token', formData, {
        baseURL: '', // Override to use root path for proxy
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        // Remove auth header for token requests
        transformRequest: [(data, headers) => {
          delete headers?.Authorization;
          return data;
        }]
      });
      return response.data.access_token;
    } catch (error) {
      console.error('Ошибка получения токена:', error);
      throw error;
    }
  },

  // Advanced letter generation methods
  generateAdvancedLetter: async (data: AdvancedLetterData) => {
    try {
      const response = await api.post<LetterResponse>('/tools/generate_letter', { tool_args: data });
      return response.data || { status: 'error', file_path: '', message: 'Пустой ответ от сервера' };
    } catch (error) {
      console.error('Ошибка генерации письма:', error);
      throw error;
    }
  },

  // Text-to-Speech Tools
  textToSpeech: (data: any) => 
    apiService.executeUnifiedTool('text_to_speech', data),


  // Submit query to multi-agent system
  submitQuery: async (query: string) => {
    try {
      const response = await api.post('/submit_query', { 
        query,
        source: 'frontend',
        user_id: 'web_user',
        project_id: 'web'
      });
      return response.data;
    } catch (error) {
      console.error('Ошибка отправки запроса в multi-agent систему:', error);
      throw error;
    }
  },

  // Submit query to multi-agent system asynchronously
  submitQueryAsync: async (query: string) => {
    try {
      const response = await api.post('/submit_query_async', { 
        query,
        source: 'frontend',
        user_id: 'web_user',
        project_id: 'web'
      });
      return response.data;
    } catch (error) {
      console.error('Ошибка отправки асинхронного запроса в multi-agent систему:', error);
      throw error;
    }
  },

  // Get async query result
  getAsyncResult: async (taskId: string) => {
    try {
      const response = await api.get(`/submit_query_result?task_id=${taskId}`);
      return response.data;
    } catch (error) {
      console.error('Ошибка получения результата асинхронного запроса:', error);
      throw error;
    }
  },

  // ===== UNIFIED TOOLS SYSTEM =====
  
  // Universal tool execution with **kwargs support
  executeUnifiedTool: async (toolName: string, params: Record<string, any> = {}) => {
    try {
      // Filter out null/undefined/empty values for cleaner **kwargs
      const filteredParams = Object.fromEntries(
        Object.entries(params).filter(([_, value]) => 
          value !== null && value !== undefined && value !== ''
        )
      );

      const response = await api.post(`/tools/${toolName}`, filteredParams);
      
      // Ensure standardized response format
      return {
        status: response.data.status || 'success',
        data: response.data.data,
        files: response.data.files,
        metadata: response.data.metadata,
        error: response.data.error,
        execution_time: response.data.execution_time,
        tool_name: toolName,
        timestamp: response.data.timestamp || new Date().toISOString(),
        // !!! ИСПРАВЛЕНИЕ: Передаем result_type и result_table для ToolResultDisplay !!!
        result_type: response.data.result_type,
        result_title: response.data.result_title,
        result_content: response.data.result_content,
        result_table: response.data.result_table,
        result_chart_config: response.data.result_chart_config,
        ...response.data
      };
    } catch (error: any) {
      console.error(`Tool execution error for ${toolName}:`, error);
      
      // Return standardized error response
      return {
        status: 'error' as const,
        error: error.response?.data?.detail || error.message || 'Unknown error',
        tool_name: toolName,
        timestamp: new Date().toISOString(),
        metadata: {
          error_category: error.response?.status >= 500 ? 'server' : 'client',
          suggestions: 'Check tool parameters and try again'
        }
      };
    }
  },

  // Tool discovery with enhanced response
  discoverTools: async (category?: string) => {
    try {
      const url = category ? `/tools/list?category=${category}` : '/tools/list';
      const response = await api.get(url);
      
      // Ensure consistent response format
      return {
        status: 'success',
        data: {
          tools: response.data.tools || response.data.data?.tools || {},
          total_count: response.data.total_count || response.data.data?.total_count || 0,
          categories: response.data.categories || response.data.data?.categories || {}
        },
        timestamp: new Date().toISOString()
      };
    } catch (error: any) {
      console.error('Tool discovery error:', error);
      
      // Return empty tools list on error
      return {
        status: 'error',
        data: {
          tools: {},
          total_count: 0,
          categories: {}
        },
        error: error.message || 'Failed to discover tools',
        timestamp: new Date().toISOString()
      };
    }
  },

  // ===== TOOLS REGISTRY (modular plugins) =====
  listRegistryTools: async () => {
    const response = await api.get('/api/tools/registry/list');
    return response.data?.tools || [];
  },
  getRegistryToolInfo: async (name: string) => {
    const response = await api.get(`/api/tools/registry/info?name=${encodeURIComponent(name)}`);
    return response.data?.tool;
  },
  updateRegistryManifest: async (name: string, patch: any) => {
    const response = await api.post(`/api/tools/registry/update-manifest?name=${encodeURIComponent(name)}`, patch);
    return response.data;
  },
  enableRegistryTool: async (name: string) => {
    const response = await api.post(`/api/tools/registry/enable?name=${encodeURIComponent(name)}`);
    return response.data;
  },
  disableRegistryTool: async (name: string) => {
    const response = await api.post(`/api/tools/registry/disable?name=${encodeURIComponent(name)}`);
    return response.data;
  },
  reloadRegistry: async (name?: string) => {
    const url = name ? `/api/tools/registry/reload?name=${encodeURIComponent(name)}` : '/api/tools/registry/reload';
    const response = await api.post(url, {});
    return response.data;
  },
  registerRegistryTool: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post('/api/tools/registry/register', formData, { headers: { 'Content-Type': 'multipart/form-data' } });
    return response.data;
  },
  createRegistryTemplate: async (name: string, namespace: string = 'custom') => {
    const response = await api.post(`/api/tools/registry/create-template?name=${encodeURIComponent(name)}&namespace=${encodeURIComponent(namespace)}`);
    return response.data;
  },
  executeRegistryTool: async (name: string, params: Record<string, any>) => {
    const response = await api.post(`/api/tools/registry/execute?name=${encodeURIComponent(name)}`, params || {});
    return response.data;
  },

  // Get tool information with enhanced details
  getToolInfo: async (toolName: string) => {
    try {
      console.log(`[API] Fetching tool info for: ${toolName}`); // DEBUG
      // Add cache-busting parameter to force fresh data
      const response = await api.get(`/tools/${toolName}/info?_t=${Date.now()}`);
      console.log(`[API] Tool info response:`, response.data); // DEBUG
      return {
        status: 'success',
        data: response.data,
        timestamp: new Date().toISOString()
      };
    } catch (error: any) {
      console.error(`Tool info error for ${toolName}:`, error);
      return {
        status: 'error',
        error: error.message || `Failed to get info for ${toolName}`,
        timestamp: new Date().toISOString()
      };
    }
  },

  // Get tools by UI placement
  getToolsByPlacement: async (placement: 'dashboard' | 'tools' | 'service') => {
    try {
      const discovery = await apiService.discoverTools();
      const tools = Object.values(discovery.data.tools);
      return tools.filter((tool: any) => tool.ui_placement === placement);
    } catch (error) {
      console.error(`Error getting tools by placement ${placement}:`, error);
      return [];
    }
  },

  // Get dashboard tools (high-impact daily tools)
  getDashboardTools: async () => {
    return apiService.getToolsByPlacement('dashboard');
  },

  // Get professional tools (tools tab)
  getProfessionalTools: async () => {
    return apiService.getToolsByPlacement('tools');
  },
  reloadCoordinator: async () => {
    try {
      const response = await api.post('/api/settings/models/reload-coordinator', {});
      return response.data;
    } catch (error) {
      console.error('Ошибка перезагрузки координатора:', error);
      throw error;
    }
  },

  // ===== PROMPTS: Preview =====
  previewPrompt: async (role: string) => {
    try {
      const response = await api.get(`/api/settings/prompts/preview?role=${encodeURIComponent(role)}`);
      return response.data;
    } catch (error) {
      console.error('Ошибка предпросмотра промпта:', error);
      throw error;
    }
  },

  // ===== SETTINGS: Autotest =====
  runAutoTest: async (variants: Array<{ name: string; coordinator?: any; models_overrides?: any }>, queries?: string[], files?: { image?: string; audio?: string; document?: string }) => {
    try {
      const response = await api.post('/api/settings/autotest/run', { variants, queries, files });
      return response.data;
    } catch (error) {
      console.error('Ошибка автотестирования:', error);
      throw error;
    }
  },
  uploadAutotestFile: async (file: File, kind?: 'image' | 'audio' | 'document') => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      if (kind) formData.append('kind', kind);
      const response = await api.post('/api/settings/autotest/upload', formData, { headers: { 'Content-Type': 'multipart/form-data' } });
      return response.data;
    } catch (error) {
      console.error('Ошибка загрузки файла для автотеста:', error);
      throw error;
    }
  },

  // ===== UPDATED TOOL METHODS (using unified API) =====
  
  // Document Generation Tools
  generateLetterUnified: (data: LetterData) => 
    apiService.executeUnifiedTool('generate_letter', data),
    
  generateOfficialLetter: (data: any) => 
    apiService.executeUnifiedTool('generate_official_letter', data),

  // Financial Tools
  calculateEstimateUnified: (data: any) => 
    apiService.executeUnifiedTool('calculate_estimate', data),
    
  autoBudgetUnified: (data: BudgetData) => 
    apiService.executeUnifiedTool('auto_budget', data),
    
  calculateFinancialMetrics: (data: any) => 
    apiService.executeUnifiedTool('calculate_financial_metrics', data),
    
  parseEstimateUnified: (inputData: any, region?: string) => 
    apiService.executeUnifiedTool('parse_estimate_unified', { input_data: inputData, region }),

  // Analysis Tools
  analyzeImageUnified: (imagePath: string, analysisType?: string) => 
    apiService.executeUnifiedTool('analyze_image', { image_path: imagePath, analysis_type: analysisType }),
    
  analyzeTenderUnified: (data: TenderData) => 
    apiService.executeUnifiedTool('analyze_tender', data),
    
  comprehensiveAnalysis: (data: any) => 
    apiService.executeUnifiedTool('comprehensive_analysis', data),

  // Core RAG Tools
  searchRAGDatabase: (query: string, docTypes?: string[], k?: number) => 
    apiService.executeUnifiedTool('search_rag_database', { query, doc_types: docTypes, k }),
    
  checkNormative: (normativeCode: string, projectData?: any) => 
    apiService.executeUnifiedTool('check_normative', { normative_code: normativeCode, project_data: projectData }),

  // Project Management Tools
  generateConstructionSchedule: (works: any[], constraints?: any) => 
    apiService.executeUnifiedTool('generate_construction_schedule', { works, constraints }),
    
  createGanttChart: (tasks: any[], timeline?: any) => 
    apiService.executeUnifiedTool('create_gantt_chart', { tasks, timeline }),
    
  monteCarloSimulation: (projectData: any) => 
    apiService.executeUnifiedTool('monte_carlo_sim', { project_data: projectData }),

  // ===== RAG SYSTEM API METHODS =====
  
  // Получить метрики RAG системы
  getMetrics: async () => {
    try {
      const response = await api.get('/rag/metrics');
      return response.data;
    } catch (error) {
      console.error('Ошибка загрузки метрик RAG:', error);
      throw error;
    }
  },

  // Получить сводку по нормам
  getNormsSummary: async () => {
    try {
      const response = await api.get('/rag/norms/summary');
      return response.data;
    } catch (error) {
      console.error('Ошибка загрузки сводки по нормам:', error);
      throw error;
    }
  },

  // Получить список документов с пагинацией
  getNormsList: async (params: { page?: number; limit?: number } = {}) => {
    try {
      const response = await api.get('/rag/norms/list', { params });
      return response.data;
    } catch (error) {
      console.error('Ошибка загрузки списка документов:', error);
      throw error;
    }
  },

  // ===== QUEUE MANAGEMENT API METHODS =====
  
  // Получить активные задачи
  getActiveJobs: async () => {
    try {
      const response = await api.get('/queue/active');
      return response.data;
    } catch (error) {
      console.error('Ошибка загрузки активных задач:', error);
      throw error;
    }
  },

  // Получить завершенные задачи
  getCompletedJobs: async (limit: number = 100) => {
    try {
      const response = await api.get('/queue/completed', { params: { limit } });
      return response.data;
    } catch (error) {
      console.error('Ошибка загрузки завершенных задач:', error);
      throw error;
    }
  },

  // Отменить задачу
  cancelJob: async (jobId: string, reason?: string) => {
    try {
      const response = await api.post(`/queue/cancel/${jobId}`, { reason });
      return response.data;
    } catch (error) {
      console.error('Ошибка отмены задачи:', error);
      throw error;
    }
  },

  // Скачать результат задачи
  downloadJobResult: async (jobId: string) => {
    try {
      const response = await api.get(`/queue/download/${jobId}`, { 
        responseType: 'blob' 
      });
      return response.data;
    } catch (error) {
      console.error('Ошибка скачивания результата задачи:', error);
      throw error;
    }
  },

  // Получить статистику очереди
  getQueueStatistics: async () => {
    try {
      const response = await api.get('/queue/statistics');
      return response.data;
    } catch (error) {
      console.error('Ошибка загрузки статистики очереди:', error);
      throw error;
    }
  },

};

export default api;