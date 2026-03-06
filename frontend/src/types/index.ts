// Enums matching backend
export type ManuscriptState = 'draft' | 'ready' | 'archived';
export type SourceFormat = 'epub' | 'pdf' | 'docx' | 'odt';
export type OutputFormat = 'epub' | 'pdf';

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
  created_at: string;
  updated_at: string;
}

export interface ManuscriptListItem {
  id: string;
  title: string;
  state: ManuscriptState;
  source_format: SourceFormat;
  created_at: string;
  updated_at: string;
  deleted_at: string | null;
}

export interface ManuscriptCreateRequest {
  title: string;
  description?: string;
  source_format: SourceFormat;
  file: File;
}

export interface ManuscriptUpdateRequest {
  title?: string;
  description?: string;
}

// Ebook types
export interface Ebook {
  id: string;
  manuscript_id: string;
  sample_id: string | null;
  output_format: OutputFormat;
  file_size_bytes: number;
  download_count: number;
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
