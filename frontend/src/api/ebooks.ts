import { apiClient } from './client';
import type { Ebook, EbookListItem, OutputFormat } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const ebooksApi = {
  async list(includeDeleted = false): Promise<EbookListItem[]> {
    const params = includeDeleted ? '?include_deleted=true' : '';
    return apiClient.get<EbookListItem[]>(`/ebooks/${params}`);
  },

  async get(id: string): Promise<Ebook> {
    return apiClient.get<Ebook>(`/ebooks/${id}`);
  },

  async generate(manuscriptId: string, outputFormats: OutputFormat[]): Promise<Ebook[]> {
    return apiClient.post<Ebook[]>(`/ebooks/manuscripts/${manuscriptId}/generate`, {
      output_formats: outputFormats,
    });
  },

  async delete(id: string): Promise<void> {
    return apiClient.delete(`/ebooks/${id}`);
  },

  async restore(id: string): Promise<Ebook> {
    return apiClient.post<Ebook>(`/ebooks/${id}/restore`);
  },

  async updatePrice(
    id: string,
    update: { list_price_cents?: number | null; sale_price_cents?: number | null },
  ): Promise<Ebook> {
    return apiClient.patch<Ebook>(`/ebooks/${id}`, update);
  },

  async publish(id: string): Promise<Ebook> {
    return apiClient.post<Ebook>(`/ebooks/${id}/publish`);
  },

  async unlist(id: string): Promise<Ebook> {
    return apiClient.post<Ebook>(`/ebooks/${id}/unlist`);
  },

  async makePrivate(id: string): Promise<Ebook> {
    return apiClient.post<Ebook>(`/ebooks/${id}/make-private`);
  },

  getDownloadUrl(id: string): string {
    return `${API_BASE_URL}/ebooks/${id}/download`;
  },
};
