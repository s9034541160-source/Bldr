import apiClient from '../services/api'

export interface Document {
  id: number
  title: string
  file_name: string
  document_type: string
  version: number
  status: string
  created_at: string
  mime_type?: string
  metadata?: Record<string, unknown>
}

export interface DocumentVersion {
  id: number
  version_number: number
  change_description: string
  created_at: string
  changed_by: number
}

export interface DocumentComparison {
  document_id: number
  base_version: {
    version_number: number
    file_hash: string
    file_size: number
    change_description: string
    created_at: string | null
  }
  target_version: {
    version_number: number
    file_hash: string
    file_size: number
    change_description: string
    created_at: string | null
  }
  hash_equal: boolean
  size_difference: number
  diff_preview: string[]
}

export const documentsApi = {
  getDocuments: async (params?: {
    query?: string
    document_type?: string
    project_id?: number
    status?: string
    search_type?: 'fulltext' | 'semantic' | 'hybrid'
    limit?: number
  }) => {
    const response = await apiClient.get<Document[]>('/sod/documents', { params })
    return response.data
  },

  getDocument: async (id: number) => {
    const response = await apiClient.get<Document>(`/sod/documents/${id}`)
    return response.data
  },

  uploadDocument: async (
    file: File,
    title: string,
    documentType: string,
    projectId?: number,
    onUploadProgress?: (event: ProgressEvent) => void,
  ) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('title', title)
    formData.append('document_type', documentType)
    if (projectId) {
      formData.append('project_id', projectId.toString())
    }

    const response = await apiClient.post<Document>('/sod/documents', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress,
    })
    return response.data
  },

  downloadDocument: async (id: number, version?: number) => {
    const params = version ? { version } : {}
    const response = await apiClient.get(`/sod/documents/${id}/download`, {
      params,
      responseType: 'blob',
    })
    return response.data
  },

  getDocumentVersions: async (id: number) => {
    const response = await apiClient.get<DocumentVersion[]>(`/sod/documents/${id}/versions`)
    return response.data
  },

  createVersion: async (id: number, file: File, changeDescription: string) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('change_description', changeDescription)

    const response = await apiClient.post(`/sod/documents/${id}/versions`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  revertToVersion: async (id: number, versionNumber: number) => {
    const form = new FormData()
    form.append('version_number', versionNumber.toString())
    const response = await apiClient.post(`/sod/documents/${id}/revert`, form)
    return response.data
  },

  deleteDocument: async (id: number) => {
    await apiClient.delete(`/sod/documents/${id}`)
  },

  compareVersions: async (id: number, baseVersion: number, targetVersion: number) => {
    const response = await apiClient.get<DocumentComparison>(`/sod/documents/${id}/compare`, {
      params: {
        base_version: baseVersion,
        target_version: targetVersion,
      },
    })
    return response.data
  },

  updateMetadata: async (
    id: number,
    payload: {
      metadata?: Record<string, unknown>
      tags?: string[]
      linked_document_ids?: number[]
    }
  ) => {
    const response = await apiClient.patch<Document>(`/sod/documents/${id}/metadata`, payload)
    return response.data
  },
}

