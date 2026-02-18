import { useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  useManuscript,
  useUpdateManuscript,
  useMarkReady,
  useDeleteManuscript,
  useGenerateEbook,
} from '../hooks/useManuscripts';
import { ebooksApi } from '../api/ebooks';
import type { OutputFormat, ManuscriptState } from '../types';

const stateColors: Record<ManuscriptState, string> = {
  draft: 'bg-yellow-100 text-yellow-800',
  ready: 'bg-green-100 text-green-800',
  archived: 'bg-gray-100 text-gray-800',
};

export function ManuscriptDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const { data: manuscript, isLoading, error } = useManuscript(id!);
  const updateManuscript = useUpdateManuscript();
  const markReady = useMarkReady();
  const deleteManuscript = useDeleteManuscript();
  const generateEbook = useGenerateEbook();

  const [isEditing, setIsEditing] = useState(false);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [selectedFormats, setSelectedFormats] = useState<OutputFormat[]>(['epub']);

  const handleEdit = () => {
    if (manuscript) {
      setTitle(manuscript.title);
      setDescription(manuscript.description || '');
      setIsEditing(true);
    }
  };

  const handleSave = async () => {
    if (!id) return;
    await updateManuscript.mutateAsync({
      id,
      data: { title, description: description || undefined },
    });
    setIsEditing(false);
  };

  const handleMarkReady = async () => {
    if (!id) return;
    await markReady.mutateAsync(id);
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
    } catch {
      alert('Failed to generate ebook. Make sure the manuscript is in READY state.');
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
    </div>
  );
}
