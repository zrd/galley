import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useEbooks } from '../hooks/useEbooks';
import { useManuscripts } from '../hooks/useManuscripts';
import { ebooksApi } from '../api/ebooks';
import type { OutputFormat } from '../types';

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

const formatLabels: Record<OutputFormat, string> = {
  epub: 'EPUB',
  pdf: 'PDF',
};

export function Ebooks() {
  const { data: ebooks, isLoading: ebooksLoading, error: ebooksError } = useEbooks();
  const { data: manuscripts, isLoading: manuscriptsLoading } = useManuscripts();
  const [downloadErrors, setDownloadErrors] = useState<Record<string, string>>({});

  const isLoading = ebooksLoading || manuscriptsLoading;

  const getManuscriptTitle = (manuscriptId: string) => {
    const manuscript = manuscripts?.find((m) => m.id === manuscriptId);
    return manuscript?.title || 'Unknown Manuscript';
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
    const blob = await response.blob();
    const objectUrl = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = objectUrl;
    a.click();
    URL.revokeObjectURL(objectUrl);
  };

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <div className="text-gray-600">Loading ebooks...</div>
      </div>
    );
  }

  if (ebooksError) {
    return (
      <div className="rounded bg-red-50 p-4 text-red-600">
        Failed to load ebooks. Please try again.
      </div>
    );
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold">My Ebooks</h1>
        <p className="mt-2 text-gray-600">
          Download your generated ebooks or view their details.
        </p>
      </div>

      {ebooks?.length === 0 ? (
        <div className="rounded border-2 border-dashed border-gray-300 p-12 text-center">
          <h3 className="text-lg font-medium text-gray-900">No ebooks yet</h3>
          <p className="mt-2 text-gray-600">
            Generate ebooks from your manuscripts to see them here.
          </p>
          <Link
            to="/dashboard"
            className="mt-4 inline-block rounded bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700"
          >
            View Manuscripts
          </Link>
        </div>
      ) : (
        <div className="overflow-hidden rounded-lg border border-gray-200 bg-white shadow">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="w-16 px-4 py-3" />
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Manuscript
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Format
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Size
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Downloads
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Created
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 bg-white">
              {ebooks?.map((ebook) => {
                const manuscript = manuscripts?.find((m) => m.id === ebook.manuscript_id);
                return (
                <tr key={ebook.id} className="hover:bg-gray-50">
                  <td className="px-4 py-2 align-middle">
                    {manuscript?.cover_image_url ? (
                      <div className="h-24 w-16 overflow-hidden rounded shadow-sm">
                        <img
                          src={`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}${manuscript.cover_image_url}?t=${manuscript.updated_at}`}
                          alt=""
                          className="h-full w-full object-cover"
                        />
                      </div>
                    ) : (
                      <div className="h-24 w-16 rounded bg-gray-100" />
                    )}
                  </td>
                  <td className="whitespace-nowrap px-6 py-2 align-middle">
                    <Link
                      to={`/manuscripts/${ebook.manuscript_id}`}
                      className="font-medium text-blue-600 hover:underline"
                    >
                      {getManuscriptTitle(ebook.manuscript_id)}
                    </Link>
                    {ebook.sample_id && (
                      <span className="ml-2 text-xs text-gray-500">(Sample)</span>
                    )}
                  </td>
                  <td className="whitespace-nowrap px-6 py-2 align-middle">
                    <span className="inline-flex rounded bg-gray-100 px-2 py-1 text-xs font-semibold text-gray-800">
                      {formatLabels[ebook.output_format]}
                    </span>
                  </td>
                  <td className="whitespace-nowrap px-6 py-2 align-middle text-sm text-gray-600">
                    {formatBytes(ebook.file_size_bytes)}
                  </td>
                  <td className="whitespace-nowrap px-6 py-2 align-middle text-sm text-gray-600">
                    {ebook.download_count}
                  </td>
                  <td className="whitespace-nowrap px-6 py-2 align-middle text-sm text-gray-600">
                    {new Date(ebook.created_at).toLocaleDateString()}
                  </td>
                  <td className="whitespace-nowrap px-6 py-2 align-middle text-right text-sm">
                    {manuscript?.state === 'draft' ? (
                      <span className="text-gray-400 italic">Unavailable while in draft</span>
                    ) : (
                      <div className="flex flex-col items-end gap-1">
                        <button
                          onClick={() => handleDownloadEbook(ebook.id)}
                          className="rounded bg-blue-600 px-3 py-1 text-white hover:bg-blue-700"
                        >
                          Download
                        </button>
                        {downloadErrors[ebook.id] && (
                          <span className="text-xs text-red-600">{downloadErrors[ebook.id]}</span>
                        )}
                      </div>
                    )}
                  </td>
                </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
