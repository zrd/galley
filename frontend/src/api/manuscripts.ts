import { apiClient } from './client';
import type {
  Manuscript,
  ManuscriptListItem,
  ManuscriptUpdateRequest,
  SourceFormat,
} from '../types';

export const manuscriptsApi = {
  async list(includeDeleted = false): Promise<ManuscriptListItem[]> {
    const params = includeDeleted ? '?include_deleted=true' : '';
    return apiClient.get<ManuscriptListItem[]>(`/manuscripts/${params}`);
  },

  async get(id: string): Promise<Manuscript> {
    return apiClient.get<Manuscript>(`/manuscripts/${id}`);
  },

  async create(data: {
    title: string;
    description?: string;
    source_format: SourceFormat;
    file: File;
  }): Promise<Manuscript> {
    const formData = new FormData();
    formData.append('title', data.title);
    formData.append('source_format', data.source_format);
    if (data.description) {
      formData.append('description', data.description);
    }
    formData.append('file', data.file);

    return apiClient.postFormData<Manuscript>('/manuscripts/', formData);
  },

  async update(id: string, data: ManuscriptUpdateRequest): Promise<Manuscript> {
    return apiClient.put<Manuscript>(`/manuscripts/${id}`, data);
  },

  async updateFile(id: string, file: File, sourceFormat: SourceFormat): Promise<Manuscript> {
    const formData = new FormData();
    formData.append('source_format', sourceFormat);
    formData.append('file', file);

    const response = await fetch(
      `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/manuscripts/${id}/file`,
      {
        method: 'PUT',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        },
        body: formData,
      }
    );

    if (!response.ok) {
      throw new Error(`Failed to update file: ${response.statusText}`);
    }

    return response.json();
  },

  async markReady(id: string): Promise<Manuscript> {
    return apiClient.post<Manuscript>(`/manuscripts/${id}/ready`);
  },

  async archive(id: string): Promise<Manuscript> {
    return apiClient.post<Manuscript>(`/manuscripts/${id}/archive`);
  },

  async unarchive(id: string): Promise<Manuscript> {
    return apiClient.post<Manuscript>(`/manuscripts/${id}/unarchive`);
  },

  async delete(id: string): Promise<void> {
    return apiClient.delete(`/manuscripts/${id}`);
  },

  async restore(id: string): Promise<Manuscript> {
    return apiClient.post<Manuscript>(`/manuscripts/${id}/restore`);
  },
};
