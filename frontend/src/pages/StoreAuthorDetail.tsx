import { Link, useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { storeApi } from '../api/store';
import type { StoreBrowseItem } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

function ListingCard({ item }: { item: StoreBrowseItem }) {
  const price =
    item.editions.length === 0
      ? null
      : item.editions.some((e) => e.is_free)
        ? 'Free'
        : item.editions[0].formatted_price;

  return (
    <Link
      to={`/store/ebooks/${item.id}`}
      className="group overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm transition-shadow hover:shadow-md"
    >
      <div className="relative aspect-[2/3] bg-gray-100">
        {item.cover_url ? (
          <img
            src={`${API_BASE_URL}${item.cover_url}`}
            alt={item.title}
            className="h-full w-full object-cover"
          />
        ) : (
          <div className="flex h-full items-center justify-center text-5xl text-gray-300">
            📖
          </div>
        )}
        {price && (
          <div className="absolute right-2 top-2 rounded bg-white px-2 py-0.5 text-xs font-semibold text-gray-800 shadow">
            {price}
          </div>
        )}
      </div>
      <div className="p-3">
        <h3 className="font-semibold text-gray-900 group-hover:text-blue-600">
          {item.title}
        </h3>
        {item.editions.length > 0 && (
          <div className="mt-1 flex flex-wrap gap-1">
            {[...new Set(item.editions.map((e) => e.output_format.toUpperCase()))].map((f) => (
              <span key={f} className="rounded bg-gray-100 px-1.5 py-0.5 text-xs text-gray-600">
                {f}
              </span>
            ))}
          </div>
        )}
      </div>
    </Link>
  );
}

export function StoreAuthorDetail() {
  const { id } = useParams<{ id: string }>();

  const { data, isLoading, error } = useQuery({
    queryKey: ['store', 'author', id],
    queryFn: () => storeApi.getAuthor(id!),
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
      <div className="rounded bg-red-50 p-4 text-red-600">Author not found.</div>
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
        {data.display_name}
      </p>

      <div className="mb-8 flex items-start gap-6">
        {data.avatar_url && (
          <img
            src={`${API_BASE_URL}${data.avatar_url}`}
            alt={data.display_name}
            className="h-20 w-20 shrink-0 rounded-full object-cover"
          />
        )}
        <div>
          <h1 className="text-3xl font-bold text-gray-900">{data.display_name}</h1>
          {data.bio && (
            <p className="mt-2 leading-relaxed text-gray-600">{data.bio}</p>
          )}
          {data.website && (
            <p className="mt-2">
              <a
                href={data.website}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-blue-600 hover:underline"
              >
                {data.website}
              </a>
            </p>
          )}
        </div>
      </div>

      <h2 className="mb-4 text-xl font-semibold text-gray-900">Published Books</h2>

      {data.listings.length === 0 ? (
        <div className="rounded border-2 border-dashed border-gray-300 p-12 text-center">
          <p className="text-gray-600">No published books yet.</p>
        </div>
      ) : (
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {data.listings.map((item) => (
            <ListingCard key={item.id} item={item} />
          ))}
        </div>
      )}
    </div>
  );
}
