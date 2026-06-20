import { useState, useEffect } from 'react';
import { authApi } from '../api/auth';
import type { Author } from '../types';

export function Profile() {
  const [profile, setProfile] = useState<Author | null>(null);
  const [displayName, setDisplayName] = useState('');
  const [bio, setBio] = useState('');
  const [website, setWebsite] = useState('');
  const [isPublic, setIsPublic] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    authApi.getMe().then((author) => {
      setProfile(author);
      setDisplayName(author.display_name);
      setBio(author.bio ?? '');
      setWebsite(author.website ?? '');
      setIsPublic(author.is_public);
    });
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    setSuccess(false);

    if (!displayName.trim()) {
      setError('Display name cannot be empty.');
      setSaving(false);
      return;
    }

    try {
      const updated = await authApi.updateProfile({
        display_name: displayName,
        bio: bio || null,
        website: website || null,
        is_public: isPublic,
      });
      setProfile(updated);
      setSuccess(true);
    } catch (err: unknown) {
      const detail = (err as { data?: { detail?: string | { msg: string }[] } }).data?.detail;
      if (Array.isArray(detail)) {
        setError(detail.map((d) => d.msg).join(', '));
      } else {
        setError(detail ?? 'Failed to save profile.');
      }
    } finally {
      setSaving(false);
    }
  };

  if (!profile) return <p className="text-gray-600">Loading...</p>;

  return (
    <div className="mx-auto max-w-xl">
      <h1 className="mb-6 text-3xl font-bold">Profile</h1>

      <form onSubmit={handleSubmit} className="space-y-5">
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">
            Display name
          </label>
          <input
            type="text"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            className="w-full rounded border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">
            Bio
          </label>
          <textarea
            value={bio}
            onChange={(e) => setBio(e.target.value)}
            rows={5}
            placeholder="Tell readers about yourself. Markdown supported."
            className="w-full rounded border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">
            Website
          </label>
          <input
            type="text"
            value={website}
            onChange={(e) => setWebsite(e.target.value)}
            placeholder="https://yoursite.com"
            className="w-full rounded border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div className="flex items-center gap-3">
          <input
            id="is-public"
            type="checkbox"
            checked={isPublic}
            onChange={(e) => setIsPublic(e.target.checked)}
            className="h-4 w-4 rounded border-gray-300 text-blue-600"
          />
          <label htmlFor="is-public" className="text-sm text-gray-700">
            Show my profile in the public store
          </label>
        </div>

        {error && <p className="text-sm text-red-600">{error}</p>}
        {success && <p className="text-sm text-green-600">Profile saved.</p>}

        <button
          type="submit"
          disabled={saving}
          className="rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {saving ? 'Saving…' : 'Save'}
        </button>
      </form>
    </div>
  );
}
