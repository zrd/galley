import { Link, useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { storeApi } from '../api/store';
import { ApiError } from '../api/client';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

function formatBytes(bytes: number): string {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function StoreEditionDetail() {
  const { id } = useParams<{ id: string }>();

  const { data, isLoading, error } = useQuery({
    queryKey: ['store', 'edition', id],
    queryFn: () => storeApi.getEdition(id!),
    enabled: !!id,
    retry: false,
  });

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <div className="text-gray-600">Loading...</div>
      </div>
    );
  }

  if (error) {
    const isGone = error instanceof ApiError && error.status === 410;
    return (
      <div className="rounded bg-red-50 p-4 text-red-600">
        {isGone
          ? 'This edition is no longer available for download.'
          : 'Edition not found.'}
      </div>
    );
  }

  if (!data) return null;

  const m = data.manuscript;

  return (
    <div className="mx-auto max-w-2xl">
      <p className="mb-6 text-sm text-gray-500">
        <Link to="/store" className="hover:text-blue-600">
          Store
        </Link>
        {' › '}
        <Link to={`/store/ebooks/${m.id}`} className="hover:text-blue-600">
          {m.title}
        </Link>
        {' › '}
        {data.output_format.toUpperCase()} edition
      </p>

      <div className="rounded-lg border border-gray-200 bg-white p-8 shadow">
        <div className="flex items-start gap-6">
          {m.cover_url ? (
            <img
              src={`${API_BASE_URL}${m.cover_url}`}
              alt={m.title}
              className="w-28 shrink-0 rounded shadow"
            />
          ) : (
            <div className="flex aspect-[2/3] w-28 shrink-0 items-center justify-center rounded bg-gray-100 text-3xl text-gray-300">
              📖
            </div>
          )}

          <div className="flex-1">
            <h1 className="text-2xl font-bold text-gray-900">{m.title}</h1>
            <p className="mt-1 text-gray-600">
              by{' '}
              <Link
                to={`/store/authors/${m.author.id}`}
                className="text-blue-600 hover:underline"
              >
                {m.author.display_name}
              </Link>
            </p>

            <dl className="mt-4 space-y-2 text-sm">
              <div className="flex gap-3">
                <dt className="w-24 font-medium text-gray-700">Format</dt>
                <dd>
                  <span className="rounded bg-gray-100 px-2 py-0.5 uppercase text-gray-700">
                    {data.output_format}
                  </span>
                </dd>
              </div>
              <div className="flex gap-3">
                <dt className="w-24 font-medium text-gray-700">File size</dt>
                <dd className="text-gray-600">{formatBytes(data.file_size_bytes)}</dd>
              </div>
              <div className="flex gap-3">
                <dt className="w-24 font-medium text-gray-700">Price</dt>
                <dd
                  className={`font-semibold ${data.is_free ? 'text-green-600' : 'text-gray-900'}`}
                >
                  {data.formatted_price}
                </dd>
              </div>
            </dl>
          </div>
        </div>

        <div className="mt-8 border-t border-gray-100 pt-6">
          <a
            href={`${API_BASE_URL}${data.download_url}`}
            className="block w-full rounded bg-blue-600 px-6 py-3 text-center text-base font-semibold text-white hover:bg-blue-700"
          >
            Download {data.output_format.toUpperCase()}
          </a>
        </div>
      </div>
    </div>
  );
}
