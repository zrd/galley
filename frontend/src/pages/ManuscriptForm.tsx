import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCreateManuscript } from '../hooks/useManuscripts';
import { manuscriptsApi } from '../api/manuscripts';
import { useGenreList } from '../hooks/useGenres';
import type { SourceFormat } from '../types';

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

const SOURCE_FORMATS: { value: SourceFormat; label: string }[] = [
  { value: 'epub', label: 'EPUB' },
  { value: 'pdf', label: 'PDF' },
  { value: 'docx', label: 'Word Document (.docx)' },
  { value: 'odt', label: 'OpenDocument (.odt)' },
];

export function ManuscriptForm() {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [sourceFormat, setSourceFormat] = useState<SourceFormat>('epub');
  const [file, setFile] = useState<File | null>(null);
  const [selectedGenreIds, setSelectedGenreIds] = useState<number[]>([]);
  const [tagNames, setTagNames] = useState<string[]>([]);
  const [coverFile, setCoverFile] = useState<File | null>(null);
  const [coverPreviewUrl, setCoverPreviewUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const coverInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    return () => {
      if (coverPreviewUrl) URL.revokeObjectURL(coverPreviewUrl);
    };
  }, [coverPreviewUrl]);

  const navigate = useNavigate();
  const createManuscript = useCreateManuscript();
  const { data: genres } = useGenreList();

  const handleCoverChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0];
    if (!selected) return;
    if (coverPreviewUrl) URL.revokeObjectURL(coverPreviewUrl);
    setCoverFile(selected);
    setCoverPreviewUrl(URL.createObjectURL(selected));
  };

  const removeCover = () => {
    setCoverFile(null);
    if (coverPreviewUrl) URL.revokeObjectURL(coverPreviewUrl);
    setCoverPreviewUrl(null);
    if (coverInputRef.current) coverInputRef.current.value = '';
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);

      // Auto-detect format from extension
      const extension = selectedFile.name.split('.').pop()?.toLowerCase();
      if (extension && ['epub', 'pdf', 'docx', 'odt'].includes(extension)) {
        setSourceFormat(extension as SourceFormat);
      }
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!file) {
      setError('Please select a file');
      return;
    }

    try {
      const manuscript = await createManuscript.mutateAsync({
        title,
        description: description || undefined,
        source_format: sourceFormat,
        file,
        genre_ids: selectedGenreIds,
        tag_names: tagNames,
      });
      try {
        if (coverFile) {
          await manuscriptsApi.uploadCover(manuscript.id, coverFile);
        }
      } catch {
        // Cover upload failed; navigate anyway — user can re-upload from the detail page
      }
      navigate(`/manuscripts/${manuscript.id}`);
    } catch (err) {
      setError('Failed to create manuscript. Please try again.');
    }
  };

  return (
    <div className="mx-auto max-w-2xl">
      <h1 className="mb-8 text-3xl font-bold">Upload New Manuscript</h1>

      <form onSubmit={handleSubmit} className="space-y-6">
        {error && (
          <div className="rounded bg-red-50 p-4 text-red-600">{error}</div>
        )}

        <div>
          <label
            htmlFor="title"
            className="block text-sm font-medium text-gray-700"
          >
            Title
          </label>
          <input
            id="title"
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
            className="mt-1 block w-full rounded border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>

        <div>
          <label
            htmlFor="description"
            className="block text-sm font-medium text-gray-700"
          >
            Description (optional)
          </label>
          <textarea
            id="description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={3}
            className="mt-1 block w-full rounded border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">
            Genres (optional)
          </label>
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
          <label className="block text-sm font-medium text-gray-700">
            Tags (optional)
          </label>
          <div className="mt-1">
            <TagInput tags={tagNames} onChange={setTagNames} />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">
            Cover Image (optional)
          </label>
          <div className="mt-1 flex items-start gap-4">
            <div className="h-36 w-24 flex-shrink-0 overflow-hidden rounded border border-gray-200 bg-gray-100 shadow-sm">
              {coverPreviewUrl && (
                <img
                  src={coverPreviewUrl}
                  alt="Cover preview"
                  className="h-full w-full object-cover"
                />
              )}
            </div>
            <div className="flex flex-col gap-2">
              <input
                ref={coverInputRef}
                type="file"
                accept=".jpg,.jpeg,.png"
                onChange={handleCoverChange}
                className="hidden"
              />
              <button
                type="button"
                onClick={() => coverInputRef.current?.click()}
                className="rounded border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                {coverFile ? 'Replace Image' : 'Choose Image'}
              </button>
              {coverFile && (
                <>
                  <span className="text-sm text-gray-600">{coverFile.name}</span>
                  <button
                    type="button"
                    onClick={removeCover}
                    className="text-left text-sm text-red-600 hover:text-red-800"
                  >
                    Remove
                  </button>
                </>
              )}
            </div>
          </div>
        </div>

        <div>
          <label
            htmlFor="sourceFormat"
            className="block text-sm font-medium text-gray-700"
          >
            Source Format
          </label>
          <select
            id="sourceFormat"
            value={sourceFormat}
            onChange={(e) => setSourceFormat(e.target.value as SourceFormat)}
            className="mt-1 block w-full rounded border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            {SOURCE_FORMATS.map((format) => (
              <option key={format.value} value={format.value}>
                {format.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">
            Manuscript File
          </label>
          <div className="mt-1">
            <input
              ref={fileInputRef}
              type="file"
              accept=".epub,.pdf,.docx,.odt"
              onChange={handleFileChange}
              className="hidden"
            />
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="rounded border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              Choose File
            </button>
            {file && (
              <span className="ml-3 text-sm text-gray-600">{file.name}</span>
            )}
          </div>
        </div>

        <div className="flex justify-end space-x-4">
          <button
            type="button"
            onClick={() => navigate('/dashboard')}
            className="rounded border border-gray-300 bg-white px-4 py-2 font-medium text-gray-700 hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={createManuscript.isPending}
            className="rounded bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {createManuscript.isPending ? 'Uploading...' : 'Upload Manuscript'}
          </button>
        </div>
      </form>
    </div>
  );
}
