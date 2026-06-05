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
    genre_ids?: number[];
    tag_names?: string[];
  }): Promise<Manuscript> {
    const formData = new FormData();
    formData.append('title', data.title);
    formData.append('source_format', data.source_format);
    if (data.description) {
      formData.append('description', data.description);
    }
    formData.append('file', data.file);
    for (const id of data.genre_ids ?? []) {
      formData.append('genre_ids', String(id));
    }
    for (const name of data.tag_names ?? []) {
      formData.append('tag_names', name);
    }

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

  async markDraft(id: string): Promise<Manuscript> {
    return apiClient.post<Manuscript>(`/manuscripts/${id}/draft`);
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

  async uploadCover(id: string, file: File): Promise<Manuscript> {
    const formData = new FormData();
    formData.append('file', file);
    const response = await fetch(
      `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/manuscripts/${id}/cover`,
      {
        method: 'PUT',
        headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` },
        body: formData,
      }
    );
    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      throw new Error((data as { detail?: string }).detail ?? 'Failed to upload cover');
    }
    return response.json();
  },

  async deleteCover(id: string): Promise<Manuscript> {
    return apiClient.delete<Manuscript>(`/manuscripts/${id}/cover`);
  },
};
