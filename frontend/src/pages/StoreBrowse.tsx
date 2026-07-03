import { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { storeApi } from '../api/store';
import type { StoreBrowseItem, StoreGenreTree } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const SORT_OPTIONS = [
  { value: 'newest', label: 'Newest' },
  { value: 'oldest', label: 'Oldest' },
  { value: 'a_to_z', label: 'A to Z' },
  { value: 'z_to_a', label: 'Z to A' },
  { value: 'least_expensive', label: 'Price: Low to High' },
  { value: 'most_expensive', label: 'Price: High to Low' },
];

const PER_PAGE = 12;

function flattenGenres(
  tree: StoreGenreTree[] | undefined,
  depth = 0,
): { slug: string; name: string; depth: number }[] {
  if (!tree) return [];
  return tree.flatMap((g) => [
    { slug: g.slug, name: g.name, depth },
    ...flattenGenres(g.children, depth + 1),
  ]);
}

function effectivePrice(item: StoreBrowseItem): string {
  if (item.editions.length === 0) return 'Free';
  if (item.editions.some((e) => e.is_free)) return 'Free';
  return item.editions[0].formatted_price;
}

function BookCard({ item }: { item: StoreBrowseItem }) {
  const formats = [...new Set(item.editions.map((e) => e.output_format.toUpperCase()))];
  const price = effectivePrice(item);

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
        <div className="absolute right-2 top-2 rounded bg-white px-2 py-0.5 text-xs font-semibold text-gray-800 shadow">
          {price}
        </div>
      </div>
      <div className="p-3">
        <h3 className="line-clamp-2 font-semibold text-gray-900 group-hover:text-blue-600">
          {item.title}
        </h3>
        <p className="mt-0.5 text-sm text-gray-500">{item.author.display_name}</p>
        {formats.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1">
            {formats.map((f) => (
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

export function StoreBrowse() {
  const [searchParams, setSearchParams] = useSearchParams();

  const [q, setQ] = useState(searchParams.get('q') || '');
  const [genre, setGenre] = useState(searchParams.get('genre') || '');
  const [tag] = useState(searchParams.get('tag') || '');
  const [sort, setSort] = useState(searchParams.get('sort') || 'newest');
  const [page, setPage] = useState(Number(searchParams.get('page')) || 1);

  useEffect(() => {
    const params: Record<string, string> = {};
    if (q) params.q = q;
    if (genre) params.genre = genre;
    if (tag) params.tag = tag;
    if (sort !== 'newest') params.sort = sort;
    if (page > 1) params.page = String(page);
    setSearchParams(params, { replace: true });
  }, [q, genre, tag, sort, page, setSearchParams]);

  const { data: genreTree } = useQuery({
    queryKey: ['store', 'genres'],
    queryFn: () => storeApi.listGenres(),
  });

  const { data, isLoading, error } = useQuery({
    queryKey: ['store', 'ebooks', { q, genre, tag, sort, page }],
    queryFn: () =>
      storeApi.browseEbooks({
        q: q || undefined,
        genre: genre || undefined,
        tag: tag || undefined,
        sort,
        page,
        per_page: PER_PAGE,
      }),
  });

  const totalPages = data ? Math.ceil(data.total / PER_PAGE) : 1;
  const flatGenres = flattenGenres(genreTree);

  function handleFilterChange(updater: () => void) {
    updater();
    setPage(1);
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-3xl font-bold">Store</h1>
        <p className="mt-1 text-gray-600">Browse published books</p>
      </div>

      <div className="mb-6 flex flex-wrap gap-3">
        <input
          type="text"
          placeholder="Search titles..."
          value={q}
          onChange={(e) => handleFilterChange(() => setQ(e.target.value))}
          className="rounded border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        />
        <select
          value={genre}
          onChange={(e) => handleFilterChange(() => setGenre(e.target.value))}
          className="rounded border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        >
          <option value="">All genres</option>
          {flatGenres.map((g) => (
            <option key={g.slug} value={g.slug}>
              {'  '.repeat(g.depth)}
              {g.name}
            </option>
          ))}
        </select>
        <select
          value={sort}
          onChange={(e) => handleFilterChange(() => setSort(e.target.value))}
          className="rounded border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        >
          {SORT_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
      </div>

      {isLoading && (
        <div className="flex justify-center py-12">
          <div className="text-gray-600">Loading...</div>
        </div>
      )}

      {error && (
        <div className="rounded bg-red-50 p-4 text-red-600">Failed to load listings.</div>
      )}

      {data && (
        <>
          <p className="mb-4 text-sm text-gray-500">
            {data.total} {data.total === 1 ? 'book' : 'books'}
          </p>

          {data.items.length === 0 ? (
            <div className="rounded border-2 border-dashed border-gray-300 p-12 text-center">
              <p className="text-gray-600">No books found.</p>
            </div>
          ) : (
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              {data.items.map((item) => (
                <BookCard key={item.id} item={item} />
              ))}
            </div>
          )}

          {totalPages > 1 && (
            <div className="mt-8 flex items-center justify-center gap-4">
              <button
                onClick={() => setPage((p) => p - 1)}
                disabled={page === 1}
                className="rounded border border-gray-300 px-4 py-2 text-sm disabled:opacity-40 hover:bg-gray-50"
              >
                Previous
              </button>
              <span className="text-sm text-gray-600">
                Page {page} of {totalPages}
              </span>
              <button
                onClick={() => setPage((p) => p + 1)}
                disabled={page === totalPages}
                className="rounded border border-gray-300 px-4 py-2 text-sm disabled:opacity-40 hover:bg-gray-50"
              >
                Next
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
