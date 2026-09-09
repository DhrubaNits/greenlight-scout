// ============================================================
// ANALYSIS REQUEST
// ============================================================

export interface AnalyzeRequest {
  location: string;
  scene_description: string;
  requirements: string[];
}


// ============================================================
// SCENE ANALYSIS
// ============================================================

export interface SceneAnalysis {
  night_shoot: boolean;
  drone_required: boolean;
  road_closure_required: boolean;
  emergency_vehicle: boolean;
  crowd_present: boolean;
  special_effects: boolean;
  research_required: boolean;
}


// ============================================================
// CLAIM
// ============================================================

export interface Claim {
  claim_id: string;

  category: string;

  statement: string;

  status:
    | "VERIFIED"
    | "REQUIRES_CONFIRMATION";

  source_ids: string[];

  excerpt_ids: string[];

  reason?: string | null;

  semantic_reason?: string | null;

  support_level?: string | null;
}


// ============================================================
// SOURCE
// ============================================================

export interface Source {
  source_id: string;

  title: string;

  url: string;

  publish_date?: string | null;

  authority_level: string;
}


// ============================================================
// METRICS
// ============================================================

export interface Metrics {
  sources_retrieved: number;

  claims_proposed: number;

  candidate_verified: number;

  final_verified: number;

  requires_confirmation: number;
}


// ============================================================
// ANALYSIS RESPONSE
// ============================================================

export interface AnalyzeResponse {
  status: string;

  request_id: string;

  location: string;

  scene_analysis: SceneAnalysis;

  verified_findings: Claim[];

  requires_confirmation: Claim[];

  open_questions: string[];

  sources: Source[];

  metrics: Metrics;
}


// ============================================================
// SAVED ANALYSIS RESPONSE
// ============================================================

export interface SavedAnalysisResponse {
  analysis_id: string;

  location: string;

  scene_description: string;

  requirements: string[];

  analysis: AnalyzeResponse;

  created_at: string;
}


// ============================================================
// HUMAN DECISION
// ============================================================

export type DecisionType =
  | "GREENLIGHT"
  | "GREENLIGHT_WITH_CONDITIONS"
  | "DO_NOT_GREENLIGHT";


export type ReviewItemType =
  | "CONFIRMATION"
  | "OPEN_QUESTION";


export interface ReviewedItem {
  item_id: string;

  item_type: ReviewItemType;

  title: string;

  reviewed: boolean;

  resolution?: string | null;
}


export interface DecisionRequest {
  analysis_id: string;

  decision: DecisionType;

  decision_notes?: string | null;

  reviewer_name?: string | null;

  reviewed_items: ReviewedItem[];
}


export interface DecisionResponse {
  analysis_id: string;

  decision: DecisionType;

  decision_notes?: string | null;

  reviewer_name?: string | null;

  reviewed_items: ReviewedItem[];

  created_at: string;

  updated_at: string;

  status: string;
}


export interface DecisionHistoryItem {
  history_id: number;

  analysis_id: string;

  decision: DecisionType;

  decision_notes?: string | null;

  reviewer_name?: string | null;

  reviewed_items: ReviewedItem[];

  recorded_at: string;
}