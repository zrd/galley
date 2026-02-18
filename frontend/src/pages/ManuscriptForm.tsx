import { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCreateManuscript } from '../hooks/useManuscripts';
import type { SourceFormat } from '../types';

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
  const [error, setError] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();
  const createManuscript = useCreateManuscript();

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
      });
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
