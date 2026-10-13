export type SkillLevel =
  | "familiar"
  | "comfortable"
  | "strong"
  | "beginner"
  | "intermediate"
  | "advanced"
  | "expert";

export interface SkillItem {
  category_id: string;
  name: string;
  taxonomy_id?: string | null;
  custom?: boolean;
  pinned?: boolean;
  level?: SkillLevel | null;
}

export interface SocialLink {
  platform_id: string;
  value: string;
}

export interface Location {
  city?: string | null;
  region_country?: string | null;
}

export interface Basics {
  name: string;
  email: string;
  headline?: string | null;
  phone?: string | null;
  location?: Location | null;
  links?: SocialLink[];
}

export interface ExperienceItem {
  company: string;
  title: string;
  location?: string | null;
  start?: string | null;
  end?: string | null;
  current?: boolean;
  bullets: string[];
}

export interface ProjectItem {
  name: string;
  link?: string | null;
  tech: string[];
  bullets: string[];
}

export interface EducationItem {
  school: string;
  degree?: string | null;
  field?: string | null;
  start?: string | null;
  end?: string | null;
  score?: string | null;
  details?: string[];
}

export interface CertificationItem {
  name: string;
  issuer?: string | null;
  date?: string | null;
}

export interface PublicationItem {
  title: string;
  venue?: string | null;
  year?: string | null;
  link?: string | null;
}

export interface CustomSectionItem {
  title: string;
  bullets: string[];
}

export interface ResumeMeta {
  template: "classic" | "compact" | "technical";
  target_role?: string | null;
}

export interface Resume {
  meta: ResumeMeta;
  basics: Basics;
  summary?: string | null;
  skills: SkillItem[];
  experience: ExperienceItem[];
  projects: ProjectItem[];
  education: EducationItem[];
  certifications?: CertificationItem[];
  achievements?: string[];
  publications?: PublicationItem[];
  custom_sections?: CustomSectionItem[];
}

export interface CatalogSkill {
  id: string;
  name: string;
  aliases: string[];
  taxonomy_id?: string | null;
}

export interface CatalogCategory {
  id: string;
  name: string;
  skills: CatalogSkill[];
}

export interface TechCatalog {
  categories: CatalogCategory[];
}

export interface SocialPlatform {
  id: string;
  label: string;
  input_label: string;
  placeholder: string;
  url_template: string;
  accepts_full_url: boolean;
  validator: string;
  default_visible: boolean;
  resume_friendly: boolean;
  hint: string | null;
}

export interface LintIssue {
  level: "error" | "warning" | "tip";
  section: string;
  message: string;
  path: string;
}

export interface AIImproveBulletVariant {
  text: string;
  changes: string[];
  checks: {
    verb: string;
    fact_overlap: number;
    word_count: number;
  };
}

export interface AIImproveBulletResponse {
  source: "slm" | "rules";
  original: string;
  variants: AIImproveBulletVariant[];
}

export interface AISummaryResponse {
  source: "slm" | "rules";
  variants: string[];
}

export interface AIPolishProjectResponse {
  source: "slm" | "rules";
  bullets: string[];
}

export interface AISkillSuggestion {
  name: string;
  category_id: string;
  taxonomy_id: string | null;
  source_sentence: string;
  matched_text: string;
}

export interface AISuggestSkillsResponse {
  suggestions: AISkillSuggestion[];
}

export interface TailorCoveredSkill {
  name: string;
  taxonomy_id: string;
  importance: "required" | "preferred";
}

export interface TailorMissingSkill {
  name: string;
  taxonomy_id: string;
  importance: "required" | "preferred";
  impact: number;
  tier: "high" | "medium" | "low";
}

export interface TailorResponse {
  source: "analyzer";
  target_role: string;
  score: number;
  covered: TailorCoveredSkill[];
  missing: TailorMissingSkill[];
  suggest_only: boolean;
  keyword_coverage?: number;
}
