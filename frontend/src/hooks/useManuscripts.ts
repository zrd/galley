import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { manuscriptsApi } from '../api/manuscripts';
import { ebooksApi } from '../api/ebooks';
import type { ManuscriptUpdateRequest, SourceFormat, OutputFormat } from '../types';

export function useManuscripts(includeDeleted = false) {
  return useQuery({
    queryKey: ['manuscripts', { includeDeleted }],
    queryFn: () => manuscriptsApi.list(includeDeleted),
  });
}

export function useManuscript(id: string) {
  return useQuery({
    queryKey: ['manuscripts', id],
    queryFn: () => manuscriptsApi.get(id),
    enabled: !!id,
  });
}

export function useCreateManuscript() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: {
      title: string;
      description?: string;
      source_format: SourceFormat;
      file: File;
    }) => manuscriptsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['manuscripts'] });
    },
  });
}

export function useUpdateManuscript() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: ManuscriptUpdateRequest }) =>
      manuscriptsApi.update(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['manuscripts'] });
      queryClient.invalidateQueries({ queryKey: ['manuscripts', id] });
    },
  });
}

export function useMarkReady() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => manuscriptsApi.markReady(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['manuscripts'] });
      queryClient.invalidateQueries({ queryKey: ['manuscripts', id] });
    },
  });
}

export function useArchiveManuscript() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => manuscriptsApi.archive(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['manuscripts'] });
      queryClient.invalidateQueries({ queryKey: ['manuscripts', id] });
    },
  });
}

export function useDeleteManuscript() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => manuscriptsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['manuscripts'] });
    },
  });
}

export function useGenerateEbook() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ manuscriptId, formats }: { manuscriptId: string; formats: OutputFormat[] }) =>
      ebooksApi.generate(manuscriptId, formats),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ebooks'] });
    },
  });
}
