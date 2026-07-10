import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ebooksApi } from '../api/ebooks';

export function useEbooks(includeDeleted = false) {
  return useQuery({
    queryKey: ['ebooks', { includeDeleted }],
    queryFn: () => ebooksApi.list(includeDeleted),
  });
}

export function useEbooksByManuscript(manuscriptId: string) {
  const { data: allEbooks, ...rest } = useEbooks();

  const ebooks = allEbooks?.filter(
    (ebook) => ebook.manuscript_id === manuscriptId
  );

  return { data: ebooks, ...rest };
}

export function useDeleteEbook() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => ebooksApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ebooks'] });
    },
  });
}

export function useRestoreEbook() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => ebooksApi.restore(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ebooks'] });
    },
  });
}

export function useUpdateEbookPrice() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      id,
      ...update
    }: {
      id: string;
      list_price_cents?: number | null;
      sale_price_cents?: number | null;
      unlisted_download_limit?: number | null;
    }) => ebooksApi.updatePrice(id, update),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ebooks'] });
      queryClient.invalidateQueries({ queryKey: ['store'] });
    },
  });
}

export function usePublishEbook() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => ebooksApi.publish(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ebooks'] });
      queryClient.invalidateQueries({ queryKey: ['store'] });
    },
  });
}

export function useUnlistEbook() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => ebooksApi.unlist(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ebooks'] });
      queryClient.invalidateQueries({ queryKey: ['store'] });
    },
  });
}

export function useMakePrivateEbook() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => ebooksApi.makePrivate(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ebooks'] });
      queryClient.invalidateQueries({ queryKey: ['store'] });
    },
  });
}
