import { Link } from 'react-router-dom';
import { useManuscripts } from '../hooks/useManuscripts';
import type { ManuscriptState } from '../types';

const stateColors: Record<ManuscriptState, string> = {
  draft: 'bg-yellow-100 text-yellow-800',
  ready: 'bg-green-100 text-green-800',
  archived: 'bg-gray-100 text-gray-800',
};

export function Dashboard() {
  const { data: manuscripts, isLoading, error } = useManuscripts();

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <div className="text-gray-600">Loading manuscripts...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded bg-red-50 p-4 text-red-600">
        Failed to load manuscripts. Please try again.
      </div>
    );
  }

  return (
    <div>
      <div className="mb-8 flex items-center justify-between">
        <h1 className="text-3xl font-bold">My Manuscripts</h1>
        <Link
          to="/manuscripts/new"
          className="rounded bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700"
        >
          New Manuscript
        </Link>
      </div>

      {manuscripts?.length === 0 ? (
        <div className="rounded border-2 border-dashed border-gray-300 p-12 text-center">
          <h3 className="text-lg font-medium text-gray-900">
            No manuscripts yet
          </h3>
          <p className="mt-2 text-gray-600">
            Get started by uploading your first manuscript.
          </p>
          <Link
            to="/manuscripts/new"
            className="mt-4 inline-block rounded bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700"
          >
            Upload Manuscript
          </Link>
        </div>
      ) : (
        <div className="overflow-hidden rounded-lg border border-gray-200 bg-white shadow">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Title
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Format
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  State
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Updated
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 bg-white">
              {manuscripts?.map((manuscript) => (
                <tr key={manuscript.id} className="hover:bg-gray-50">
                  <td className="whitespace-nowrap px-6 py-4">
                    <Link
                      to={`/manuscripts/${manuscript.id}`}
                      className="font-medium text-blue-600 hover:underline"
                    >
                      {manuscript.title}
                    </Link>
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-600">
                    {manuscript.source_format.toUpperCase()}
                  </td>
                  <td className="whitespace-nowrap px-6 py-4">
                    <span
                      className={`inline-flex rounded-full px-2 py-1 text-xs font-semibold ${stateColors[manuscript.state]}`}
                    >
                      {manuscript.state}
                    </span>
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-600">
                    {new Date(manuscript.updated_at).toLocaleDateString()}
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-right text-sm">
                    <Link
                      to={`/manuscripts/${manuscript.id}`}
                      className="text-blue-600 hover:underline"
                    >
                      View
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
