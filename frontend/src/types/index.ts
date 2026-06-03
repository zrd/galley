// Enums matching backend
export type ManuscriptState = 'draft' | 'ready' | 'archived';
export type SourceFormat = 'epub' | 'pdf' | 'docx' | 'odt';
export type OutputFormat = 'epub' | 'pdf';
export type Visibility = 'private' | 'unlisted' | 'published';

// Auth types
export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  display_name: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

// Author types
export interface Author {
  id: string;
  email: string;
  display_name: string;
  created_at: string;
}

// Manuscript types
export interface Manuscript {
  id: string;
  author_id: string;
  title: string;
  description: string | null;
  source_format: SourceFormat;
  state: ManuscriptState;
  cover_image_key: string | null;
  cover_image_url: string | null;
  created_at: string;
  updated_at: string;
  genres: GenreRead[];
  tags: TagRead[];
}

export interface ManuscriptListItem {
  id: string;
  title: string;
  state: ManuscriptState;
  source_format: SourceFormat;
  cover_image_key: string | null;
  cover_image_url: string | null;
  created_at: string;
  updated_at: string;
  deleted_at: string | null;
}

export interface ManuscriptCreateRequest {
  title: string;
  description?: string;
  source_format: SourceFormat;
  file: File;
  genre_ids?: number[];
  tag_names?: string[];
}

export interface ManuscriptUpdateRequest {
  title?: string;
  description?: string;
  genre_ids?: number[];
  tag_names?: string[];
}

// Ebook types
export interface Ebook {
  id: string;
  manuscript_id: string;
  sample_id: string | null;
  output_format: OutputFormat;
  list_price_cents: number | null;
  sale_price_cents: number | null;
  price_currency: string;
  file_size_bytes: number;
  download_count: number;
  visibility: Visibility;
  unlisted_download_limit: number | null;
  published_at: string | null;
  created_at: string;
}

export interface EbookListItem extends Ebook {
  deleted_at: string | null;
}

export interface EbookGenerateRequest {
  output_formats: OutputFormat[];
}

// Sample types
export interface Sample {
  id: string;
  manuscript_id: string;
  title: string;
  excerpt_start: string;
  excerpt_end: string;
  promo_header: string | null;
  promo_footer: string | null;
  created_at: string;
  updated_at: string;
}

// Tag types
export interface TagRead {
  id: string;
  name: string;
  slug: string;
}

// Genre types
export interface GenreTree {
  id: number;
  name: string;
  slug: string;
  description: string | null;
  children: GenreTree[];
}

export interface GenreListItem {
  id: number;
  name: string;
  slug: string;
  parent_id: number | null;
}

export interface GenreRead {
  id: number;
  name: string;
  slug: string;
  description: string | null;
  parent_id: number | null;
}

export interface GenreCreateRequest {
  name: string;
  description?: string;
  parent_id?: number;
}

// API Error
export interface ApiError {
  detail: string | { loc: string[]; msg: string; type: string }[];
}
