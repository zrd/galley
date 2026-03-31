import { apiClient } from './client';
import type { TagRead } from '../types';

export const tagsApi = {
  async list(): Promise<TagRead[]> {
    return apiClient.get<TagRead[]>('/tags/');
  },

  async getBySlug(slug: string): Promise<TagRead> {
    return apiClient.get<TagRead>(`/tags/${slug}`);
  },
};
