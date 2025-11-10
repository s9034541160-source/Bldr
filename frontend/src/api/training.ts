import apiClient from '../services/api'

export interface TrainingDataset {
  id: number
  name: string
  description?: string
  status: string
  total_examples: number
  created_at?: string
  updated_at?: string
  config?: Record<string, unknown>
  sample_preview?: Array<Record<string, unknown>>
}

export interface TrainingJob {
  id: number
  dataset_id: number
  base_model_id: string
  status: string
  metrics?: Record<string, unknown>
  adapter_path?: string
  artifact_path?: string
  gguf_path?: string
  model_id?: string
  validation_status?: string
  validation_metrics?: Record<string, unknown>
  created_at?: string
  started_at?: string
  completed_at?: string
  output_path?: string
}

export interface CreateDatasetPayload {
  name: string
  description?: string
  document_ids: number[]
  questions_per_chunk?: number
  total_pairs_target?: number
  qa_model_id?: string
  prompt_template?: string
}

export interface CreateJobPayload {
  dataset_id: number
  base_model_id: string
  model_id?: string
  hyperparameters?: Record<string, unknown>
  validation_prompts?: string[]
}

export interface TrainingJobArtifacts {
  job_id: number
  model_id?: string
  adapter_url?: string
  gguf_url?: string
}

export const trainingApi = {
  listDatasets: async (): Promise<TrainingDataset[]> => {
    const response = await apiClient.get<TrainingDataset[]>('/training/datasets')
    return response.data
  },
  createDataset: async (payload: CreateDatasetPayload): Promise<TrainingDataset> => {
    const response = await apiClient.post<TrainingDataset>('/training/datasets', payload)
    return response.data
  },
  listJobs: async (): Promise<TrainingJob[]> => {
    const response = await apiClient.get<TrainingJob[]>('/training/jobs')
    return response.data
  },
  createJob: async (payload: CreateJobPayload): Promise<TrainingJob> => {
    const response = await apiClient.post<TrainingJob>('/training/jobs', payload)
    return response.data
  },
  getJobArtifacts: async (jobId: number): Promise<TrainingJobArtifacts> => {
    const response = await apiClient.get<TrainingJobArtifacts>(`/training/jobs/${jobId}/artifacts`)
    return response.data
  },
}


