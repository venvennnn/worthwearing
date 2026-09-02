export type Recommendation = "worth_it" | "think_again" | "skip_it";
export type TryOnStatus = "queued" | "processing" | "completed" | "failed";
export type ProviderMode = "live" | "demo" | "disabled";

export type Garment = {
  id: string;
  name: string;
  category: string;
  subcategory: string;
  colors: string[];
  style_tags: string[];
  season_tags: string[];
  occasion_tags: string[];
  layer: string;
  image_url: string;
  price?: number | null;
  description?: string | null;
  brand?: string | null;
};

export type ScenarioAsset = {
  id: string;
  label: string;
  context: string;
  image_url: string;
  alt: string;
};

export type CandidateProduct = Garment & {
  short_label: string;
  demo_role: "duplicative" | "versatile";
  prepared_try_on_url: string;
  prepared_try_on_alt: string;
  scenario_assets: ScenarioAsset[];
};

export type Shopper = {
  id: string;
  name: string;
  photo_url: string;
  photo_alt: string;
  climate_tags: string[];
  target_occasions: string[];
  city: string;
  notes?: string | null;
};

export type FactorComponent = {
  key: string;
  label: string;
  value: number;
  weight: number;
  contribution: number;
  explanation: string;
};

export type MatchedItem = {
  item_id: string;
  name: string;
  image_url: string;
  reason: string;
  similarity?: number | null;
};

export type RejectedCombination = {
  item_ids: string[];
  names: string[];
  rule: string;
  reason: string;
};

export type OutfitPiece = {
  item_id: string;
  name: string;
  image_url: string;
  layer: string;
};

export type CompatibleOutfit = {
  id: string;
  occasion: string;
  pieces: OutfitPiece[];
  rationale: string;
};

export type CostPerWearScenario = {
  price: number;
  estimated_wears: number;
  estimated_cpw: number;
  horizon_months: number;
  formula: string;
  assumptions: string[];
};

export type AnalysisResult = {
  candidate_id: string;
  candidate_name: string;
  recommendation: Recommendation;
  recommendation_label: string;
  return_risk: number;
  worth_score: number;
  wardrobe_compatibility: number;
  factors: FactorComponent[];
  matched_items: MatchedItem[];
  rejected_combinations: RejectedCombination[];
  outfits: CompatibleOutfit[];
  outfit_count: number;
  cost_per_wear: CostPerWearScenario | null;
  summary: string;
  methodology_notes: string[];
  is_prototype: boolean;
};

export type TryOnJob = {
  job_id: string;
  status: TryOnStatus;
  provider: ProviderMode;
  result_image_url?: string | null;
  error_category?: string | null;
  error_message?: string | null;
  prepared_fallback_available: boolean;
  prepared_fallback_url?: string | null;
  elapsed_ms?: number | null;
};

export type DemoPayload = {
  shopper: Shopper;
  closet: Garment[];
  candidates: CandidateProduct[];
  config: {
    wear_horizon_months: number;
    live_timeout_seconds: number;
    target_occasions: string[];
  };
  tagline: string;
  pitch: string;
  close_line: string;
};

export type HealthResponse = {
  status: string;
  try_on_mode: ProviderMode;
  scenario_mode: ProviderMode;
  demo_mode: boolean;
  mcp_active: boolean;
};

export type ScenarioResult = {
  enabled: boolean;
  provider: ProviderMode;
  images: ScenarioAsset[];
  message: string;
};
