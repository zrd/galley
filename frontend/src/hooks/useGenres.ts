import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { genresApi } from '../api/genres';
import type { GenreCreateRequest } from '../types';

export function useGenreTree() {
  return useQuery({
    queryKey: ['genres', 'tree'],
    queryFn: () => genresApi.tree(),
  });
}

export function useGenreList() {
  return useQuery({
    queryKey: ['genres', 'list'],
    queryFn: () => genresApi.list(),
  });
}

export function useCreateGenre() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: GenreCreateRequest) => genresApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['genres', 'tree'] });
      queryClient.invalidateQueries({ queryKey: ['genres', 'list'] });
    },
  });
}
