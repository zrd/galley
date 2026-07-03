import { Link, useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { storeApi } from '../api/store';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export function StoreManuscriptDetail() {
  const { id } = useParams<{ id: string }>();

  const { data, isLoading, error } = useQuery({
    queryKey: ['store', 'listing', id],
    queryFn: () => storeApi.getListing(id!),
    enabled: !!id,
  });

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <div className="text-gray-600">Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded bg-red-50 p-4 text-red-600">Book not found.</div>
    );
  }

  if (!data) return null;

  return (
    <div>
      <p className="mb-6 text-sm text-gray-500">
        <Link to="/store" className="hover:text-blue-600">
          Store
        </Link>
        {' › '}
        {data.title}
      </p>

      <div className="flex flex-col gap-8 md:flex-row">
        <div className="w-full shrink-0 md:w-56">
          {data.cover_url ? (
            <img
              src={`${API_BASE_URL}${data.cover_url}`}
              alt={data.title}
              className="w-full rounded-lg shadow"
            />
          ) : (
            <div className="flex aspect-[2/3] items-center justify-center rounded-lg bg-gray-100 text-6xl text-gray-300">
              📖
            </div>
          )}
        </div>

        <div className="flex-1">
          <h1 className="text-3xl font-bold text-gray-900">{data.title}</h1>
          <p className="mt-1 text-lg text-gray-600">
            by{' '}
            <Link
              to={`/store/authors/${data.author.id}`}
              className="text-blue-600 hover:underline"
            >
              {data.author.display_name}
            </Link>
          </p>

          {data.description && (
            <p className="mt-4 leading-relaxed text-gray-700">{data.description}</p>
          )}

          {data.genres.length > 0 && (
            <div className="mt-4 flex flex-wrap gap-2">
              {data.genres.map((g) => (
                <Link
                  key={g.id}
                  to={`/store?genre=${g.slug}`}
                  className="rounded-full bg-blue-50 px-3 py-1 text-sm text-blue-700 hover:bg-blue-100"
                >
                  {g.name}
                </Link>
              ))}
            </div>
          )}

          {data.tags.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-2">
              {data.tags.map((t) => (
                <span
                  key={t.id}
                  className="rounded-full bg-purple-50 px-3 py-1 text-sm text-purple-700"
                >
                  {t.name}
                </span>
              ))}
            </div>
          )}

          <div className="mt-6">
            <h2 className="text-lg font-semibold text-gray-900">Editions</h2>
            {data.editions.length === 0 ? (
              <p className="mt-2 text-sm text-gray-500">No editions available.</p>
            ) : (
              <div className="mt-3 space-y-3">
                {data.editions.map((edition) => (
                  <Link
                    key={edition.id}
                    to={`/store/editions/${edition.id}`}
                    className="flex items-center justify-between rounded-lg border border-gray-200 bg-white p-4 shadow-sm transition-shadow hover:shadow-md"
                  >
                    <div className="flex items-center gap-3">
                      <span className="rounded bg-gray-100 px-2 py-1 text-sm font-medium uppercase text-gray-700">
                        {edition.output_format}
                      </span>
                      {edition.published_at && (
                        <span className="text-sm text-gray-500">
                          {new Date(edition.published_at).toLocaleDateString()}
                        </span>
                      )}
                    </div>
                    <span
                      className={`font-semibold ${edition.is_free ? 'text-green-600' : 'text-gray-900'}`}
                    >
                      {edition.formatted_price}
                    </span>
                  </Link>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
