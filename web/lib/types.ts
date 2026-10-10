/**
 * TypeScript interfaces matching SkillGap FastAPI schemas.
 */

export interface RoleItem {
  role: string;
  postings_count: number;
  core_skills_count: number;
}

export interface SkillItem {
  skill_id: string;
  name: string;
  category: string;
  aliases: string[];
}

export interface ExtractedSkillItem {
  skill: string;
  skill_id: string;
  category: string;
  confidence: number;
  source: string;
  evidence: string;
}

export interface ScoreBreakdown {
  final: number;
  coverage: number;
  semantic: number;
}

export interface CoveredSkillItem {
  skill: string;
  skill_id: string;
  tier: string;
  weight: number;
  match_type: string;
  earned_weight: number;
}

export interface PartialSkillItem {
  skill: string;
  skill_id: string;
  covered_by: string;
  similarity: number;
}

export interface MissingSkillItem {
  skill: string;
  skill_id: string;
  tier: string;
  weight: number;
  gain_if_learned: number;
}

export interface CategoryCoverageItem {
  category: string;
  coverage_score: number;
  total_weight: number;
  earned_weight: number;
  skills_count: number;
  covered_count: number;
}

export interface CourseDetail {
  course_id: string;
  title: string;
  platform: string;
  level: string;
  duration_hours: number;
  rating: number;
  url: string;
  taught_skills: string[];
}

export interface LearningStepItem {
  step_number: number;
  phase_label: string;
  primary_skill_name: string;
  primary_skill_id: string;
  course: CourseDetail;
  score_gain: number;
  cumulative_score: number;
  why_chosen: string;
}

export interface AnalyzeResponse {
  analysis_id: string;
  extracted_skills: ExtractedSkillItem[];
  score: ScoreBreakdown;
  covered: CoveredSkillItem[];
  partial: PartialSkillItem[];
  missing: MissingSkillItem[];
  category_coverage: CategoryCoverageItem[];
  learning_path: LearningStepItem[];
  summary_text: string;
}

export interface WhatIfResponse {
  original_score: number;
  original_coverage: number;
  new_score: number;
  new_coverage: number;
  delta_final: number;
  delta_coverage: number;
  added_skills: string[];
}

export interface CompareRoleResult {
  role: string;
  final_score: number;
  coverage_score: number;
  semantic_score: number;
  exact_matches_count: number;
  partial_matches_count: number;
  missing_skills_count: number;
}

export interface CompareResponse {
  best_fit_role: string | null;
  best_fit_score: number;
  ranked_roles: CompareRoleResult[];
}
