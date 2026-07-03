import { apiClient } from './client';
import type {
  StorePaginatedResponse,
  StoreBrowseItem,
  StoreManuscriptDetail,
  StoreEditionDetail,
  StoreAuthorListItem,
  StoreAuthorDetail,
  StoreGenreTree,
} from '../types';

export interface BrowseParams {
  page?: number;
  per_page?: number;
  q?: string;
  genre?: string;
  tag?: string;
  min_price?: number;
  max_price?: number;
  sort?: string;
}

function buildQs(params: Record<string, string | number | undefined>): string {
  const p = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== '') p.set(k, String(v));
  }
  const s = p.toString();
  return s ? `?${s}` : '';
}

export const storeApi = {
  async browseEbooks(params: BrowseParams = {}): Promise<StorePaginatedResponse<StoreBrowseItem>> {
    return apiClient.get<StorePaginatedResponse<StoreBrowseItem>>(`/store/ebooks${buildQs(params as Record<string, string | number | undefined>)}`);
  },

  async getListing(manuscriptId: string): Promise<StoreManuscriptDetail> {
    return apiClient.get<StoreManuscriptDetail>(`/store/ebooks/${manuscriptId}`);
  },

  async getEdition(ebookId: string): Promise<StoreEditionDetail> {
    return apiClient.get<StoreEditionDetail>(`/store/editions/${ebookId}`);
  },

  async browseAuthors(params: { page?: number; per_page?: number } = {}): Promise<StorePaginatedResponse<StoreAuthorListItem>> {
    return apiClient.get<StorePaginatedResponse<StoreAuthorListItem>>(`/store/authors${buildQs(params)}`);
  },

  async getAuthor(authorId: string): Promise<StoreAuthorDetail> {
    return apiClient.get<StoreAuthorDetail>(`/store/authors/${authorId}`);
  },

  async listGenres(): Promise<StoreGenreTree[]> {
    return apiClient.get<StoreGenreTree[]>('/store/genres');
  },
};
