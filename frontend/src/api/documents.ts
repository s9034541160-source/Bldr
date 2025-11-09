import apiClient from '../services/api'

export interface Document {
  id: number
  title: string
  file_name: string
  document_type: string
  version: number
  status: string
  created_at: string
}

export interface DocumentVersion {
  id: number
  version_number: number
  change_description: string
  created_at: string
  changed_by: number
}

export const documentsApi = {
  // Получение списка документов
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

  // Получение документа по ID
  getDocument: async (id: number) => {
    const response = await apiClient.get<Document>(`/sod/documents/${id}`)
    return response.data
  },

  // Загрузка документа
  uploadDocument: async (file: File, title: string, documentType: string, projectId?: number) => {
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
    })
    return response.data
  },

  // Скачивание документа
  downloadDocument: async (id: number, version?: number) => {
    const params = version ? { version } : {}
    const response = await apiClient.get(`/sod/documents/${id}/download`, {
      params,
      responseType: 'blob',
    })
    return response.data
  },

  // Получение версий документа
  getDocumentVersions: async (id: number) => {
    const response = await apiClient.get<DocumentVersion[]>(`/sod/documents/${id}/versions`)
    return response.data
  },

  // Создание новой версии
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

  // Откат к версии
  revertToVersion: async (id: number, versionNumber: number) => {
    const response = await apiClient.post(`/sod/documents/${id}/revert`, {
      version_number: versionNumber,
    })
    return response.data
  },

  // Удаление документа
  deleteDocument: async (id: number) => {
    await apiClient.delete(`/sod/documents/${id}`)
  },
}

