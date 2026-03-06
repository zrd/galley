import { useState } from 'react';
import { useGenreTree, useGenreList, useCreateGenre } from '../hooks/useGenres';
import { useAuth } from '../hooks/useAuth';
import { ApiError } from '../api/client';
import type { GenreTree } from '../types';

function GenreNode({ genre, depth = 0 }: { genre: GenreTree; depth?: number }) {
  const [expanded, setExpanded] = useState(depth === 0);
  const hasChildren = genre.children.length > 0;

  return (
    <div className={depth > 0 ? 'ml-6' : ''}>
      <div className="flex items-start py-2">
        <button
          onClick={() => setExpanded(!expanded)}
          className="mr-2 mt-0.5 w-4 shrink-0 text-gray-400 hover:text-gray-600"
          aria-label={expanded ? 'Collapse' : 'Expand'}
          disabled={!hasChildren}
        >
          {hasChildren ? (expanded ? '▾' : '▸') : '·'}
        </button>
        <div>
          <span className="font-medium text-gray-900">{genre.name}</span>
          {genre.description && (
            <p className="mt-0.5 text-sm text-gray-500">{genre.description}</p>
          )}
        </div>
      </div>
      {hasChildren && expanded && (
        <div className="border-l border-gray-200">
          {genre.children.map((child) => (
            <GenreNode key={child.id} genre={child} depth={depth + 1} />
          ))}
        </div>
      )}
    </div>
  );
}

export function Genres() {
  const { data: tree, isLoading, error } = useGenreTree();
  const { data: genreList } = useGenreList();
  const { isAuthenticated } = useAuth();
  const createGenre = useCreateGenre();

  const [showForm, setShowForm] = useState(false);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [parentId, setParentId] = useState('');
  const [formError, setFormError] = useState<string | null>(null);

  const resetForm = () => {
    setName('');
    setDescription('');
    setParentId('');
    setFormError(null);
    setShowForm(false);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    if (!name.trim()) {
      setFormError('Name is required.');
      return;
    }

    try {
      await createGenre.mutateAsync({
        name: name.trim(),
        description: description.trim() || undefined,
        parent_id: parentId ? Number(parentId) : undefined,
      });
      resetForm();
    } catch (err) {
      if (err instanceof ApiError) {
        const data = err.data as { detail?: string };
        setFormError(data?.detail ?? `Error ${err.status}: ${err.statusText}`);
      } else {
        setFormError('Failed to create genre. Please try again.');
      }
    }
  };

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <div className="text-gray-600">Loading genres...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded bg-red-50 p-4 text-red-600">
        Failed to load genres. Please try again.
      </div>
    );
  }

  return (
    <div>
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Genre Browser</h1>
          <p className="mt-2 text-gray-600">Browse the genre hierarchy.</p>
        </div>
        {isAuthenticated && !showForm && (
          <button
            onClick={() => setShowForm(true)}
            className="rounded bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700"
          >
            Add Genre
          </button>
        )}
      </div>

      {showForm && (
        <div className="mb-8 rounded-lg border border-gray-200 bg-white px-6 py-5 shadow">
          <h2 className="mb-4 text-lg font-semibold">New Genre</h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            {formError && (
              <div className="rounded bg-red-50 p-4 text-red-600">{formError}</div>
            )}

            <div>
              <label htmlFor="genre-name" className="block text-sm font-medium text-gray-700">
                Name
              </label>
              <input
                id="genre-name"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                className="mt-1 block w-full rounded border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </div>

            <div>
              <label htmlFor="genre-description" className="block text-sm font-medium text-gray-700">
                Description (optional)
              </label>
              <textarea
                id="genre-description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={3}
                className="mt-1 block w-full rounded border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </div>

            <div>
              <label htmlFor="genre-parent" className="block text-sm font-medium text-gray-700">
                Parent genre (optional)
              </label>
              <select
                id="genre-parent"
                value={parentId}
                onChange={(e) => setParentId(e.target.value)}
                className="mt-1 block w-full rounded border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              >
                <option value="">— none —</option>
                {genreList?.map((g) => (
                  <option key={g.id} value={g.id}>
                    {g.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex justify-end space-x-4">
              <button
                type="button"
                onClick={resetForm}
                className="rounded border border-gray-300 bg-white px-4 py-2 font-medium text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={createGenre.isPending}
                className="rounded bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700 disabled:opacity-50"
              >
                {createGenre.isPending ? 'Saving...' : 'Add Genre'}
              </button>
            </div>
          </form>
        </div>
      )}

      {tree?.length === 0 ? (
        <div className="rounded border-2 border-dashed border-gray-300 p-12 text-center">
          <p className="text-gray-600">No genres have been added yet.</p>
        </div>
      ) : (
        <div className="rounded-lg border border-gray-200 bg-white px-6 py-4 shadow">
          {tree?.map((genre) => (
            <GenreNode key={genre.id} genre={genre} />
          ))}
        </div>
      )}
    </div>
  );
}
