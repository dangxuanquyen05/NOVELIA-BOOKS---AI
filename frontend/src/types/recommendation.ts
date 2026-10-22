/**
 * TypeScript interfaces for BookMatch AI personalized recommendations.
 */

export interface BookRecommendationItem {
  book_id: number;
  title: string;
  slug: string;
  price: number;
  original_price?: number | null;
  primary_author?: string | null;
  cover_image_url?: string | null;
  category_id?: number | null;
  category_name?: string | null;
  available_stock: number;
  match_score: number;
  algorithm_type: string;
  explanation: string;
  explanation_source: 'AI_GENERATED' | 'RULE_BASED_FALLBACK';
}

export interface UserTasteCategory {
  category_id: number;
  name: string;
  weight: number;
}

export interface UserTasteAuthor {
  author_id: number;
  name: string;
  weight: number;
}

export interface UserTasteProfile {
  user_id?: number | null;
  is_cold_start: boolean;
  top_categories: UserTasteCategory[];
  top_authors: UserTasteAuthor[];
  total_orders_analyzed: number;
  total_reviews_analyzed: number;
  total_wishlist_analyzed: number;
}

export interface BookMatchResponse {
  user_id?: number | null;
  is_cold_start: boolean;
  algorithm: string;
  total_candidates_analyzed: number;
  recommendations: BookRecommendationItem[];
  taste_profile?: UserTasteProfile | null;
  generated_at: string;
  disclaimer: string;
}

export interface BaselineComparisonResponse {
  sample_size: number;
  bookmatch_avg_affinity_score: number;
  baseline_avg_affinity_score: number;
  affinity_improvement_pct: number;
  catalog_groundedness_rate: number;
  in_stock_guarantee_rate: number;
  evaluation_notes: string;
}

export interface RecommendationEventCreate {
  book_id: number;
  event_type: 'VIEW' | 'CLICK' | 'ADD_TO_CART' | 'DISMISS' | 'PURCHASE';
  session_id?: string | null;
  metadata_json?: Record<string, unknown>;
}
