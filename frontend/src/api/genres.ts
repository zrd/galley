import { apiClient } from './client';
import { GenreTree, GenreListItem, GenreRead, GenreCreateRequest } from '../types';

export const genresApi = {
  async list(): Promise<GenreListItem[]> {
    return apiClient.get<GenreListItem[]>('/genres/');
  },

  async tree(): Promise<GenreTree[]> {
    return apiClient.get<GenreTree[]>('/genres/tree');
  },

  async create(data: GenreCreateRequest): Promise<GenreRead> {
    const formData = new FormData();
    formData.append('name', data.name);
    if (data.description) formData.append('description', data.description);
    if (data.parent_id != null) formData.append('parent_id', String(data.parent_id));
    return apiClient.postFormData<GenreRead>('/genres/', formData);
  },
};
