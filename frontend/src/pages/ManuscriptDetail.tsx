import { useState, useRef } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  useManuscript,
  useUpdateManuscript,
  useMarkReady,
  useMarkDraft,
  useArchiveManuscript,
  useUnarchiveManuscript,
  useDeleteManuscript,
  useGenerateEbook,
} from '../hooks/useManuscripts';
import { useEbooksByManuscript } from '../hooks/useEbooks';
import { useGenreList } from '../hooks/useGenres';
import { ebooksApi } from '../api/ebooks';
import { manuscriptsApi } from '../api/manuscripts';
import { ApiError } from '../api/client';
import type { OutputFormat, ManuscriptState } from '../types';

function TagInput({
  tags,
  onChange,
}: {
  tags: string[];
  onChange: (tags: string[]) => void;
}) {
  const [input, setInput] = useState('');

  const addTag = () => {
    const trimmed = input.trim();
    if (trimmed && !tags.includes(trimmed)) {
      onChange([...tags, trimmed]);
    }
    setInput('');
  };

  const removeTag = (name: string) => {
    onChange(tags.filter((t) => t !== name));
  };

  return (
    <div>
      <div className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              e.preventDefault();
              addTag();
            }
          }}
          placeholder="Add a tag…"
          className="block flex-1 rounded border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        />
        <button
          type="button"
          onClick={addTag}
          className="rounded border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
        >
          Add
        </button>
      </div>
      {tags.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1">
          {tags.map((tag) => (
            <span
              key={tag}
              className="inline-flex items-center gap-1 rounded-full bg-purple-100 px-2 py-0.5 text-xs font-medium text-purple-800"
            >
              {tag}
              <button
                type="button"
                onClick={() => removeTag(tag)}
                className="text-purple-500 hover:text-purple-700"
              >
                &times;
              </button>
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

const stateColors: Record<ManuscriptState, string> = {
  draft: 'bg-yellow-100 text-yellow-800',
  ready: 'bg-green-100 text-green-800',
  archived: 'bg-gray-100 text-gray-800',
};

export function ManuscriptDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const { data: manuscript, isLoading, error, refetch } = useManuscript(id!);
  const { data: ebooks, isLoading: ebooksLoading } = useEbooksByManuscript(id!);
  const updateManuscript = useUpdateManuscript();
  const markReady = useMarkReady();
  const markDraft = useMarkDraft();
  const archiveManuscript = useArchiveManuscript();
  const unarchiveManuscript = useUnarchiveManuscript();
  const deleteManuscript = useDeleteManuscript();
  const generateEbook = useGenerateEbook();

  const { data: genres } = useGenreList();

  const [isEditing, setIsEditing] = useState(false);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [selectedGenreIds, setSelectedGenreIds] = useState<number[]>([]);
  const [tagNames, setTagNames] = useState<string[]>([]);
  const [selectedFormats, setSelectedFormats] = useState<OutputFormat[]>(['epub']);
  const [downloadErrors, setDownloadErrors] = useState<Record<string, string>>({});

  const coverFileInputRef = useRef<HTMLInputElement>(null);
  const [isUploadingCover, setIsUploadingCover] = useState(false);
  const [isDeletingCover, setIsDeletingCover] = useState(false);
  const [coverError, setCoverError] = useState<string | null>(null);

  const handleEdit = () => {
    if (manuscript) {
      setTitle(manuscript.title);
      setDescription(manuscript.description || '');
      setSelectedGenreIds(manuscript.genres.map((g) => g.id));
      setTagNames(manuscript.tags.map((t) => t.name));
      setIsEditing(true);
    }
  };

  const handleSave = async () => {
    if (!id) return;
    await updateManuscript.mutateAsync({
      id,
      data: { title, description: description || undefined, genre_ids: selectedGenreIds, tag_names: tagNames },
    });
    setIsEditing(false);
  };

  const handleMarkReady = async () => {
    if (!id) return;
    await markReady.mutateAsync(id);
  };

  const handleMarkDraft = async () => {
    if (!id) return;
    if (!window.confirm('Revert to Draft? Ebook downloads will be temporarily unavailable until you mark it Ready again.')) return;
    await markDraft.mutateAsync(id);
  };

  const handleArchive = async () => {
    if (!id) return;
    if (!window.confirm('Archive this manuscript? It will no longer appear in active listings.')) return;
    await archiveManuscript.mutateAsync(id);
  };

  const handleUnarchive = async () => {
    if (!id) return;
    await unarchiveManuscript.mutateAsync(id);
  };

  const handleDownloadEbook = async (ebookId: string) => {
    const url = ebooksApi.getDownloadUrl(ebookId);
    const response = await fetch(url);
    if (!response.ok) {
      setDownloadErrors((prev) => ({
        ...prev,
        [ebookId]: response.status === 403 ? 'Temporarily unavailable' : 'Download failed',
      }));
      return;
    }
    setDownloadErrors((prev) => { const next = { ...prev }; delete next[ebookId]; return next; });
    const cd = response.headers.get('Content-Disposition');
    const match = cd?.match(/filename\*=UTF-8''([^;]+)/i) ?? cd?.match(/filename="([^"]+)"/i);
    const filename = match ? decodeURIComponent(match[1]) : 'download.epub';
    const blob = await response.blob();
    const objectUrl = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = objectUrl;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(objectUrl);
  };

  const handleDelete = async () => {
    if (!id) return;
    if (window.confirm('Are you sure you want to delete this manuscript?')) {
      await deleteManuscript.mutateAsync(id);
      navigate('/dashboard');
    }
  };

  const handleGenerateEbook = async () => {
    if (!id || selectedFormats.length === 0) return;
    try {
      const ebooks = await generateEbook.mutateAsync({
        manuscriptId: id,
        formats: selectedFormats,
      });
      alert(`Generated ${ebooks.length} ebook(s) successfully!`);
    } catch (err) {
      const detail =
        err instanceof ApiError &&
        typeof err.data === 'object' &&
        err.data !== null &&
        'detail' in err.data
          ? String((err.data as { detail: unknown }).detail)
          : null;
      alert(detail ?? 'Failed to generate ebook.');
    }
  };

  const handleCoverFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !id) return;
    setIsUploadingCover(true);
    setCoverError(null);
    try {
      await manuscriptsApi.uploadCover(id, file);
      await refetch();
    } catch (err) {
      setCoverError(err instanceof Error ? err.message : 'Failed to upload cover');
    } finally {
      setIsUploadingCover(false);
      if (coverFileInputRef.current) coverFileInputRef.current.value = '';
    }
  };

  const handleDownloadCover = async () => {
    if (!manuscript?.cover_image_url) return;
    const url = `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}${manuscript?.cover_image_url}`;
    const response = await fetch(url, {
      headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` },
    });
    const blob = await response.blob();
    const objectUrl = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = objectUrl;
    a.download = `${manuscript?.title}-cover`;
    a.click();
    URL.revokeObjectURL(objectUrl);
  };

  const handleDeleteCover = async () => {
    if (!id || !window.confirm('Remove this cover image?')) return;
    setIsDeletingCover(true);
    setCoverError(null);
    try {
      await manuscriptsApi.deleteCover(id);
      await refetch();
    } catch (err) {
      setCoverError(err instanceof Error ? err.message : 'Failed to remove cover');
    } finally {
      setIsDeletingCover(false);
    }
  };

  const toggleFormat = (format: OutputFormat) => {
    setSelectedFormats((prev) =>
      prev.includes(format)
        ? prev.filter((f) => f !== format)
        : [...prev, format]
    );
  };

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <div className="text-gray-600">Loading manuscript...</div>
      </div>
    );
  }

  if (error || !manuscript) {
    return (
      <div className="rounded bg-red-50 p-4 text-red-600">
        Failed to load manuscript.{' '}
        <Link to="/dashboard" className="underline">
          Return to dashboard
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl">
      <div className="mb-4">
        <Link to="/dashboard" className="text-blue-600 hover:underline">
          &larr; Back to Dashboard
        </Link>
      </div>

      <div className="rounded-lg border border-gray-200 bg-white p-6 shadow">
        {isEditing ? (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Title
              </label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="mt-1 block w-full rounded border border-gray-300 px-3 py-2"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Description
              </label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={3}
                className="mt-1 block w-full rounded border border-gray-300 px-3 py-2"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Genres</label>
              <div className="mt-1 max-h-48 overflow-y-auto rounded border border-gray-200 p-2 space-y-1">
                {genres?.map((genre) => (
                  <label key={genre.id} className="flex items-center">
                    <input
                      type="checkbox"
                      checked={selectedGenreIds.includes(genre.id)}
                      onChange={() => setSelectedGenreIds((prev) =>
                        prev.includes(genre.id)
                          ? prev.filter((id) => id !== genre.id)
                          : [...prev, genre.id]
                      )}
                      className="mr-2"
                    />
                    <span className="text-sm">{genre.name}</span>
                  </label>
                ))}
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Tags</label>
              <div className="mt-1">
                <TagInput tags={tagNames} onChange={setTagNames} />
              </div>
            </div>
            <div className="flex space-x-2">
              <button
                onClick={handleSave}
                disabled={updateManuscript.isPending}
                className="rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:opacity-50"
              >
                Save
              </button>
              <button
                onClick={() => setIsEditing(false)}
                className="rounded border border-gray-300 px-4 py-2 hover:bg-gray-50"
              >
                Cancel
              </button>
            </div>
          </div>
        ) : (
          <>
            <div className="mb-6 flex items-start justify-between">
              <div>
                <h1 className="text-2xl font-bold">{manuscript.title}</h1>
                <p className="mt-1 text-gray-600">
                  {manuscript.description || 'No description'}
                </p>
              </div>
              <span
                className={`rounded-full px-3 py-1 text-sm font-semibold ${stateColors[manuscript.state]}`}
              >
                {manuscript.state}
              </span>
            </div>

            <div className="mb-6 grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-500">Format:</span>{' '}
                <span className="font-medium">
                  {manuscript.source_format.toUpperCase()}
                </span>
              </div>
              <div>
                <span className="text-gray-500">Created:</span>{' '}
                <span className="font-medium">
                  {new Date(manuscript.created_at).toLocaleString()}
                </span>
              </div>
              <div>
                <span className="text-gray-500">Updated:</span>{' '}
                <span className="font-medium">
                  {new Date(manuscript.updated_at).toLocaleString()}
                </span>
              </div>
            </div>

            <div className="mb-2">
              <span className="text-sm text-gray-500">Genres: </span>
              {manuscript.genres?.length > 0 ? (
                manuscript.genres.map((g) => (
                  <span key={g.id} className="mr-1 inline-flex rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-800">
                    {g.name}
                  </span>
                ))
              ) : (
                <span className="text-sm text-gray-400">None</span>
              )}
            </div>

            <div className="mb-4">
              <span className="text-sm text-gray-500">Tags: </span>
              {manuscript.tags?.length > 0 ? (
                manuscript.tags.map((t) => (
                  <span key={t.id} className="mr-1 inline-flex rounded-full bg-purple-100 px-2 py-0.5 text-xs font-medium text-purple-800">
                    {t.name}
                  </span>
                ))
              ) : (
                <span className="text-sm text-gray-400">None</span>
              )}
            </div>

            <div className="mb-4">
              <span className="block text-sm font-medium text-gray-700 mb-2">Cover Image</span>
              {manuscript.cover_image_url ? (
                <div className="flex items-start gap-4">
                  <img
                    src={`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}${manuscript.cover_image_url}?t=${manuscript.updated_at}`}
                    alt="Cover"
                    className="h-40 w-auto rounded border border-gray-200 shadow-sm object-cover"
                  />
                  <div className="flex flex-col gap-2">
                    <button
                      type="button"
                      onClick={handleDownloadCover}
                      className="rounded border border-gray-300 px-3 py-1 text-center text-sm hover:bg-gray-50"
                    >
                      Download
                    </button>
                    <button
                      type="button"
                      onClick={handleDeleteCover}
                      disabled={isDeletingCover}
                      className="rounded border border-red-300 px-3 py-1 text-sm text-red-600 hover:bg-red-50 disabled:opacity-50"
                    >
                      {isDeletingCover ? 'Removing…' : 'Remove'}
                    </button>
                  </div>
                </div>
              ) : (
                <p className="text-sm text-gray-400">No cover image</p>
              )}
              <div className="mt-2 flex items-center gap-3">
                <input
                  ref={coverFileInputRef}
                  type="file"
                  accept=".jpg,.jpeg,.png"
                  onChange={handleCoverFileChange}
                  className="hidden"
                />
                <button
                  type="button"
                  onClick={() => coverFileInputRef.current?.click()}
                  disabled={isUploadingCover}
                  className="rounded border border-gray-300 bg-white px-3 py-1 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
                >
                  {isUploadingCover ? 'Uploading…' : manuscript.cover_image_url ? 'Replace Cover' : 'Upload Cover'}
                </button>
                {coverError && <span className="text-sm text-red-600">{coverError}</span>}
              </div>
            </div>

            <div className="flex flex-wrap gap-2 border-t border-gray-200 pt-4">
              <button
                onClick={handleEdit}
                className="rounded border border-gray-300 px-4 py-2 text-sm hover:bg-gray-50"
              >
                Edit
              </button>

              {manuscript.state === 'draft' && (
                <button
                  onClick={handleMarkReady}
                  disabled={markReady.isPending}
                  className="rounded bg-green-600 px-4 py-2 text-sm text-white hover:bg-green-700 disabled:opacity-50"
                >
                  Mark Ready
                </button>
              )}

              {manuscript.state === 'ready' && (
                <button
                  onClick={handleMarkDraft}
                  disabled={markDraft.isPending}
                  className="rounded border border-yellow-400 px-4 py-2 text-sm text-yellow-700 hover:bg-yellow-50 disabled:opacity-50"
                >
                  Revert to Draft
                </button>
              )}

              {manuscript.state === 'ready' && (
                <button
                  onClick={handleArchive}
                  disabled={archiveManuscript.isPending}
                  className="rounded border border-gray-400 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 disabled:opacity-50"
                >
                  Archive
                </button>
              )}

              {manuscript.state === 'archived' && (
                <button
                  onClick={handleUnarchive}
                  disabled={unarchiveManuscript.isPending}
                  className="rounded border border-blue-400 px-4 py-2 text-sm text-blue-700 hover:bg-blue-50 disabled:opacity-50"
                >
                  Unarchive
                </button>
              )}

              <button
                onClick={handleDelete}
                disabled={deleteManuscript.isPending}
                className="rounded bg-red-600 px-4 py-2 text-sm text-white hover:bg-red-700 disabled:opacity-50"
              >
                Delete
              </button>
            </div>
          </>
        )}
      </div>

      {manuscript.state === 'ready' && (
        <div className="mt-6 rounded-lg border border-gray-200 bg-white p-6 shadow">
          <h2 className="mb-4 text-lg font-semibold">Generate Ebook</h2>

          <div className="mb-4">
            <p className="mb-2 text-sm text-gray-600">Select output formats:</p>
            <div className="flex space-x-4">
              {(['epub', 'pdf'] as OutputFormat[]).map((format) => (
                <label key={format} className="flex items-center">
                  <input
                    type="checkbox"
                    checked={selectedFormats.includes(format)}
                    onChange={() => toggleFormat(format)}
                    className="mr-2"
                  />
                  {format.toUpperCase()}
                </label>
              ))}
            </div>
          </div>

          <button
            onClick={handleGenerateEbook}
            disabled={generateEbook.isPending || selectedFormats.length === 0}
            className="rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {generateEbook.isPending ? 'Generating...' : 'Generate Ebook'}
          </button>
        </div>
      )}

      {/* Ebooks Section */}
      <div className="mt-6 rounded-lg border border-gray-200 bg-white p-6 shadow">
        <h2 className="mb-4 text-lg font-semibold">Generated Ebooks</h2>

        {ebooksLoading ? (
          <p className="text-gray-600">Loading ebooks...</p>
        ) : ebooks && ebooks.length > 0 ? (
          <div className="space-y-3">
            {ebooks.map((ebook) => (
              <div
                key={ebook.id}
                className="flex items-center justify-between rounded border border-gray-200 p-3"
              >
                <div className="flex items-center space-x-4">
                  <span className="inline-flex rounded bg-gray-100 px-2 py-1 text-xs font-semibold text-gray-800">
                    {ebook.output_format.toUpperCase()}
                  </span>
                  <span className="text-sm text-gray-600">
                    {formatBytes(ebook.file_size_bytes)}
                  </span>
                  <span className="text-sm text-gray-500">
                    {ebook.download_count} downloads
                  </span>
                  {ebook.sample_id && (
                    <span className="text-xs text-gray-500">(Sample)</span>
                  )}
                </div>
                {manuscript.state === 'draft' ? (
                  <span className="text-sm text-gray-400 italic">
                    Unavailable while in draft
                  </span>
                ) : (
                  <div className="flex flex-col items-end gap-1">
                    <button
                      onClick={() => handleDownloadEbook(ebook.id)}
                      className="rounded bg-blue-600 px-3 py-1 text-sm text-white hover:bg-blue-700"
                    >
                      Download
                    </button>
                    {downloadErrors[ebook.id] && (
                      <span className="text-xs text-red-600">{downloadErrors[ebook.id]}</span>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-500">
            No ebooks generated yet.{' '}
            {manuscript.state === 'draft' && 'Mark the manuscript as ready to generate ebooks.'}
          </p>
        )}
      </div>
    </div>
  );
}
