import { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  useEbooks,
  usePublishEbook,
  useUnlistEbook,
  useMakePrivateEbook,
  useUpdateEbookPrice,
} from '../hooks/useEbooks';
import { useManuscripts } from '../hooks/useManuscripts';
import { ebooksApi } from '../api/ebooks';
import type { EbookListItem, OutputFormat, Visibility } from '../types';

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

const formatLabels: Record<OutputFormat, string> = {
  epub: 'EPUB',
  pdf: 'PDF',
};

const visibilityConfig: Record<Visibility, { label: string; dot: string; text: string }> = {
  private: { label: 'Private', dot: 'bg-gray-400', text: 'text-gray-600' },
  unlisted: { label: 'Unlisted', dot: 'bg-amber-400', text: 'text-amber-700' },
  published: { label: 'Published', dot: 'bg-green-500', text: 'text-green-700' },
};

function centsToDollars(cents: number | null): string {
  if (cents === null) return '';
  return (cents / 100).toFixed(2);
}

function dollarsToCents(dollars: string): number | null {
  const trimmed = dollars.trim();
  if (!trimmed) return null;
  const val = parseFloat(trimmed);
  if (isNaN(val) || val < 0) return null;
  return Math.round(val * 100);
}

function VisibilityCell({ ebook }: { ebook: EbookListItem }) {
  const publish = usePublishEbook();
  const unlist = useUnlistEbook();
  const makePrivate = useMakePrivateEbook();
  const [copied, setCopied] = useState(false);
  const cfg = visibilityConfig[ebook.visibility];
  const isPending = publish.isPending || unlist.isPending || makePrivate.isPending;
  const error = publish.error || unlist.error || makePrivate.error;

  const unlistedUrl = `${window.location.origin}/store/editions/${ebook.id}`;

  const copyLink = () => {
    navigator.clipboard.writeText(unlistedUrl).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  return (
    <div className="space-y-2">
      <div className={`flex items-center gap-1.5 text-sm font-medium ${cfg.text}`}>
        <span className={`inline-block h-2 w-2 rounded-full ${cfg.dot}`} />
        {cfg.label}
      </div>
      <div className="flex flex-wrap gap-1">
        {ebook.visibility !== 'published' && (
          <button
            onClick={() => publish.mutate(ebook.id)}
            disabled={isPending}
            className="rounded bg-green-600 px-2 py-0.5 text-xs text-white hover:bg-green-700 disabled:opacity-50"
          >
            Publish
          </button>
        )}
        {ebook.visibility !== 'unlisted' && (
          <button
            onClick={() => unlist.mutate(ebook.id)}
            disabled={isPending}
            className="rounded bg-amber-500 px-2 py-0.5 text-xs text-white hover:bg-amber-600 disabled:opacity-50"
          >
            Unlist
          </button>
        )}
        {ebook.visibility !== 'private' && (
          <button
            onClick={() => makePrivate.mutate(ebook.id)}
            disabled={isPending}
            className="rounded bg-gray-500 px-2 py-0.5 text-xs text-white hover:bg-gray-600 disabled:opacity-50"
          >
            Make Private
          </button>
        )}
      </div>
      {(ebook.visibility === 'published' || ebook.visibility === 'unlisted') && (
        <div className="flex items-center gap-2">
          <Link
            to={`/store/editions/${ebook.id}`}
            className="text-xs text-blue-600 hover:underline"
          >
            View in Store
          </Link>
          <button
            onClick={copyLink}
            className="shrink-0 rounded border border-gray-300 bg-white px-1.5 py-0.5 text-xs text-gray-600 hover:bg-gray-50"
          >
            {copied ? 'Copied!' : 'Copy Link'}
          </button>
        </div>
      )}
      {error && <p className="text-xs text-red-600">Action failed.</p>}
    </div>
  );
}

function PriceCell({ ebook }: { ebook: EbookListItem }) {
  const [editing, setEditing] = useState(false);
  const [listInput, setListInput] = useState('');
  const [saleInput, setSaleInput] = useState('');
  const [validationError, setValidationError] = useState<string | null>(null);
  const updatePrice = useUpdateEbookPrice();

  const effectiveCents =
    ebook.sale_price_cents ?? ebook.list_price_cents ?? 0;
  const displayPrice =
    effectiveCents === 0 ? 'Free' : `$${(effectiveCents / 100).toFixed(2)}`;

  function openEdit() {
    setListInput(centsToDollars(ebook.list_price_cents));
    setSaleInput(centsToDollars(ebook.sale_price_cents));
    setValidationError(null);
    setEditing(true);
  }

  function cancel() {
    setEditing(false);
    setValidationError(null);
    updatePrice.reset();
  }

  async function save() {
    setValidationError(null);
    const listCents = listInput.trim() ? dollarsToCents(listInput) : null;
    const saleCents = saleInput.trim() ? dollarsToCents(saleInput) : null;

    if (listInput.trim() && listCents === null) {
      setValidationError('Invalid list price.');
      return;
    }
    if (saleInput.trim() && saleCents === null) {
      setValidationError('Invalid sale price.');
      return;
    }
    if (saleCents !== null && listCents !== null && saleCents >= listCents) {
      setValidationError('Sale price must be less than list price.');
      return;
    }

    try {
      await updatePrice.mutateAsync({ id: ebook.id, list_price_cents: listCents, sale_price_cents: saleCents });
      setEditing(false);
    } catch {
      // error shown below
    }
  }

  if (!editing) {
    return (
      <div className="flex items-center gap-2">
        <span className="text-sm text-gray-700">{displayPrice}</span>
        {ebook.list_price_cents !== null && ebook.sale_price_cents !== null && (
          <span className="text-xs text-gray-400 line-through">
            ${(ebook.list_price_cents / 100).toFixed(2)}
          </span>
        )}
        <button
          onClick={openEdit}
          className="text-xs text-blue-600 hover:underline"
        >
          Edit
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-2 text-sm">
      <div className="flex items-center gap-1.5">
        <span className="w-10 shrink-0 text-gray-600">List</span>
        <span className="text-gray-400">$</span>
        <input
          type="number"
          min="0"
          step="0.01"
          placeholder="0.00"
          value={listInput}
          onChange={(e) => setListInput(e.target.value)}
          className="w-20 rounded border border-gray-300 px-2 py-0.5 text-sm focus:border-blue-500 focus:outline-none"
        />
      </div>
      <div className="flex items-center gap-1.5">
        <span className="w-10 shrink-0 text-gray-600">Sale</span>
        <span className="text-gray-400">$</span>
        <input
          type="number"
          min="0"
          step="0.01"
          placeholder="optional"
          value={saleInput}
          onChange={(e) => setSaleInput(e.target.value)}
          className="w-20 rounded border border-gray-300 px-2 py-0.5 text-sm focus:border-blue-500 focus:outline-none"
        />
      </div>
      {(validationError || updatePrice.error) && (
        <p className="text-xs text-red-600">{validationError ?? 'Save failed.'}</p>
      )}
      <div className="flex gap-2">
        <button
          onClick={save}
          disabled={updatePrice.isPending}
          className="rounded bg-blue-600 px-2 py-0.5 text-xs text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {updatePrice.isPending ? 'Saving…' : 'Save'}
        </button>
        <button
          onClick={cancel}
          className="rounded border border-gray-300 px-2 py-0.5 text-xs text-gray-600 hover:bg-gray-50"
        >
          Cancel
        </button>
      </div>
    </div>
  );
}

export function Ebooks() {
  const { data: ebooks, isLoading: ebooksLoading, error: ebooksError } = useEbooks();
  const { data: manuscripts, isLoading: manuscriptsLoading } = useManuscripts();
  const [downloadErrors, setDownloadErrors] = useState<Record<string, string>>({});

  const isLoading = ebooksLoading || manuscriptsLoading;

  const getManuscript = (manuscriptId: string) =>
    manuscripts?.find((m) => m.id === manuscriptId);

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
    setDownloadErrors((prev) => {
      const next = { ...prev };
      delete next[ebookId];
      return next;
    });
    const cd = response.headers.get('Content-Disposition');
    const match =
      cd?.match(/filename\*=UTF-8''([^;]+)/i) ?? cd?.match(/filename="([^"]+)"/i);
    const filename = match ? decodeURIComponent(match[1]) : 'download.epub';
    const blob = await response.blob();
    const objectUrl = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = objectUrl;
    a.download = filename;
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
          Manage visibility and pricing, or download your generated ebooks.
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
        <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white shadow">
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
                  Visibility
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Price
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">
                  Download
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 bg-white">
              {ebooks?.map((ebook) => {
                const manuscript = getManuscript(ebook.manuscript_id);
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
                        {manuscript?.title ?? 'Unknown Manuscript'}
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
                    <td className="px-6 py-2 align-middle">
                      {manuscript?.state === 'draft' ? (
                        <span className="text-xs italic text-gray-400">
                          Unavailable in draft
                        </span>
                      ) : (
                        <VisibilityCell ebook={ebook} />
                      )}
                    </td>
                    <td className="px-6 py-2 align-middle">
                      <PriceCell ebook={ebook} />
                    </td>
                    <td className="whitespace-nowrap px-6 py-2 align-middle text-right">
                      {manuscript?.state === 'draft' ? (
                        <span className="text-xs italic text-gray-400">Unavailable</span>
                      ) : (
                        <div className="flex flex-col items-end gap-1">
                          <button
                            onClick={() => handleDownloadEbook(ebook.id)}
                            className="rounded bg-blue-600 px-3 py-1 text-sm text-white hover:bg-blue-700"
                          >
                            Download
                          </button>
                          {downloadErrors[ebook.id] && (
                            <span className="text-xs text-red-600">
                              {downloadErrors[ebook.id]}
                            </span>
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
