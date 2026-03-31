import { useTags } from '../hooks/useTags';

export function Tags() {
  const { data: tags, isLoading } = useTags();

  return (
    <div className="mx-auto max-w-2xl">
      <h1 className="mb-6 text-3xl font-bold">Tags</h1>

      {isLoading ? (
        <p className="text-gray-600">Loading tags...</p>
      ) : tags && tags.length > 0 ? (
        <div className="flex flex-wrap gap-2">
          {tags.map((tag) => (
            <span
              key={tag.id}
              className="inline-flex rounded-full bg-purple-100 px-3 py-1 text-sm font-medium text-purple-800"
            >
              {tag.name}
            </span>
          ))}
        </div>
      ) : (
        <p className="text-gray-500">
          No tags yet. Add tags when uploading or editing a manuscript.
        </p>
      )}
    </div>
  );
}
