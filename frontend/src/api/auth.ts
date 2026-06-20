import { apiClient } from './client';
import type { LoginRequest, RegisterRequest, TokenResponse, Author, AuthorUpdateRequest } from '../types';

export const authApi = {
  async login(data: LoginRequest): Promise<TokenResponse> {
    return apiClient.post<TokenResponse>('/auth/login', data);
  },

  async register(data: RegisterRequest): Promise<TokenResponse> {
    return apiClient.post<TokenResponse>('/auth/register', data);
  },

  async refresh(refreshToken: string): Promise<TokenResponse> {
    return apiClient.post<TokenResponse>('/auth/refresh', { refresh_token: refreshToken });
  },

  async getMe(): Promise<Author> {
    return apiClient.get<Author>('/authors/me');
  },

  async updateProfile(data: AuthorUpdateRequest): Promise<Author> {
    return apiClient.put<Author>('/authors/me', data);
  },
};
